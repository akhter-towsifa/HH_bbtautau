from __future__ import annotations

import argparse
import os

import torch
from sklearn.metrics import confusion_matrix, roc_auc_score

from .config import CLASSES, ModelConfig, TrainingConfig, categorical_cardinalities
from .data import assign_train_val, load_all_shards
from .model import Ensemble, GGFClassifier
from .train import gather_split


def load_ensemble(path: str, model_cfg: ModelConfig, n_seeds: int, device: str) -> Ensemble:
    state = torch.load(path, map_location=device)
    models = [GGFClassifier(model_cfg, categorical_cardinalities()) for _ in range(n_seeds)]
    ensemble = Ensemble(models)
    ensemble.load_state_dict(state)
    ensemble.to(device)
    ensemble.eval()
    return ensemble


def evaluate_fold(cfg: TrainingConfig, fold: int, device: str):
    shards = load_all_shards(cfg.data, cfg.kfold.n_folds)
    _, _, test_idx = assign_train_val(shards, fold, cfg.kfold.val_fraction, cfg.kfold.split_seed)
    cat_inputs, lbn_vectors, extra_continuous, label, _ = gather_split(shards, test_idx, device)

    moe_path = os.path.join(cfg.output_dir, f"model_fold{fold}_moe.pt")
    ensemble = load_ensemble(moe_path, cfg.model, cfg.kfold.n_seeds, device)

    with torch.no_grad():
        probs = ensemble(cat_inputs, lbn_vectors, extra_continuous).cpu().numpy()
    y_true = label.cpu().numpy()
    y_pred = probs.argmax(axis=1)

    cm = confusion_matrix(y_true, y_pred, labels=range(len(CLASSES)), normalize="true")
    print(f"Fold {fold} row-normalized confusion matrix ({CLASSES}):\n{cm}")

    for i, cls in enumerate(CLASSES):
        y_bin = (y_true == i).astype(int)
        auc = roc_auc_score(y_bin, probs[:, i])
        print(f"  {cls} one-vs-rest AUC: {auc:.4f}")

    return cm, probs, y_true


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--fold", type=int, required=True)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    cfg = TrainingConfig.from_yaml(args.config) if args.config else TrainingConfig()
    cfg.data.data_root = args.data_root
    evaluate_fold(cfg, args.fold, args.device)
