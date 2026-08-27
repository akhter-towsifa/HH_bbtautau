import os

from FLAF.Common.Utilities import DeclareHeader


# Gen-level information the MC stitching selects on. It is derived from GenPart/LHEPart,
# which the anaTuple does not keep, so it has to be stored here: the merge stage evaluates
# the same bin selections to pick the cross-section and the denominator, and can only read
# these back from the anaTuple. Which kinds a process needs is declared as `genInfo` in
# config/<era>/processes.yaml, next to the stitching processor that consumes them.
def addGenProcessInfo(dfw, gen_info):
    if "DY" in gen_info or "TauTau" in gen_info:
        DeclareHeader(
            os.path.join(os.environ["FLAF_PATH"], "include", "GenProcess", "DY.h")
        )
    if "TT" in gen_info:
        DeclareHeader(
            os.path.join(os.environ["FLAF_PATH"], "include", "GenProcess", "TT.h")
        )

    if "DY" in gen_info:
        dfw.Define(
            "_DYInfo",
            "gen_process::dy::identifyLHE(LHEPart_pt, LHEPart_eta, LHEPart_phi, "
            "LHEPart_mass, LHEPart_pdgId, LHEPart_status)",
        )
        dfw.DefineAndAppend("DYInfo_flavor", "_DYInfo.flavor")
        dfw.DefineAndAppend("DYInfo_mll", "_DYInfo.mll")

    if "TauTau" in gen_info:
        dfw.Define(
            "_TauTauInfo",
            "gen_process::dy::identifyTauTau(GenPart_pt, GenPart_eta, GenPart_phi, "
            "GenPart_mass, GenPart_pdgId, GenPart_statusFlags, "
            "GenPart_genPartIdxMother)",
        )
        dfw.DefineAndAppend("TauTauInfo_passFilter", "_TauTauInfo.passFilter()")
        # The quantities the filter is made of, so that a change of its definition does not
        # require reprocessing the nanoAOD again.
        for idx in range(2):
            dfw.DefineAndAppend(
                f"TauTauInfo_vis_type{idx + 1}",
                f"static_cast<int>(_TauTauInfo.vis_type[{idx}])",
            )
            dfw.DefineAndAppend(
                f"TauTauInfo_vis_pt{idx + 1}",
                f"static_cast<float>(_TauTauInfo.vis_pt[{idx}])",
            )
            dfw.DefineAndAppend(
                f"TauTauInfo_vis_abseta{idx + 1}",
                f"static_cast<float>(_TauTauInfo.vis_abseta[{idx}])",
            )

    if "TT" in gen_info:
        dfw.Define(
            "_TTInfo",
            "gen_process::tt::identify(GenPart_pdgId, GenPart_statusFlags, "
            "GenPart_genPartIdxMother)",
        )
        dfw.DefineAndAppend("TTInfo_nLeptonicW", "_TTInfo.nLeptonicW()")
        for idx in range(2):
            dfw.DefineAndAppend(
                f"TTInfo_wDecay{idx + 1}",
                f"static_cast<int>(_TTInfo.w_decay[{idx}])",
            )
