from __future__ import annotations

import argparse
import csv
import os

import numpy as np
import torch
from torch import nn

from .config import CATEGORICAL_SPECS, CLASSES, TrainingConfig, categorical_cardinalities
from .data import DatasetShard, assign_train_val, load_all_shards
from .model import Ensemble, GGFClassifier, linear_layers
from .sampling import OversampledBatchIterator, ProcessSubset

"""
Trains the GGF signal-extraction DNN following AN-25-103 Sec. 5.3, 4-way
softmax (HH/TT/DY/SingleH). Requires --data-root pointing at an accessible
directory with AnaTupleMergeTask-style anaTuple output (local mount or EOS
path) -- the local repo mirror is empty, so this has not been run end-to-end
against real data. See DNN_training/{model,sampling,data}.py __main__ blocks
for synthetic smoke tests that don't need real data.
"""


class BatchStepLR:
    """Halves the LR every `halve_every_n_epochs * batches_per_epoch` optimizer steps."""

    def __init__(self, optimizer, batches_per_epoch: int, halve_every_n_epochs: int):
        self.optimizer = optimizer
        self.step_interval = batches_per_epoch * halve_every_n_epochs
        self._step_count = 0

    def step(self):
        self._step_count += 1
        if self._step_count % self.step_interval == 0:
            for g in self.optimizer.param_groups:
                g["lr"] *= 0.5


def build_optimizer(model: nn.Module, initial_lr: float, decay_factor: float) -> torch.optim.AdamW:
    """AdamW with weight decay applied only to Linear-layer weights, one param
    group per layer, normalized by the layer's weight count (AN Sec. 5.3.4)."""
    decayed_ids = set()
    param_groups = []
    for layer in linear_layers(model):
        n_weights = layer.weight.numel()
        param_groups.append({"params": [layer.weight], "weight_decay": decay_factor / n_weights})
        decayed_ids.add(id(layer.weight))

    other_params = [p for p in model.parameters() if id(p) not in decayed_ids]
    param_groups.append({"params": other_params, "weight_decay": 0.0})

    return torch.optim.AdamW(param_groups, lr=initial_lr)


def to_tensors(shard: DatasetShard, idx: np.ndarray, device: str):
    cat_inputs = {name: torch.as_tensor(shard.cat_inputs[name][idx], device=device) for name in CATEGORICAL_SPECS}
    lbn_vectors = torch.as_tensor(shard.lbn_vectors[idx], device=device)
    extra_continuous = torch.as_tensor(shard.extra_continuous[idx], device=device)
    label = torch.as_tensor(shard.label[idx], device=device)
    return cat_inputs, lbn_vectors, extra_continuous, label


def gather_split(shards: list[DatasetShard], idx_by_shard: dict[int, np.ndarray], device: str, weight_fn=None):
    """Concatenates a given split (train/val/test) across all shards into flat
    tensors, in the fixed order `enumerate(shards)` skipping shards with an
    empty idx -- callers that build sample indices into this split (e.g. the
    oversampling subsets in train_one_model) must use the exact same order/
    skip logic to stay aligned with the returned tensors.

    *weight_fn(shard) -> np.ndarray*, if given, replaces the physical
    shard.weight with a per-shard-computed array (same length) before slicing
    by idx; used for the class-equal-representation diagnostic weighting
    (AN Sec. 5.3.6). Defaults to the physical weight (used as-is by evaluate.py).
    """
    cats, lbns, conts, labels, weights = [], [], [], [], []
    for i, shard in enumerate(shards):
        idx = idx_by_shard[i]
        if len(idx) == 0:
            continue
        c, l, e, lab = to_tensors(shard, idx, device)
        w_source = weight_fn(shard) if weight_fn is not None else shard.weight
        w = torch.as_tensor(w_source[idx], device=device)
        cats.append(c)
        lbns.append(l)
        conts.append(e)
        labels.append(lab)
        weights.append(w)
    cat_inputs = {name: torch.cat([c[name] for c in cats]) for name in CATEGORICAL_SPECS}
    return cat_inputs, torch.cat(lbns), torch.cat(conts), torch.cat(labels), torch.cat(weights)


def cross_entropy(probs: torch.Tensor, label: torch.Tensor) -> torch.Tensor:
    logp = torch.log(probs.gather(1, label.unsqueeze(1)).squeeze(1).clamp_min(1e-12))
    return -logp.mean()


def weighted_cross_entropy(probs: torch.Tensor, label: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    logp = torch.log(probs.gather(1, label.unsqueeze(1)).squeeze(1).clamp_min(1e-12))
    return -(weight * logp).sum() / weight.sum().clamp_min(1e-12)


def evaluate_loss(model: nn.Module, split, device: str, batch_size: int = 8192) -> float:
    cat_inputs, lbn_vectors, extra_continuous, label, weight = split
    n = len(label)
    model.eval()
    total_loss, total_weight = 0.0, 0.0
    with torch.no_grad():
        for start in range(0, n, batch_size):
            sl = slice(start, start + batch_size)
            probs = model({k: v[sl] for k, v in cat_inputs.items()}, lbn_vectors[sl], extra_continuous[sl])
            w = weight[sl]
            loss = weighted_cross_entropy(probs, label[sl], w)
            total_loss += loss.item() * w.sum().item()
            total_weight += w.sum().item()
    model.train()
    return total_loss / max(total_weight, 1e-12)


def train_one_model(
    shards: list[DatasetShard],
    test_fold: int,
    seed: int,
    cfg: TrainingConfig,
    device: str,
    log_path: str,
) -> GGFClassifier:
    torch.manual_seed(seed)
    np.random.seed(seed)

    train_idx, val_idx, _ = assign_train_val(shards, test_fold, cfg.kfold.val_fraction, cfg.kfold.split_seed)

    # Oversampling subsets: `indices` are positions into the *flat* train_split
    # tensors built below by gather_split (not shard-local indices) -- this
    # relies on iterating `shards` in the same fixed order and skipping empty
    # train_idx[i] exactly like gather_split does, so the offsets line up.
    subsets = []
    offset = 0
    for i, shard in enumerate(shards):
        idx = train_idx[i]
        if len(idx) == 0:
            continue
        n_i = len(idx)
        subsets.append(ProcessSubset(
            class_name=shard.class_name,
            subprocess=shard.subprocess,
            indices=np.arange(offset, offset + n_i),
            total_weight=float(shard.weight[idx].sum()),
        ))
        offset += n_i

    # Per-class scale factor so each class contributes cfg.data.class_weights[c]
    # of the total physical weight in the non-oversampled train/val loss
    # diagnostic (AN Sec. 5.3.6: "weights ... which represent the oversampling
    # frequency"). The oversampled training step itself is unweighted (see
    # cross_entropy() below) since the oversampling already balances classes.
    class_totals = {c: 0.0 for c in CLASSES}
    for s in subsets:
        class_totals[s.class_name] += s.total_weight
    grand_total = sum(class_totals.values())
    class_scale = {
        c: (cfg.data.class_weights[c] * grand_total / class_totals[c]) if class_totals[c] > 0 else 0.0
        for c in CLASSES
    }

    def diagnostic_weight_fn(shard: DatasetShard) -> np.ndarray:
        return shard.weight * class_scale[shard.class_name]

    train_split = gather_split(shards, train_idx, device, weight_fn=diagnostic_weight_fn)
    val_split = gather_split(shards, val_idx, device, weight_fn=diagnostic_weight_fn)

    model = GGFClassifier(cfg.model, categorical_cardinalities()).to(device)
    optimizer = build_optimizer(model, cfg.optim.initial_lr, cfg.optim.weight_decay_factor)
    scheduler = BatchStepLR(optimizer, cfg.optim.batches_per_epoch, cfg.optim.lr_halve_every_n_epochs)
    batch_iter = iter(OversampledBatchIterator(subsets, cfg.data.batch_size, cfg.data.class_weights))

    best_val_loss = float("inf")
    best_state = None
    epochs_without_improvement = 0
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", newline="") as log_file:
        writer = csv.writer(log_file)
        writer.writerow(["epoch", "train_loss", "val_loss", "lr"])

        epoch = 0
        while epochs_without_improvement < cfg.optim.early_stop_patience:
            model.train()
            for _ in range(cfg.optim.batches_per_epoch):
                batch_idx = torch.as_tensor(next(batch_iter), device=device, dtype=torch.long)
                cat_b = {k: v[batch_idx] for k, v in train_split[0].items()}
                lbn_b = train_split[1][batch_idx]
                cont_b = train_split[2][batch_idx]
                label_b = train_split[3][batch_idx]

                optimizer.zero_grad()
                probs = model(cat_b, lbn_b, cont_b)
                # unweighted: the oversampling algorithm already balances class
                # representation within the batch (AN Sec. 5.3.5-5.3.6)
                loss = cross_entropy(probs, label_b)
                loss.backward()
                optimizer.step()
                scheduler.step()

            train_loss = evaluate_loss(model, train_split, device)
            val_loss = evaluate_loss(model, val_split, device)
            lr = optimizer.param_groups[0]["lr"]
            writer.writerow([epoch, train_loss, val_loss, lr])
            log_file.flush()
            print(f"[fold {test_fold} seed {seed}] epoch {epoch}: train={train_loss:.4f} val={val_loss:.4f} lr={lr:.2e}")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                epochs_without_improvement = 0
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
            else:
                epochs_without_improvement += 1
            epoch += 1

    model.load_state_dict(best_state)
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--fold", type=int, default=None, help="train a single fold (default: all 5)")
    parser.add_argument("--n-seeds", type=int, default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    cfg = TrainingConfig.from_yaml(args.config) if args.config else TrainingConfig()
    cfg.data.data_root = args.data_root
    if args.n_seeds is not None:
        cfg.kfold.n_seeds = args.n_seeds
    if args.output_dir is not None:
        cfg.output_dir = args.output_dir

    shards = load_all_shards(cfg.data, cfg.kfold.n_folds)
    if not shards:
        raise RuntimeError(f"No anaTuple shards found under {cfg.data.data_root}; check --data-root and config.")

    folds = [args.fold] if args.fold is not None else range(cfg.kfold.n_folds)
    for fold in folds:
        seed_models = []
        for seed in range(cfg.kfold.n_seeds):
            log_path = os.path.join(cfg.output_dir, f"logs/fold{fold}_seed{seed}.csv")
            model = train_one_model(shards, fold, seed, cfg, args.device, log_path)
            seed_dir = os.path.join(cfg.output_dir, f"fold{fold}_seed{seed}")
            os.makedirs(seed_dir, exist_ok=True)
            torch.save(model.state_dict(), os.path.join(seed_dir, "model.pt"))
            seed_models.append(model)

        ensemble = Ensemble(seed_models)
        moe_path = os.path.join(cfg.output_dir, f"model_fold{fold}_moe.pt")
        torch.save(ensemble.state_dict(), moe_path)
        print(f"Saved fold {fold} ensemble ({cfg.kfold.n_seeds} seeds) to {moe_path}")


if __name__ == "__main__":
    main()
