# Datacards: HH → bbττ non-resonant

How to produce CMS Combine datacards for the non-resonant HH → bbττ analysis from the
merged histograms of `HistMergerTask`.

Datacards are built by the `StatInference` submodule's law task chain
(`CreateDatacardsTask`). It reads the `HistMergerTask` output files in place: there is no
flattening or preprocessing step in between.

## Files involved

| File | Role |
|---|---|
| `config/Datacards/x_hh_bbtautau_run3_nonres.yaml` | The datacard config: model, eras, channels, categories, processes, uncertainties. |
| `config/global.yaml` → `StatInference.config` | Points the task chain at the datacard config above. |
| `config/law.cfg` → `[modules]` | Registers the tasks via `StatInference.law.tasks`. |
| `StatInference/law/StatInferenceTask.py` | `get_variable_points()` handles a model with no parameters (`parameters: [ ]`), as used here. |

`StatInference/config/x_hh_bbtautau_run3_nonres.yaml` is the original copy of the config,
written for the older hand-run recipe (`select_region_shapes.py` →
`compute_equal_yield_binning.py` → `create_datacards.py`). It is kept for reference and is
not used by the law chain.

## Prerequisites

1. **Merged histograms for the shape discriminant.** The config reads exactly one
   variable, set by `model.input_file_pattern`:

   ```yaml
   input_file_pattern: ${ERA}/ggF_DNN_HH/ggF_DNN_HH.root
   ```

   so `HistMergerTask` must have finished for that variable and era:

   ```
   <fs_HistTuple>/<version>/Hists_merged/Run3_2022EE/ggF_DNN_HH/ggF_DNN_HH.root
   ```

   Other merged variables (`ggF_DNN_TT`, `ggF_DNN_DY`, the `ggF_DNN_pytorch_full_*`
   variants other than the one chosen, …) are not read and need not exist.

2. **Environment.** From the repository root:

   ```bash
   source env.sh
   ```

3. **Grid proxy**, if `fs_default` points at EOS over `davs://` (the default in
   `config/user_custom.yaml`). Outputs on EOS cannot be written without one:

   ```bash
   voms-proxy-init -voms cms -rfc -valid 192:00
   ```

## Producing the datacards

### 1. Check the task graph (builds nothing)

```bash
law run CreateDatacardsTask --version <version> --era Run3_2022EE --print-status 2
```

The only dependency should be `MergedHists(variable=ggF_DNN_HH, ...)`, shown as
`existent`. If it shows `absent`, the merge for that version/variable is not done.

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

Invoke the task by its plain class name, `CreateDatacardsTask`. The fully-qualified
`StatInference.law.CreateDatacardsTask` fails with
`TypeError: issubclass() arg 1 must be a class` (a law CLI lookup issue).

To rebuild datacards that already exist, `--remove-output` is needed; it deletes the
existing output, so use it deliberately.

### 3. Output

Datacards are written to `fs_default`:

```
<fs_default>/<version>/Datacards/Run3_2022EE/
```

e.g. `/eos/user/t/toakhter/HH_bbtautau_Run3/v2608_ggF_DNN_ELR/Datacards/Run3_2022EE/`.
Print the exact path with:

```bash
law run CreateDatacardsTask --version <version> --era Run3_2022EE --print-output 0
```

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
    --config config/Datacards/x_hh_bbtautau_run3_nonres.yaml \
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

The datacard maker looks histograms up as `<channel>/<category>/<hist_name>`, and a
category may contain `/`. The categories therefore include the QCD region:

```yaml
categories:
  - OS_Iso/res1b
  - OS_Iso/res2b
  - OS_Iso/boosted
```

Only `OS_Iso` (the signal region) is read. The other regions already enter through the
data-driven `QCD` process that `HistMergerTask` builds.

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

The VBF names follow the `cws` sample labels, so all 10 points match the 10-point
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

## Binning and negative bins

No `--hist-bins` binning is configured yet, so the histograms' native binning (100 bins
in [0, 1] for the DNN scores) is used. At that granularity, low-statistics background bins
can be negative and stop the run with

```
RuntimeError: Negative bins found in histogram for <channel>/OS_Iso/<category>/<process>
```

(seen for `DY` and `TT` in a test run on `ggF_DNN_DY`). Either coarsen the binning or
relax that process's tolerances in `processes:`. For the law chain, a binning file can be
set in `config/global.yaml`:

```yaml
StatInference:
  config: config/Datacards/x_hh_bbtautau_run3_nonres.yaml
  hist_bins: config/Datacards/bins_${ERA}.json   # ${ERA} is substituted per era
```

`StatInference/dc_make/compute_equal_yield_binning.py` and `autocoarsen_binning.py` can
produce such a file.

## Adding an era

Add it to `eras:` in the datacard config and pass it with `--era` (comma-separated for
several). Every era listed needs its own `Hists_merged/<era>/<variable>/<variable>.root`.
Check that the `lumi_*` uncertainties cover it.
