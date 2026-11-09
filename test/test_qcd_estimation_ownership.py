#!/usr/bin/env python3
"""The histograms that the QCD estimation clones must be freed once nothing refers to them.

FLAF's HistMergerFromHists runs AddQCDInHistDict -> QCD_Estimation with gROOT as the current
directory, once per channel, category, uncertainty source and scale. PyROOT (ROOT 6.40) does
not own what Clone() returns, so an undetached clone stays in gROOT's list until the job ends.
The live histograms are counted with ROOT's object table, which counts only the objects made
after it is switched on, so the estimation runs in a child process that switches it on first.

Needs ROOT: run inside the analysis environment (source env.sh).
"""

import json
import math
import os
import subprocess
import sys
import unittest

import pytest

pytestmark = pytest.mark.needs_root

ana_repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHILD = """
import gc, json, sys
sys.path[:0] = sys.argv[1:3]
import ROOT
ROOT.TObject.SetObjectStat(True)
from Analysis.QCD_estimation import (
    QCD_Estimation,
    QCD_Estimation_Inverted,
    QCD_Estimation_symm,
)

def live():
    gc.collect()
    ROOT.gObjectTable.UpdateInstCount()
    return ROOT.TH1D.Class().GetInstanceCount()

# Two bins per region: data, TT, DY.
REGIONS = {
    "OS_Iso": ([50.0, 30.0], [2.0, 2.0], [3.0, 1.0]),
    "OS_AntiIso": ([40.0, 20.0], [2.0, 2.0], [3.0, 1.0]),
    "SS_Iso": ([30.0, 10.0], [2.0, 2.0], [3.0, 1.0]),
    "SS_AntiIso": ([60.0, 40.0], [2.0, 2.0], [3.0, 1.0]),
}

# In a function, so that no name keeps a proxy of the inputs between the cases. The inputs are
# held as HistMergerFromHists holds them: in no directory, owned by Python.
def make_inputs(data_name):
    histograms = {}
    for process, index in ((data_name, 0), ("TT", 1), ("DY", 2)):
        for region, contents in REGIONS.items():
            hist = ROOT.TH1D(f"{process}_{region}", "", 2, 0.0, 2.0)
            hist.SetDirectory(0)
            for i, value in enumerate(contents[index]):
                hist.SetBinContent(i + 1, value)
            key = (("tauTau", region, "res2b"), ("Central", "Central"))
            histograms.setdefault(process, {})[key] = hist
    return histograms

cases = [
    ("QCD_Estimation", QCD_Estimation, "Data", ("Data", True)),
    ("QCD_Estimation_symm", QCD_Estimation_symm, "data", (True,)),
    ("QCD_Estimation_Inverted", QCD_Estimation_Inverted, "data", (True,)),
]
counts, values = {}, {}
for name, estimate, data_name, args in cases:
    histograms = make_inputs(data_name)
    start = live()
    held = []
    for _ in range(2):
        result = estimate(
            histograms, list(histograms), "tauTau", "res2b", "Central", "Central", *args
        )
        held.append(live() - start)
    values[name] = [
        [hist.GetBinContent(i) for i in range(4)] for hist in result[:3]
    ] + list(result[3:])
    del result
    counts[name] = {"held": held, "after": live() - start}
    del histograms
print(json.dumps({"counts": counts, "values": values}))
"""


def qcd_errors(n_num, n_den):
    return math.sqrt(n_num / n_den**2 + n_num**2 * n_den / n_den**4)


# Background-subtracted yields: OS_AntiIso [35, 17] (52), SS_Iso [25, 7] (32), SS_AntiIso 92.
os_anti_iso, ss_iso = [35.0, 17.0], [25.0, 7.0]
n_os_anti_iso, n_ss_iso, n_ss_anti_iso = 52.0, 32.0, 92.0


def scaled(contents, factor):
    return [0.0] + [value * factor for value in contents] + [0.0]


symm_norm = n_os_anti_iso * n_ss_iso / n_ss_anti_iso
symm_os = [value / n_os_anti_iso for value in os_anti_iso]
symm_ss = [value / n_ss_iso for value in ss_iso]
EXPECTED = {
    "QCD_Estimation": [
        scaled(ss_iso, n_os_anti_iso / n_ss_anti_iso),
        scaled(os_anti_iso, n_ss_iso / n_ss_anti_iso),
        scaled(os_anti_iso, n_ss_iso / n_ss_anti_iso),
        qcd_errors(n_os_anti_iso, n_ss_anti_iso),
        qcd_errors(n_ss_iso, n_ss_anti_iso),
    ],
    "QCD_Estimation_symm": [
        scaled([(a + b) / 2 for a, b in zip(symm_os, symm_ss)], symm_norm),
        scaled(symm_os, symm_norm),
        scaled(symm_ss, symm_norm),
        1.0,
        1.0,
    ],
    "QCD_Estimation_Inverted": [
        scaled(os_anti_iso, n_ss_iso / n_ss_anti_iso),
        scaled(ss_iso, n_os_anti_iso / n_ss_anti_iso),
        scaled(ss_iso, n_os_anti_iso / n_ss_anti_iso),
        qcd_errors(n_ss_iso, n_ss_anti_iso),
        qcd_errors(n_os_anti_iso, n_ss_anti_iso),
    ],
}


class TestQCDEstimationOwnership(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.child = subprocess.run(
            [sys.executable, "-c", CHILD, ana_repo, os.path.dirname(ana_repo)],
            capture_output=True,
            text=True,
            # FLAF's HistHelper reads it on import, as in HistMergerFromHists
            env=dict(os.environ, ANALYSIS_PATH=ana_repo),
        )

    def setUp(self):
        self.assertEqual(self.child.returncode, 0, self.child.stderr)
        self.result = json.loads(self.child.stdout.strip().splitlines()[-1])

    def test_clones_are_freed(self):
        for name, counts in self.result["counts"].items():
            with self.subTest(name=name):
                # the three histograms returned are held; the previous call's are not
                self.assertEqual(
                    counts["held"], [3, 3], f"{name} leaves clones that are never freed"
                )
                self.assertEqual(
                    counts["after"], 0, f"{name} leaves clones that are never freed"
                )

    def test_estimates_are_unchanged(self):
        self.assertEqual(set(self.result["values"]), set(EXPECTED))
        for name, expected in EXPECTED.items():
            got = self.result["values"][name]
            self.assertEqual(len(got), len(expected), name)
            for i, (got_hist, expected_hist) in enumerate(zip(got[:3], expected[:3])):
                for got_bin, expected_bin in zip(got_hist, expected_hist, strict=True):
                    with self.subTest(name=name, hist=i):
                        self.assertAlmostEqual(got_bin, expected_bin, places=12)
            for got_error, expected_error in zip(got[3:], expected[3:]):
                with self.subTest(name=name, error=expected_error):
                    self.assertAlmostEqual(got_error, expected_error, places=12)


if __name__ == "__main__":
    unittest.main()
