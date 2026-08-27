# Running the analysis

The pipeline itself — producing anaTuples, computing observables, filling and merging histograms,
plotting — is the **standard FLAF chain**. Follow the
**[FLAF full-workflow walkthrough](https://cms-flaf.github.io/FLAF/workflow/walkthrough/)** for the
commands (`InputFileTask` → `AnaTupleFileTask` → `AnaTupleMergeTask` → `HistTupleProducerTask` →
`HistFromNtupleProducerTask` → `HistMergerTask` → `HistPlotTask`). This page collects the points
that are **specific to HH→bb̄ττ**.

## Always pick the DeepTau version

Every stage that depends on τ identification must agree on the DeepTau version. Pass it
consistently across the whole production:

```sh
ERA=Run3_2022
VER=v1_deepTau2p5            # version name encodes the DeepTau version (see Setup)

law run FLAF.Analysis.tasks.HistPlotTask \
  --period $ERA --version $VER --workflow local \
  --customisations deepTauVersion=2p5
```

If you omit `deepTauVersion`, the default (`2p1`) is used. Keep the `--version` name and the
`deepTauVersion` customisation in sync to avoid mixing productions.

## Channels

HH→bb̄ττ is analysed in the three τ-pair channels — **eτ**, **μτ** and **ττ**. Channel selection is
driven by the analysis configuration (`config/global.yaml`); restrict or extend the channels there
or via your [`user_custom.yaml`](https://cms-flaf.github.io/FLAF/configuration/user-custom/).

## Choosing which variables to histogram

The set of variables produced by `HistFromNtupleProducerTask`/`HistPlotTask` is controlled by the
`variables:` list in your `user_custom.yaml` (or the `--variables` argument):

```yaml
variables:
  - tau1_pt
  - ggF_DNN_HH
```

Some observables are **computed in the cache step** (`AnalysisCacheTask`, e.g. the
LegacyVariables/heavier quantities) rather than directly from the anaTuple. When you request such a
variable, LAW pulls in the cache task automatically — see
[FLAF → Task reference](https://cms-flaf.github.io/FLAF/reference/tasks/#analysiscachetask). Listing
a short `variables:` set is the easiest way to keep test runs fast.

## Stitched backgrounds: DY and t̄t

DY and t̄t are stitched from several samples, so each event is normalised with the
cross-section of the bin it belongs to
([MC stitching](https://cms-flaf.github.io/FLAF/concepts/stitching/)). The bins select on
gen-level quantities that nanoAOD does not provide directly, so the anaTuple stores them:

| Branch | Stored for | Meaning |
|---|---|---|
| `DYInfo_flavor`, `DYInfo_mll` | `DYto2Tau_M_50` | flavour (11/13/15) and mass of the LHE dilepton pair |
| `TauTauInfo_passFilter` | `DYto2Tau_M_50` | the Z→ττ generator filter decision, the axis that stitches the filtered samples in |
| `TauTauInfo_vis_type{1,2}`, `TauTauInfo_vis_pt{1,2}`, `TauTauInfo_vis_abseta{1,2}` | `DYto2Tau_M_50` | the visible tau quantities the filter is made of, so its definition can be revisited without reprocessing |
| `TTInfo_nLeptonicW`, `TTInfo_wDecay{1,2}` | `TT` | gen-level t̄t decay channel |

Which of these a process gets is declared as `genInfo` next to its `processors` in
`config/<era>/processes.yaml`, and only where a stitcher selects on it — adding a kind to a
process that is already produced means producing it again; `AnaProd/genProcessInfo.py` turns that into the branches
above. A process that stitches on one of these quantities without declaring `genInfo` fails
in `AnaTupleMergeTask`, where `GenPart`/`LHEPart` are no longer available.

The integration test guards this. `TestModel` runs two backgrounds — `custom_CI_Background_TT`,
one t̄t dataset, and `custom_CI_Background_DY`, one DY→ττ dataset — and each carries the same
`processors:` and `genInfo:` as the real `TT` and `DYto2Tau_M_50` process **for that era**
(`TTStitcher` and `DYtautauStitcher` for 2022–2023BPix; the plain `MCStitcher` and no
stitching of t̄t for 2024 onwards, which is what those eras configure). The stitchers therefore
run over the whole anaTuple → merge → histogram chain in CI, which is exactly where a missing
gen-level branch shows up. Change one of the real processes and change its CI counterpart with
it.

### Signal points with more than one sample

Some GluGlutoHH points are produced more than once — an `_ext1` extension, or a variant
carrying LHE weights. Both are declared and both are used, so the point gets all the
statistics; the `GluGlutoHHto2B2Tau` process therefore carries the `*ext_processors`
stitcher, which normalises the point with the summed event count instead of counting it
twice ([MC stitching](https://cms-flaf.github.io/FLAF/concepts/stitching/)). Which samples
exist differs per era — Run3_2022EE, for instance, has only the LHE-weighted variant of
kl = 2.45 and no plain one.

## Quick stack plots

For a fast look at distributions (outside the full `HistPlotTask` styling), the analysis ships a
helper script. Edit the paths/variable names at the top to match your run, then:

```sh
cd Analysis
python3 make_stackplots.py
```

## Publishing plots

To share plots through a personal interactive web browser, see
[Interactive plot browser](interactive_plot_browser.md).

## Statistical interpretation

Once histograms exist, continue to [Statistical inference](stat_inference.md) for datacards,
limits and diagnostics.
