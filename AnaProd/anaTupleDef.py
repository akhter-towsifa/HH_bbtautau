import AnaProd.baseline as AnaBaseline
import FLAF.Common.BaselineSelection as CommonBaseline
from Corrections.Corrections import Corrections

loadTF = True
loadHHBtag = True
lepton_legs = ["tau1", "tau2"]
offline_legs = ["tau1", "tau2", "b1", "b2"]

deepTauScores = [
    "rawDeepTau2017v2p1VSe",
    "rawDeepTau2017v2p1VSmu",
    "rawDeepTau2017v2p1VSjet",
    "rawDeepTau2018v2p5VSe",
    "rawDeepTau2018v2p5VSmu",
    "rawDeepTau2018v2p5VSjet",
    "idDeepTau2017v2p1VSe",
    "idDeepTau2017v2p1VSjet",
    "idDeepTau2017v2p1VSmu",
    "idDeepTau2018v2p5VSe",
    "idDeepTau2018v2p5VSjet",
    "idDeepTau2018v2p5VSmu",
    "decayMode",
]
Muon_observables = [
    "Muon_tkRelIso",
    "Muon_pfRelIso04_all",
    "Muon_highPtId",
    "Muon_tightId",
    "Muon_mediumId",
]
Electron_observables = [
    "Electron_mvaNoIso_WP80",
    "Electron_mvaIso_WP80",
    "Electron_pfRelIso03_all",
]

JetObservables = [
    "PNetRegPtRawCorr",
    "PNetRegPtRawCorrNeutrino",
    "PNetRegPtRawRes",
    "UParTAK4RegPtRawCorr",
    "UParTAK4RegPtRawCorrNeutrino",
    "UParTAK4RegPtRawRes",
    "area",
    "btagDeepFlavB",
    "btagDeepFlavCvB",
    "btagDeepFlavCvL",
    "btagDeepFlavQG",
    "btagPNetB",
    "btagPNetCvB",
    "btagPNetCvL",
    "btagPNetCvNotB",
    "btagPNetQvG",
    "btagPNetTauVJet",
    "btagUParTAK4B",
    "btagUParTAK4CvB",
    "btagUParTAK4CvL",
    "btagUParTAK4CvNotB",
    "btagUParTAK4QvG",
    "btagUParTAK4TauVJet",
    "chEmEF",
    "chHEF",
    "chMultiplicity",
    "hfEmEF",
    "hfHEF",
    "hfadjacentEtaStripsSize",
    "hfcentralEtaStripSize",
    "hfsigmaEtaEta",
    "hfsigmaPhiPhi",
    "jetId",
    "muEF",
    "muonSubtrFactor",
    "nConstituents",
    "nElectrons",
    "nMuons",
    "nSVs",
    "neEmEF",
    "neHEF",
    "neMultiplicity",
    "puIdDisc",
    "puId_beta",
    "puId_dR2Mean",
    "puId_frac01",
    "puId_frac02",
    "puId_frac03",
    "puId_frac04",
    "puId_jetR",
    "puId_jetRchg",
    "puId_majW",
    "puId_minW",
    "puId_nCharged",
    "puId_ptD",
    "puId_pull",
    "rawFactor",
    "ptRes",
    "idbtagPNetB",
    "HHbtag",
]
JetObservablesMC = ["hadronFlavour", "partonFlavour"]
FatJetObservables = [
    "area",
    "chEmEF",
    "chHEF",
    "chMultiplicity",
    "globalParT2_QCD0HF",
    "globalParT2_QCD1HF",
    "globalParT2_QCD2HF",
    "globalParT2_TopW",
    "globalParT2_TopbW",
    "globalParT2_TopbWev",
    "globalParT2_TopbWmv",
    "globalParT2_TopbWq",
    "globalParT2_TopbWqq",
    "globalParT2_TopbWtauhv",
    "globalParT2_Xbb",
    "globalParT2_XbbVsQCD",
    "globalParT2_Xcc",
    "globalParT2_Xcs",
    "globalParT2_Xgg",
    "globalParT2_Xqq",
    "globalParT2_Xtauhtaue",
    "globalParT2_Xtauhtauh",
    "globalParT2_Xtauhtaum",
    "globalParT_massRes",
    "globalParT_massVis",
    "jetId",
    "lsf3",
    "msoftdrop",
    "muEF",
    "n2b1",
    "n3b1",
    "nConstituents",
    "neEmEF",
    "neHEF",
    "neMultiplicity",
    "particleNetLegacy_QCD",
    "particleNetLegacy_QCDb",
    "particleNetLegacy_QCDbb",
    "particleNetLegacy_QCDc",
    "particleNetLegacy_QCDcc",
    "particleNetLegacy_QCDothers",
    "particleNetLegacy_Xbb",
    "particleNetLegacy_Xcc",
    "particleNetLegacy_Xqq",
    "particleNetLegacy_mass",
    "particleNetWithMass_H4qvsQCD",
    "particleNetWithMass_HbbvsQCD",
    "particleNetWithMass_HccvsQCD",
    "particleNetWithMass_QCD",
    "particleNetWithMass_TvsQCD",
    "particleNetWithMass_WvsQCD",
    "particleNetWithMass_ZvsQCD",
    "particleNet_QCD",
    "particleNet_QCD0HF",
    "particleNet_QCD1HF",
    "particleNet_QCD2HF",
    "particleNet_Xbb",
    "particleNet_XbbVsQCD",
    "particleNet_XccVsQCD",
    "particleNet_XggVsQCD",
    "particleNet_XqqVsQCD",
    "particleNet_XteVsQCD",
    "particleNet_XtmVsQCD",
    "particleNet_XttVsQCD",
    "particleNet_massCorr",
    "rawFactor",
    "tau1",
    "tau2",
    "tau3",
    "tau4",
]
FatJetObservablesMC = ["hadronFlavour"]

SubJetObservables = ["btagDeepB", "eta", "mass", "phi", "pt", "rawFactor"]
SubJetObservablesMC = ["hadronFlavour", "partonFlavour"]

defaultColToSave = [
    "FullEventId",
    "luminosityBlock",
    "run",
    "event",
    "period",
    "X_mass",
    "X_spin",
    "isData",
    "PuppiMET_pt",
    "PuppiMET_phi",
    "nJet",
    "DeepMETResolutionTune_pt",
    "DeepMETResolutionTune_phi",
    "DeepMETResponseTune_pt",
    "DeepMETResponseTune_phi",
    "PV_npvs",
]


def getDefaultColumnsToSave(isData):
    colToSave = defaultColToSave.copy()
    if not isData:
        colToSave.extend(["Pileup_nTrueInt"])
    return colToSave


def addAllVariables(
    dfw,
    syst_name,
    isData,
    trigger_class,
    lepton_legs,
    isSignal,
    applyTriggerFilter,
    global_params,
    channels,
):
    dfw.Apply(AnaBaseline.RecoHttCandidateSelection, global_params)
    dfw.Apply(AnaBaseline.RecoJetSelection, global_params["era"])
    dfw.Apply(AnaBaseline.ThirdLeptonVeto)
    dfw.Apply(AnaBaseline.DefineHbbCand, global_params["met_type"])
    dfw.DefineAndAppend("Hbb_isValid", "HbbCandidate.has_value()")
    dfw.Apply(AnaBaseline.ExtraRecoJetSelection, global_params["era"])
    dfw.Apply(AnaBaseline.VBFJetSelection)
    dfw.Apply(Corrections.getGlobal().JetVetoMap.GetJetVetoMap)
    dfw.Apply(CommonBaseline.ApplyJetVetoMap)
    dfw.Apply(Corrections.getGlobal().jet.getEnergyResolution)
    dfw.Apply(Corrections.getGlobal().btag.getWPid, "Jet")
    jet_obs = []
    jet_obs.extend(JetObservables)
    if global_params["requireHbbJets"]:
        dfw.Apply(AnaBaseline.ApplyJetSelection)
    if not isData:
        # dfw.Define(f"Jet_genJet_idx", " FindMatching(Jet_p4,GenJet_p4,0.3)")
        jet_obs.extend(JetObservablesMC)
        if isSignal:
            dfw.Define(f"Jet_fromGenHbb", f"Take(GenJet_Hbb, Jet_genJetIdx, false)")
            dfw.DefineAndAppend(
                "nJetFromGenHbb", "Jet_p4[Jet_fromGenHbb && Jet_bCand].size()"
            )

            for gen_idx in range(2):
                dfw.DefineAndAppend(
                    f"genLepton{gen_idx+1}_legType",
                    f"static_cast<int>(genHttCandidate->leg_type[{gen_idx}])",
                )
                for var in ["pt", "eta", "phi", "mass"]:
                    dfw.DefineAndAppend(
                        f"genLepton{gen_idx+1}_{var}",
                        f"static_cast<float>(genHttCandidate->leg_p4[{gen_idx}].{var}())",
                    )

    dfw.DefineAndAppend(f"nBJets", f"Jet_p4[Jet_bCand].size()")

    centralJet_vars = ["p4", "btagPNetB"]
    if not isData:
        centralJet_vars.extend(["hadronFlavour"])
    for jetVar in centralJet_vars:
        dfw.Define(f"centralJet_{jetVar}", f"Jet_{jetVar}[Jet_bCand]")

    if global_params["storeVBFJets"]:
        dfw.DefineAndAppend(f"VBFJet_pt", f"v_ops::pt(Jet_p4[VBFJet_B1])")
        dfw.DefineAndAppend(f"VBFJet_pt_raw", f"Jet_pt[VBFJet_B1]")
        dfw.DefineAndAppend(f"VBFJet_eta", f"v_ops::eta(Jet_p4[VBFJet_B1])")
        dfw.DefineAndAppend(f"VBFJet_phi", f"v_ops::phi(Jet_p4[VBFJet_B1])")
        dfw.DefineAndAppend(f"VBFJet_mass", f"v_ops::mass(Jet_p4[VBFJet_B1])")

        for jetVar in jet_obs:
            dfw.DefineAndAppend(f"VBFJet_{jetVar}", f"Jet_{jetVar}[VBFJet_B1]")
    else:
        dfw.DefineAndAppend(f"nVBFJets", f"Jet_p4[VBFJet_B1].size()")

    if not isData:
        dfw.colToSave.append("nLHEPart")
        # dfw.colToSave.append("nLHEPdfWeight")
        # # dfw.colToSave.append("nLHEScaleWeight")
        # dfw.colToSave.append("LHEPdfWeight")
        # dfw.colToSave.append("LHEReweightingWeight")
        # dfw.colToSave.append("LHEScaleWeight")
        # # dfw.colToSave.append("LHEWeight_originalXWGTUP")
        dfw.colToSave.append("LHEPart_pdgId")
        dfw.colToSave.append("LHEPart_pt")
        dfw.colToSave.append("LHEPart_eta")
        dfw.colToSave.append("LHEPart_phi")
        dfw.colToSave.append("LHEPart_mass")
        dfw.colToSave.append("LHEPart_status")
        dfw.colToSave.append("LHEPart_spin")
        dfw.colToSave.append("LHEPart_incomingpz")
        dfw.colToSave.append("LHE_AlphaS")
        dfw.colToSave.append("LHE_HT")
        dfw.colToSave.append("LHE_HTIncoming")
        dfw.colToSave.append("LHE_Nb")
        dfw.colToSave.append("LHE_Nc")
        dfw.colToSave.append("LHE_Nglu")
        dfw.colToSave.append("LHE_Njets")
        dfw.colToSave.append("LHE_NpLO")
        dfw.colToSave.append("LHE_NpNLO")
        dfw.colToSave.append("LHE_Nuds")
        dfw.colToSave.append("LHE_Vpt")

        dfw.colToSave.append("GenJet_eta")
        dfw.colToSave.append("GenJet_hadronFlavour")
        dfw.colToSave.append("GenJet_mass")
        # dfw.colToSave.append("GenJet_nBHadrons")
        # dfw.colToSave.append("GenJet_nCHadrons")
        dfw.colToSave.append("GenJet_partonFlavour")
        dfw.colToSave.append("GenJet_phi")
        dfw.colToSave.append("GenJet_pt")

        # dfw.colToSave.append("GenJetAK8_eta")
        # dfw.colToSave.append("GenJetAK8_hadronFlavour")
        # dfw.colToSave.append("GenJetAK8_mass")
        # dfw.colToSave.append("GenJetAK8_nBHadrons")
        # dfw.colToSave.append("GenJetAK8_nCHadrons")
        # dfw.colToSave.append("GenJetAK8_partonFlavour")
        # dfw.colToSave.append("GenJetAK8_phi")
        # dfw.colToSave.append("GenJetAK8_pt")

    pf_str = global_params["met_type"]
    dfw.DefineAndAppend(f"met_pt_nano", f"static_cast<float>({pf_str}_p4_nano.pt())")
    dfw.DefineAndAppend(f"met_phi_nano", f"static_cast<float>({pf_str}_p4_nano.phi())")
    dfw.DefineAndAppend("met_pt", f"static_cast<float>({pf_str}_p4.pt())")
    dfw.DefineAndAppend("met_phi", f"static_cast<float>({pf_str}_p4.phi())")
    dfw.DefineAndAppend(
        "metnomu_pt_nano",
        f"static_cast<float>(GetMetNoMu(HttCandidate, {pf_str}_p4_nano).pt())",
    )
    dfw.DefineAndAppend(
        "metnomu_phi_nano",
        f"static_cast<float>(GetMetNoMu(HttCandidate, {pf_str}_p4_nano).phi())",
    )
    dfw.DefineAndAppend(
        "metnomu_pt", f"static_cast<float>(GetMetNoMu(HttCandidate, {pf_str}_p4).pt())"
    )
    dfw.DefineAndAppend(
        "metnomu_phi",
        f"static_cast<float>(GetMetNoMu(HttCandidate, {pf_str}_p4).phi())",
    )
    for var in ["covXX", "covXY", "covYY"]:
        dfw.DefineAndAppend(f"met_{var}", f"static_cast<float>({pf_str}_{var})")

    dfw.DefineAndAppend("channelId", "static_cast<int>(HttCandidate.channel())")
    channel_to_select = " || ".join(
        f"HttCandidate.channel()==Channel::{ch}" for ch in channels
    )  # global_params["channelSelection"])
    dfw.Filter(channel_to_select, "select channels")
    fatjet_obs = []
    fatjet_obs.extend(FatJetObservables)
    if not isData:
        dfw.Define(
            f"FatJet_genJet_idx",
            f" FindMatching(FatJet_p4[FatJet_bbCand],GenJetAK8_p4,0.3)",
        )
        fatjet_obs.extend(FatJetObservablesMC)
        if isSignal:
            dfw.DefineAndAppend(
                "genchannelId", "static_cast<int>(genHttCandidate->channel())"
            )
    dfw.DefineAndAppend(f"SelectedFatJet_pt", f"v_ops::pt(FatJet_p4[FatJet_bbCand])")
    dfw.DefineAndAppend(f"SelectedFatJet_eta", f"v_ops::eta(FatJet_p4[FatJet_bbCand])")
    dfw.DefineAndAppend(f"SelectedFatJet_phi", f"v_ops::phi(FatJet_p4[FatJet_bbCand])")
    dfw.DefineAndAppend(
        f"SelectedFatJet_mass", f"v_ops::mass(FatJet_p4[FatJet_bbCand])"
    )

    for fatjetVar in fatjet_obs:
        dfw.DefineAndAppend(
            f"SelectedFatJet_{fatjetVar}", f"FatJet_{fatjetVar}[FatJet_bbCand]"
        )
    subjet_obs = []
    subjet_obs.extend(SubJetObservables)
    if not isData:
        dfw.Define(
            f"SubJet1_genJet_idx",
            f" FindMatching(SubJet_p4[FatJet_subJetIdx1],SubGenJetAK8_p4,0.3)",
        )
        dfw.Define(
            f"SubJet2_genJet_idx",
            f" FindMatching(SubJet_p4[FatJet_subJetIdx2],SubGenJetAK8_p4,0.3)",
        )
        fatjet_obs.extend(SubJetObservablesMC)

    for subJetIdx in [1, 2]:
        dfw.Define(
            f"SelectedFatJet_subJetIdx{subJetIdx}",
            f"FatJet_subJetIdx{subJetIdx}[FatJet_bbCand]",
        )
        dfw.Define(
            f"FatJet_SubJet{subJetIdx}_isValid",
            f" FatJet_subJetIdx{subJetIdx} >=0 && FatJet_subJetIdx{subJetIdx} < nSubJet",
        )
        dfw.DefineAndAppend(
            f"SelectedFatJet_SubJet{subJetIdx}_isValid",
            f"FatJet_SubJet{subJetIdx}_isValid[FatJet_bbCand]",
        )
        for subJetVar in subjet_obs:
            dfw.DefineAndAppend(
                f"SelectedFatJet_SubJet{subJetIdx}_{subJetVar}",
                f"""
                                RVecF subjet_var(SelectedFatJet_pt.size(), 0.f);
                                for(size_t fj_idx = 0; fj_idx<SelectedFatJet_pt.size(); fj_idx++) {{
                                    auto sj_idx = SelectedFatJet_subJetIdx{subJetIdx}.at(fj_idx);
                                    if(sj_idx >= 0 && sj_idx < SubJet_{subJetVar}.size()){{
                                        subjet_var[fj_idx] = SubJet_{subJetVar}.at(sj_idx);
                                    }}
                                }}
                                return subjet_var;
                                """,
            )

    n_legs = 2

    for leg_idx in range(n_legs):

        def LegVar(
            var_name,
            var_expr,
            var_type=None,
            var_cond=None,
            check_leg_type=True,
            default=0,
        ):
            cond = var_cond
            if check_leg_type:
                type_cond = f"HttCandidate.leg_type[{leg_idx}] != Leg::none"
                cond = f"{type_cond} && ({cond})" if cond else type_cond
            define_expr = (
                f"static_cast<{var_type}>({var_expr})" if var_type else var_expr
            )
            if cond:
                define_expr = f"{cond} ? ({define_expr}) : {default}"
            dfw.DefineAndAppend(f"tau{leg_idx+1}_{var_name}", define_expr)

        LegVar("legType", f"HttCandidate.leg_type[{leg_idx}]", check_leg_type=False)
        for var in ["pt", "eta", "phi", "mass"]:
            LegVar(
                var,
                f"HttCandidate.leg_p4[{leg_idx}].{var}()",
                var_type="float",
                default="-1.f",
            )
        LegVar("charge", f"HttCandidate.leg_charge[{leg_idx}]", var_type="int")

        dfw.Define(
            f"tau{leg_idx+1}_jetIdx",
            f"""
                if(HttCandidate.leg_type[{leg_idx}] == Leg::e)
                    return Electron_jetIdx.at(HttCandidate.leg_index[{leg_idx}]);
                if(HttCandidate.leg_type[{leg_idx}] == Leg::mu)
                    return Muon_jetIdx.at(HttCandidate.leg_index[{leg_idx}]);
                if(HttCandidate.leg_type[{leg_idx}] == Leg::tau)
                    return Tau_jetIdx.at(HttCandidate.leg_index[{leg_idx}]);
                return short(-1);
            """,
        )
        LegVar("iso", f"HttCandidate.leg_rawIso.at({leg_idx})")
        for pnetVar in [
            "btagPNetB",
            "btagPNetCvB",
            "btagPNetCvL",
            "btagPNetCvNotB",
            "btagPNetQvG",
            "btagPNetTauVJet",
        ]:
            LegVar(
                f"seedingJet_{pnetVar}",
                f"Jet_{pnetVar}.at(tau{leg_idx+1}_jetIdx)",
                var_type="float",
                var_cond=f"tau{leg_idx+1}_jetIdx>=0",
                default="-1.f",
            )

        for deepTauScore in deepTauScores:
            LegVar(
                deepTauScore,
                f"Tau_{deepTauScore}.at(HttCandidate.leg_index[{leg_idx}])",
                var_cond=f"HttCandidate.leg_type[{leg_idx}] == Leg::tau",
                default="-1.f",
            )
        for muon_obs in Muon_observables:
            LegVar(
                muon_obs,
                f"{muon_obs}.at(HttCandidate.leg_index[{leg_idx}])",
                var_cond=f"HttCandidate.leg_type[{leg_idx}] == Leg::mu",
                default="-1",
            )
        for ele_obs in Electron_observables:
            LegVar(
                ele_obs,
                f"{ele_obs}.at(HttCandidate.leg_index[{leg_idx}])",
                var_cond=f"HttCandidate.leg_type[{leg_idx}] == Leg::e",
                default="-1",
            )
        if not isData:
            dfw.Define(
                f"tau{leg_idx+1}_genMatchIdx",
                f"HttCandidate.leg_type[{leg_idx}] != Leg::none ? HttCandidate.leg_genMatchIdx[{leg_idx}] : -1",
            )
            LegVar(
                "gen_kind",
                f"genLeptons.at(tau{leg_idx+1}_genMatchIdx).kind()",
                var_type="int",
                var_cond=f"tau{leg_idx+1}_genMatchIdx>=0",
                default="static_cast<int>(GenLeptonMatch::NoMatch)",
            )
            for var in ["pt", "eta", "phi", "mass"]:
                LegVar(
                    f"gen_vis_{var}",
                    f"genLeptons.at(tau{leg_idx+1}_genMatchIdx).visibleP4().{var}()",
                    var_type="float",
                    var_cond=f"tau{leg_idx+1}_genMatchIdx>=0",
                    default="-1.f",
                )
            LegVar(
                "gen_nChHad",
                f"genLeptons.at(tau{leg_idx+1}_genMatchIdx).nChargedHadrons()",
                var_type="int",
                var_cond=f"tau{leg_idx+1}_genMatchIdx>=0",
                default="-1",
            )
            LegVar(
                "gen_nNeutHad",
                f"genLeptons.at(tau{leg_idx+1}_genMatchIdx).nNeutralHadrons()",
                var_type="int",
                var_cond=f"tau{leg_idx+1}_genMatchIdx>=0",
                default="-1",
            )
            LegVar(
                "gen_charge",
                f"genLeptons.at(tau{leg_idx+1}_genMatchIdx).charge()",
                var_type="int",
                var_cond=f"tau{leg_idx+1}_genMatchIdx>=0",
                default="-10",
            )
            LegVar(
                "seedingJet_partonFlavour",
                f"Jet_partonFlavour.at(tau{leg_idx+1}_jetIdx)",
                var_type="int",
                var_cond=f"tau{leg_idx+1}_jetIdx>=0",
                default="-10",
            )
            LegVar(
                "seedingJet_hadronFlavour",
                f"Jet_hadronFlavour.at(tau{leg_idx+1}_jetIdx)",
                var_type="int",
                var_cond=f"tau{leg_idx+1}_jetIdx>=0",
                default="-10",
            )

        for var in ["pt", "eta", "phi", "mass"]:
            LegVar(
                f"seedingJet_{var}",
                f"Jet_p4.at(tau{leg_idx+1}_jetIdx).{var}()",
                var_type="float",
                var_cond=f"tau{leg_idx+1}_jetIdx>=0",
                default="-1.f",
            )

        # Save the lep* p4 and index directly to avoid using HwwCandidate in SF LUTs
        dfw.Define(
            f"tau{leg_idx+1}_p4",
            f"HttCandidate.leg_type.size() > {leg_idx} ? HttCandidate.leg_p4.at({leg_idx}) : LorentzVectorM()",
        )
        dfw.Define(
            f"tau{leg_idx+1}_index",
            f"HttCandidate.leg_type.size() > {leg_idx} ? HttCandidate.leg_index.at({leg_idx}) : -1",
        )
        dfw.Define(
            f"tau{leg_idx+1}_type",
            f"HttCandidate.leg_type.size() > {leg_idx} ? static_cast<int>(HttCandidate.leg_type.at({leg_idx})) : -1",
        )
        # dfw.df.Print(f"tau{leg_idx+1}_type").Print()
        dfw.Define(
            f"b{leg_idx+1}_index",
            f"Hbb_isValid ? HbbCandidate->leg_index[{leg_idx}] : -1",
        )
        dfw.DefineAndAppend(
            f"b{leg_idx+1}_pt",
            f"Hbb_isValid ? static_cast<float>(HbbCandidate->leg_p4[{leg_idx}].Pt()) : 0.f",
        )
        dfw.DefineAndAppend(
            f"b{leg_idx+1}_pt_raw",
            f"Hbb_isValid ? static_cast<float>(Jet_pt.at(HbbCandidate->leg_index[{leg_idx}])) : 0.f",
        )
        dfw.DefineAndAppend(
            f"b{leg_idx+1}_eta",
            f"Hbb_isValid ? static_cast<float>(HbbCandidate->leg_p4[{leg_idx}].Eta()) : 0.f",
        )
        dfw.DefineAndAppend(
            f"b{leg_idx+1}_phi",
            f"Hbb_isValid ? static_cast<float>(HbbCandidate->leg_p4[{leg_idx}].Phi()) : 0.f",
        )
        dfw.DefineAndAppend(
            f"b{leg_idx+1}_mass",
            f"Hbb_isValid ? static_cast<float>(HbbCandidate->leg_p4[{leg_idx}].M()) : 0.f",
        )
        # ###### capire perchè questo non viene definito
        dfw.Define(
            f"b{leg_idx+1}_p4",
            f"Hbb_isValid ? HbbCandidate->leg_p4[{leg_idx}] : LorentzVectorM()",
        )

        dfw.Define(f"b{leg_idx+1}_legType", f"Hbb_isValid ? (Leg::jet) : (Leg::none)")
        dfw.Define(f"b{leg_idx+1}_decayMode", f"-2")  # dummy values
        if not isData:
            dfw.Define(
                f"b{leg_idx+1}_genJet_idx",
                f"Hbb_isValid ?  Jet_genJetIdx.at(HbbCandidate->leg_index[{leg_idx}]) : -1",
            )
            for var in ["pt", "eta", "phi", "mass"]:
                dfw.DefineAndAppend(
                    f"b{leg_idx+1}_genJet_{var}",
                    f"Hbb_isValid && b{leg_idx+1}_genJet_idx>=0 ? static_cast<float>(GenJet_p4.at(b{leg_idx+1}_genJet_idx).{var}()) : -1.f",
                )
            if isSignal:
                dfw.DefineAndAppend(
                    f"b{leg_idx+1}_fromGenHbb",
                    f"b{leg_idx+1}_genJet_idx>=0 ? GenJet_Hbb.at(b{leg_idx+1}_genJet_idx) : false",
                )
        for jetVar in jet_obs:
            dfw.DefineAndAppend(
                f"b{leg_idx+1}_{jetVar}",
                f"Hbb_isValid ? Jet_{jetVar}.at(HbbCandidate->leg_index[{leg_idx}]) : 0",
            )

    if trigger_class is not None:
        hltBranches = dfw.Apply(
            trigger_class.ApplyTriggers, offline_legs, isData, applyTriggerFilter
        )
        dfw.colToSave.extend(hltBranches)
    # for leg_name in offline_legs:
    #     dfw.Redefine(f"{leg_name}_legType", f"static_cast<int>({leg_name}_legType)")
