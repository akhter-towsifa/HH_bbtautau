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
from Analysis.dnn_kinematics import convert_to_numpy, convert_kinematics
import enum


class DNNProducer:
    def __init__(self, cfg, payload_name, period):

        self.payload_name = payload_name
        self.period = period

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
            inputs = convert_to_numpy(valid_array, self.period, 400, 2)
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
