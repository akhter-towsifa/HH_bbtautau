from __future__ import annotations
import os
import numpy as np
import torch

from Analysis.DNN_training.config import CLASSES, ModelConfig, categorical_cardinalities
from Analysis.DNN_training.model import Ensemble, GGFClassifier
from Analysis.DNN_training.data import build_features


def _infer_ensemble_size(state_dict) -> int:
    """The deployed `model_fold{N}_moe.pt` checkpoints are `Ensemble.state_dict()`s
    with keys prefixed "models.<seed_index>." -- infer the seed count from those
    keys rather than hardcoding it (KFoldConfig.n_seeds defaults to 5, but the
    checkpoints actually deployed here were saved with n_seeds=1)."""
    indices = {int(key.split(".")[1]) for key in state_dict if key.startswith("models.")}
    if not indices:
        raise ValueError("Could not infer ensemble size: no 'models.<N>.*' keys in checkpoint")
    return max(indices) + 1


def load_ensemble(model_path: str) -> Ensemble:
    state = torch.load(model_path, map_location="cpu")
    n_seeds = _infer_ensemble_size(state)
    model_cfg = ModelConfig()
    cardinalities = categorical_cardinalities()
    ensemble = Ensemble([GGFClassifier(model_cfg, cardinalities) for _ in range(n_seeds)])
    ensemble.load_state_dict(state)
    ensemble.eval()
    return ensemble


class PyTorchNNInterface:
    """PyTorch counterpart of Analysis.interface.NNInterface: one fold's model,
    evaluated only on the events whose event_number % n_folds == fold_index (the
    fold that model was held out from during training)."""

    n_folds = 5
    n_out = len(CLASSES)

    def __init__(self, fold_index: int, model_path: str):
        self.fold_index = fold_index
        self.model_path = os.path.expandvars(model_path)
        self.model = load_ensemble(self.model_path)

    def predict(self, event_number, cat_inputs, lbn_vectors, extra_continuous):
        event_number = np.asarray(event_number)
        pred = np.full((event_number.shape[0], self.n_out), np.nan, dtype=np.float32)
        fold_mask = (event_number % self.n_folds) == self.fold_index
        if not np.any(fold_mask):
            return pred
        with torch.no_grad():
            cat_t = {
                name: torch.as_tensor(values[fold_mask], dtype=torch.long)
                for name, values in cat_inputs.items()
            }
            lbn_t = torch.as_tensor(lbn_vectors[fold_mask], dtype=torch.float32)
            cont_t = torch.as_tensor(extra_continuous[fold_mask], dtype=torch.float32)
            out = self.model(cat_t, lbn_t, cont_t).numpy()
        pred[fold_mask] = out
        return pred


def _load_fold_models(model_dir: str, version: str) -> list[PyTorchNNInterface]:
    if not os.path.isabs(model_dir):
        model_dir = os.path.join(os.environ["ANALYSIS_PATH"], model_dir)
    return [
        PyTorchNNInterface(
            fold_index=fold_index,
            model_path=os.path.join(model_dir, f"{version.format(fold_index)}.pt"),
        )
        for fold_index in range(PyTorchNNInterface.n_folds)
    ]


def _average_over_folds(predictions_array: np.ndarray) -> np.ndarray:
    """predictions_array: (n_folds, n_events, n_out), NaN outside each fold
    model's own held-out fold -- exactly one fold is non-NaN per event, so this
    just selects that fold's prediction (nanmean over an axis with a single
    finite entry), matching DNN_application.py::DNNProducer.ApplyDNN."""
    finite_mask = np.isfinite(predictions_array)
    counts = finite_mask.sum(axis=0)
    sums = np.nansum(predictions_array, axis=0)
    return np.divide(
        sums, counts, out=np.full_like(sums, np.nan, dtype=np.float32), where=counts > 0
    )


class PyTorchDNNProducer:
    """Deploys one of the standalone-trained PyTorch ggF DNN variants (no kinFit
    region cut, e.g. the "full" model) as a FLAF payload producer, parallel to
    DNN_application.py::DNNProducer for the TF-based central model."""

    def __init__(self, cfg, payload_name, period):
        self.payload_name = payload_name
        self.period = period
        self.dnnConfig = cfg
        version = cfg.get("version", "model_fold{}_moe")
        self.models = _load_fold_models(cfg["model_dir"], version)
        self.features = cfg["features"]
        self.cols_to_save = [f"{self.payload_name}_{col}" for col in self.dnnConfig["columns"]]
        self.vars_to_save = self.features

    def prepare_dfw(self, rdf, dataset):
        return rdf

    def run(self, array):
        array = self.ApplyDNN(array)
        for col in array.fields:
            if col not in self.dnnConfig["columns"] and col != "FullEventId":
                del array[col]
        for col in self.dnnConfig["columns"]:
            if col in array.fields:
                array[f"{self.payload_name}_{col}"] = array[f"{col}"]
                del array[f"{col}"]
            else:
                print(f"Expected column {col} not found in your payload array!")
        return array

    def ApplyDNN(self, array):
        columns = self.dnnConfig["columns"]
        num_events = len(array["event"])
        mean_predictions = np.full((num_events, PyTorchNNInterface.n_out), np.nan, dtype=np.float32)

        if num_events > 0:
            valid_channels = np.isin(np.asarray(array["channelId"]), [13, 23, 33])
            if np.any(valid_channels):
                valid_event_indices = np.flatnonzero(valid_channels)
                valid_array = array[valid_channels]
                cat_inputs, lbn_vectors, extra_continuous = build_features(
                    valid_array, period=self.period
                )
                event_number = np.asarray(valid_array["event"])

                predictions_array = np.full(
                    (PyTorchNNInterface.n_folds, num_events, PyTorchNNInterface.n_out), np.nan
                )
                for fold_index, nn_interface in enumerate(self.models):
                    preds = nn_interface.predict(event_number, cat_inputs, lbn_vectors, extra_continuous)
                    predictions_array[fold_index, valid_event_indices, :] = preds

                mean_predictions[valid_event_indices, :] = _average_over_folds(
                    predictions_array[:, valid_event_indices, :]
                )

        for i, col in enumerate(columns):
            array[col] = mean_predictions[:, i]
        return array


class PyTorchRegionRoutedDNNProducer:
    """Deploys N kinFit_m-region-specialist PyTorch ggF DNN models (e.g. "low"
    and "high") as a single combined payload producer: each event is routed to
    whichever region's model covers its kinFit_m, and evaluated only by that
    region's model (hard routing, not a calibrated blend). Events where the
    kinematic fit did not converge (kinFit_convergence <= 0) get no score at
    all -- kinFit_m isn't meaningful for them, so no region assignment is made.

    Config carries a `regions:` list, each entry:
      {name: str, kinFit_m_min?: float, kinFit_m_max?: float, model_dir: str}
    (bounds are half-open [min, max); an omitted bound is unbounded on that
    side). This generalizes to more than two regions -- add more entries.
    """

    def __init__(self, cfg, payload_name, period):
        self.payload_name = payload_name
        self.period = period
        self.dnnConfig = cfg
        self.regions = cfg["regions"]
        self._validate_regions(self.regions)
        version = cfg.get("version", "model_fold{}_moe")
        self.region_models = {
            region["name"]: _load_fold_models(region["model_dir"], version)
            for region in self.regions
        }
        self.features = cfg["features"]
        self.cols_to_save = [f"{self.payload_name}_{col}" for col in self.dnnConfig["columns"]]
        self.vars_to_save = self.features

    @staticmethod
    def _validate_regions(regions):
        if not regions:
            raise ValueError("PyTorchRegionRoutedDNNProducer requires at least one region")
        bounds = []
        for region in regions:
            lo = region.get("kinFit_m_min", -np.inf)
            hi = region.get("kinFit_m_max", np.inf)
            if lo >= hi:
                raise ValueError(f"region {region['name']!r} has empty bounds [{lo}, {hi})")
            bounds.append((lo, hi))
        bounds.sort()
        if bounds[0][0] > 0:
            raise ValueError(
                f"regions must cover kinFit_m starting from 0 (or -inf), got lowest bound {bounds[0][0]}"
            )
        for (_, hi), (lo2, _) in zip(bounds, bounds[1:]):
            if hi != lo2:
                raise ValueError(f"regions must be contiguous with no gaps/overlaps: {hi} != {lo2}")
        if bounds[-1][1] != np.inf:
            raise ValueError("regions must cover kinFit_m up to +inf")

    def prepare_dfw(self, rdf, dataset):
        return rdf

    def run(self, array):
        array = self.ApplyDNN(array)
        for col in array.fields:
            if col not in self.dnnConfig["columns"] and col != "FullEventId":
                del array[col]
        for col in self.dnnConfig["columns"]:
            if col in array.fields:
                array[f"{self.payload_name}_{col}"] = array[f"{col}"]
                del array[f"{col}"]
            else:
                print(f"Expected column {col} not found in your payload array!")
        return array

    def ApplyDNN(self, array):
        columns = self.dnnConfig["columns"]
        num_events = len(array["event"])
        mean_predictions = np.full((num_events, PyTorchNNInterface.n_out), np.nan, dtype=np.float32)

        if num_events > 0:
            channel_ok = np.isin(np.asarray(array["channelId"]), [13, 23, 33])
            converged = np.asarray(array["kinFit_convergence"]) > 0
            valid = channel_ok & converged

            if np.any(valid):
                valid_event_indices = np.flatnonzero(valid)
                valid_array = array[valid]
                kinfit_m = np.asarray(valid_array["kinFit_m"])
                event_number = np.asarray(valid_array["event"])

                for region in self.regions:
                    lo = region.get("kinFit_m_min", -np.inf)
                    hi = region.get("kinFit_m_max", np.inf)
                    region_mask = (kinfit_m >= lo) & (kinfit_m < hi)
                    if not np.any(region_mask):
                        continue

                    region_array = valid_array[region_mask]
                    cat_inputs, lbn_vectors, extra_continuous = build_features(
                        region_array, period=self.period
                    )
                    region_event_number = event_number[region_mask]

                    predictions_array = np.full(
                        (PyTorchNNInterface.n_folds, int(np.count_nonzero(region_mask)), PyTorchNNInterface.n_out),
                        np.nan,
                    )
                    for fold_index, nn_interface in enumerate(self.region_models[region["name"]]):
                        predictions_array[fold_index] = nn_interface.predict(
                            region_event_number, cat_inputs, lbn_vectors, extra_continuous
                        )

                    region_mean = _average_over_folds(predictions_array)
                    target_indices = valid_event_indices[region_mask]
                    mean_predictions[target_indices, :] = region_mean

        for i, col in enumerate(columns):
            array[col] = mean_predictions[:, i]
        return array
