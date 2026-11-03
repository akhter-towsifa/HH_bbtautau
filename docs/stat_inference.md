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

```sh
cwsEnv law index --verbose          # once, and after updating cws
cwsEnv cws run --analysis CONFIG --task-config ENTRY
cwsEnv law run PlotUpperLimitsAtPoint --analysis dummy_hh_nonres --use-initialfit False --workers 4
```

Outputs go to `cws/data/store`, unless the analysis config sets `store:`. The non-resonant HH
models are fetched into `cws/cws/models/multih_models` on first use. Only local running is
set up: HTCondor submission of CWS tasks is not wired into FLAF yet.
