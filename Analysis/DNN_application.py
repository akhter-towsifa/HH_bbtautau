from __future__ import annotations
import os, sys
import numpy as np
import awkward as ak
import psutil
import yaml
import os
import ROOT
import FLAF.Common.Utilities as Utilities
import Analysis.hh_bbtautau as analysis
import tensorflow as tf
from Analysis.interface import NNInterface
import enum


class DNNProducer:
    def __init__(self, cfg, payload_name, era):

        self.payload_name = payload_name
        self.era = era

        sys.path.append(os.environ["ANALYSIS_PATH"])
        ROOT.gROOT.ProcessLine(".include " + os.environ["ANALYSIS_PATH"])
        ROOT.gInterpreter.Declare(f'#include "FLAF/include/Utilities.h"')
        ROOT.gROOT.ProcessLine(f'#include "FLAF/include/HistHelper.h"')
        ROOT.gROOT.ProcessLine(f'#include "FLAF/include/AnalysisTools.h"')
        ROOT.gROOT.ProcessLine(f'#include "FLAF/include/AnalysisMath.h"')
        ROOT.gROOT.ProcessLine(f'#include "FLAF/include/MT2.h"')

        self.dnnConfig = cfg

        self.models = self.load_models(self.dnnConfig["model_dir"])
        self.features = self.dnnConfig["features"]

        self.cols_to_save = [
            f"{self.payload_name}_{col}" for col in self.dnnConfig["columns"]
        ]
        load_features = self.features
        self.vars_to_save = load_features

    def load_models(self, model_dir):
        if not os.path.isabs(model_dir):
            model_dir = os.path.join(os.environ["ANALYSIS_PATH"], model_dir)
        models = [
            NNInterface(
                fold_index=fold_index,
                model_path=os.path.join(
                    model_dir,
                    f"model_fold{fold_index}_moe",
                ),
            )
            for fold_index in range(NNInterface.n_folds)
        ]
        return models

    def prepare_dfw(self, rdf, dataset):
        return rdf

    def run(self, array):
        array = self.ApplyDNN(array)

        # Delete not-needed branches
        for col in array.fields:
            if col not in self.dnnConfig["columns"]:
                if col != "FullEventId":
                    del array[col]

        # Rename the branches
        for col in self.dnnConfig["columns"]:
            if col in array.fields:
                array[f"{self.payload_name}_{col}"] = array[f"{col}"]
                del array[f"{col}"]
            else:
                print(f"Expected column {col} not found in your payload array!")

        return array

    def ApplyDNN(self, array):
        models = self.models

        other_columns_dict = array
        num_events = len(array["event"])

        if num_events == 0:
            print(f"No events found for inference, skipping.")
            return array

        # mask events to only those with channelId in [13,23,33]
        valid_channels = np.isin(array["channelId"], [13, 23, 33])
        valid_event_indices = np.flatnonzero(valid_channels)
        if not np.any(valid_channels):
            print("No events with channelId in [13,23,33], skipping inference.")
            return array

        predictions_array = np.full(
            (NNInterface.n_folds, num_events, NNInterface.n_out),
            np.nan,
        )
        for fold_index, nn_interface in enumerate(models):
            # build inputs only for valid events
            valid_array = array[valid_channels]
            inputs = convert_to_numpy(valid_array, self.era, 400, 2)
            predictions = self.run_inference(nn_interface, inputs)
            predictions_array[fold_index, valid_event_indices, :] = predictions

        valid_predictions = predictions_array[:, valid_event_indices, :]
        finite_mask = np.isfinite(valid_predictions)
        counts = finite_mask.sum(axis=0)
        sums = np.nansum(valid_predictions, axis=0)
        mean_predictions_valid = np.divide(
            sums,
            counts,
            out=np.full_like(sums, np.nan, dtype=np.float32),
            where=counts > 0,
        )

        mean_predictions = np.full(
            (num_events, NNInterface.n_out),
            np.nan,
        )
        mean_predictions[valid_event_indices, :] = mean_predictions_valid
        for i, col in enumerate(self.dnnConfig["columns"]):
            array[f"{col}"] = mean_predictions[:, i]

        return array

    def run_inference(self, nn_interface, inputs):
        predictions = nn_interface(**inputs)
        return predictions


def convert_to_numpy(event_data, era, mass, spin):
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
        # some samples have tau2_decayMode=2, these need to be remapped as 1
        "dau1_dm": np.where(
            np.array(event_data["tau1_decayMode"]) == 2, 1, event_data["tau1_decayMode"]
        ),
        "dau2_dm": np.where(
            np.array(event_data["tau2_decayMode"]) == 2, 1, event_data["tau2_decayMode"]
        ),
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


def convert_kinematics(pt, eta, phi, mass):
    px = pt * np.cos(phi)
    py = pt * np.sin(phi)
    pz = pt * np.sinh(eta)
    energy = np.sqrt(pt**2 * np.cosh(eta) ** 2 + mass**2)
    return px, py, pz, energy
