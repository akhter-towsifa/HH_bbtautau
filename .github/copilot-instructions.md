# Copilot Instructions for HH_bbtautau

## Repository Overview

This repository implements the HH→bbττ analysis for the CMS experiment at CERN. It uses the **FLAF** (Flexible LAW-based Analysis Framework) with Luigi workflow management for high-energy physics data analysis.

**Key characteristics:**
- **Language**: Python (analysis code), C++ (physics algorithms), YAML (configuration)
- **Framework**: LAW (Luigi Analysis Framework) for task workflows
- **Purpose**: Search for Higgs boson pair production with bb and ττ final states
- **Data**: CMS Run2 (2016-2018) and Run3 (2022-2023) collision data

## Project Structure

```
HH_bbtautau/
├── AnaProd/              # AnaTuple production code (main analysis)
│   ├── anaTupleDef.py    # Variable definitions for analysis tuples
│   ├── baseline.py       # Baseline selection cuts
│   ├── interface.py      # Framework interface
│   └── NNInterface.py    # Neural network interface
├── Analysis/             # Analysis tasks and histogram production
│   ├── hh_bbtautau.py    # Main analysis class
│   ├── histTupleDef.py   # Histogram definitions
│   └── make_stackplots.py
├── Studies/              # Various analysis studies
├── config/               # Configuration files
│   ├── global.yaml       # Global configuration
│   ├── law.cfg           # LAW task configuration
│   ├── Run3_2022/        # Era-specific configs (samples, triggers, etc.)
│   └── ...               # Other era configs
├── include/              # C++ header files
├── docs/                 # MkDocs documentation source
├── FLAF/                 # Submodule: Core framework
├── StatInference/        # Submodule: Statistical inference
├── Corrections/          # Submodule: Physics corrections
└── env.sh                # Environment setup script
```

## Code Formatting Requirements

**All PRs must pass formatting checks.** The CI uses configuration from FLAF submodule:

### Python (Black)
```bash
pip install black
black --check --diff <file.py>
black <file.py>  # to auto-format
```

### YAML (yamllint)
Configuration: `FLAF/.yamllint`
```bash
pip install yamllint
yamllint -s -c FLAF/.yamllint <file.yaml>
```
Key rules:
- No document start markers required
- No line length limit
- 2-space indentation
- Spaces inside braces/brackets: `{ key: value }`, `[ item ]`

### C++ (clang-format)
Configuration: `FLAF/.clang-format`
```bash
clang-format --dry-run --Werror --style "file:FLAF/.clang-format" <file.cpp>
clang-format -i --style "file:FLAF/.clang-format" <file.cpp>  # to auto-format
```
Key style: Google-based, 120 column limit, 4-space indent

## CI/CD Workflows

Three GitHub workflows run on PRs:

1. **`formatting-check.yaml`**: Checks Python/YAML/C++ formatting
2. **`repo-sanity-checks.yaml`**: Repository size and binary file checks
3. **`trigger-flaf-integration.yaml`**: Integration tests (manual trigger via comment)

**Binary files**: Never commit binary files directly. Use Git LFS for large files.

## Configuration Files

### Key Configuration Locations
- **`config/global.yaml`**: Analysis-wide settings (channels, categories, cuts)
- **`config/law.cfg`**: LAW module definitions for tasks
- **`config/<ERA>/samples.yaml`**: Dataset samples per era
- **`config/<ERA>/triggers.yaml`**: Trigger paths per era
- **`config/user_custom.yaml`**: Local user overrides (gitignored)

### Supported Eras
- Run2: `Run2_2016`, `Run2_2016_HIPM`, `Run2_2017`, `Run2_2018`
- Run3: `Run3_2022`, `Run3_2022EE`, `Run3_2023`, `Run3_2023BPix`

## Making Code Changes

### Python Files (`.py`)
- Analysis logic in `AnaProd/` and `Analysis/`
- Use RDataFrame operations for data processing
- Follow existing patterns for defining variables
- Key files: `anaTupleDef.py`, `baseline.py`, `hh_bbtautau.py`

### Configuration Files (`.yaml`)
- Maintain consistent indentation (2 spaces)
- Use proper YAML list/dict syntax with spaces: `{ key: value }`
- Validate with yamllint before committing

### C++ Headers (`.h`)
- Located in `include/` directory
- Physics algorithm implementations
- Follow Google C++ style with 4-space indent

## Common Analysis Patterns

### Channel Definitions
Channels: `eTau`, `muTau`, `tauTau`, `eE`, `eMu`, `muMu`

### Category Structure
Categories defined in `config/global.yaml`:
- `inclusive`, `baseline`, `btag_shape`
- `res0b_cat3`, `res1b_cat3`, `res2b_cat3` (resolved b-tag categories)
- `boosted`, `boosted_cat3` (boosted topology)

### Adding New Variables
1. Define in `AnaProd/anaTupleDef.py` for AnaTuple stage
2. Or in `Analysis/histTupleDef.py` for histogram stage
3. Add to appropriate observable lists

## Submodules

The repository depends on several Git submodules:
- **FLAF**: Core framework (required for all operations)
- **Corrections**: Physics correction factors
- **StatInference**: Statistical inference tools
- **HHKinFit2**, **ClassicSVfit**, **SVfitTF**: Physics algorithms
- **HHbtag**: HH b-tagging tools
- **inference**: CERN GitLab inference code

**Note**: Submodules require SSH keys for CERN GitLab and GitHub.

## Important Notes

1. **Do not modify submodule contents** - Changes should go to respective repositories
2. **User config is gitignored** - `config/user_custom.yaml` for local settings
3. **Environment requires CMSSW** - Full setup needs CMS software environment
4. **Test locally before submitting** - Format checks will fail the CI

## Quick Reference

| File Type | Formatter | Config Location |
|-----------|-----------|-----------------|
| Python | Black | Default |
| YAML | yamllint | `FLAF/.yamllint` |
| C++ | clang-format | `FLAF/.clang-format` |

Trust these instructions. Only search the codebase if information here is incomplete or incorrect.
