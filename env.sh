apply_cmssw_customization_steps() {
    run_cmd mkdir -p HHTools
    run_cmd ln -s "$ANALYSIS_PATH/HHbtag" HHTools/HHbtag
    run_cmd mkdir -p TauAnalysis
    run_cmd ln -s "$ANALYSIS_PATH/ClassicSVfit" TauAnalysis/ClassicSVfit
    run_cmd ln -s "$ANALYSIS_PATH/SVfitTF" TauAnalysis/SVfitTF
    run_cmd mkdir -p HHKinFit2
    run_cmd ln -s "$ANALYSIS_PATH/HHKinFit2" HHKinFit2/HHKinFit2
}

# apply_cmssw_customization_steps() (above) only symlinks HHTools/TauAnalysis/
# HHKinFit2 inside the CMSSW src/ tree, for scram's benefit. The Python-side
# legacy-variable code (AnaProd/LegacyVariables.py) declares headers like
# "HHKinFit2/HHKinFit2/interface/..." resolved via cling's ".include
# $ANALYSIS_PATH" directive -- it needs the same symlinks at $ANALYSIS_PATH
# root too, which nothing else creates.
setup_kinfit_runtime_symlinks() {
    if [[ ! -e "$ANALYSIS_PATH/HHKinFit2/HHKinFit2" ]]; then
        mkdir -p "$ANALYSIS_PATH/HHTools" "$ANALYSIS_PATH/TauAnalysis"
        ln -sfn "$ANALYSIS_PATH/HHbtag" "$ANALYSIS_PATH/HHTools/HHbtag"
        ln -sfn "$ANALYSIS_PATH/ClassicSVfit" "$ANALYSIS_PATH/TauAnalysis/ClassicSVfit"
        ln -sfn "$ANALYSIS_PATH/SVfitTF" "$ANALYSIS_PATH/TauAnalysis/SVfitTF"
        ln -sfn "$ANALYSIS_PATH/HHKinFit2" "$ANALYSIS_PATH/HHKinFit2/HHKinFit2"
    fi
}

# HHKinFit2's CMSSW-built shared lib (soft/$FLAF_CMSSW_VERSION/lib/.../
# libHHKinFit2HHKinFit2.so) is compiled against CMSSW's bundled ROOT, but
# AnaProd/LegacyVariables.py loads a KinFit lib from plain python3 under
# flaf_env's ROOT -- different ROOT builds aren't ABI-compatible
# ("TUnixSystem::Load: version mismatch"). Build a standalone lib against
# the now-active flaf_env ROOT instead. Remove HHKinFit2/libHHKinFit2.so to
# force a rebuild after a flaf_env/ROOT version bump.
build_standalone_kinfit_lib() {
    if [[ ! -f "$ANALYSIS_PATH/HHKinFit2/libHHKinFit2.so" ]]; then
        if ! ( cd "$ANALYSIS_PATH/HHKinFit2" && bash compile.sh ); then
            kill -INT $$
        fi
    fi
}

action() {
    local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
    local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"
    local this_file_path="$this_dir/$(basename $this_file)"
    export ANALYSIS_PATH="$this_dir"
    export HH_INFERENCE_PATH="$ANALYSIS_PATH/inference"
    export FLAF_CMSSW_VERSION="CMSSW_16_0_6"
    export FLAF_CMSSW_COMPILER="gcc13"
    # FLAF_PATH defaults to the submodule copy but is respected if pre-set (flaf_dev.sh
    # points it at the edited top-level FLAF in a FLAF_all workspace).
    [ -z "$FLAF_PATH" ] && export FLAF_PATH="$ANALYSIS_PATH/FLAF"
    # FLAF/env.sh re-invokes this same script recursively as "bash env.sh
    # install_cmssw ..." (and install_combine/install_inference) in an
    # isolated `env -i` subshell to do the actual installs; only the plain
    # top-level call below falls through to load_flaf_env, which is what
    # activates flaf_env (so root-config/clang resolve to its ROOT). Skip the
    # KinFit setup in the recursive calls, where flaf_env isn't active yet.
    local cmd="$1"
    source "$FLAF_PATH/env.sh" "$this_file_path" "$@"
    if [[ "$cmd" != "install_cmssw" && "$cmd" != "install_combine" && "$cmd" != "install_inference" ]]; then
        setup_kinfit_runtime_symlinks
        build_standalone_kinfit_lib
    fi
}

action "$@"
unset -f apply_cmssw_customization_steps
unset -f setup_kinfit_runtime_symlinks
unset -f build_standalone_kinfit_lib
unset -f action
