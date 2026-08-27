#!/usr/bin/env python3
"""The gen-process information the MC stitching selects on must reach the anaTuple.

`addGenProcessInfo` defines it from GenPart/LHEPart and appends it to the columns the
anaTuple stores, which is the only place the merge stage can read it back from: there the
nanoAOD collections are gone, while the same bin selections still have to be evaluated to
pick the cross-section and the denominator.
"""

import os
import sys
import unittest

ana_repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ana_repo, os.path.dirname(ana_repo)):
    if path not in sys.path:
        sys.path.insert(0, path)
os.environ.setdefault("FLAF_PATH", os.path.join(ana_repo, "FLAF"))

import ROOT

from AnaProd.genProcessInfo import addGenProcessInfo
from FLAF.Common.Utilities import DataFrameWrapper

ROOT.gROOT.SetBatch(True)

# statusFlags bits used by the gen-level identification: isHardProcess (7), isLastCopy (13).
HARD_LAST_COPY = (1 << 7) | (1 << 13)
LAST_COPY = 1 << 13

# Z -> tau tau, both taus hadronic: tau (pt 50) -> nu_tau (pt 20) + hadrons, so each
# visible pt is 30 > 20 and the gen filter accepts the event.
# t -> W(-> mu nu) b, tbar -> W(-> u dbar) bbar: exactly one leptonically decaying W.
# Drell-Yan to two muons at LHE level, back to back with pt 40 each.
NANOAOD = {
    "GenPart_pdgId": "ROOT::RVecI{15, -15, 16, -16, 6, -6, 24, 5, -24, -5, -13, 14, 2, -1}",
    "GenPart_statusFlags": (
        f"ROOT::RVecI{{{HARD_LAST_COPY}, {HARD_LAST_COPY}, 0, 0, {LAST_COPY}, "
        f"{LAST_COPY}, {LAST_COPY}, 0, {LAST_COPY}, 0, 0, 0, 0, 0}}"
    ),
    "GenPart_genPartIdxMother": "ROOT::RVecI{-1, -1, 0, 1, -1, -1, 4, 4, 5, 5, 6, 6, 8, 8}",
    "GenPart_pt": (
        "ROOT::RVecF{50.f, 50.f, 20.f, 20.f, 200.f, 200.f, 100.f, 100.f, 100.f, 100.f, "
        "50.f, 50.f, 50.f, 50.f}"
    ),
    "GenPart_eta": "ROOT::RVecF(14, 0.f)",
    "GenPart_phi": (
        "ROOT::RVecF{0.f, 3.14159f, 0.f, 3.14159f, 0.f, 3.14159f, 0.f, 3.14159f, 0.f, "
        "3.14159f, 0.f, 3.14159f, 0.f, 3.14159f}"
    ),
    "GenPart_mass": (
        "ROOT::RVecF{1.777f, 1.777f, 0.f, 0.f, 172.5f, 172.5f, 80.4f, 4.18f, 80.4f, "
        "4.18f, 0.105f, 0.f, 0.f, 0.f}"
    ),
    "LHEPart_pdgId": "ROOT::RVecI{13, -13}",
    "LHEPart_status": "ROOT::RVecI{1, 1}",
    "LHEPart_pt": "ROOT::RVecF{40.f, 40.f}",
    "LHEPart_eta": "ROOT::RVecF{0.f, 0.f}",
    "LHEPart_phi": "ROOT::RVecF{0.f, 3.14159f}",
    "LHEPart_mass": "ROOT::RVecF{0.105f, 0.105f}",
}


def make_dfw():
    df = ROOT.RDataFrame(4)
    for name, expression in NANOAOD.items():
        df = df.Define(name, expression)
    return DataFrameWrapper(df, [])


def values(dfw, column):
    return list(dfw.df.Take[dfw.df.GetColumnType(column)](column).GetValue())


class TestGenProcessInfo(unittest.TestCase):
    def test_dy_and_tautau_info_is_defined_and_stored(self):
        dfw = make_dfw()
        addGenProcessInfo(dfw, ["DY", "TauTau"])

        for column in ["DYInfo_flavor", "DYInfo_mll", "TauTauInfo_passFilter"]:
            self.assertIn(column, dfw.colToSave)
        for idx in (1, 2):
            for name in ("vis_type", "vis_pt", "vis_abseta"):
                self.assertIn(f"TauTauInfo_{name}{idx}", dfw.colToSave)
        # The intermediate structs are not storable branches.
        self.assertNotIn("_DYInfo", dfw.colToSave)
        self.assertNotIn("_TauTauInfo", dfw.colToSave)

        self.assertEqual(values(dfw, "DYInfo_flavor"), [13] * 4)
        self.assertAlmostEqual(values(dfw, "DYInfo_mll")[0], 80.0, delta=1.0)
        self.assertEqual(values(dfw, "TauTauInfo_passFilter"), [True] * 4)
        self.assertEqual(values(dfw, "TauTauInfo_vis_type1"), [2] * 4)  # hadronic
        self.assertAlmostEqual(values(dfw, "TauTauInfo_vis_pt1")[0], 30.0, delta=0.5)

    def test_tt_info_is_defined_and_stored(self):
        dfw = make_dfw()
        addGenProcessInfo(dfw, ["TT"])

        for column in ["TTInfo_nLeptonicW", "TTInfo_wDecay1", "TTInfo_wDecay2"]:
            self.assertIn(column, dfw.colToSave)
        self.assertNotIn("_TTInfo", dfw.colToSave)

        self.assertEqual(values(dfw, "TTInfo_nLeptonicW"), [1] * 4)
        self.assertEqual(sorted(set(values(dfw, "TTInfo_wDecay1"))), [13])  # W -> mu nu
        self.assertEqual(sorted(set(values(dfw, "TTInfo_wDecay2"))), [0])  # W -> q q'

    def test_nothing_is_defined_without_a_declaration(self):
        dfw = make_dfw()
        addGenProcessInfo(dfw, [])
        self.assertEqual(dfw.colToSave, [])

    def test_stored_columns_survive_a_snapshot(self):
        # What the merge stage will actually read: the branches have to be writable, which
        # the intermediate structs are not.
        dfw = make_dfw()
        addGenProcessInfo(dfw, ["DY", "TauTau", "TT"])
        out = os.path.join(
            os.environ.get("TMPDIR", "/tmp"), "test_gen_process_info.root"
        )
        dfw.df.Snapshot("Events", out, dfw.colToSave)
        try:
            snapshot = ROOT.TFile.Open(out)
            branches = {b.GetName() for b in snapshot.Get("Events").GetListOfBranches()}
            snapshot.Close()
        finally:
            os.remove(out)
        self.assertEqual(set(dfw.colToSave) - branches, set())


if __name__ == "__main__":
    unittest.main()
