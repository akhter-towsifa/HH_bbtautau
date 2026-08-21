from __future__ import annotations
import os
from dataclasses import dataclass, field
import yaml

# Class order used throughout this package. Index 0 is the signal class; the
# remaining three are the backgrounds requested for this training. Note this
# differs from AN-25-103 Sec. 5.3, which only trains against TT/DY -- single
# Higgs is an addition on top of the AN for this pipeline.
CLASSES = ["HH", "TT", "DY", "SingleH"]
CLASS_INDEX = {name: i for i, name in enumerate(CLASSES)}

HH_SIGNAL_POINTS = [
    # (kl, kt, c2): kappa lambda scan with kt=1, c2=0
    ("0p00", "1p00", "0p00"),
    ("1p00", "1p00", "0p00"),
    ("2p45", "1p00", "0p00"),
    ("5p00", "1p00", "0p00"),
    # c2 scan with kl=1, kt=1
    ("1p00", "1p00", "1p00"),
    ("1p00", "1p00", "0p10"),
    ("1p00", "1p00", "0p35"),
    ("1p00", "1p00", "3p00"),
    ("1p00", "1p00", "m2p00"),
    # c2 scan at kl=0
    ("0p00", "1p00", "1p00"),
]
HH_META_PROCESS = "GluGlutoHHto2B2Tau"

def hh_dataset_name(kl: str, kt: str, c2: str) -> str:
    return f"{HH_META_PROCESS}_kl_{kl}_kt_{kt}_c2_{c2}"

# Background class -> process-group name(s) in bbtautau/config/{era}/processes.yaml.
# "TT" and "DY" are meta-groups (DY has no direct `datasets:`, only
# `sub_processes:` pointing at DY_M_10to50/DYto2E_M_50/DYto2Mu_M_50/DYto2Tau_M_50 --
# resolve_class_datasets() in data.py follows that recursively).
CLASS_PROCESS_GROUPS = {
    "TT": ["TT"],
    "DY": ["DY"],
    "SingleH": ["ggH", "VBFH", "VH", "ttH"],
}

# Eras used for training. NOTE: Run3_2025/Run3_2026 set reuse_mc_from_era:
# Run3_2024 in FLAF/config/Run3_{2025,2026}/global.yaml -- if their anaTuples
# are reprocessed copies of the same underlying MC events as Run3_2024,
# keeping all three here will multiply-count that MC in training. Kept as
# configured; verify before a real run.
ERAS = ["Run3_2022", "Run3_2022EE", "Run3_2023", "Run3_2023BPix", "Run3_2024", "Run3_2025", "Run3_2026"]

# Channel IDs, per channelDefinition in bbtautau/FLAF/config/{era}/global.yaml
# (confirmed against the Channel enum in FLAF/include/AnalysisTools.h, which
# encodes channelId = 10*leg1 + leg2 with Leg::e=1, Leg::mu=2, Leg::tau=3):
#   eTau=13, muTau=23, tauTau=33.
CHANNEL_ETAU = 13
CHANNEL_MUTAU = 23
CHANNEL_TAUTAU = 33
VALID_CHANNEL_IDS = (CHANNEL_ETAU, CHANNEL_MUTAU, CHANNEL_TAUTAU)

# Our own pair_type convention for this training (intentionally different from
# DNN_application.py's internal pairtype_map={23:0,13:1,33:2} -- this is a new
# PyTorch model, not required to match the old TF model's category numbering).
PAIRTYPE_MAP = {CHANNEL_ETAU: 0, CHANNEL_MUTAU: 1, CHANNEL_TAUTAU: 2}

# Categorical input features and their raw allowed values, in a fixed order.
# Used to build both nn.Embedding cardinalities (model.py) and value->index
# remapping tables (data.py). dau1_dm can be -1 (electron/muon leg); dau2_dm
# never is (always a hadronic tau).
CATEGORICAL_SPECS: dict[str, list[int]] = {
    "pair_type": [0, 1, 2],
    "dau1_dm": [-1, 0, 1, 10, 11],
    "dau2_dm": [0, 1, 10, 11],
    "dau1_charge": [-1, 1],
    "dau2_charge": [-1, 1],
    "is_boosted": [0, 1],
    "has_bjet_pair": [0, 1],
}


def categorical_index_maps() -> dict[str, dict[int, int]]:
    return {name: {v: i for i, v in enumerate(values)} for name, values in CATEGORICAL_SPECS.items()}


def categorical_cardinalities() -> dict[str, int]:
    return {name: len(values) for name, values in CATEGORICAL_SPECS.items()}


# The five four-vectors fed into the LBN (AN Sec. 5.3.3: N=5 particles).
LBN_OBJECTS = ["dau1", "dau2", "bjet1", "bjet2", "fatjet"]

# Continuous scalar features concatenated directly (not through the LBN): MET
# + its covariance, the two b-tag score triplets, and the four composite
# four-vectors (Htt, Hbb, HHbbtautau, FatJet+tautau) the AN table lists as
# explicit inputs so the network has a "proxy" for parent-particle origin.
EXTRA_CONTINUOUS_FEATURES = [
    "met_px", "met_py", "met_cov00", "met_cov01", "met_cov11",
    "bjet1_btag_df", "bjet1_cvsb", "bjet1_cvsl", "bjet1_hhbtag",
    "bjet2_btag_df", "bjet2_cvsb", "bjet2_cvsl", "bjet2_hhbtag",
    "htt_e", "htt_px", "htt_py", "htt_pz",
    "hbb_e", "hbb_px", "hbb_py", "hbb_pz",
    "htthbb_e", "htthbb_px", "htthbb_py", "htthbb_pz",
    "httfatjet_e", "httfatjet_px", "httfatjet_py", "httfatjet_pz",
]


@dataclass
class ModelConfig:
    embedding_dim: int = 5
    lbn_n_in: int = 5
    lbn_n_out: int = 10
    dense_n_blocks: int = 8
    dense_width: int = 128
    n_classes: int = len(CLASSES)
    dropout: float = 0.0  # AN Sec. 5.3.3 (GGF) uses no dropout, unlike the VBF net


@dataclass
class OptimConfig:
    initial_lr: float = 0.1
    lr_halve_every_n_epochs: int = 2
    batches_per_epoch: int = 5000
    weight_decay_factor: float = 500.0
    early_stop_patience: int = 10  # epochs without val-loss improvement


@dataclass
class KFoldConfig:
    n_folds: int = 5
    val_fraction: float = 0.25  # train:val = 3:1 of the 4 non-test folds
    n_seeds: int = 5  # per-fold ensemble size, matches existing "_SDx5" checkpoints
    split_seed: int = 42


@dataclass
class DataConfig:
    data_root: str = ""  # local/EOS directory containing AnaTupleMergeTask-style output
    eras: list[str] = field(default_factory=lambda: list(ERAS))
    # Absolute by default (via ANALYSIS_PATH, set by env.sh to the bbtautau/
    # checkout root -- same variable DNN_application.py itself relies on), so
    # this doesn't silently break depending on the caller's cwd the way a
    # plain relative "bbtautau/config" string would. Holds
    # {era}/{datasets,processes}.yaml.
    config_dir: str = field(
        default_factory=lambda: os.path.join(os.environ.get("ANALYSIS_PATH", "bbtautau"), "config")
    )
    batch_size: int = 4096
    class_weights: dict[str, float] = field(
        default_factory=lambda: {c: 1.0 / len(CLASSES) for c in CLASSES}
    )
    step_size: str = "50 MB"  # uproot.iterate step size, matches AnalysisCacheProducer.py
    # Confirmed against a real v2605 Run3_2022EE anaTuple; FLAF.Common.Utilities.
    # WorkingPointsTauVSjet.Medium.value == 5. Re-verify if other eras/versions differ.
    deep_tau_branch: str = "idDeepTau2018v2p5VSjet"
    deep_tau_medium_wp: int = 5


@dataclass
class TrainingConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    optim: OptimConfig = field(default_factory=OptimConfig)
    kfold: KFoldConfig = field(default_factory=KFoldConfig)
    data: DataConfig = field(default_factory=DataConfig)
    output_dir: str = "bbtautau/config/nn_models/ggf_pytorch"

    @classmethod
    def from_yaml(cls, path: str) -> TrainingConfig:
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        cfg = cls()
        for section in ("model", "optim", "kfold", "data"):
            if section in raw:
                sub = getattr(cfg, section)
                for key, value in raw[section].items():
                    setattr(sub, key, value)
        if "output_dir" in raw:
            cfg.output_dir = raw["output_dir"]
        return cfg
