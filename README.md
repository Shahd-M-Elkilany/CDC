# CDC — Concurrent Design Center (license-free)

![tests](../../actions/workflows/tests.yml/badge.svg)

A concurrent design environment for Earth-observation mission design, built
only on free software (Python, Streamlit, SQLite). It replaces the Mathcad
worksheets: the Yuzhnoye `Video.mcd` signal/noise model (EGS YZH MAN 129 00)
is ported to Python and reproduces the Annex B results exactly
(µL = 152.35, µD = 121.88, µx = 4.27, µy = 6.70) — checked by CI on every push.

## Quick start

Requires Python 3.10+ and git.

```bash
git clone https://github.com/<you>/cdc.git
cd cdc
python -m venv .venv
# Windows:  .venv\Scripts\activate      Linux/macOS:  source .venv/bin/activate
pip install -e ".[dev]"
cdc serve
```

`cdc serve` prints a *Network URL* (e.g. `http://192.168.1.20:8501`). Everyone
on the lab network opens it in a browser — nothing to install on their PCs.
Each engineer types their name in the sidebar and works in their own subsystem
sheet.

`pip install -e .` installs the project in *editable* mode: edits to the model
files take effect on the next run, no reinstall needed.

## Working in VS Code

1. Open the folder, accept the recommended extensions (Python, Ruff).
2. `Ctrl+Shift+P` → **Python: Select Interpreter** → `.venv`.
3. **Run and Debug** (`F5`) has ready configurations:

| Configuration | What it does |
|---|---|
| CDC: run app (this PC only) | Starts the app on `localhost:8501` under the debugger — breakpoints in models and `app.py` work |
| CDC: serve to lab network | Same as `cdc serve` |
| CDC: evaluate baseline (CLI) | Runs every model once and prints all results |
| CDC: debug current test file | Runs the open test file under the debugger |

Tests also appear in the **Testing** panel. **Terminal → Run Task** has
*run tests*, *lint* and *check requirements*.

## Command line

```bash
cdc serve                        # web app for the lab network (port 8501)
cdc serve --local --port 8600    # only this PC
cdc eval                         # all results for the default inputs
cdc eval -s system.altitude_km=700 -s payload.aperture_m=0.2 -p payload.pan_gsd_m -p payload.pan_snr_x
cdc check --design baseline      # compliance table; exit code 1 if anything FAILs
cdc export --design baseline -o baseline.xlsx
```

`python -m cdc ...` works the same as `cdc ...`.

## Project structure

```
cdc/
├── pyproject.toml          # package, dependencies, `cdc` command, pytest + ruff config
├── src/cdc/
│   ├── cli.py              # `cdc` command (serve / eval / check / export)
│   ├── app.py              # web UI: master, subsystem, comparison, trade, options, log
│   ├── framework.py        # Param, Subsystem, Requirement
│   ├── engine.py           # runs sheets in dependency order, requirement checks, sweeps
│   ├── store.py            # master sheet (SQLite): get/send parameter, history, design options
│   ├── excel.py            # .xlsx export / import
│   └── models/             # one file per subsystem sheet
│       ├── snr.py          # Video.mcd SNR model (pure math)
│       ├── system.py  payload.py  adcs.py  power.py  mission.py
│       └── __init__.py     # subsystem list + example requirements
├── tests/                  # Annex B regression + master sheet behaviour
├── .vscode/                # run/debug configs, tasks, settings
├── .github/workflows/      # CI: lint + tests on Windows and Linux
└── data/                   # live master sheet (git-ignored, created on first run)
```

## How it maps to the design notes

| Note | In the tool |
|---|---|
| Master sheet with Sys, PS… sheets | **Master sheet** page: every parameter, its owner, who changed it and when |
| For each subsystem: input → models → results → outputs | **Subsystem sheet** page: *Inputs* (mine), *Get parameters*, *Send parameters* (results) |
| Get parameter: call parameters from another subsystem | `gets = {"altitude_km": "system.altitude_km"}` in each model file |
| Send parameter: send results to my sheet in the master; it reflects on other sheets | **📤 Send parameters to master sheet**; every sheet that gets them is recomputed in dependency order |
| Comparison sheet: alert on more-than / less-than depending on the nature of the parameter | Each parameter declares its nature (`better="higher"` for SNR, swath, coverage; `better="lower"` for GSD, location error, array area). A requirement is only a threshold → PASS / MARGINAL (<5 %) / FAIL with alerts |
| Assess how changing one parameter reflects on the models and results | **Trade & sensitivity** page: sweep any input, plot results against requirement lines |
| Alternative systems for system design & mission requirements | **Design options** page: clone the baseline, change it, compare side by side |
| Step #1 build models | `src/cdc/models/*.py` |

### Outputs already computed

- SNR: PAN (uniform background, test pattern ⟂ and ∥ to track), Blue, Green, Red, NIR
- GSD PAN / MS at nadir and at max off-nadir, swath, along-track sampling, line-rate match
- Reflection of pointing accuracy along / across track on the ground
- Captured scene percentage
- Ground location accuracy without refinement (along / across track)
- Daily coverage area, field of regard, slew time
- Orbit: period, ground speed, eclipse; power: solar array area, battery

**Not yet modelled** (MTF is an input for now): PAN / MS MTF from optics,
diffraction and detector; repeat orbit / revisit.

## Add a subsystem (thermal, comms, structure, …)

1. Copy `src/cdc/models/adcs.py` to e.g. `src/cdc/models/thermal.py`.
2. Fill in `inputs` (defaults, units, ranges), `gets` (what it needs from other
   sheets), `sends` (its results) and the `model(p)` function. Give each result
   that can carry a requirement its nature: `better="higher"` or `better="lower"`.
3. Add it to `SUBSYSTEMS` in `src/cdc/models/__init__.py`.
4. Add a test in `tests/`, run `pytest`, open a pull request — CI runs the checks.

## Use from Python / Jupyter

```python
from cdc.engine import evaluate
from cdc.store import MasterSheet

evaluate({"system.altitude_km": 700}).values["payload.pan_gsd_m"]   # what-if, nothing saved

ms = MasterSheet("data/cdc_master.db")
ms.get_parameter("baseline", "payload.pan_snr_x")                    # 4.266
ms.send_parameter("baseline", "payload.aperture_m", 0.2, user="Shahd")
```

## Data and backups

- The live design lives in `data/cdc_master.db` (override with `--db` or the
  `CDC_DB` environment variable). It is git-ignored: the repo holds the code
  and models, the database holds the team's design session.
- Back it up by copying the file, or snapshot a design with `cdc export`.
- Excel: Master sheet → **Export** gives an `.xlsx` (Master tab, one tab per
  subsystem, Comparison tab); edit inputs in the Master tab and **Import** them back.

## Default values

Parameters marked `Video.mcd` come from the worksheet. Everything marked
`placeholder` (MS band edges, ADCS accuracies, power figures, all
requirements) is an example to replace with your mission's numbers.
