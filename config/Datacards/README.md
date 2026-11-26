# Datacards: HH → bbττ non-resonant

How to produce CMS Combine datacards for the non-resonant HH → bbττ analysis from the
merged histograms of `HistMergerTask`.

Datacards are built by the `StatInference` submodule's law task chain
(`CreateDatacardsTask`). It reads the `HistMergerTask` output files in place: there is no
flattening or preprocessing step in between.

## Files involved

| File | Role |
|---|---|
| `config/Datacards/hh_bbtautau_run3_nonres.yaml` | The datacard config: model, eras, channels, categories, processes, uncertainties. |
| `config/global.yaml` → `StatInference.config` | Points the task chain at the datacard config above. |
| `config/law.cfg` → `[modules]` | Registers the tasks via `StatInference.law.tasks`. |
| `StatInference/law/StatInferenceTask.py`, `CreateDatacardsTask.py` | Handle a model with no parameters (`parameters: [ ]`), as used here: such a card is built as one point per era with mass `None`, in the same `(card, era, mass)` branch layout as the resonant cards. |
| `StatInference/law/NonResonantLimitsTask.py`, `NonResonantLimitsAndHistPlotTask.py` | The limits of a non-resonant card (see *Limits* below), and the full pipeline CI runs (see *Integration CI*). |
| `config/Datacards/CI/CI_card_nonres.yaml`, `config/ci_custom.yaml` | The CI card and its wiring (see *Integration CI* below). |

## Prerequisites

**Merged histograms for the shape discriminant.** 
   The config reads exactly one
   variable, set by `model.input_file_pattern`:

   ```yaml
   input_file_pattern: ${ERA}/ggF_DNN_HH/ggF_DNN_HH.root
   ```

   so `HistMergerTask` must have finished for that variable and era:

   ```
   <fs_Hists>/<version>/Hists_merged/Run3_2022EE/ggF_DNN_HH/ggF_DNN_HH.root
   ```

   `fs_Hists` falls back to `fs_HistTuple`, then to `fs_default`, when unset.

   Other merged variables (`ggF_DNN_TT`, `ggF_DNN_DY`, the `ggF_DNN_pytorch_full_*`
   variants other than the one chosen, …) are not read and need not exist.

## Producing the datacards

### 1. Check the task graph (builds nothing)

```bash
law run CreateDatacardsTask --version <version> --era Run3_2022EE --print-status 2
```

The only dependency should be `MergedHists(variable=ggF_DNN_HH, ...)`, shown as
`existent`. If it shows `absent`, either the merge for that version/variable is not done
or the grid proxy has expired.

### 2. Build the datacards

On HTCondor (the task's default workflow):

```bash
law run CreateDatacardsTask --version <version> --era Run3_2022EE
```

or locally:

```bash
law run CreateDatacardsTask --version <version> --era Run3_2022EE --workflow local
```

`<version>` is the version of the `HistMergerTask` output to read, e.g.
`v2608_ggF_DNN_ELR`.

Invoke the task by its plain class name, `CreateDatacardsTask`, or through the `tasks`
module, `StatInference.law.tasks.CreateDatacardsTask`. `StatInference.law.CreateDatacardsTask`
names the module of the same name, not the class, and fails with
`TypeError: issubclass() arg 1 must be a class`.

To rebuild datacards that already exist, `--remove-output` is needed; it deletes the
existing output, so use it deliberately.

### 3. Output

Datacards are written to `fs_StatInference` (which falls back to `fs_default` when
unset), one directory per card and era. The card is named after its config file, here
`hh_bbtautau_run3_nonres`. A non-resonant card has no mass point, so there is no
`<param>_<mass>` level below the era:

```
<fs_StatInference>/<version>/Datacards/hh_bbtautau_run3_nonres/<ERA>/
```

e.g. `/eos/user/u/username/HH_bbtautau_Run3/v2608/Datacards/hh_bbtautau_run3_nonres/Run3_2022EE/`:

```
datacard_combined_signals.txt          # all bins and all signal points in one card
combined_signals_all.root              # its shapes
card_config.yaml                       # the config the card was built from
<era>/<channel>/<category>/datacard_<bin>.txt, <bin>.root   # one card per bin
plots/                                 # shape plots per channel/category, and grids
```
Print the exact path with:

```bash
law run CreateDatacardsTask --version <version> --era Run3_2022EE --print-output 0
```

### 4. Limits

```bash
law run NonResonantLimitsTask --version <version> --era Run3_2022EE --workflow local
```

builds the datacards if needed, then computes the asymptotic CLs upper limit on the signal
strength `r` for each era of the card and for the combination of its top-level eras
(`combineCards.py`). It runs `text2workspace.py` with combine's default physics model,
where `r` scales every signal process of the card together, and
`combine -M AsymptoticLimits`. No HH model is applied. The limits are blinded (expected
only, from an Asimov dataset) unless `--unblinded` is given.

Outputs, local under `$ANALYSIS_DATA_PATH/<version>/`:

```
NonResonantLimitsTask/hh_bbtautau_run3_nonres/combined/limits.json   # per era and "combined"
Datacards/hh_bbtautau_run3_nonres/<era>/      # local mirror of each era's datacards
Datacards/hh_bbtautau_run3_nonres/combined/datacard_combined.txt
```

`limits.json` holds, for each era and for `combined`, the expected limits at the 2.5, 16,
50, 84 and 97.5% quantiles (and `observed` when unblinded). The task fails if combine
leaves any of them out.

### Running `create_datacards.py` by hand

Useful for quick tests against a single file without law. `--input` must be a directory
laid out as `<era>/<variable>/<variable>.root` (a symlink to the merged file is enough).
CombineHarvester needs the CMSSW environment:

```bash
source env.sh
mkdir -p <input_dir>/Run3_2022EE/ggF_DNN_HH
ln -s <path to Hists_merged>/Run3_2022EE/ggF_DNN_HH/ggF_DNN_HH.root \
      <input_dir>/Run3_2022EE/ggF_DNN_HH/ggF_DNN_HH.root

env -i HOME=$HOME ANALYSIS_PATH=$ANALYSIS_PATH ANALYSIS_DATA_PATH=$ANALYSIS_DATA_PATH \
  X509_USER_PROXY=$X509_USER_PROXY FLAF_CMSSW_BASE=$FLAF_CMSSW_BASE \
  FLAF_CMSSW_ARCH=$FLAF_CMSSW_ARCH \
  $FLAF_PATH/cmsEnv.sh python3 StatInference/dc_make/create_datacards.py \
    --input  <input_dir> \
    --output <output_dir> \
    --config config/Datacards/hh_bbtautau_run3_nonres.yaml \
    --eras   Run3_2022EE
```

Add `--hist-bins <binning.json>` to rebin (see *Binning* below).

## What the config describes

### Input layout and categories

`HistMergerTask` writes each merged file as

```
<channel>/<QCDRegion>/<category>/<process>[_<unc>_<Up|Down>]   # histograms
SignalTrees/<process>/<variation>                              # ELReweighter trees
```

A category name becomes part of the datacard bin name
(`<era>_hh_bbtautau_<channel>_<category>`) and of the per-bin output files, so it must not
contain `/`. The categories therefore keep plain names, and `input_categories` says where
each one is read from in the merged file:

```yaml
categories:
  - res1b
  - res2b
  - boosted
input_categories:
  res1b: OS_Iso/res1b
  res2b: OS_Iso/res2b
  boosted: OS_Iso/boosted
```

The maker then reads `<channel>/OS_Iso/<category>/<hist_name>`. Only `OS_Iso` (the signal
region) is read. The other regions already enter through the data-driven `QCD` process
that `HistMergerTask` builds.

Channels are `eTau`, `muTau`, `tauTau`. The merged files also contain `eE`, `eMu` and
`muMu`, which are not used for the fit.

### ELReweighter trees

The `SignalTrees/` directory is not read by the datacard maker, which only fetches named
histograms. `CreateDatacardsTask` copies each merged file whole before reading it, so the
trees travel with the shape file untouched. They are only present if the histograms were
produced with `signal_tree_hists_ELReweighter.store_signal_trees: true` (off by default in
`config/global.yaml`).

### Shape discriminant

The default is `ggF_DNN_HH`. To use the PyTorch full-resolution score instead, change both
path segments of `input_file_pattern`:

```yaml
input_file_pattern: ${ERA}/ggF_DNN_pytorch_full_HH/ggF_DNN_pytorch_full_HH.root
```

and make sure `HistMergerTask` has produced that variable.

### Signal processes

`process:` is the name written in the datacard; `hist_name:` is the histogram name in the
merged file.

- **ggF**: 4 points, `ggHH_kl_<kl>_kt_1_13p6TeV_hbbhtt` (kl = 0, 1, 2.45, 5).
- **VBF**: 10 points, `qqHH_CV_<CV>_C2V_<C2V>_kl_<kl>_13p6TeV_hbbhtt`.

The VBF names follow the `cws` submodule sample labels, so all 10 points match the 10-point
`default` VBF basis of `cws`'s `model_nonres_hh_heft`
(`cws/models/multih_models/nonresonant_HHplus/kappa_framework/hh_model_kappa_framework/qqhh_default.csv`).
`cws` ignores the trailing `_hbbhtt` decay tag and differences in zero padding
(e.g. `m1p6` vs `m1p60`) when matching. `model_nonres_hh_kappa` uses the 6-point `alt`
basis and so covers only 6 of the 10.

### Backgrounds

`TT`, `DY`, `ST`, `VV`, `VVV`, `ttH`, `VBFH`, `ggH`, `VH`, `QCD`. `WtoLNu` is left out.
Several processes carry `allow_zero_integral` / `allow_negative_bins_within_error` /
`max_n_sigma_for_negative_bins` to tolerate negative bins.

### Uncertainties

Only the theory and luminosity normalisation uncertainties are declared so far:
`lumi_*`, `QCD_scale_<process>` and `PDF_alphas`, all `lnN`.

The experimental systematics that `HistMergerTask` writes as `_<unc>_Up/Down` histograms
(pileup, lepton/tau ID and trigger SFs, `JES_Total`, `JER`, DY stat/syst, …) are not in
the datacards until they are added to `uncertainties:`. The maker only applies uncertainties
listed there. Each entry can be:

| `type` | Behaviour |
|---|---|
| `lnN` | Fixed log-normal from `value:` (symmetric, or `[down, up]`). |
| `shape` | Shape nuisance from the `<hist_name>_<name>_Up/Down` histograms. |
| `auto` | Reads the Up/Down histograms and becomes `lnN` if they are compatible with a flat rescaling, `shape` otherwise. Controlled by `autolnNThr`, `asymlnNThr`, `ignorelnNThr`. |

Example:

```yaml
  - name: JER
    type: shape
    processes: ["^(?!data_obs|QCD).*"]   # a pattern starting with ^ is a regex
```

The `name` must match the uncertainty part of the histogram names in the merged file.

## Integration CI

`config/ci_custom.yaml` replaces the `StatInference:` block with the CI card:

```yaml
StatInference:
  cards:
    CI: config/Datacards/CI/CI_card_nonres.yaml
```

`CI_card_nonres.yaml` has the structure of the analysis card (no model parameters,
`ggF_DNN_HH`, the same channels) on the processes of the CI physics model
(`TestModel`: `custom_CI_Signal`, `custom_CI_Background_TT`, `custom_CI_Background_DY`),
with one bin per channel and category (`hist_bins: [ 0.0, 1.0 ]`) and the luminosity
uncertainties only. Its eras are the ones the integration pipeline runs.

It reads the `res2b` category only. At `--test 1000` the CI backgrounds leave the Asimov data
(their sum) of the other categories empty or negative in some channel and era -- `boosted`
needs an AK8 fat jet, and `tauTau/res1b` came out at 0 or, from DY's negative weights,
below 0 -- and the datacard step refuses such a histogram.

The full pipeline -- histograms, plots, datacards and limits -- is
`StatInference.law.tasks.NonResonantLimitsAndHistPlotTask`, which requires
`NonResonantLimitsTask` and `HistPlotTask` (the non-resonant counterpart of HH_bbWW's
`ResonantLimitsAndHistPlotTask`). A task whose name contains `Inference` runs once over all
eras, after the histogram jobs of each era.

The task a bare `@cms-flaf-bot test` runs is `HH_bbtautau_task` in `integration_cfg.yaml`
of `cms-flaf/FLAF_ci`. Until that is set to the task above, name it in the trigger:

```
@cms-flaf-bot test
- HH_bbtautau_task=StatInference.law.tasks.NonResonantLimitsAndHistPlotTask
```

The CI card's eras need only be among the eras CI runs (`HH_bbtautau_eras`); the other
eras get histograms and plots only.

## Binning and negative bins

No `--hist-bins` binning is configured yet, so the histograms' native binning (100 bins
in [0, 1] for the DNN scores) is used. At that granularity, low-statistics background bins
can be negative and stop the run with

```
RuntimeError: Negative bins found in histogram for <channel>/OS_Iso/<category>/<process>
```

This is why `DY` carries `allow_negative_bins_within_error` with
`max_n_sigma_for_negative_bins: 2`: on `ggF_DNN_HH` its negative bins are all within
1.3σ of zero, and the boosted DY templates hold less than one event over 100 bins. If
another process fails the same way, either coarsen the binning or relax that process's
tolerances in `processes:`. For the law chain, a binning file can be
set in `config/global.yaml`:

```yaml
StatInference:
  config: config/Datacards/hh_bbtautau_run3_nonres.yaml
  hist_bins: config/Datacards/bins_${ERA}.json   # ${ERA} is substituted per era
```

The file is a JSON list of entries, each giving the bin edges for a set of channels and
categories:

```json
[
  {"bins": [0.0, 0.5, 0.8, 0.9, 1.0], "channels": ["tauTau"], "categories": ["res2b"]}
]
```

## Adding an era

Add it to `eras:` in the datacard config and pass it with `--era` (comma-separated for
several). Every era listed needs its own `Hists_merged/<era>/<variable>/<variable>.root`.
Check that the `lumi_*` uncertainties cover it.
