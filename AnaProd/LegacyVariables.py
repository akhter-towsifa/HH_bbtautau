import os
import subprocess
from FLAF.Common.Utilities import *

initialized = False


def _setup_kinfit_runtime(analysis_path):
    """One-time HHKinFit2 standalone-build setup, done lazily here (not in
    env.sh) so it only happens -- and is only required to succeed -- when
    kinFit is actually used. Other tasks/workflows that never call
    Initialize(load_kinfit=True) never pay this cost and never depend on
    HHKinFit2 building successfully.

    Mirrors apply_cmssw_customization_steps() in env.sh (which only runs
    during a fresh CMSSW install, for scram's benefit, inside the CMSSW
    src/ tree) -- the Python-side header declare below resolves
    "HHKinFit2/HHKinFit2/interface/..." via cling's ".include $ANALYSIS_PATH"
    directive, so it needs the same symlinks at $ANALYSIS_PATH root too.

    The CMSSW-built lib (soft/$FLAF_CMSSW_VERSION/lib/.../libHHKinFit2HHKinFit2.so)
    is compiled against CMSSW's bundled ROOT, not flaf_env's -- different
    ROOT builds aren't ABI-compatible ("TUnixSystem::Load: version
    mismatch") -- so a standalone lib is built against whatever ROOT is
    active here instead. Remove HHKinFit2/libHHKinFit2.so to force a
    rebuild after a flaf_env/ROOT version bump.
    """
    hhkinfit_link = os.path.join(analysis_path, "HHKinFit2", "HHKinFit2")
    if not os.path.exists(hhkinfit_link):
        os.makedirs(os.path.join(analysis_path, "HHTools"), exist_ok=True)
        os.makedirs(os.path.join(analysis_path, "TauAnalysis"), exist_ok=True)
        for target, link in (
            (os.path.join(analysis_path, "HHbtag"), os.path.join(analysis_path, "HHTools", "HHbtag")),
            (os.path.join(analysis_path, "ClassicSVfit"), os.path.join(analysis_path, "TauAnalysis", "ClassicSVfit")),
            (os.path.join(analysis_path, "SVfitTF"), os.path.join(analysis_path, "TauAnalysis", "SVfitTF")),
            (os.path.join(analysis_path, "HHKinFit2"), hhkinfit_link),
        ):
            if not os.path.exists(link):
                os.symlink(target, link)

    kinfit_lib = os.path.join(analysis_path, "HHKinFit2", "libHHKinFit2.so")
    if not os.path.isfile(kinfit_lib):
        print(f"Building standalone {kinfit_lib} against the active ROOT...")
        result = subprocess.run(["bash", "compile.sh"], cwd=os.path.join(analysis_path, "HHKinFit2"))
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build {kinfit_lib}")
    return kinfit_lib


def Initialize(load_kinfit=True, load_svfit=True, load_mt2=True):
    global initialized
    global tau1_p4
    global tau2_p4
    global b1_p4
    global b2_p4
    global MET_p4
    if initialized:
        raise RuntimeError("Legacy variables are already initialized")
    headers_to_include = ["FLAF/include/AnalysisTools.h"]
    if load_kinfit:
        kinfit_lib = _setup_kinfit_runtime(os.environ["ANALYSIS_PATH"])
        load_result = ROOT.gSystem.Load(kinfit_lib)
        if load_result != 0:
            raise RuntimeError(f"Failed to load {kinfit_lib}, status {load_result}")
        headers_to_include += ["include/KinFitInterface.h"]
    if load_svfit:
        headers_to_include += ["include/SVfitAnaInterface.h"]
    if load_mt2:
        headers_to_include += [
            "FLAF/include/MT2.h",
            "FLAF/include/Lester_mt2_bisect.cpp",
        ]

    for header in headers_to_include:
        DeclareHeader(os.environ["ANALYSIS_PATH"] + "/" + header)

    tau1_p4 = "ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>(tau1_pt,tau1_eta,tau1_phi,tau1_mass)"
    tau2_p4 = "ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>(tau2_pt,tau2_eta,tau2_phi,tau2_mass)"
    b1_p4 = "ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>(b1_pt,b1_eta,b1_phi,b1_mass)"
    b2_p4 = "ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>(b2_pt,b2_eta,b2_phi,b2_mass)"
    MET_p4 = "ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>(met_pt, 0., met_phi, 0.)"
    initialized = True


def GetMT2(df):
    if not initialized:
        raise RuntimeError("Legacy Variables not initialized!")
    df = df.Define(
        "MT2",
        f"entry_valid ?  float(analysis::Calculate_MT2({tau1_p4}, {tau2_p4}, {b1_p4},{b2_p4}, {MET_p4})): -100.",
    )
    return df, ["MT2"]


def GetKinFit(df):
    if not initialized:
        raise RuntimeError("Legacy Variables not initialized!")
    df = df.Define("bjet1_JER", f"b1_ptRes*{b1_p4}.E()")
    df = df.Define("bjet2_JER", f"b2_ptRes*{b2_p4}.E()")
    df = df.Define(
        "kinFit_result",
        f"""entry_valid ? kin_fit::FitProducer::Fit({tau1_p4}, {tau2_p4},{b1_p4}, {b2_p4}, {MET_p4}, met_covXX, met_covXY, met_covYY, bjet1_JER,bjet2_JER, 0): kin_fit::FitResults()""",
    )

    df = df.Define(
        "kinFit_convergence", "entry_valid ? kinFit_result.convergence: -100."
    )
    df = df.Define("kinFit_m", "entry_valid ? float(kinFit_result.mass): -100.")
    df = df.Define("kinFit_chi2", "entry_valid ? float(kinFit_result.chi2): -100.")
    return df, ["kinFit_convergence", "kinFit_m", "kinFit_chi2", "kinFit_result"]


def GetSVFit(df):
    df = df.Define(
        "SVfit_result",
        f"""entry_valid ? sv_fit::FitProducer::Fit({tau1_p4}, static_cast<Leg>(tau1_legType), tau1_decayMode, {tau2_p4}, static_cast<Leg>(tau2_legType), tau2_decayMode, {MET_p4}, met_covXX, met_covXY, met_covYY) : sv_fit::FitResults()""",
    )
    df = df.Define(
        "SVfit_valid", "entry_valid ? int(SVfit_result.has_valid_momentum) : -100."
    )
    df = df.Define(
        "SVfit_pt", "entry_valid ? float(SVfit_result.momentum.pt()) : -100."
    )
    df = df.Define(
        "SVfit_eta", "entry_valid ? float(SVfit_result.momentum.eta()) : -100."
    )
    df = df.Define(
        "SVfit_phi", "entry_valid ? float(SVfit_result.momentum.phi()) : -100."
    )
    df = df.Define(
        "SVfit_m", "entry_valid ? float(SVfit_result.momentum.mass()) : -100."
    )
    df = df.Define(
        "SVfit_pt_error",
        "entry_valid ? float(SVfit_result.momentum_error.pt()) : -100.",
    )
    df = df.Define(
        "SVfit_eta_error",
        "entry_valid ? float(SVfit_result.momentum_error.eta()) : -100.",
    )
    df = df.Define(
        "SVfit_phi_error",
        "entry_valid ? float(SVfit_result.momentum_error.phi()) : -100.",
    )
    df = df.Define(
        "SVfit_m_error",
        "entry_valid ? float(SVfit_result.momentum_error.mass()) : -100.",
    )
    df = df.Define(
        "SVfit_mt", "entry_valid ? float(SVfit_result.transverseMass) : -100."
    )
    df = df.Define(
        "SVfit_mt_error",
        "entry_valid ? float(SVfit_result.transverseMass_error) : -100.",
    )
    return df, [
        "SVfit_valid",
        "SVfit_pt",
        "SVfit_eta",
        "SVfit_phi",
        "SVfit_m",
        "SVfit_pt_error",
        "SVfit_eta_error",
        "SVfit_phi_error",
        "SVfit_m_error",
        "SVfit_mt",
        "SVfit_mt_error",
    ]
