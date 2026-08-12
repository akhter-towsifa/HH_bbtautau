import ROOT

if __name__ == "__main__":
    sys.path.append(os.environ["ANALYSIS_PATH"])

from FLAF.Common.HistHelper import *
from Analysis.GetCrossWeights import *
from Corrections.Corrections import Corrections

# from Analysis.GetTauTauWeights import *
from FLAF.Common.Utilities import *

WorkingPointsParticleNet = {
    "Run3_2022": {
        "Loose": 0.047,  # /cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run3-22CDSep23-Summer22-NanoAODv12/2025-08-20/btagging.json.g
        "Medium": 0.245,
        "Tight": 0.6734,
    },
    "Run3_2022EE": {"Loose": 0.0499, "Medium": 0.2605, "Tight": 0.6915},
    "Run3_2023": {"Loose": 0.0358, "Medium": 0.1917, "Tight": 0.6172},
    "Run3_2023BPix": {"Loose": 0.0359, "Medium": 0.1919, "Tight": 0.6133},
    # UParTAK4 WP values from BTV Summer24 NanoAODv15 (L/M/T).
    "Run3_2024": {"Loose": 0.0246, "Medium": 0.1272, "Tight": 0.4648},
    "Run3_2025": {"Loose": 0.0246, "Medium": 0.1272, "Tight": 0.4648},
    "Run3_2026": {"Loose": 0.0246, "Medium": 0.1272, "Tight": 0.4648},
}
WorkingPointsDeepFlav = {
    "Run3_2022": {"Loose": 0.0583, "Medium": 0.3086, "Tight": 0.7183},
    "Run3_2022EE": {"Loose": 0.0614, "Medium": 0.3196, "Tight": 0.73},
    "Run3_2023": {"Loose": 0.0479, "Medium": 0.2431, "Tight": 0.6553},
    "Run3_2023BPix": {"Loose": 0.048, "Medium": 0.2435, "Tight": 0.6563},
    "Run3_2024": {"Loose": 0.048, "Medium": 0.2435, "Tight": 0.6563},
    "Run3_2025": {"Loose": 0.048, "Medium": 0.2435, "Tight": 0.6563},
    "Run3_2026": {"Loose": 0.048, "Medium": 0.2435, "Tight": 0.6563},
}


def createInvMass(df):
    df = df.Define("tautau_m_vis", "static_cast<float>((tau1_p4+tau2_p4).M())")
    particleNet_mass = (
        "particleNet_mass"
        if "SelectedFatJet_particleNet_mass_boosted" in df.GetColumnNames()
        else "particleNetLegacy_mass"
    )
    df = df.Define(
        "bb_m_vis_pnet",
        f"""
                   return static_cast<float>(SelectedFatJet_{particleNet_mass}_boosted);
                   """,
    )
    df = df.Define(
        "bb_m_vis_softdrop",
        f"""
                   return static_cast<float>(SelectedFatJet_msoftdrop_boosted);
                   """,
    )
    df = df.Define(
        "bb_m_vis_fj",
        f"""
                   return static_cast<float>(SelectedFatJet_mass_boosted);
                    """,
    )

    df = df.Define(
        "bb_m_vis",
        f""" if(b1_pt < 0. || b2_pt < 0.) return 0.f; return static_cast<float>((b1_p4+b2_p4).M());""",
    )
    df = df.Define(
        "bbtautau_mass_boosted",
        """return static_cast<float>((SelectedFatJet_p4_boosted+tau1_p4+tau2_p4).M());""",
    )
    df = df.Define(
        "bbtautau_mass",
        """if(b1_pt < 0. || b2_pt < 0.) return 0.f; return static_cast<float>((b1_p4+b2_p4+tau1_p4+tau2_p4).M());""",
    )
    df = df.Define("dR_tautau", "ROOT::Math::VectorUtil::DeltaR(tau1_p4, tau2_p4)")
    df = df.Define("dR_bb", "ROOT::Math::VectorUtil::DeltaR(b1_p4, b2_p4)")
    df = df.Define("Htt_p4", "(tau1_p4 + tau2_p4)")
    df = df.Define("Hbb_p4", "(b1_p4 + b2_p4)")
    df = df.Define("dR_Htt_Hbb", "ROOT::Math::VectorUtil::DeltaR(Htt_p4, Hbb_p4)")
    df = df.Define("deltaEta_Htt_Hbb", "(Htt_p4.Eta() - Hbb_p4.Eta())")
    df = df.Define(
        "deltaPhi_Htt_Hbb", "ROOT::Math::VectorUtil::DeltaPhi(Htt_p4, Hbb_p4)"
    )

    df = df.Define(
        "deltaPhi_met_Htt", "ROOT::Math::VectorUtil::DeltaPhi(met_p4, Htt_p4)"
    )
    df = df.Define(
        "deltaPhi_met_Hbb", "ROOT::Math::VectorUtil::DeltaPhi(met_p4, Hbb_p4)"
    )
    df = df.Define(
        "deltaPhi_metnomu_Htt",
        "ROOT::Math::VectorUtil::DeltaPhi(metnomu_p4, Htt_p4)",
    )
    df = df.Define(
        "deltaPhi_metnomu_Hbb",
        "ROOT::Math::VectorUtil::DeltaPhi(metnomu_p4, Hbb_p4)",
    )

    df = df.Define("pt_HH", "((Htt_p4 + Hbb_p4).Pt())")

    for tau_idx in [1, 2]:
        for met_var in ["met", "metnomu", "met_nano"]:
            df = df.Define(
                f"tau{tau_idx}_{met_var}_mt",
                f"static_cast<float>((tau{tau_idx}_p4+{met_var}_p4).Mt())",
            )
    return df


def createKeyFilterDict(global_params, period):
    filter_dict = {}
    filter_str = ""
    channels_to_consider = global_params["channels_to_consider"]

    categories = global_params["categories"]
    boosted_categories = global_params["boosted_categories"]
    ### add custom categories eventually:
    # custom_categories = []
    # custom_categories_name = global_params.get(
    #     "custom_categories", None
    # )  # can be extended to list of names
    # if custom_categories_name:
    #     custom_categories = list(global_params.get(custom_categories_name, []))
    #     if not custom_categories:
    #         print("No custom categories found")

    ### regions
    custom_regions = []
    custom_regions_name = global_params.get(
        "custom_regions", None
    )  # can be extended to list of names, if for example adding QCD regions + other control regions
    if custom_regions_name:
        custom_regions = list(global_params.get(custom_regions_name, []))
        if not custom_regions:
            print("No custom regions found")

    all_categories = categories + boosted_categories  # + custom_categories
    custom_subcategories = list(global_params.get("custom_subcategories", []))
    triggers_dict = global_params["hist_triggers"]
    for ch in channels_to_consider:
        triggers = triggers_dict[ch]["default"]
        if period in triggers_dict[ch].keys():
            triggers = triggers_dict[ch][period]
        for reg in custom_regions:
            for cat in all_categories:
                filter_base = f" ( {ch} && {triggers} && {reg} && {cat} ) "
                if cat not in boosted_categories and not (cat.startswith("baseline")):
                    filter_str += "&& (b1_pt>0 && b2_pt>0)"
                if custom_subcategories:
                    for subcat in custom_subcategories:
                        # filter_base += f"&& {custom_subcat}"
                        filter_str = f"(" + filter_base + f" && {subcat}"
                        filter_str += ")"
                        key = (ch, reg, cat, subcat)
                        filter_dict[key] = filter_str
                else:
                    filter_str = f"(" + filter_base
                    filter_str += ")"
                    key = (ch, reg, cat)
                    filter_dict[key] = filter_str
    return filter_dict


# def createKeyFilterDict(global_cfg_dict, year):
#     reg_dict = {}
#     filter_str = ""
#     channels_to_consider = global_cfg_dict["channels_to_consider"]
#     qcd_regions_to_consider = global_cfg_dict["SignRegions"]
#     categories_to_consider = (
#         global_cfg_dict["categories"] + global_cfg_dict["boosted_categories"]
#     )
#     boosted_categories = global_cfg_dict["boosted_categories"]
#     triggers_dict = global_cfg_dict["hist_triggers"]
#     mass_cut_limits = global_cfg_dict["mass_cut_limits"]
#     for ch in channels_to_consider:
#         triggers = triggers_dict[ch]["default"]
#         if year in triggers_dict[ch].keys():
#             triggers = triggers_dict[ch][year]
#         for reg in qcd_regions_to_consider:
#             for cat in categories_to_consider:
#                 filter_base = f" ({ch} && {triggers} && {reg} && {cat})"
#                 filter_str = f"(" + filter_base
#                 if cat not in boosted_categories and not (cat.startswith("baseline")):
#                     filter_str += "&& (b1_pt>0 && b2_pt>0)"
#                 filter_str += ")"
#                 key = (ch, reg, cat)
#                 reg_dict[key] = filter_str

#     return reg_dict


def GetBTagWeight(global_cfg_dict, cat, applyBtag=False):
    btag_weight = "1"
    btagshape_weight = "1"
    if applyBtag:
        if global_cfg_dict["btag_wps"][cat] != "":
            btag_weight = f"weight_bTagSF_{btag_wps[cat]}_Central"
    else:
        if cat not in global_cfg_dict["boosted_categories"] and not cat.startswith(
            "baseline"
        ):
            btagshape_weight = "weight_bTagShape_Central"
    return f"{btag_weight}*{btagshape_weight}"


def GetWeight(channels, weights_this_process=None, weight_base_name="weight_base"):
    weights_dict = {}
    weights_this_process = set(weights_this_process or [])
    apply_dy_hhbbtautau = False
    if "dy_hhbbtautau" in weights_this_process:
        apply_dy_hhbbtautau = True
    weights_to_apply = [
        weight_base_name
    ]  # , "weight_L1PreFiring_Central","weight_L1PreFiring_ECAL_Central", "weight_L1PreFiring_Muon_Central"]
    trg_weights_dict = {
        "eTau": [
            "weight_HLT_singleEle"
        ],  # ["weight_HLT_eTau", "weight_HLT_singleTau", "weight_HLT_MET"],
        "muTau": [
            "weight_HLT_singleMu"
        ],  # ["weight_HLT_muTau", "weight_HLT_singleTau", "weight_HLT_MET"],
        "tauTau": [
            "weight_HLT_diTau"
        ],  # ["weight_HLT_diTau", "weight_HLT_diTauJet", "weight_HLT_singleTau", "weight_HLT_MET"],
        "eE": ["weight_HLT_singleEle"],
        "muMu": ["weight_HLT_singleMu"],
        "eMu": ["weight_HLT_singleMu"],  # ["weight_HLT_eMu"]
    }
    ID_weights_dict = {
        "eTau": [
            "weight_tau1_EleSF_wp80iso_EleIDCentral",
            "weight_tau2_TauID_SF_Medium_Central",
            "weight_trgSF_eTau_Central",
        ],  # theorically
        # 'muTau': ["weight_tau1_HighPt_MuonID_SF_RecoCentral", "weight_tau1_HighPt_MuonID_SF_TightIDCentral", "weight_tau1_MuonID_SF_RecoCentral", "weight_tau1_MuonID_SF_TightID_TrkCentral", "weight_tau1_MuonID_SF_TightRelIsoCentral","weight_tau2_TauID_SF_Medium_Central"],
        "muTau": [
            "weight_tau1_HighPt_MuonID_SF_RecoCentral",
            "weight_tau1_HighPt_MuonID_SF_TightIDCentral",
            "weight_tau1_MuonID_SF_TightID_TrkCentral",
            "weight_tau2_TauID_SF_Medium_Central",
            "weight_trgSF_muTau_Central",
        ],
        "tauTau": [
            "weight_tau1_TauID_SF_Medium_Central",
            "weight_tau2_TauID_SF_Medium_Central",
            "weight_trgSF_tauTau_Central",
        ],
        # 'muMu': ["weight_tau1_HighPt_MuonID_SF_RecoCentral", "weight_tau1_HighPt_MuonID_SF_TightIDCentral", "weight_tau1_MuonID_SF_RecoCentral", "weight_tau1_MuonID_SF_TightID_TrkCentral", "weight_tau1_MuonID_SF_TightRelIsoCentral", "weight_tau2_HighPt_MuonID_SF_RecoCentral", "weight_tau2_HighPt_MuonID_SF_TightIDCentral", "weight_tau2_MuonID_SF_RecoCentral", "weight_tau2_MuonID_SF_TightID_TrkCentral", "weight_tau2_MuonID_SF_TightRelIsoCentral"],
        "muMu": [
            "weight_tau1_HighPt_MuonID_SF_RecoCentral",
            "weight_tau1_HighPt_MuonID_SF_TightIDCentral",
            "weight_tau1_MuonID_SF_TightID_TrkCentral",
            "weight_tau2_HighPt_MuonID_SF_RecoCentral",
            "weight_tau2_HighPt_MuonID_SF_TightIDCentral",
            "weight_tau2_MuonID_SF_TightID_TrkCentral",
            "weight_trgSF_muMueMu_Central",
        ],
        "eMu": [
            "weight_tau1_EleSF_wp80iso_EleIDCentral",
            "weight_tau2_HighPt_MuonID_SF_RecoCentral",
            "weight_tau2_HighPt_MuonID_SF_TightIDCentral",
            "weight_tau2_MuonID_SF_TightID_TrkCentral",
            "weight_trgSF_muMueMu_Central",
        ],
        #'eMu': ["weight_tau1_EleSF_wp80iso_EleIDCentral","weight_tau2_HighPt_MuonID_SF_RecoCentral", "weight_tau2_HighPt_MuonID_SF_TightIDCentral", "weight_tau2_MuonID_SF_RecoCentral", "weight_tau2_MuonID_SF_TightID_TrkCentral", "weight_tau2_MuonID_SF_TightRelIsoCentral"],
        #'eMu': ["weight_tau1_MuonID_SF_RecoCentral","weight_tau1_HighPt_MuonID_SF_RecoCentral","weight_tau1_MuonID_SF_TightID_TrkCentral","weight_tau1_MuonID_SF_TightRelIsoCentral","weight_tau2_EleSF_wp80iso_EleIDCentral"]
        "eE": [
            "weight_tau1_EleSF_wp80iso_EleIDCentral",
            "weight_tau2_EleSF_wp80noiso_EleIDCentral",
            "weight_trgSF_eE_Central",
        ],
    }
    weights_full_string = ""
    for channel in channels:
        weights_list = [weight_base_name]
        # weights_list.extend(trg_weights_dict[channel]) ## currently commented because there are no trigger weights ??
        weights_list.extend(ID_weights_dict[channel])
        if apply_dy_hhbbtautau:  # isDY:
            weights_list.append("weight_dy_central")

        # if categories dependent weights are present do a sub loop here extending the dict
        weights_full_string += (
            f"""if ({channel}) {{return """ + "*".join(weights_list) + """; } """
        )
    weights_full_string += "return 1.f;"
    print(weights_full_string)
    ## as it used to be before
    # weights_to_apply.extend(trg_weights_dict[channel])

    # if cat not in boosted_categories:
    #      weights_to_apply.extend(["weight_Jet_PUJetID_Central_b1_2", "weight_Jet_PUJetID_Central_b2_2"])
    # else:
    #     weights_to_apply.extend(["weight_pNet_Central"])

    # total_weight = "*".join(weights_to_apply)
    return weights_full_string


class DataFrameBuilderForHistograms(DataFrameBuilderBase):

    def defineBoostedVariables(self):  # needs p4 def
        FatJetObservables = self.config["FatJetObservables"]
        particleNet_MD_JetTagger = "SelectedFatJet_particleNetMD_Xbb/(SelectedFatJet_particleNetMD_QCD + SelectedFatJet_particleNetMD_Xbb)"
        if (
            "SelectedFatJet_particleNetMD_Xbb" not in self.df.GetColumnNames()
            and "SelectedFatJet_particleNetLegacy_Xbb" in self.df.GetColumnNames()
        ):
            particleNet_MD_JetTagger = "SelectedFatJet_particleNetLegacy_Xbb/ (SelectedFatJet_particleNetLegacy_Xbb + SelectedFatJet_particleNetLegacy_QCD)"
        particleNet_HbbvsQCD = (
            "SelectedFatJet_particleNet_HbbvsQCD"
            if "SelectedFatJet_particleNet_HbbvsQCD" in self.df.GetColumnNames()
            else "SelectedFatJet_particleNetWithMass_HbbvsQCD"
        )
        self.df = self.df.Define(
            "SelectedFatJet_particleNet_MD_JetTagger", particleNet_MD_JetTagger
        )
        self.df = self.df.Define("fatJet_presel", f"SelectedFatJet_pt>250")
        self.df = self.df.Define(
            "fatJet_sel",
            " RemoveOverlaps(SelectedFatJet_p4, fatJet_presel, {tau1_p4, tau2_p4}, 0.8)",
        )

        self.df = self.df.Define(
            "SelectedFatJet_size_boosted", "SelectedFatJet_p4[fatJet_sel].size()"
        )
        self.DefineAndAppend("boosted_baseline", "SelectedFatJet_size_boosted >= 1")

        # def the correct discriminator
        self.df = self.df.Define(
            f"SelectedFatJet_particleNet_MD_JetTagger_boosted_vec",
            f"SelectedFatJet_particleNet_MD_JetTagger[fatJet_sel]",
        )
        # Run 3
        self.df = self.df.Define(
            f"SelectedFatJet_particleNet_XbbVsQCD_boosted_vec",
            f"SelectedFatJet_particleNet_XbbVsQCD[fatJet_sel];",
        )  # FatJet_particleNet_XbbVsQCD: ParticleNet X->bb vs. QCD score: Xbb/(Xbb+QCD)
        self.df = self.df.Define(
            "SelectedFatJet_idxUnordered",
            "CreateIndexes(SelectedFatJet_p4[fatJet_sel].size())",
        )
        self.df = self.df.Define(
            "SelectedFatJet_idxOrdered",
            "ReorderObjects(SelectedFatJet_particleNet_XbbVsQCD_boosted_vec, SelectedFatJet_idxUnordered)",
            # f"ReorderObjects(SelectedFatJet_particleNet_MD_JetTagger_boosted_vec, SelectedFatJet_idxUnordered)",
        )

        for fatJetVar in FatJetObservables:
            if f"SelectedFatJet_{fatJetVar}" in self.df.GetColumnNames():
                if (
                    f"SelectedFatJet_{fatJetVar}_boosted_vec"
                    not in self.df.GetColumnNames()
                ):
                    self.df = self.df.Define(
                        f"SelectedFatJet_{fatJetVar}_boosted_vec",
                        f""" SelectedFatJet_{fatJetVar}[fatJet_sel];""",
                    )
                self.df = self.df.Define(
                    f"SelectedFatJet_{fatJetVar}_boosted",
                    f"""
                                    SelectedFatJet_{fatJetVar}_boosted_vec[SelectedFatJet_idxOrdered[0]];
                                   """,
                )

    def defineTriggers(self):
        for ch in self.config["channelSelection"]:
            for trg in self.config["triggers"][ch]:
                trg_name = "HLT_" + trg
                self.colToSave.append(trg_name)
                if trg_name not in self.df.GetColumnNames():
                    print(f"{trg_name} not present in colNames")
                    self.df = self.df.Define(trg_name, "1")

    def definePNetSFs(self):
        self.df = self.df.Define(
            "weight_pNet_Central",
            f"""getSFPNet(SelectedFatJet_p4_boosted.Pt(), "{self.period}", "Central", "{self.pNetWPstring}",{self.whichType})""",
        )
        self.df = self.df.Define(
            "weight_pNet_Up",
            f"""getSFPNet(SelectedFatJet_p4_boosted.Pt(), "{self.period}", "Up", "{self.pNetWPstring}",{self.whichType})""",
        )
        self.df = self.df.Define(
            "weight_pNet_Up_rel", f"""weight_pNet_Up/weight_pNet_Central"""
        )
        self.df = self.df.Define(
            "weight_pNet_Down",
            f"""getSFPNet(SelectedFatJet_p4_boosted.Pt(), "{self.period}", "Down", "{self.pNetWPstring}",{self.whichType})""",
        )
        self.df = self.df.Define(
            "weight_pNet_Down_rel", f"""weight_pNet_Down/weight_pNet_Central"""
        )

    def defineApplicationRegions(self):
        for ch in self.config["channels_to_consider"]:
            for trg in self.config["triggers"][ch]:
                if f"HLT_{trg}" not in self.df.GetColumnNames():
                    print(f"{trg} not present in colNames")
                    self.df = self.df.Define(trg, "1")
        singleTau_th_dict = self.config["singleTau_th"]
        singleMu_th_dict = self.config["singleMu_th"]
        singleEle_th_dict = self.config["singleEle_th"]
        # legacy_region_definition= "( ( eTau && (SingleEle_region  || CrossEleTau_region) ) || ( muTau && (SingleMu_region  || CrossMuTau_region) ) || ( tauTau && ( diTau_region || diTauJet_region) ) || ( eE && (SingleEle_region)) || (eMu && ( SingleEle_region || SingleMu_region ) ) || (muMu && (SingleMu_region)) )"
        legacy_region_definition = "( ( eTau && (SingleEle_region ) ) || ( muTau && (SingleMu_region ) ) || ( tauTau && ( diTau_region ) ) || ( eE && (SingleEle_region)) || (eMu && ( SingleMu_region ) ) || (muMu && (SingleMu_region)) )"  # if not including xtrgs
        for reg_name, reg_exp in self.config["application_regions"].items():
            self.df = self.df.Define(
                reg_name,
                reg_exp.format(
                    tau_th=singleTau_th_dict[self.period],
                    ele_th=singleEle_th_dict[self.period],
                    mu_th=singleMu_th_dict[self.period],
                ),
            )
            self.colToSave.append(reg_name)
        self.df = self.df.Define("Legacy_region", legacy_region_definition)
        self.colToSave.append("Legacy_region")

    def DefineAndAppend(self, varToDefine, var_expression):
        self.df = self.df.Define(varToDefine, var_expression)
        self.colToSave.append(varToDefine)

    def defineCRs(self):  # needs inv mass def
        SR_mass_limits_bb_boosted = self.config["mass_cut_limits"]["bb_m_vis"][
            "boosted"
        ]
        SR_mass_limits_bb = self.config["mass_cut_limits"]["bb_m_vis"]["other"]
        SR_mass_limits_tt = self.config["mass_cut_limits"]["tautau_m_vis"]
        self.DefineAndAppend(
            "SR_tt",
            f"return (tautau_m_vis > {SR_mass_limits_tt[0]} && tautau_m_vis  < {SR_mass_limits_tt[1]});",
        )
        self.DefineAndAppend(
            "SR_bb",
            f"(bb_m_vis > {SR_mass_limits_bb[0]} && bb_m_vis < {SR_mass_limits_bb[1]});",
        )
        self.DefineAndAppend(
            "SR_bb_boosted",
            f"(bb_m_vis_softdrop > {SR_mass_limits_bb_boosted[0]} && bb_m_vis_softdrop < {SR_mass_limits_bb_boosted[1]});",
        )
        self.DefineAndAppend("SR", f" SR_tt &&  SR_bb")
        self.DefineAndAppend("SR_boosted", f" SR_tt &&  SR_bb_boosted")

        self.DefineAndAppend(
            "DYCR",
            "if(muMu || eE) {return (tautau_m_vis < 100 && tautau_m_vis > 80);} return true;",
        )
        self.DefineAndAppend("DYCR_boosted", "DYCR")

        TTCR_mass_limits_eTau = self.config["TTCR_mass_limits"]["eTau"]
        TTCR_mass_limits_muTau = self.config["TTCR_mass_limits"]["muTau"]
        TTCR_mass_limits_tauTau = self.config["TTCR_mass_limits"]["tauTau"]
        TTCR_mass_limits_muMu = self.config["TTCR_mass_limits"]["muMu"]
        TTCR_mass_limits_eE = self.config["TTCR_mass_limits"]["eE"]
        self.DefineAndAppend(
            "TTCR",
            f"""
                                if(eTau) {{return (tautau_m_vis < {TTCR_mass_limits_eTau[0]} || tautau_m_vis > {TTCR_mass_limits_eTau[1]});
                                }};
                                 if(muTau) {{return (tautau_m_vis < {TTCR_mass_limits_muTau[0]} || tautau_m_vis > {TTCR_mass_limits_muTau[1]});
                                 }};
                                 if(tauTau) {{return (tautau_m_vis < {TTCR_mass_limits_tauTau[0]} || tautau_m_vis > {TTCR_mass_limits_tauTau[1]});
                                 }};
                                 if(muMu) {{return (tautau_m_vis < {TTCR_mass_limits_muMu[0]} || tautau_m_vis > {TTCR_mass_limits_muMu[1]});
                                 }};
                                 if(eE) {{return (tautau_m_vis < {TTCR_mass_limits_eE[0]} || tautau_m_vis > {TTCR_mass_limits_eE[1]});
                                 }};
                                 return true;""",
        )
        self.DefineAndAppend("TTCR_boosted", "TTCR")

    def redefinePUJetIDWeights(self):
        for weight in [
            "weight_Jet_PUJetID_Central_b1",
            "weight_Jet_PUJetID_Central_b2",
            "weight_Jet_PUJetID_effUp_rel_b1",
            "weight_Jet_PUJetID_effUp_rel_b2",
            "weight_Jet_PUJetID_effDown_rel_b1",
            "weight_Jet_PUJetID_effDown_rel_b2",
        ]:
            if weight not in self.df.GetColumnNames():
                continue
            self.df = self.df.Define(
                f"{weight}_2",
                f"""
                                         if({weight}!=-100)
                                            return static_cast<float>({weight}) ;
                                         return 1.f;""",
            )

    def defineCategories(self):  # needs lot of stuff --> at the end

        self.df = self.df.Define("bjet1_isValid", "nBJets > 0")
        self.df = self.df.Define("bjet2_isValid", "nBJets > 1")

        nBjets_PNetTag = f"int(bjet1_isValid && b1_idbtagPNetB >= 2) + int( bjet2_isValid && b2_idbtagPNetB >= 2)"

        # self.df = self.df.Define(
        #     "nSelBtag",
        #     f"int(b1_btagDeepFlavB >{self.bTagWP}) + int(b2_btagDeepFlavB >{self.bTagWP})",
        # )
        self.df = self.df.Define("nSelBtag", nBjets_PNetTag)
        self.df = self.df.Define("nBjets_PNetTag", nBjets_PNetTag)

        for category_to_def in self.config["category_definition"].keys():
            category_name = category_to_def
            if category_name == "boosted":
                pNetWP = 0.75  # Run 3 AN has optimized cut at 0.75
            else:
                pNetWP = self.pNetWP
            self.DefineAndAppend(
                category_to_def,
                self.config["category_definition"][category_to_def].format(
                    pNetWP=pNetWP, region=self.region
                ),
            )

    def defineChannels(self):
        for channel in self.config["all_channels"]:
            ch_value = self.config["channelDefinition"][channel]
            self.DefineAndAppend(f"{channel}", f"channelId=={ch_value}")

    def defineL1PrefiringRelativeWeights(self):
        if "weight_L1PreFiringDown_rel" not in self.df.GetColumnNames():
            self.df = self.df.Define(
                "weight_L1PreFiringDown_rel",
                "weight_L1PreFiring_Down/weight_L1PreFiring_Central",
            )
        if "weight_L1PreFiringUp_rel" not in self.df.GetColumnNames():
            self.df = self.df.Define(
                "weight_L1PreFiringUp_rel",
                "weight_L1PreFiringUp/weight_L1PreFiring_Central",
            )
        if "weight_L1PreFiring_ECALDown_rel" not in self.df.GetColumnNames():
            self.df = self.df.Define(
                "weight_L1PreFiring_ECALDown_rel",
                "weight_L1PreFiring_ECALDown/weight_L1PreFiring_ECAL_Central",
            )
        if "weight_L1PreFiring_Muon_StatUp_rel" not in self.df.GetColumnNames():
            self.df = self.df.Define(
                "weight_L1PreFiring_Muon_StatUp_rel",
                "weight_L1PreFiring_Muon_StatUp/weight_L1PreFiring_Muon_Central",
            )
        if "weight_L1PreFiring_Muon_StatDown_rel" not in self.df.GetColumnNames():
            self.df = self.df.Define(
                "weight_L1PreFiring_Muon_StatDown_rel",
                "weight_L1PreFiring_Muon_StatDown/weight_L1PreFiring_Muon_Central",
            )
        if "weight_L1PreFiring_Muon_SystUp_rel" not in self.df.GetColumnNames():
            self.df = self.df.Define(
                "weight_L1PreFiring_Muon_SystUp_rel",
                "weight_L1PreFiring_Muon_SystUp/weight_L1PreFiring_Muon_Central",
            )
        if "weight_L1PreFiring_Muon_SystDown_rel" not in self.df.GetColumnNames():
            self.df = self.df.Define(
                "weight_L1PreFiring_Muon_SystDown_rel",
                "weight_L1PreFiring_Muon_SystDown/weight_L1PreFiring_Muon_Central",
            )

    def defineLeptonPreselection(self):  # needs channel def
        self.df = self.df.Define(
            "muon1_tightId",
            "if(muTau || muMu) {return (tau1_Muon_tightId && tau1_Muon_pfRelIso04_all < 0.15); } return true;",
        )
        self.df = self.df.Define(
            "muon2_tightId",
            "if(muMu || eMu) {return (tau2_Muon_tightId && tau2_Muon_pfRelIso04_all < 0.3);} return true;",
        )
        self.df = self.df.Define(
            "firstele_mvaIso",
            "if(eMu || eE){return tau1_Electron_mvaIso_WP80==1 && tau1_Electron_pfRelIso03_all < 0.15 ; } return true; ",
        )
        self.df = self.df.Define(
            "tau1_iso_medium",
            f"if(tauTau) return (tau1_idDeepTau{self.deepTauYear()}v{self.deepTauVersion}VSjet >= {Utilities.WorkingPointsTauVSjet.Medium.value}); return true;",
        )
        if f"tau1_gen_kind" not in self.df.GetColumnNames():
            self.df = self.df.Define("tau1_gen_kind", "if(isData) return 5; return 0;")
        if f"tau2_gen_kind" not in self.df.GetColumnNames():
            self.df = self.df.Define("tau2_gen_kind", "if(isData) return 5; return 0;")
        self.df = self.df.Define(
            "tau_true", f"""(tau1_gen_kind==5 && tau2_gen_kind==5)"""
        )
        self.df = self.df.Define(
            f"lepton_preselection",
            "tau1_iso_medium && muon1_tightId && muon2_tightId && firstele_mvaIso",
        )

    def defineQCDRegions(self):
        self.DefineAndAppend("OS", "tau1_charge*tau2_charge < 0")
        self.DefineAndAppend("SS", "!OS")

        self.DefineAndAppend(
            "Iso",
            f"(((tauTau || eTau || muTau) && (tau2_idDeepTau{self.deepTauYear()}v{self.deepTauVersion}VSjet >= {Utilities.WorkingPointsTauVSjet.Medium.value} )) || ((muMu||eMu) && (tau2_Muon_pfRelIso04_all < 0.15)) || (eE && tau2_Electron_pfRelIso03_all < 0.15 && tau2_Electron_mvaNoIso_WP80))",
        )

        self.DefineAndAppend(
            "AntiIso",
            f"(((tauTau || eTau || muTau) && (tau2_idDeepTau{self.deepTauYear()}v{self.deepTauVersion}VSjet >= {Utilities.WorkingPointsTauVSjet.VVVLoose.value} && tau2_idDeepTau{self.deepTauYear()}v{self.deepTauVersion}VSjet < {Utilities.WorkingPointsTauVSjet.Medium.value})) || ((muMu||eMu) && (tau2_Muon_pfRelIso04_all >= 0.15 && tau2_Muon_pfRelIso04_all < 0.3) ) || (eE && (tau2_Electron_pfRelIso03_all < 0.3 && tau2_Electron_pfRelIso03_all >= 0.15 && tau2_Electron_mvaNoIso_WP80 )))",
        )

        self.DefineAndAppend("OS_Iso", f"lepton_preselection && OS && Iso")
        self.DefineAndAppend("SS_Iso", f"lepton_preselection && SS && Iso")
        self.DefineAndAppend("OS_AntiIso", f"lepton_preselection && OS && AntiIso")
        self.DefineAndAppend("SS_AntiIso", f"lepton_preselection && SS && AntiIso")

    def deepTauYear(self):
        return self.config["deepTauYears"][f"v{self.deepTauVersion}"]

    def addNewCols(self):
        self.colNames = []
        self.colTypes = []
        colNames = [
            str(c) for c in self.df.GetColumnNames()
        ]  # if 'kinFit_result' not in str(c)]
        cols_to_remove = []
        for colName in colNames:
            col_name_split = colName.split("_")
            if "p4" in col_name_split or "vec" in col_name_split:
                cols_to_remove.append(colName)
        for col_to_remove in cols_to_remove:
            colNames.remove(col_to_remove)
        entryIndexIdx = colNames.index("entryIndex")
        runIdx = colNames.index("run")
        eventIdx = colNames.index("event")
        lumiIdx = colNames.index("luminosityBlock")
        colNames[entryIndexIdx], colNames[0] = colNames[0], colNames[entryIndexIdx]
        colNames[runIdx], colNames[1] = colNames[1], colNames[runIdx]
        colNames[eventIdx], colNames[2] = colNames[2], colNames[eventIdx]
        colNames[lumiIdx], colNames[3] = colNames[3], colNames[lumiIdx]
        self.colNames = colNames
        self.colTypes = [str(self.df.GetColumnType(c)) for c in self.colNames]
        for colName, colType in zip(self.colNames, self.colTypes):
            print(colName, colType)

    def __init__(
        self,
        df,
        config,
        period,
        deepTauVersion="v2p1",
        bTagWPString="Medium",
        pNetWPstring="Loose",
        region="SR",
        isData=False,
        isCentral=False,
        wantTriggerSFErrors=False,
        whichType=3,
        wantScales=True,
        colToSave=[],
    ):
        super(DataFrameBuilderForHistograms, self).__init__(df)
        self.deepTauVersion = config["deepTauVersion"]
        self.config = config
        self.bTagWPString = bTagWPString
        self.pNetWPstring = pNetWPstring
        self.pNetWP = WorkingPointsParticleNet[period][pNetWPstring]
        self.bTagWP = WorkingPointsDeepFlav[period][bTagWPString]
        self.period = period
        self.region = region
        self.isData = isData
        self.whichType = whichType
        self.isCentral = isCentral
        self.wantTriggerSFErrors = wantTriggerSFErrors
        self.wantScales = isCentral and wantScales
        self.colToSave = colToSave


def PrepareDfForDNN(dfForHistograms):
    dfForHistograms.df = defineAllP4(dfForHistograms.df, isData=dfForHistograms.isData)
    dfForHistograms.defineBoostedVariables()
    return dfForHistograms


def PrepareDfForHistograms(dfForHistograms):
    for leg_idx in [1, 2]:
        tau_legType = f"tau{leg_idx}_legType"
        dfForHistograms.df = dfForHistograms.df.Redefine(
            tau_legType, f"static_cast<Leg>({tau_legType})"
        )
        dfForHistograms.df = dfForHistograms.df.Define(
            f"b{leg_idx}_legType", f"b{leg_idx}_pt > 0 ? Leg::jet : Leg::none"
        )
        dfForHistograms.df = dfForHistograms.df.Define(f"b{leg_idx}_decayMode", "-2")

    dfForHistograms.df = defineAllP4(dfForHistograms.df, isData=dfForHistograms.isData)

    dfForHistograms.defineTriggers()
    dfForHistograms.defineBoostedVariables()
    dfForHistograms.redefinePUJetIDWeights()
    dfForHistograms.df = createInvMass(dfForHistograms.df)
    dfForHistograms.defineChannels()
    dfForHistograms.defineLeptonPreselection()
    dfForHistograms.defineApplicationRegions()
    # if not dfForHistograms.isData:
    #     # dfForHistograms.definePNetSFs()
    #     defineTriggersCentralWeights(dfForHistograms)
    #     if dfForHistograms.wantTriggerSFErrors and dfForHistograms.isCentral:
    #         defineTriggersWeightsErrors(dfForHistograms)
    dfForHistograms.defineCRs()
    dfForHistograms.defineCategories()
    dfForHistograms.defineQCDRegions()
    dfForHistograms.df = RedefineMETbosonicRecoil(
        dfForHistograms.df, isData=dfForHistograms.isData
    )

    return dfForHistograms


def defineAllP4(df, isData=False):
    df = df.Define(f"SelectedFatJet_idx", f"CreateIndexes(SelectedFatJet_pt.size())")
    df = df.Define(
        f"SelectedFatJet_p4",
        f"GetP4(SelectedFatJet_pt, SelectedFatJet_eta, SelectedFatJet_phi, SelectedFatJet_mass, SelectedFatJet_idx)",
    )
    for idx in [0, 1]:
        df = Utilities.defineP4(df, f"tau{idx+1}")
        df = Utilities.defineP4(df, f"b{idx+1}")
    if not isData:
        df = df.Define(f"pt_ll_gen", f"LHE_Vpt")
    for met_var in ["met", "metnomu"]:
        df = df.Define(
            f"{met_var}_p4",
            f"ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>({met_var}_pt,0.,{met_var}_phi,0.)",
        )
        for leg_idx in [0, 1]:
            df = df.Define(
                f"deltaPhi_{met_var}_tau{leg_idx+1}",
                f"ROOT::Math::VectorUtil::DeltaPhi({met_var}_p4,tau{leg_idx+1}_p4)",
            )
            df = df.Define(
                f"deltaPhi_{met_var}_b{leg_idx+1}",
                f"ROOT::Math::VectorUtil::DeltaPhi({met_var}_p4,b{leg_idx+1}_p4)",
            )
    df = df.Define(
        f"met_nano_p4",
        f"ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>(met_pt_nano,0.,met_phi_nano,0.)",
    )
    df = df.Define(f"pt_ll", "(tau1_p4+tau2_p4).Pt()")
    df = df.Define(f"pt_bb", "(b1_p4+b2_p4).Pt()")
    return df


def RedefineMETbosonicRecoil(df, isData=False):
    if (not isData) and ("bosonicRecoil" in Corrections.getGlobal().to_apply):
        process_cfg = Corrections.getGlobal().process_cfg
        if (
            process_cfg.get("corrections", {})
            .get("bosonicRecoil", {})
            .get("enabled", False)
        ):
            df = df.Redefine("met_pt", "PuppiMET_pt_recoil")
            df = df.Redefine("met_phi", "PuppiMET_phi_recoil")
            df = df.Redefine(
                "met_p4",
                "ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>(met_pt,0.,met_phi,0.)",
            )
            for met_var in ["met", "metnomu"]:
                df = df.Redefine(
                    f"{met_var}_p4",
                    f"ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>({met_var}_pt,0.,{met_var}_phi,0.)",
                )
                for leg_idx in [0, 1]:
                    df = df.Redefine(
                        f"deltaPhi_{met_var}_tau{leg_idx+1}",
                        f"ROOT::Math::VectorUtil::DeltaPhi({met_var}_p4,tau{leg_idx+1}_p4)",
                    )
                    df = df.Redefine(
                        f"deltaPhi_{met_var}_b{leg_idx+1}",
                        f"ROOT::Math::VectorUtil::DeltaPhi({met_var}_p4,b{leg_idx+1}_p4)",
                    )
    return df
