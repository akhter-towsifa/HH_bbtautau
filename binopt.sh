# !/bin/bash

# source FLAF environment
source env.sh

# source inference setup
# source inference/setup.sh

# restore python library path from FLAF
# export PYTHONPATH="$ANALYSIS_SOFT_PATH/flaf_env/lib/python3.11/site-packages:$PYTHONPATH"

# activate python libraries from FLAF
# source $ANALYSIS_SOFT_PATH/flaf_env/bin/activate

# export PATH="$FLAF_CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/build/bin:$PATH"
# export LD_LIBRARY_PATH="$FLAF_CMSSW_BASE/lib:$FLAF_CMSSW_BASE/biglib:$FLAF_CMSSW_BASE/external/lib:$FLAF_CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/build/lib"


# Run Combine tool in a subshell
# (
#   cd "$FLAF_CMSSW_BASE/src"
#   eval "$(scramv1 runtime -sh)"
#   cd -
#   export PATH="$FLAF_CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/build/bin:$PATH"
# #   export LD_LIBRARY_PATH="$FLAF_CMSSW_BASE/lib:$FLAF_CMSSW_BASE/biglib:$FLAF_CMSSW_BASE/external/lib:$FLAF_CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/build/lib"
#   text2workspace.py /afs/cern.ch/work/t/toakhter/private/HH_bbtautau/datacard/hh_res2b_tauTau_2018_13TeV.txt --out workspace.root --mass 125.0 --optimize-simpdf-constraints cms --physics-model dhi.models.hh_model:model_default --physics-option doNNLOscaling=True --physics-option doklDependentUnc=True --physics-option doBRscaling=True --physics-option doHscaling=True --physics-option doProfilergghh=None --physics-option doProfilerqqhh=None --physics-option doProfilervhh=None --physics-option doProfilekl=None --physics-option doProfilekt=None --physics-option doProfileCV=None --physics-option doProfileC2V=None 
#   combine --method AsymptoticLimits workspace.root --verbose 1 --mass 125.0 --seed 0 --toys -1 --run expected --noFitAsimov --redefineSignalPOIs r --setParameters kl=1.0,r_gghh=1.0,r_qqhh=1.0,kt=1.0,CV=1.0,C2V=1.0 --freezeParameters r_gghh,r_qqhh,kl,kt,CV,C2V --cminDefaultMinimizerType Minuit2 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --cminFallbackAlgo Minuit2,0:0.2 --cminFallbackAlgo Minuit2,0:0.4 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --X-rtd TMCSO_AdaptivePseudoAsimov=0 --X-rtd TMCSO_PseudoAsimov=0
#   #law run UpperLimits --version 20250717 --hh-model hh_model.model_default --datacards /afs/cern.ch/work/t/toakhter/private/HH_bbtautau/datacard/hh_res2b_tauTau_2018_13TeV.txt --pois r --scan-parameters kl,1,1,1 --remove-output 0,a,y
# )

# # FLAF Python code in another subshell 
# (
#   source $ANALYSIS_SOFT_PATH/flaf_env/bin/activate
#   python3 -c "import bayes_opt; print(bayes_opt.__version__)"
#   # or your FLAF Python script
# )

(
  source inference/setup.sh
  # text2workspace.py /afs/cern.ch/work/t/toakhter/private/HH_bbtautau/datacard/hh_res2b_tauTau_2018_13TeV.txt --out workspace.root --mass 125.0 --optimize-simpdf-constraints cms --physics-model dhi.models.hh_model:model_default --physics-option doNNLOscaling=True --physics-option doklDependentUnc=True --physics-option doBRscaling=True --physics-option doHscaling=True --physics-option doProfilergghh=None --physics-option doProfilerqqhh=None --physics-option doProfilervhh=None --physics-option doProfilekl=None --physics-option doProfilekt=None --physics-option doProfileCV=None --physics-option doProfileC2V=None 
  # combine --method AsymptoticLimits workspace.root --verbose 1 --mass 125.0 --seed 0 --toys -1 --run expected --noFitAsimov --redefineSignalPOIs r --setParameters kl=1.0,r_gghh=1.0,r_qqhh=1.0,kt=1.0,CV=1.0,C2V=1.0 --freezeParameters r_gghh,r_qqhh,kl,kt,CV,C2V --cminDefaultMinimizerType Minuit2 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --cminFallbackAlgo Minuit2,0:0.2 --cminFallbackAlgo Minuit2,0:0.4 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --X-rtd TMCSO_AdaptivePseudoAsimov=0 --X-rtd TMCSO_PseudoAsimov=0
  #law run UpperLimits --version 20250721 --hh-model hh_model.model_default --datacards /afs/cern.ch/work/t/toakhter/private/HH_bbtautau/datacard/hh_res2b_tauTau_2018_13TeV.txt --pois r --scan-parameters kl,1,1,1 --remove-output 0,a,y
  #july below
  # text2workspace.py /eos/user/t/toakhter/bin_opt_tests_july24_2025/hh_res2b_tauTau_2018_13TeV.txt --out workspace.root --mass 125.0 --optimize-simpdf-constraints cms --physics-model dhi.models.hh_model:model_default --physics-option doNNLOscaling=True --physics-option doklDependentUnc=True --physics-option doBRscaling=True --physics-option doHscaling=True --physics-option doProfilergghh=None --physics-option doProfilerqqhh=None --physics-option doProfilervhh=None --physics-option doProfilekl=None --physics-option doProfilekt=None --physics-option doProfileCV=None --physics-option doProfileC2V=None
  # combine --method AsymptoticLimits workspace.root --verbose 1 --mass 125.0 --seed 0 --toys -1 --run expected --noFitAsimov --redefineSignalPOIs r --setParameters kl=1.0,r_gghh=1.0,r_qqhh=1.0,kt=1.0,CV=1.0,C2V=1.0 --freezeParameters r_gghh,r_qqhh,kl,kt,CV,C2V --cminDefaultMinimizerType Minuit2 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --cminFallbackAlgo Minuit2,0:0.2 --cminFallbackAlgo Minuit2,0:0.4 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --X-rtd TMCSO_AdaptivePseudoAsimov=0 --X-rtd TMCSO_PseudoAsimov=0

  #sept 24
  # text2workspace.py /eos/user/t/toakhter/bin_opt_tests_sept17_hamburg/renamed_datacard_shapes/datacard__cat_22preEE_tautau_res2b__hooks_qcd.txt --out workspace.root --mass 125.0 --optimize-simpdf-constraints cms --physics-model dhi.models.hh_model:model_default --physics-option doNNLOscaling=True --physics-option doklDependentUnc=True --physics-option doBRscaling=True --physics-option doHscaling=True --physics-option doProfilergghh=None --physics-option doProfilerqqhh=None --physics-option doProfilervhh=None --physics-option doProfilekl=None --physics-option doProfilekt=None --physics-option doProfileCV=None --physics-option doProfileC2V=None
  # combine --method AsymptoticLimits workspace.root --verbose 1 --mass 125.0 --seed 0 --toys -1 --run expected --noFitAsimov --redefineSignalPOIs r --setParameters kl=1.0,r_gghh=1.0,r_qqhh=1.0,kt=1.0,CV=1.0,C2V=1.0 --freezeParameters r_gghh,r_qqhh,kl,kt,CV,C2V --cminDefaultMinimizerType Minuit2 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --cminFallbackAlgo Minuit2,0:0.2 --cminFallbackAlgo Minuit2,0:0.4 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --X-rtd TMCSO_AdaptivePseudoAsimov=0 --X-rtd TMCSO_PseudoAsimov=0

  #sept 30
  #text2workspace.py /eos/user/t/toakhter/bin_opt_tests_sept30_hamburg/hh_res2b_tauTau_2022_13p6TeV.txt --out workspace.root --mass 125.0 --optimize-simpdf-constraints cms --physics-model dhi.models.hh_model:model_default --physics-option doNNLOscaling=True --physics-option doklDependentUnc=True --physics-option doBRscaling=True --physics-option doHscaling=True --physics-option doProfilergghh=None --physics-option doProfilerqqhh=None --physics-option doProfilervhh=None --physics-option doProfilekl=None --physics-option doProfilekt=None --physics-option doProfileCV=None --physics-option doProfileC2V=None
  #combine --method AsymptoticLimits workspace.root --verbose 1 --mass 125.0 --seed 0 --toys -1 --run expected --noFitAsimov --redefineSignalPOIs r --setParameters kl=1.0,r_gghh=1.0,r_qqhh=1.0,kt=1.0,CV=1.0,C2V=1.0 --freezeParameters r_gghh,r_qqhh,kl,kt,CV,C2V --cminDefaultMinimizerType Minuit2 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --cminFallbackAlgo Minuit2,0:0.2 --cminFallbackAlgo Minuit2,0:0.4 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --X-rtd TMCSO_AdaptivePseudoAsimov=0 --X-rtd TMCSO_PseudoAsimov=0

  #oct 8,23
  text2workspace.py /eos/user/t/toakhter/bin_opt_tests/bin_opt_test_oct_hamburg_v2/equal_integral/hh_res2b_tauTau_2022_13p6TeV.txt --out workspace.root --mass 125.0 --optimize-simpdf-constraints cms --physics-model dhi.models.hh_model_NNLOFix_13p6:model_default --physics-option doNNLOscaling=True --physics-option doklDependentUnc=True --physics-option doBRscaling=True --physics-option doHscaling=True --physics-option doProfilergghh=None --physics-option doProfilerqqhh=None --physics-option doProfilervhh=None --physics-option doProfilekl=None --physics-option doProfilekt=None --physics-option doProfileCV=None --physics-option doProfileC2V=None
  combine --method AsymptoticLimits workspace.root --verbose 1 --mass 125.0 --seed 0 --toys -1 --run expected --noFitAsimov --redefineSignalPOIs r --setParameters kl=1.0,r_gghh=1.0,r_qqhh=1.0,kt=1.0,CV=1.0,C2V=1.0 --freezeParameters r_gghh,r_qqhh,kl,kt,CV,C2V --cminDefaultMinimizerType Minuit2 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --cminFallbackAlgo Minuit2,0:0.2 --cminFallbackAlgo Minuit2,0:0.4 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --X-rtd TMCSO_AdaptivePseudoAsimov=0 --X-rtd TMCSO_PseudoAsimov=0

  # law run UpperLimits --version 20250724 --hh-model hh_model.model_default --datacards /eos/user/t/toakhter/bin_opt_tests_july24_2025/hh_res2b_tauTau_2018_13TeV.txt --pois r --scan-parameters kl,1,1,1 --remove-output 0,a,y
)



# run the following to unset inference/setup.sh and reset flaf env
source env.sh
source $ANALYSIS_SOFT_PATH/flaf_env/bin/activate
python3 -c "import bayes_opt; print(bayes_opt.__version__)"
