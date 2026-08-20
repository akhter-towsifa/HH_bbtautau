from __future__ import annotations

import glob
import os
from dataclasses import dataclass

import numpy as np
import uproot
import yaml

from Analysis.DNN_application import convert_to_numpy

from .config import (
    CATEGORICAL_SPECS,
    CHANNEL_MUTAU,
    CHANNEL_TAUTAU,
    CLASSES,
    CLASS_INDEX,
    CLASS_PROCESS_GROUPS,
    EXTRA_CONTINUOUS_FEATURES,
    HH_SIGNAL_POINTS,
    LBN_OBJECTS,
    PAIRTYPE_MAP,
    VALID_CHANNEL_IDS,
    DataConfig,
    categorical_index_maps,
    hh_dataset_name,
)

# Branches read from the anaTuple. NNInterface.array_inputs (interface.py)
# already documents the feature set consumed at inference time; this list is
# the raw-branch superset needed to reconstruct that, plus selection/weight/
# label branches.
RAW_BRANCHES = [
    "event", "channelId",
    "tau1_pt", "tau1_eta", "tau1_phi", "tau1_mass", "tau1_charge", "tau1_decayMode",
    "tau2_pt", "tau2_eta", "tau2_phi", "tau2_mass", "tau2_charge", "tau2_decayMode",
    "b1_pt", "b1_eta", "b1_phi", "b1_mass",
    "b1_btagDeepFlavB", "b1_btagPNetCvB", "b1_btagPNetCvL", "b1_HHbtag",
    "b2_pt", "b2_eta", "b2_phi", "b2_mass",
    "b2_btagDeepFlavB", "b2_btagPNetCvB", "b2_btagPNetCvL", "b2_HHbtag",
    "SelectedFatJet_pt_boosted", "SelectedFatJet_eta_boosted",
    "SelectedFatJet_phi_boosted", "SelectedFatJet_mass_boosted",
    "met_pt", "met_phi", "met_covXX", "met_covXY", "met_covYY",
    "boosted_baseline", "Hbb_isValid",
    "weight_base",
]


@dataclass
class DatasetShard:
    class_name: str
    subprocess: str  # e.g. "GluGlutoHHto2B2Tau_kl_1p00_kt_1p00_c2_0p00__Run3_2022EE"
    era: str
    cat_inputs: dict[str, np.ndarray]  # int64 arrays, already remapped to embedding indices
    lbn_vectors: np.ndarray  # (n_events, 5, 4)
    extra_continuous: np.ndarray  # (n_events, len(EXTRA_CONTINUOUS_FEATURES))
    label: np.ndarray  # (n_events,) int64, constant == CLASS_INDEX[class_name]
    weight: np.ndarray  # (n_events,) float32 physical MC weight
    fold: np.ndarray  # (n_events,) int64, event % n_folds


def _expand_process_group(processes: dict, group_name: str) -> list[str]:
    """Recursively expands a process-group entry into a flat list of dataset
    names, following `sub_processes` (meta-groups, e.g. "DY", which has no
    `datasets:` of its own) down to the leaf groups that do."""
    entry = processes[group_name]
    if "sub_processes" in entry:
        datasets: list[str] = []
        for sub in entry["sub_processes"]:
            datasets.extend(_expand_process_group(processes, sub))
        return datasets
    return entry.get("datasets", [])


def resolve_class_datasets(class_name: str, era: str, config_dir: str) -> list[str]:
    """Expand a background class into its underlying dataset names by reading
    bbtautau/config/{era}/processes.yaml. Wildcard group names (ending in "*")
    match by prefix against the top-level process-group keys."""
    if class_name == "HH":
        return [hh_dataset_name(kl, kt, c2) for kl, kt, c2 in HH_SIGNAL_POINTS]

    processes_path = os.path.join(config_dir, era, "processes.yaml")
    with open(processes_path) as f:
        processes = yaml.safe_load(f)

    datasets: list[str] = []
    for group_pattern in CLASS_PROCESS_GROUPS[class_name]:
        if group_pattern.endswith("*"):
            prefix = group_pattern[:-1]
            matching_groups = [k for k in processes if k.startswith(prefix)]
        else:
            matching_groups = [group_pattern]
        for group in matching_groups:
            datasets.extend(_expand_process_group(processes, group))
    return datasets


def anatuple_files(data_root: str, era: str, dataset: str) -> list[str]:
    """Locate merged anaTuple ROOT files for one (era, dataset), mirroring the
    AnaTupleMergeTask output layout seen under bbtautau/data/v*/AnaTupleMergeTask/
    {era}/{dataset}/*.root."""
    pattern = os.path.join(data_root, "AnaTupleMergeTask", era, dataset, "*.root")
    return sorted(glob.glob(pattern))


def iter_events(files: list[str], branches: list[str], step_size: str, tree_name: str = "Events"):
    """Thin wrapper around uproot.iterate, mirroring the pattern used at
    bbtautau/FLAF/Analysis/AnalysisCacheProducer.py:91-93."""
    file_specs = [f"{path}:{tree_name}" for path in files]
    yield from uproot.iterate(file_specs, filter_name=branches, step_size=step_size)


def select_training_events(array, deep_tau_branch: str, medium_wp: int) -> np.ndarray:
    """Boolean mask reproducing the training-data selection of AN Sec. 5.3.1:
    >=1 hadronic tau (channelId in VALID_CHANNEL_IDS), opposite-sign, isolated
    second tau. Ported from hh_bbtautau.py:594-619 (OS_Iso = lepton_preselection
    && OS && Iso), specialized to the eTau/muTau/tauTau-only channel set (the
    muMu/eMu/eE branches of that logic never apply here, so they're dropped).

    *deep_tau_branch* is the DeepTauVSjet ID branch suffix used for both tau
    legs (e.g. "idDeepTau2018v2p5VSjet"); *medium_wp* is the integer Medium
    working-point value -- get it from
    FLAF.Common.Utilities.WorkingPointsTauVSjet.Medium.value for the era/version
    in use (see hh_bbtautau.py:588, 608). No default is hardcoded here since it
    wasn't verified during exploration.
    """
    channel_id = np.asarray(array["channelId"])
    channel_mask = np.isin(channel_id, VALID_CHANNEL_IDS)

    os_mask = np.asarray(array["tau1_charge"]) * np.asarray(array["tau2_charge"]) < 0

    tau2_iso = np.asarray(array[f"tau2_{deep_tau_branch}"]) >= medium_wp

    # lepton_preselection, specialized to eTau(13)/muTau(23)/tauTau(33):
    #   tau1_iso_medium applies only for tauTau; muon1_tightId only for muTau;
    #   muon2_tightId/firstele_mvaIso never apply for this channel set.
    is_tautau = channel_id == CHANNEL_TAUTAU
    is_mutau = channel_id == CHANNEL_MUTAU
    tau1_iso_medium = np.where(
        is_tautau, np.asarray(array[f"tau1_{deep_tau_branch}"]) >= medium_wp, True
    )
    muon1_tight = np.where(
        is_mutau,
        np.asarray(array["tau1_Muon_tightId"]) & (np.asarray(array["tau1_Muon_pfRelIso04_all"]) < 0.15),
        True,
    )
    lepton_preselection = tau1_iso_medium & muon1_tight

    return channel_mask & os_mask & tau2_iso & lepton_preselection


def _rotate_to_phi(ref_phi: np.ndarray, px: np.ndarray, py: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rotates (px, py) in the transverse plane to reference angle ref_phi.
    Reimplemented locally (matches interface.py::rotate_to_phi) so data.py
    doesn't depend on interface.py internals."""
    new_phi = np.arctan2(py, px) - ref_phi
    pt = (px**2 + py**2) ** 0.5
    return pt * np.cos(new_phi), pt * np.sin(new_phi)


def _apply_rotation_and_composites(f: dict) -> dict:
    """Rotates four-vectors relative to the visible lepton-pair phi, builds the
    composite Htt/Hbb/HHbbtautau/FatJet+tautau four-vectors, and masks
    bjet/fatjet-derived features when no bjet-pair/fatjet was reconstructed.
    Reimplements (does not import) the same preprocessing NNInterface.predict()
    applies in interface.py, so training and inference stay consistent by
    construction even though the code is duplicated rather than shared.
    Mutates and returns *f* in place.
    """
    phi_lep = np.arctan2(f["dau1_py"] + f["dau2_py"], f["dau1_px"] + f["dau2_px"])

    f["met_px"], f["met_py"] = _rotate_to_phi(phi_lep, f["met_px"], f["met_py"])
    f["dau1_px"], f["dau1_py"] = _rotate_to_phi(phi_lep, f["dau1_px"], f["dau1_py"])
    f["dau2_px"], f["dau2_py"] = _rotate_to_phi(phi_lep, f["dau2_px"], f["dau2_py"])
    f["bjet1_px"], f["bjet1_py"] = _rotate_to_phi(phi_lep, f["bjet1_px"], f["bjet1_py"])
    f["bjet2_px"], f["bjet2_py"] = _rotate_to_phi(phi_lep, f["bjet2_px"], f["bjet2_py"])
    f["fatjet_px"], f["fatjet_py"] = _rotate_to_phi(phi_lep, f["fatjet_px"], f["fatjet_py"])

    f["htt_e"] = f["dau1_e"] + f["dau2_e"]
    f["htt_px"] = f["dau1_px"] + f["dau2_px"]
    f["htt_py"] = f["dau1_py"] + f["dau2_py"]
    f["htt_pz"] = f["dau1_pz"] + f["dau2_pz"]
    f["hbb_e"] = f["bjet1_e"] + f["bjet2_e"]
    f["hbb_px"] = f["bjet1_px"] + f["bjet2_px"]
    f["hbb_py"] = f["bjet1_py"] + f["bjet2_py"]
    f["hbb_pz"] = f["bjet1_pz"] + f["bjet2_pz"]
    f["htthbb_e"] = f["htt_e"] + f["hbb_e"]
    f["htthbb_px"] = f["htt_px"] + f["hbb_px"]
    f["htthbb_py"] = f["htt_py"] + f["hbb_py"]
    f["htthbb_pz"] = f["htt_pz"] + f["hbb_pz"]
    f["httfatjet_e"] = f["htt_e"] + f["fatjet_e"]
    f["httfatjet_px"] = f["htt_px"] + f["fatjet_px"]
    f["httfatjet_py"] = f["htt_py"] + f["fatjet_py"]
    f["httfatjet_pz"] = f["htt_pz"] + f["fatjet_pz"]

    bj_mask = f["has_bjet_pair"] != 1
    f["bjet1_e"][bj_mask] = f["bjet1_px"][bj_mask] = f["bjet1_py"][bj_mask] = f["bjet1_pz"][bj_mask] = 0.0
    f["bjet2_e"][bj_mask] = f["bjet2_px"][bj_mask] = f["bjet2_py"][bj_mask] = f["bjet2_pz"][bj_mask] = 0.0
    f["bjet1_btag_df"][bj_mask] = f["bjet1_cvsb"][bj_mask] = f["bjet1_cvsl"][bj_mask] = -1.0
    f["bjet2_btag_df"][bj_mask] = f["bjet2_cvsb"][bj_mask] = f["bjet2_cvsl"][bj_mask] = -1.0
    f["hbb_e"][bj_mask] = f["hbb_px"][bj_mask] = f["hbb_py"][bj_mask] = f["hbb_pz"][bj_mask] = 0.0
    f["htthbb_e"][bj_mask] = f["htthbb_px"][bj_mask] = f["htthbb_py"][bj_mask] = f["htthbb_pz"][bj_mask] = 0.0

    fj_mask = f["is_boosted"] != 1
    f["fatjet_e"][fj_mask] = f["fatjet_px"][fj_mask] = f["fatjet_py"][fj_mask] = f["fatjet_pz"][fj_mask] = 0.0

    return f


def build_features(array, period: str) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    """Turns a selected awkward-array chunk into (cat_inputs, lbn_vectors,
    extra_continuous), reusing DNN_application.convert_to_numpy() for the raw
    four-vector construction, then applying the same rotation/composite/masking
    steps NNInterface.predict() applies at inference time (reimplemented above
    in _apply_rotation_and_composites, so interface.py stays untouched).

    convert_to_numpy() also returns a "pair_type" field using
    DNN_application.py's own hardcoded pairtype_map={23:0,13:1,33:2}; that
    field is overwritten below using config.PAIRTYPE_MAP (our own convention
    for this training) applied to the raw channelId, so the old TF model's
    category numbering never leaks into this pipeline.
    """
    raw = convert_to_numpy(array, period, mass=0.0, spin=0)  # mass/spin unused by the GGF net
    f = {k: np.asarray(v).astype(np.float64) if np.asarray(v).dtype.kind == "f" else np.asarray(v)
         for k, v in raw.items()}
    f = _apply_rotation_and_composites(f)

    channel_id = np.asarray(array["channelId"])
    f["pair_type"] = np.vectorize(PAIRTYPE_MAP.get)(channel_id).astype(np.int64)

    index_maps = categorical_index_maps()
    cat_inputs = {}
    for name in CATEGORICAL_SPECS:
        raw_values = np.asarray(f[name])
        cat_inputs[name] = np.vectorize(index_maps[name].get)(raw_values).astype(np.int64)

    lbn_vectors = np.stack(
        [np.stack([f[f"{obj}_px"], f[f"{obj}_py"], f[f"{obj}_pz"], f[f"{obj}_e"]], axis=-1)
         for obj in LBN_OBJECTS],
        axis=1,
    ).astype(np.float32)  # (n_events, 5, 4)

    extra_continuous = np.stack(
        [np.asarray(f[name]) for name in EXTRA_CONTINUOUS_FEATURES], axis=-1
    ).astype(np.float32)

    return cat_inputs, lbn_vectors, extra_continuous


def load_shard(
    class_name: str, era: str, dataset: str, cfg: DataConfig, n_folds: int
) -> DatasetShard | None:
    files = anatuple_files(cfg.data_root, era, dataset)
    if not files:
        return None

    cat_chunks, lbn_chunks, cont_chunks, weight_chunks, event_chunks = [], [], [], [], []
    for chunk in iter_events(files, RAW_BRANCHES, cfg.step_size):
        mask = select_training_events(chunk, cfg.deep_tau_branch, cfg.deep_tau_medium_wp)
        if not np.any(mask):
            continue
        selected = chunk[mask]
        cat_inputs, lbn_vectors, extra_continuous = build_features(selected, period=era)
        cat_chunks.append(cat_inputs)
        lbn_chunks.append(lbn_vectors)
        cont_chunks.append(extra_continuous)
        weight_chunks.append(np.asarray(selected["weight_base"]))
        event_chunks.append(np.asarray(selected["event"]))

    if not lbn_chunks:
        return None

    cat_inputs = {
        name: np.concatenate([c[name] for c in cat_chunks]) for name in CATEGORICAL_SPECS
    }
    lbn_vectors = np.concatenate(lbn_chunks)
    extra_continuous = np.concatenate(cont_chunks)
    weight = np.concatenate(weight_chunks).astype(np.float32)
    event = np.concatenate(event_chunks)

    n = len(weight)
    return DatasetShard(
        class_name=class_name,
        subprocess=f"{dataset}__{era}",
        era=era,
        cat_inputs=cat_inputs,
        lbn_vectors=lbn_vectors,
        extra_continuous=extra_continuous,
        label=np.full(n, CLASS_INDEX[class_name], dtype=np.int64),
        weight=weight,
        fold=(event % n_folds).astype(np.int64),
    )


def load_all_shards(cfg: DataConfig, n_folds: int) -> list[DatasetShard]:
    shards = []
    for class_name in CLASSES:
        for era in cfg.eras:
            for dataset in resolve_class_datasets(class_name, era, cfg.config_dir):
                shard = load_shard(class_name, era, dataset, cfg, n_folds)
                if shard is not None:
                    shards.append(shard)
                else:
                    print(f"[data] no events/files for {class_name}/{era}/{dataset}, skipping")
    return shards


def assign_train_val(shards: list[DatasetShard], test_fold: int, val_fraction: float, seed: int):
    """Combines the events of the 4 non-test folds across all shards and does a
    seeded random val_fraction split (AN: train:val = 3:1). Returns
    (train_indices_by_shard, val_indices_by_shard, test_indices_by_shard), each
    a dict[shard_index -> np.ndarray of local event indices]."""
    rng = np.random.default_rng(seed)
    train_idx, val_idx, test_idx = {}, {}, {}
    for i, shard in enumerate(shards):
        is_test = shard.fold == test_fold
        test_idx[i] = np.flatnonzero(is_test)

        pool = np.flatnonzero(~is_test)
        rng.shuffle(pool)
        n_val = int(round(len(pool) * val_fraction))
        val_idx[i] = pool[:n_val]
        train_idx[i] = pool[n_val:]
    return train_idx, val_idx, test_idx


if __name__ == "__main__":
    # Synthetic smoke test for select_training_events -- no real anaTuple needed.
    n = 9
    fake = {
        "channelId": np.array([13, 23, 23, 33, 33, 15, 23, 13, 33]),
        "tau1_charge": np.array([1, 1, 1, 1, 1, 1, 1, 1, 1]),
        "tau2_charge": np.array([-1, -1, -1, -1, -1, -1, 1, 1, -1]),
        "tau1_idDeepTauTest": np.array([5, 5, 5, 5, 2, 5, 5, 5, 5]),
        "tau2_idDeepTauTest": np.array([5, 5, 5, 5, 5, 5, 5, 5, 2]),
        "tau1_Muon_tightId": np.array([True, True, False, True, True, True, True, True, True]),
        "tau1_Muon_pfRelIso04_all": np.full(n, 0.05),
    }
    mask = select_training_events(fake, deep_tau_branch="idDeepTauTest", medium_wp=5)
    # 0: eTau(13), OS, tau2 iso ok                                        -> pass
    # 1: muTau(23), OS, tau2 iso ok, muon tight+iso ok                    -> pass
    # 2: muTau(23), OS, tau2 iso ok, muon NOT tight                       -> fail
    # 3: tauTau(33), OS, tau1+tau2 iso ok                                 -> pass
    # 4: tauTau(33), OS, tau1 NOT iso medium (dt1=2), tau2 iso ok         -> fail
    # 5: invalid channelId (15)                                          -> fail
    # 6: muTau(23), same-sign (OS fails)                                 -> fail
    # 7: eTau(13), same-sign (OS fails)                                  -> fail
    # 8: tauTau(33), OS, tau1 iso ok, tau2 NOT iso (dt2=2)                -> fail
    print("select_training_events mask:", mask)
    assert mask[0] and mask[1] and mask[3]
    assert not mask[2] and not mask[4] and not mask[5] and not mask[6] and not mask[7] and not mask[8]

    # pair_type convention smoke test (config.PAIRTYPE_MAP: eTau=13->0, muTau=23->1, tauTau=33->2)
    from .config import PAIRTYPE_MAP
    channel_id = np.array([13, 23, 33])
    pair_type = np.vectorize(PAIRTYPE_MAP.get)(channel_id)
    assert list(pair_type) == [0, 1, 2], pair_type

    # _apply_rotation_and_composites shape/consistency smoke test
    m = 4
    f = {
        "dau1_px": np.array([10., 0., 5., -5.]), "dau1_py": np.array([0., 10., 5., 5.]),
        "dau1_pz": np.zeros(m), "dau1_e": np.full(m, 50.),
        "dau2_px": np.array([5., 0., -5., 5.]), "dau2_py": np.array([0., 5., -5., -5.]),
        "dau2_pz": np.zeros(m), "dau2_e": np.full(m, 40.),
        "bjet1_px": np.full(m, 20.), "bjet1_py": np.full(m, 20.), "bjet1_pz": np.zeros(m), "bjet1_e": np.full(m, 60.),
        "bjet1_btag_df": np.full(m, 0.9), "bjet1_cvsb": np.full(m, 0.1), "bjet1_cvsl": np.full(m, 0.5),
        "bjet2_px": np.full(m, -20.), "bjet2_py": np.full(m, -20.), "bjet2_pz": np.zeros(m), "bjet2_e": np.full(m, 55.),
        "bjet2_btag_df": np.full(m, 0.8), "bjet2_cvsb": np.full(m, 0.05), "bjet2_cvsl": np.full(m, 0.4),
        "fatjet_px": np.zeros(m), "fatjet_py": np.zeros(m), "fatjet_pz": np.zeros(m), "fatjet_e": np.zeros(m),
        "met_px": np.full(m, 30.), "met_py": np.full(m, 10.),
        "has_bjet_pair": np.array([1, 1, 0, 1]),
        "is_boosted": np.array([0, 1, 0, 0]),
    }
    out = _apply_rotation_and_composites({k: v.copy() for k, v in f.items()})
    assert np.allclose(out["htt_e"], f["dau1_e"] + f["dau2_e"])
    assert out["bjet1_e"][2] == 0.0 and out["bjet1_btag_df"][2] == -1.0  # bj_mask applied to event 2
    assert out["fatjet_e"][0] == 0.0  # fj_mask applied to event 0 (is_boosted=0)
    print("data.py smoke test OK")
