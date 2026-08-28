from __future__ import annotations

import torch
from torch import nn

from .config import (
    EXTRA_CONTINUOUS_FEATURES,
    ModelConfig,
    categorical_cardinalities,
)


class LBN(nn.Module):
    """Lorentz Boost Network (Erdmann et al., arXiv:1812.09722).

    Takes n_in four-vectors (px, py, pz, E) per event and produces n_out
    boosted four-vectors: n_out learned convex combinations of the inputs form
    "particles", another n_out learned combinations form "rest frames", and
    each particle is boosted into its corresponding rest frame. No vendored
    LBN implementation exists in this repo, so this is implemented directly
    from the paper's formulation.
    """

    def __init__(self, n_in: int, n_out: int):
        super().__init__()
        self.n_in = n_in
        self.n_out = n_out
        self.particle_weights = nn.Parameter(torch.randn(n_in, n_out) * 0.1)
        self.restframe_weights = nn.Parameter(torch.randn(n_in, n_out) * 0.1)

    def forward(self, four_vectors: torch.Tensor) -> torch.Tensor:
        # four_vectors: (batch, n_in, 4), components (px, py, pz, E)
        pw = torch.softmax(self.particle_weights, dim=0)  # (n_in, n_out)
        rw = torch.softmax(self.restframe_weights, dim=0)  # (n_in, n_out)

        particles = torch.einsum("bic,io->boc", four_vectors, pw)  # (batch, n_out, 4)
        frames = torch.einsum("bic,io->boc", four_vectors, rw)  # (batch, n_out, 4)

        p_vec, p_E = particles[..., :3], particles[..., 3]
        f_vec, f_E = frames[..., :3], frames[..., 3]

        beta = f_vec / f_E.unsqueeze(-1).clamp_min(1e-6)
        beta2 = (beta**2).sum(-1).clamp(max=1 - 1e-6)
        gamma = 1.0 / torch.sqrt((1 - beta2).clamp_min(1e-6))

        beta_dot_p = (beta * p_vec).sum(-1)
        boosted_E = gamma * (p_E - beta_dot_p)
        coeff = (gamma - 1.0) * beta_dot_p / beta2.clamp_min(1e-6) - gamma * p_E
        boosted_vec = p_vec + coeff.unsqueeze(-1) * beta

        boosted = torch.cat([boosted_vec, boosted_E.unsqueeze(-1)], dim=-1)  # (batch, n_out, 4)
        return boosted.reshape(boosted.shape[0], -1)  # (batch, n_out * 4)


class EntityEmbedding(nn.Module):
    """Concatenated entity embeddings for the categorical inputs (AN Sec. 5.3.3)."""

    def __init__(self, cardinalities: dict[str, int], dim: int = 5):
        super().__init__()
        self.fields = list(cardinalities.keys())
        self.embeddings = nn.ModuleDict(
            {name: nn.Embedding(card, dim) for name, card in cardinalities.items()}
        )
        self._dim = dim

    @property
    def out_dim(self) -> int:
        return len(self.fields) * self._dim

    def forward(self, cat_inputs: dict[str, torch.Tensor]) -> torch.Tensor:
        return torch.cat([self.embeddings[f](cat_inputs[f]) for f in self.fields], dim=-1)


class DenseBlock(nn.Module):
    def __init__(self, in_features: int, width: int):
        super().__init__()
        self.linear = nn.Linear(in_features, width)
        self.bn = nn.BatchNorm1d(width)
        self.act = nn.ELU()
        nn.init.kaiming_uniform_(self.linear.weight, nonlinearity="relu")  # He-uniform, per AN
        nn.init.zeros_(self.linear.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.bn(self.linear(x)))


class DenseNet(nn.Module):
    """8 DenseBlocks x 128 nodes, ELU, densely (skip-)connected (AN Sec. 5.3.3)."""

    def __init__(self, input_dim: int, n_blocks: int, width: int, n_classes: int, dropout: float = 0.0):
        super().__init__()
        self.blocks = nn.ModuleList()
        in_dim = input_dim
        for _ in range(n_blocks):
            self.blocks.append(DenseBlock(in_dim, width))
            in_dim += width
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
        self.output = nn.Linear(in_dim, n_classes)
        nn.init.kaiming_uniform_(self.output.weight, nonlinearity="linear")
        nn.init.zeros_(self.output.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = [x]
        for block in self.blocks:
            features.append(block(torch.cat(features, dim=-1)))
        return self.output(self.dropout(torch.cat(features, dim=-1)))


class GGFClassifier(nn.Module):
    """LBN + DenseNet classifier for GGF HH vs. TT / DY / SingleH.

    NOTE: the tau-tau regression subnetwork described in AN-25-103 Sec. 5.3.3 is
    intentionally omitted -- its training target (neutrino momenta) isn't
    available in the standard anaTuple branches. Documented follow-up.
    """

    def __init__(self, model_cfg: ModelConfig, cat_cardinalities: dict[str, int] | None = None):
        super().__init__()
        cat_cardinalities = cat_cardinalities or categorical_cardinalities()
        self.embedding = EntityEmbedding(cat_cardinalities, dim=model_cfg.embedding_dim)
        self.lbn = LBN(model_cfg.lbn_n_in, model_cfg.lbn_n_out)
        self.lbn_bn = nn.BatchNorm1d(model_cfg.lbn_n_out * 4)

        cont_dim = self.embedding.out_dim + model_cfg.lbn_n_out * 4 + len(EXTRA_CONTINUOUS_FEATURES)
        self.dense = DenseNet(
            cont_dim,
            n_blocks=model_cfg.dense_n_blocks,
            width=model_cfg.dense_width,
            n_classes=model_cfg.n_classes,
            dropout=model_cfg.dropout,
        )

    def forward(
        self,
        cat_inputs: dict[str, torch.Tensor],
        lbn_vectors: torch.Tensor,  # (batch, 5, 4): px,py,pz,E for dau1,dau2,bjet1,bjet2,fatjet
        extra_continuous: torch.Tensor,  # (batch, len(EXTRA_CONTINUOUS_FEATURES))
    ) -> torch.Tensor:
        emb = self.embedding(cat_inputs)
        lbn_out = self.lbn_bn(self.lbn(lbn_vectors))
        x = torch.cat([emb, lbn_out, extra_continuous], dim=-1)
        return torch.softmax(self.dense(x), dim=-1)


class Ensemble(nn.Module):
    """Averages softmax outputs of several GGFClassifier instances (mixture-of-experts,
    matches the existing "_moe" checkpoint naming convention)."""

    def __init__(self, models: list[GGFClassifier]):
        super().__init__()
        self.models = nn.ModuleList(models)

    def forward(self, *args, **kwargs) -> torch.Tensor:
        outputs = torch.stack([m(*args, **kwargs) for m in self.models], dim=0)
        return outputs.mean(dim=0)


def linear_layers(module: nn.Module):
    """All nn.Linear submodules, for the per-layer weight-decay grouping in train.py."""
    return [m for m in module.modules() if isinstance(m, nn.Linear)]


if __name__ == "__main__":
    # Shape/gradient-flow smoke test with synthetic data (no real anaTuples needed).
    from .config import ModelConfig, categorical_cardinalities

    torch.manual_seed(0)
    batch = 32
    cfg = ModelConfig()
    cards = categorical_cardinalities()
    model = GGFClassifier(cfg, cards)

    cat_inputs = {name: torch.randint(0, card, (batch,)) for name, card in cards.items()}
    lbn_vectors = torch.randn(batch, cfg.lbn_n_in, 4)
    extra_continuous = torch.randn(batch, len(EXTRA_CONTINUOUS_FEATURES))

    out = model(cat_inputs, lbn_vectors, extra_continuous)
    assert out.shape == (batch, cfg.n_classes), out.shape
    assert torch.allclose(out.sum(-1), torch.ones(batch), atol=1e-4)

    loss = out.sum()
    loss.backward()
    for p in model.parameters():
        assert p.grad is not None

    ens = Ensemble([GGFClassifier(cfg, cards) for _ in range(3)])
    out_ens = ens(cat_inputs, lbn_vectors, extra_continuous)
    assert out_ens.shape == (batch, cfg.n_classes)

    print("model.py smoke test OK:", out.shape, "linear layers:", len(linear_layers(model)))
