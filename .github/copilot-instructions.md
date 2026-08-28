# HH_bbtautau — instructions for Copilot code review

The HH→bb̄ττ analysis, and the reference analysis of the [FLAF](https://github.com/cms-flaf/FLAF)
ecosystem: patterns land here first and are copied into HH_bbWW and H_mumu.

**Read `FLAF/.github/copilot-instructions.md` first.** It carries the framework invariants — law
task semantics, bundles, remote-storage caching, processor stages, concurrency — and the rules on
what a useful comment looks like and what not to flag. The rule that documentation ships in the same PR applies here too, and is restated below with the pages that matter for this repository. Everything there applies here. This file
adds only what is specific to this analysis.

## What costs the most here

A change to what the anaTuple stores or to which datasets a process declares can invalidate a
production that took days of grid time. Prioritise anything that (a) changes the stored columns,
(b) changes which datasets a process draws on, or (c) changes a normalisation.

## Analysis-specific invariants

### Stored gen-level information

- `AnaProd/genProcessInfo.py` writes the gen-level quantities the MC stitching selects on
  (`DYInfo_*`, `TauTauInfo_*`, `TTInfo_*`). The anaTuple drops `GenPart`/`LHEPart`, so anything a
  stitching bin selects on **must** be stored here or the merge stage cannot evaluate it.
- Which kinds a process gets is declared as `genInfo` in `config/<era>/processes.yaml`, next to
  the `processors` that consume them. **The two must agree per era.** A process that stitches on a
  quantity it does not declare fails in `AnaTupleMergeTask` with
  `use of undeclared identifier 'GenPart_…'`.
- **Adding a `genInfo` kind to an already-produced process means producing it again.** Flag any
  diff that widens `genInfo` without saying so.
- Store the quantities a derived flag is built from, not only the flag, so revisiting a filter
  definition does not mean going back to nanoAOD.

### Processes and datasets

- Meta processes (`is_meta_process`) expand via `meta_setup.dataset_name_pattern`. A dataset whose
  name the pattern does not match is **silently ignored** — check that a newly declared dataset
  is actually captured, and that the captured groups still yield the same `process_name` as the
  other eras.
- When one physics point has several datasets (an `_ext1` extension, or a `_LHEweights` variant),
  the process must carry the `*ext_processors` stitcher (`MCStitcher` with
  `useDatasetCrossSection`), or the point is normalised once per dataset and counted twice.
- `Run3_2025` and `Run3_2026` inherit the Run3_2024 MC list. A dataset edited for 2024 changes
  three eras.
- 2022–2023BPix read from the HLepRare skim; 2024+ resolve through Rucio/DAS. A dataset that
  exists in one is not guaranteed in the other.

### Per-era processor differences are deliberate

t̄t is stitched in 2022–2023BPix and **not** in 2024–2026, and DY→ττ uses `*DYtautau_processors`
in the first group and plain `*DY_processors` in the second. Do not "harmonise" them in review;
they follow the samples that exist.

### Integration test

`TestModel` runs two backgrounds — `custom_CI_Background_TT` and `custom_CI_Background_DY` — plus
one signal and one data process. **Each CI background must carry the same `processors:` and
`genInfo:` as the real `TT` / `DYto2Tau_M_50` process of that era**, since its purpose is to run
the stitching over the whole anaTuple → merge → histogram chain. A diff that changes a real
process's processors and leaves the CI counterpart behind removes the coverage without any test
turning red.

One dataset per CI process is enough; do not ask for more, it only makes CI slower.

The process names are also listed in `cms-flaf/FLAF_ci`, a **different repository**. Renaming or
adding a CI process here needs that updated in step, or every integration run fails with
`No processes selected in physics model 'TestModel'`.

### Jobs must not read from AFS

Model files and the like must come from the bundled analysis copy (`$ANALYSIS_PATH/...`), not from
an absolute path into AFS. A few thousand jobs each pulling a model over AFS gets batch submission
throttled. Note that bundles preserve symlinks verbatim, so a path that *looks* bundled can still
resolve back to AFS.

## Documentation must ship with the change

A PR must update the documentation **in the same PR** whenever it changes anything a user of the
framework can observe. Treat this as a review item of the same weight as correctness — docs
drifting from the code is the failure that motivated the current documentation, and a PR that
lands without them is not complete.

Ask, for every diff: does it add, rename or remove any of these?

- a task or DAG node, or the arguments/parameters of one;
- a command, a CLI flag, or the meaning of an existing one;
- a configuration key — `global.yaml`, `user_custom.yaml`, `processes.yaml`, `phys_models.yaml`,
  cross-sections, `fs_*` storage keys, bundle flavours, processor entries;
- a dataset, era, process or physics-model name;
- the environment, installation or setup steps;
- storage locations, output paths or log locations;
- a CI workflow, or how the integration test is triggered or configured;
- any behaviour a user relies on, including a default that changes.

If the answer is yes and the diff touches **no** documentation file, say so and name the page that
should have changed. If the author states the change is internal-only, that is a legitimate
answer — a pure refactor or bugfix with no user-visible effect is exempt — but it should be
stated in the PR, not left implicit.

Also flag the inverse: documentation edited to describe behaviour the diff does not implement, and
new pages added without being wired into `mkdocs.yml`'s `nav` (the build fails on that, but the
review should catch it first).

Where it goes:

- `docs/` in this repository for analysis-specific material (`analysis.md`, `setup.md`, `stat_inference.md`, `hhbtag_training.md`, …).
- **`FLAF/docs/` for anything framework-wide.** If the change alters shared behaviour, the
  documentation belongs there, in a companion PR to `cms-flaf/FLAF` — flag that it is missing
  rather than accepting an analysis-local description of a framework change.
- New pages must be added to `nav:` in `mkdocs.yml`; verified with `mkdocs build --strict`.

## Repository facts

Verified 2026-08-27; re-check before relying on any of it.

| | |
|---|---|
| Layout | `AnaProd/` (`anaTupleDef.py`, `baseline.py`, `genProcessInfo.py`), `Analysis/` (`hh_bbtautau.py`, `histTupleDef.py`), `config/`, `include/`, `Studies/`, `test/`, `docs/` |
| Submodules | `FLAF`, `Corrections`, `StatInference`, `inference`, `HHbtag`, `SyncTool`, `ClassicSVfit`, `SVfitTF`, `HHKinFit2` |
| Eras | Run 3: 2022, 2022EE, 2023, 2023BPix, 2024, 2025, 2026. Run 2 legacy configs also present |
| Configs | `config/global.yaml`, `config/processes.yaml` (shared processor anchors), `config/phys_models.yaml`, `config/<era>/{datasets,processes,triggers}.yaml` |
| Tests | `test/test_gen_process_info.py` (needs `ANALYSIS_PATH` and `FLAF_PATH` set) |
| Workflows | `formatting-check`, `repo-sanity-checks`, `test-setup-loading`, `deploy-docs`, `trigger-flaf-integration`. Formatting and era loading are checked automatically — do not comment on them |
| Docs | `docs/`, plus the shared framework docs in `FLAF/docs/`; see the documentation section above |
