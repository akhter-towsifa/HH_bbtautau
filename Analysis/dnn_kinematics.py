from __future__ import annotations
import numpy as np

"""
Raw four-vector construction shared by inference (Analysis/DNN_application.py,
runs inside the FLAF/CMSSW environment) and training (Analysis/DNN_training/,
intended to also run standalone -- numpy/uproot/torch only, no ROOT/CMSSW/FLAF)
-- kept import-light (numpy only) so importing it doesn't drag in ROOT/tensorflow/
FLAF for callers that only need this math, e.g. Analysis/DNN_training/data.py.
"""


def convert_kinematics(pt, eta, phi, mass):
    px = pt * np.cos(phi)
    py = pt * np.sin(phi)
    pz = pt * np.sinh(eta)
    energy = np.sqrt(pt**2 * np.cosh(eta) ** 2 + mass**2)
    return px, py, pz, energy


def convert_to_numpy(event_data, period, mass, spin):
    dau1_px, dau1_py, dau1_pz, dau1_e = convert_kinematics(
        event_data["tau1_pt"],
        event_data["tau1_eta"],
        event_data["tau1_phi"],
        event_data["tau1_mass"],
    )
    dau2_px, dau2_py, dau2_pz, dau2_e = convert_kinematics(
        event_data["tau2_pt"],
        event_data["tau2_eta"],
        event_data["tau2_phi"],
        event_data["tau2_mass"],
    )
    bjet1_px, bjet1_py, bjet1_pz, bjet1_e = convert_kinematics(
        event_data["b1_pt"],
        event_data["b1_eta"],
        event_data["b1_phi"],
        event_data["b1_mass"],
    )
    bjet2_px, bjet2_py, bjet2_pz, bjet2_e = convert_kinematics(
        event_data["b2_pt"],
        event_data["b2_eta"],
        event_data["b2_phi"],
        event_data["b2_mass"],
    )

    fatjet_pt = event_data["SelectedFatJet_pt_boosted"]
    fatjet_eta = event_data["SelectedFatJet_eta_boosted"]
    fatjet_phi = event_data["SelectedFatJet_phi_boosted"]
    fatjet_mass = event_data["SelectedFatJet_mass_boosted"]
    fatjet_px, fatjet_py, fatjet_pz, fatjet_e = convert_kinematics(
        fatjet_pt, fatjet_eta, fatjet_phi, fatjet_mass
    )

    met_px, met_py, _, _ = convert_kinematics(
        event_data["met_pt"], 0, event_data["met_phi"], 0
    )

    pairtype_map = {23: 0, 13: 1, 33: 2}
    event_data["channelId"] = np.where(
        event_data["channelId"] == 23, 0, event_data["channelId"]
    )
    event_data["channelId"] = np.where(
        event_data["channelId"] == 13, 1, event_data["channelId"]
    )
    event_data["channelId"] = np.where(
        event_data["channelId"] == 33, 2, event_data["channelId"]
    )
    inputs = {
        "event_number": np.array(event_data["event"]),
        "spin": np.full(
            np.array(event_data["event"]).shape,
            spin,
        ),
        "mass": np.full(
            np.array(event_data["event"]).shape,
            mass,
        ),
        # "era": np.full(
        #     np.array(event_data["event"]).shape,
        #     Era[period].value,
        # ),
        "pair_type": np.array(event_data["channelId"]),
        "dau1_dm": np.array(event_data["tau1_decayMode"]),
        "dau2_dm": np.array(event_data["tau2_decayMode"]),
        "dau1_charge": np.array(event_data["tau1_charge"]),
        "dau2_charge": np.array(event_data["tau2_charge"]),
        "is_boosted": np.array(event_data["boosted_baseline"]),
        "has_bjet_pair": np.array(event_data["Hbb_isValid"]),
        "met_px": np.array(met_px),
        "met_py": np.array(met_py),
        "met_cov00": np.array(event_data["met_covXX"]),
        "met_cov01": np.array(event_data["met_covXY"]),
        "met_cov11": np.array(event_data["met_covYY"]),
        "dau1_e": np.array(dau1_e),
        "dau1_px": np.array(dau1_px),
        "dau1_py": np.array(dau1_py),
        "dau1_pz": np.array(dau1_pz),
        "dau2_e": np.array(dau2_e),
        "dau2_px": np.array(dau2_px),
        "dau2_py": np.array(dau2_py),
        "dau2_pz": np.array(dau2_pz),
        "bjet1_e": np.array(bjet1_e),
        "bjet1_px": np.array(bjet1_px),
        "bjet1_py": np.array(bjet1_py),
        "bjet1_pz": np.array(bjet1_pz),
        "bjet1_btag_df": np.array(event_data["b1_btagDeepFlavB"]),
        "bjet1_cvsb": np.array(event_data["b1_btagPNetCvB"]),
        "bjet1_cvsl": np.array(event_data["b1_btagPNetCvL"]),
        "bjet1_hhbtag": np.array(event_data["b1_HHbtag"]),
        "bjet2_e": np.array(bjet2_e),
        "bjet2_px": np.array(bjet2_px),
        "bjet2_py": np.array(bjet2_py),
        "bjet2_pz": np.array(bjet2_pz),
        "bjet2_btag_df": np.array(event_data["b2_btagDeepFlavB"]),
        "bjet2_cvsb": np.array(event_data["b2_btagPNetCvB"]),
        "bjet2_cvsl": np.array(event_data["b2_btagPNetCvL"]),
        "bjet2_hhbtag": np.array(event_data["b2_HHbtag"]),
        "fatjet_e": np.array(fatjet_e),
        "fatjet_px": np.array(fatjet_px),
        "fatjet_py": np.array(fatjet_py),
        "fatjet_pz": np.array(fatjet_pz),
    }
    return inputs
