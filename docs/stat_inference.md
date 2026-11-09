# Statistical inference

The final step turns the merged histograms into **datacards** and runs limits and diagnostics with
[Combine](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/), via the `StatInference` and
`inference` submodules. For where this sits in the pipeline see
[FLAF → walkthrough, stage 5](https://cms-flaf.github.io/FLAF/workflow/walkthrough/#stage-5-statistical-inference).

These commands run inside CMSSW/Combine, so prefix them with `cmsEnv` — or open one Combine subshell
and run several commands in it:

```sh
cmsEnv /bin/zsh        # a CMSSW+Combine subshell (or /bin/bash)
```

## 1. Create datacards

```sh
cmsEnv python3 StatInference/dc_make/create_datacards.py \
  --input  PATH_TO_SHAPES \
  --output PATH_TO_CARDS \
  --config PATH_TO_CONFIG
```

Configurations live in [`StatInference/config/`](https://github.com/cms-flaf/StatInference/tree/main/config):

- Resonant X→HH→bb̄ττ: `x_hh_bbtautau_run3.yaml` (Run 2: `x_hh_bbtautau_run2.yaml`).
- Non-resonant HH→bb̄ττ: the corresponding non-resonant config in the same directory.

## 2. Run limits

**Resonant** (a scan over mass points):

```sh
law run PlotResonantLimits --version dev --datacards 'PATH_TO_CARDS/*.txt' --xsec fb --y-log
```

Hints:

- add `--workflow htcondor` to submit to the batch system (local by default);
- add `--remove-output 4,a,y` to clear previous outputs;
- add `--print-status 0` to get the workflow status and the output file name;
- background and options: the [cms-hh inference documentation](https://cms-hh.web.cern.ch/tools/inference/).

**Non-resonant** (run combine directly on the datacard):

```sh
cmsEnv combine StatInference/config/datacard_*.txt -t -1
```

## 3. Pulls & impacts

```sh
PlotPullsAndImpacts --version dev --datacards "PATH_TO_CARDS/<one_card>.txt" \
  --hh-model NO_STR --parameter-values r=1 --parameter-ranges r,-100,100 \
  --method robust --PlotPullsAndImpacts-order-by-impact True --mc-stats True \
  --PullsAndImpacts-custom-args="--expectSignal=1"
```

!!! warning "Do pulls per mass point"
    Run pulls & impacts on a **single** datacard (one mass point) at a time — not on a glob of
    `*.txt`. Add `--remove-output 4,a,y` to clear previous outputs and `--print-status 0` to find
    the output file name.

## Running CWS

[CWS](https://gitlab.cern.ch/cms-analysis/general/cws) (the Combine Workflow System), the
successor of `inference`, is the `cws` submodule. `source env.sh` sets it up like `inference`: on
the same standalone Combine, with its variables (`CWS_BASE`, `CWS_STORE`, …) written to
`cws/.setups/flaf.sh`. Do **not** source `cws/setup.sh` in the same shell.

Most CWS tasks have the same names as the `inference` ones, so CWS has a law config and task
index of its own (`cws/law.cfg`, `cws/.law`), and it runs on the law version it pins
(`cws/modules/law`) rather than the one of `flaf_env`. Prefix the commands with `cwsEnv`, which
selects all three; plain `law` keeps running the FLAF and `inference` tasks.

The commands run from the top of the analysis checkout (or any other directory):

```sh
source env.sh
cwsEnv law index --verbose          # once, and after updating cws
```

### The analysis config

A CWS run is described by an **analysis config**: the datacards, the physics model and the
settings of each task. The one for HH→bb̄ττ is
[`config/Datacards/cws_bbtt.yaml`](https://github.com/cms-flaf/HH_bbtautau/blob/main/config/Datacards/cws_bbtt.yaml):

- `parameters`: the `version` of the outputs (`Run3_2022EE_v2608`), the `campaign` (`2022postEE`,
  which sets the luminosity label) and the `model` with its options
  (`model_nonres_hh_kappa`, VBF dropped with `withoutProcesses=qqhh`);
- `datacards`: the cards by name. `ggF_DNN_HH` is the card of the DNN score fit, under your
  `fs_default` area: `<fs_default>/<version>/Datacards/<era>/datacard_combined_signals.txt`. Edit the `path` to point
  at your own cards;
- `tasks`: one entry per task (`PlotUpperLimitsAtPoint`, `PlotUpperLimits`, …), with its POIs,
  scan ranges and plot options. An entry with a `task:` key is a named variant of that task
  (`PlotUpperLimits_kt` is a `PlotUpperLimits` scan in kt).

`--analysis` takes the path of a config (relative to the current directory, or absolute) or, for
the examples shipped with CWS, a bare name looked up in `cws/cws/conf/task_config/`
(`--analysis dummy_hh_nonres`).

### Running a task

With `law run`, name the task and the config; the task settings come from the config entry of the
same name, or from the entry given with `--analysis-task-config`:

```sh
# expected limit on r at kl = kt = 1
cwsEnv law run PlotUpperLimitsAtPoint --analysis config/Datacards/cws_bbtt.yaml --use-initialfit False

# limit on r as a function of kl, then of kt (the PlotUpperLimits_kt entry)
cwsEnv law run PlotUpperLimits --analysis config/Datacards/cws_bbtt.yaml --use-initialfit False --workers 4
cwsEnv law run PlotUpperLimits --analysis config/Datacards/cws_bbtt.yaml \
  --analysis-task-config PlotUpperLimits_kt --use-initialfit False --workers 4

# limit map in (kl, kt)
cwsEnv law run PlotUpperLimits2D --analysis config/Datacards/cws_bbtt.yaml --use-initialfit False --workers 4

# likelihood scan in kl
cwsEnv law run PlotMultipleLikelihoodScans --analysis config/Datacards/cws_bbtt.yaml --use-initialfit False --workers 4
```

`cws run` does the same, but reads the task from the entry's `task:` key, so only the entry is
named:

```sh
cwsEnv cws run --analysis config/Datacards/cws_bbtt.yaml --task-config PlotUpperLimits_kt --use-initialfit False --workers 4
cwsEnv cws run --analysis config/Datacards/cws_bbtt.yaml --task-config list   # the entries of the config
```

Hints:

- options on the command line win over the config, e.g. `--datacards`, `--pois`,
  `--scan-parameters kl,-10,10,21`;
- add `--print-status 0` to see the output file of a task without running it, and
  `--remove-output 0,a,y` to clear it before running again;
- `--workers N` runs the points of a scan in parallel;
- the configs keep `unblinded: false`, so only expected results are computed.

Outputs go to `cws/data/store/<task>/<model>/<datacards>/…/<version>/`, unless the analysis config
sets `store:`. The non-resonant HH models are fetched into `cws/cws/models/multih_models` on first
use. Only local running is set up: HTCondor submission of CWS tasks is not wired into FLAF yet.
