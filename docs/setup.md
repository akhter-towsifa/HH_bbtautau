# Setup

HH→bb̄ττ is installed and run like any FLAF analysis — clone the repository (with submodules),
`source env.sh`, get a proxy, `law index`. The general procedure, including the prerequisites
(CERN account, CVMFS, grid certificate, SSH keys) and what the first `source env.sh` builds, is in
the **[FLAF installation guide](https://cms-flaf.github.io/FLAF/getting-started/installation/)**.

This page lists what is **specific** to HH→bb̄ττ.

## Clone

```sh
git clone --recursive git@github.com:cms-flaf/HH_bbtautau.git
cd HH_bbtautau
source env.sh
```

The `--recursive` flag is essential: HH→bb̄ττ pulls several physics submodules in addition to the
shared `FLAF` and `Corrections`.

## Analysis-specific submodules

| Submodule | Role |
|---|---|
| `ClassicSVfit`, `SVfitTF` | SVfit reconstruction of the di-τ mass. |
| `HHKinFit2` | Kinematic fit of the HH system. |
| `HHbtag` | HH-optimised b-jet tagging. |
| `SyncTool` | Synchronisation/validation tooling. |
| `StatInference`, `inference` | Datacards and combine-based limits/fits (shared). |
| `cws` | The Combine Workflow System, successor of `inference`; see [Statistical inference](stat_inference.md#running-cws). |

These are wired into the CMSSW build automatically by `env.sh` (it symlinks `HHbtag`, the SVfit
packages and `HHKinFit2` into the CMSSW source tree). You do not set them up by hand.

## DeepTau version

HH→bb̄ττ uses DeepTau for τ identification, and supports more than one version. Select it per run
with a customisation:

```sh
--customisations deepTauVersion=2p5      # default is 2p1; pass this for 2.5
```

This is the one HH→bb̄ττ-specific customisation you will use most. See
[FLAF → Command arguments](https://cms-flaf.github.io/FLAF/workflow/arguments/#customisations).

## Version-naming convention

Because the DeepTau version is part of what a production means, HH→bb̄ττ encodes it in the
`--version` label. The convention is:

```text
VERSION_NAME = v<XX>_deepTau<YY>_<ZZZ>
```

- `XX` — the anaTuple production number (`v1`, `v2`, …),
- `YY` — the DeepTau version (`2p1` or `2p5`),
- `ZZZ` — optional extra tags (e.g. `_onlyTauTau`, `_Zmumu`).

Using a consistent version name keeps DeepTau-2.1 and DeepTau-2.5 productions cleanly separated on
storage.

## Next

- [Running the analysis](analysis.md) — the bb̄ττ-specific run notes.
- [FLAF → Full workflow](https://cms-flaf.github.io/FLAF/workflow/walkthrough/) — the common
  pipeline, stage by stage.
- [FLAF → HTCondor](https://cms-flaf.github.io/FLAF/workflow/htcondor/) /
  [CRAB](https://cms-flaf.github.io/FLAF/workflow/crab/) — CERN batch and full WLCG submission.
