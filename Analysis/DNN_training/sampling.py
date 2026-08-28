from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ProcessSubset:
    """One (class, subprocess) group of training events -- e.g. class="HH",
    subprocess="GluGlutoHHto2B2Tau_kl_1p00..._Run3_2022EE". `indices` are
    positions into whatever flat array the caller intends to sample from
    (see train.py for how these are wired to the concatenated training
    tensors)."""

    class_name: str
    subprocess: str
    indices: np.ndarray
    total_weight: float  # sum of physical per-event weights (proxy for relative yield)


def _allocate_counts(weights: np.ndarray, n: int) -> np.ndarray:
    """AN Sec. 5.3.5 oversampling allocation: proportional to *weights*, floor of
    1 each, excess trimmed from the largest allocation(s) to sum exactly to n."""
    weights = np.clip(np.asarray(weights, dtype=float), 1e-12, None)
    fractions = weights / weights.sum()
    counts = np.maximum(1, np.round(fractions * n).astype(int))

    excess = int(counts.sum()) - n
    while excess > 0:
        i = int(np.argmax(counts))
        reducible = counts[i] - 1
        if reducible <= 0:
            break  # every subprocess is already at the floor of 1; can't trim further
        take = min(reducible, excess)
        counts[i] -= take
        excess -= take
    return counts


class OversampledBatchIterator:
    """Yields index arrays of length batch_size, each drawn according to the
    2-step oversampling algorithm of AN Sec. 5.3.5: split the batch into equal
    (or class_weights-weighted) per-class sub-batches, then within each
    sub-batch allocate events per subprocess proportional to total_weight."""

    def __init__(
        self,
        subsets: list[ProcessSubset],
        batch_size: int,
        class_weights: dict[str, float] | None = None,
        rng: np.random.Generator | None = None,
    ):
        self.subsets = subsets
        self.batch_size = batch_size
        self.rng = rng or np.random.default_rng()
        self.classes = sorted({s.class_name for s in subsets})
        self.class_weights = class_weights or {c: 1.0 / len(self.classes) for c in self.classes}
        self._by_class = {c: [s for s in subsets if s.class_name == c] for c in self.classes}

    def _sample_one_batch(self) -> np.ndarray:
        class_w = np.array([self.class_weights[c] for c in self.classes])
        class_counts = _allocate_counts(class_w, self.batch_size)

        parts = []
        for c, n_c in zip(self.classes, class_counts):
            subsets_in_class = self._by_class[c]
            sub_w = np.array([s.total_weight for s in subsets_in_class])
            sub_counts = _allocate_counts(sub_w, int(n_c))
            for s, k in zip(subsets_in_class, sub_counts):
                parts.append(self.rng.choice(s.indices, size=int(k), replace=True))

        batch = np.concatenate(parts)
        self.rng.shuffle(batch)
        return batch

    def __iter__(self):
        while True:
            yield self._sample_one_batch()


def compute_eval_weights(subsets: list[ProcessSubset], per_event_weight: dict[str, np.ndarray],
                          class_weights: dict[str, float] | None = None) -> dict[str, np.ndarray]:
    """Per-event weights for a non-oversampled loss diagnostic (AN Sec. 5.3.6):
    rescale each class's total contribution to class_weights[c] (default:
    equal), starting from the physical per-event weights. Returns a dict keyed
    the same way as per_event_weight (e.g. by subprocess name). Not used by
    train.py directly (which computes an equivalent per-class scale factor
    inline), but kept here as a standalone, independently-testable utility."""
    classes = sorted({s.class_name for s in subsets})
    class_weights = class_weights or {c: 1.0 / len(classes) for c in classes}

    class_totals = {c: 0.0 for c in classes}
    for s in subsets:
        class_totals[s.class_name] += per_event_weight[s.subprocess].sum()
    grand_total = sum(class_totals.values())

    out = {}
    for s in subsets:
        if class_totals[s.class_name] <= 0:
            out[s.subprocess] = np.zeros_like(per_event_weight[s.subprocess])
            continue
        scale = class_weights[s.class_name] * grand_total / class_totals[s.class_name]
        out[s.subprocess] = per_event_weight[s.subprocess] * scale
    return out


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    subsets = [
        ProcessSubset("HH", "kl1", np.arange(0, 100), total_weight=10.0),
        ProcessSubset("HH", "kl5", np.arange(100, 150), total_weight=1.0),
        ProcessSubset("TT", "ttbar", np.arange(150, 1150), total_weight=500.0),
        ProcessSubset("DY", "dy_m50", np.arange(1150, 2150), total_weight=800.0),
        ProcessSubset("SingleH", "ggH", np.arange(2150, 2200), total_weight=5.0),
        ProcessSubset("SingleH", "ttH", np.arange(2200, 2210), total_weight=0.001),
    ]
    it = OversampledBatchIterator(subsets, batch_size=400, rng=rng)
    batch = next(iter(it))
    assert len(batch) == 400
    # each of the 4 classes should get ~100 events (equal 1/4 default weighting)
    class_of = {}
    for s in subsets:
        for i in s.indices:
            class_of[i] = s.class_name
    counts = {}
    for i in batch:
        counts[class_of[i]] = counts.get(class_of[i], 0) + 1
    print("class composition of one oversampled batch:", counts)
    assert set(counts.keys()) == {"HH", "TT", "DY", "SingleH"}
    for c, n in counts.items():
        assert 90 <= n <= 110, (c, n)  # rounding-driven allocation should land near 100

    per_event_weight = {s.subprocess: np.full(len(s.indices), s.total_weight / len(s.indices)) for s in subsets}
    eval_w = compute_eval_weights(subsets, per_event_weight)
    assert set(eval_w.keys()) == {s.subprocess for s in subsets}
    print("sampling.py smoke test OK")
