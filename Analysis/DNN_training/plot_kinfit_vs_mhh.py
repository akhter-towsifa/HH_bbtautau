"""2D heatmap of kinFit_m (reco, HHKinFit2) vs mhh_lhe (gen, LHE-level) for GGF
HH signal HistTuples -- a quick sanity check of how well the reconstructed
di-Higgs mass tracks the true generated one, per benchmark point or combined
across all of them.

Reads the same histTuple_flavor: DNN_training branches used by
Analysis/DNN_training/data.py (histtuple_files() for file discovery), but only
needs two columns here, so this goes directly through uproot rather than the
full data.py loading pipeline (no LBN/embedding feature building needed for a
diagnostic plot).

Usage:
    python -m Analysis.DNN_training.plot_kinfit_vs_mhh \\
        --data-root /path/to/v2608_dnn --eras Run3_2022EE
"""

from __future__ import annotations

import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import uproot

from .config import ERAS, HH_SIGNAL_POINTS, DataConfig
from .data import histtuple_files, resolve_hh_dataset_name


def load_kinfit_vs_mhh(
    data_root: str,
    eras: list[str],
    signal_points: list[tuple[str, str, str]],
    config_dir: str,
    step_size: str = "50 MB",
) -> tuple[np.ndarray, np.ndarray]:
    """Reads kinFit_m and mhh_lhe from every (era, HH signal point) HistTuple
    found under data_root, concatenates them, and drops events where either
    is at its sentinel value (kinFit_m == -100: HHKinFit2 didn't converge /
    Hbb_isValid was false; mhh_lhe <= 0: not a signal sample, or the rare
    "didn't find exactly 2 LHE Higgs bosons" fallback -- see
    Analysis/hh_bbtautau.py::defineLHEHHVariables and include/LHEVariables.h).

    Dataset names for a given (kl, kt, c2) point aren't uniform across eras
    (some are only registered under a "_LHEweights"-suffixed name -- see
    data.py::resolve_hh_dataset_name), so the actual on-disk name is looked
    up per era rather than templated directly."""
    kinfit_chunks = []
    mhh_chunks = []
    for era in eras:
        for kl, kt, c2 in signal_points:
            dataset = resolve_hh_dataset_name(kl, kt, c2, era, config_dir)
            if dataset is None:
                print(f"[skip] {era}: no dataset registered for kl={kl},kt={kt},c2={c2}")
                continue
            files = histtuple_files(data_root, era, dataset)
            if not files:
                print(f"[skip] no HistTuple files found for {era}/{dataset}")
                continue
            file_specs = [f"{path}:Events" for path in files]
            n_events = 0
            for chunk in uproot.iterate(
                file_specs, filter_name=["kinFit_m", "mhh_lhe"], step_size=step_size
            ):
                kinfit_chunks.append(np.asarray(chunk["kinFit_m"]))
                mhh_chunks.append(np.asarray(chunk["mhh_lhe"]))
                n_events += len(chunk)
            print(f"[ok]   {era}/{dataset}: {n_events} events from {len(files)} file(s)")

    if not kinfit_chunks:
        raise RuntimeError(
            "No events read for any (era, signal point) -- check --data-root and --eras."
        )

    kinfit_m = np.concatenate(kinfit_chunks)
    mhh_lhe = np.concatenate(mhh_chunks)
    valid = (kinfit_m > -100.0) & (mhh_lhe > 0.0)
    n_dropped = valid.size - int(valid.sum())
    if n_dropped:
        print(f"Dropping {n_dropped}/{valid.size} events with a sentinel kinFit_m/mhh_lhe value.")
    return kinfit_m[valid], mhh_lhe[valid]


def plot_2d_heatmap(
    kinfit_m: np.ndarray,
    mhh_lhe: np.ndarray,
    output: str,
    bins: int = 60,
    range_: tuple[float, float] = (250.0, 3000.0),
    log_z: bool = True,
) -> None:
    counts, xedges, yedges = np.histogram2d(
        mhh_lhe, kinfit_m, bins=bins, range=[range_, range_]
    )

    fig, ax = plt.subplots(figsize=(7, 6))
    norm = matplotlib.colors.LogNorm() if log_z else None
    mesh = ax.pcolormesh(xedges, yedges, counts.T, cmap="viridis", norm=norm)
    fig.colorbar(mesh, ax=ax, label="Events")

    lo, hi = range_
    ax.plot([lo, hi], [lo, hi], color="red", linestyle="--", linewidth=1, label="kinFit_m = mhh_lhe")
    ax.legend(loc="upper left", fontsize="small")

    corr = np.corrcoef(mhh_lhe, kinfit_m)[0, 1]
    ax.set_xlabel("$m_{HH}^{LHE}$ (GeV)")
    ax.set_ylabel("$m_{H}^{kinfit}$ (GeV)")
    ax.set_title(f"kinFit_m vs mhh_lhe | {kinfit_m.size} events, corr = {corr:.3f}")

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"Saved {output}")


def parse_signal_points(raw: list[str] | None) -> list[tuple[str, str, str]]:
    if not raw:
        return HH_SIGNAL_POINTS
    points = []
    for entry in raw:
        kl, kt, c2 = entry.split(",")
        points.append((kl, kt, c2))
    return points


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--data-root", required=True,
        help='HistTupleProducerTask version directory, e.g. ".../v2608_dnn" or a '
             '"root://host//path/v2608_dnn" XRootD URL (see Analysis/DNN_training/data.py::histtuple_files).',
    )
    parser.add_argument("--eras", nargs="+", default=ERAS, help=f"default: {ERAS}")
    parser.add_argument(
        "--signal-points", nargs="+", default=None,
        help='Restrict to specific (kl,kt,c2) points, e.g. --signal-points 1p00,1p00,0p00. '
             "Default: all HH_SIGNAL_POINTS in config.py.",
    )
    parser.add_argument(
        "--config-dir", default=DataConfig().config_dir,
        help="bbtautau/config dir used to resolve HH dataset names per era (datasets.yaml). "
             "Default: DataConfig().config_dir (ANALYSIS_PATH/config).",
    )
    parser.add_argument("--output", default="output/DNN_training/kinFit_m_vs_mhh_lhe.png")
    parser.add_argument("--bins", type=int, default=60)
    parser.add_argument("--range", type=float, nargs=2, default=(250.0, 3000.0), metavar=("LO", "HI"))
    parser.add_argument("--step-size", default="50 MB")
    parser.add_argument("--linear-z", action="store_true", help="Use a linear color scale instead of log.")
    args = parser.parse_args()

    signal_points = parse_signal_points(args.signal_points)
    kinfit_m, mhh_lhe = load_kinfit_vs_mhh(
        args.data_root, args.eras, signal_points, args.config_dir, args.step_size
    )
    plot_2d_heatmap(
        kinfit_m, mhh_lhe, args.output,
        bins=args.bins, range_=tuple(args.range), log_z=not args.linear_z,
    )


if __name__ == "__main__":
    main()
