apply_cmssw_customization_steps() {
    run_cmd mkdir -p HHTools
    run_cmd ln -s "$this_dir/HHbtag" HHTools/HHbtag
    run_cmd mkdir -p TauAnalysis
    run_cmd ln -s "$this_dir/ClassicSVfit" TauAnalysis/ClassicSVfit
    run_cmd ln -s "$this_dir/SVfitTF" TauAnalysis/SVfitTF
    run_cmd mkdir -p HHKinFit2
    run_cmd ln -s "$this_dir/HHKinFit2" HHKinFit2/HHKinFit2
}

action() {
    local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
    local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"
    local this_file_path="$this_dir/$(basename $this_file)"

    export ANALYSIS_PATH="$this_dir"
    export HH_INFERENCE_PATH="$ANALYSIS_PATH/inference"

    source $this_dir/FLAF/env.sh "$this_file_path" "$@"
}

action "$@"
unset -f apply_cmssw_customization_steps
unset -f action
