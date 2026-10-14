# CDC — Concurrent Design Center, built step by step

A mission-design Concurrent Design Center for Earth-observation satellites,
built in small verified steps, with **two equivalent implementations**:
Python (no licence) and MATLAB (for labs with MATLAB on every PC). Both read the
same reference data and must give the same numbers and the same report.

```
reference/   shared test data (Annex B inputs, printed values, expected report)
python/      Python implementation   (pytest)
matlab/      MATLAB implementation   (buildtool)
```

## Roadmap

| Step | Content | Status |
|---|---|---|
| **1** | **SNR model** — EGS YZH MAN 129 00 (Video.mcd): 27 inputs, 30 stages, 4 signal/noise ratios | **done** |
| 2 | Payload geometry — GSD, swath, line-rate match; SNR per spectral band (PAN + MS) | next |
| 3 | Orbit — altitude → ground speed, period, eclipse; feeds the payload | |
| 4 | Subsystem sheets — inputs / get parameter / send parameter; shared master sheet | |
| 5 | Requirements and comparison sheet — pass/fail by the nature of each parameter | |
| 6 | More subsystems — ADCS, power, mission performance (captured scene, location accuracy) | |
| 7 | Interface — master / subsystem / comparison sheets, trade & sensitivity, design options, Excel | |

## Step 1 — the SNR model

Source: *Method of calculation of signal/noise ratio for images received by
electro-optical system of the Earth observation space system*, EGS YZH MAN 129 00,
Issue 1 (Yuzhnoye). Section 5.1 inputs, section 5.2 stages 1–30, section 6
allowed ranges, Annex B worked example.

**Verified:** with the Annex B inputs, every one of the 38 values Mathcad prints
(zS … µy) is reproduced to its last printed digit, in both languages (Python: 59 tests; MATLAB R2023a: 47 tests, run on a lab PC):

| µL | µD | µx | µy |
|---|---|---|---|
| 152.3454 | 121.8763 | 4.2657 | 6.7032 |

### Python

```bash
cd python
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"

python -m cdc snr                       # Annex B report
python -m cdc snr --set D=0.2 --set nu_x=1000
python -m cdc snr -i my_inputs.json     # {"inputs": {"D": 0.2, ...}} - missing names = Annex B
python -m cdc snr --json
python -m cdc snr --list-inputs
pytest
```

```python
from cdc.snr import SNRInputs, calculate, format_report
p = SNRInputs(D=0.2, nu_x=1000)        # any of the 27 inputs; others = Annex B
r = calculate(p)                        # r.mu_L, r.mu_x, ... every stage value
print(format_report(p, r))
```

### MATLAB (R2023a or newer, no toolboxes)

```matlab
cd matlab
runSnr                                  % Annex B report
runSnr("D", 0.2, "nu_x", 1000)
runSnr("my_inputs.json")
r = runSnr("D", 0.2);                   % results struct, no printing
runSnr("--list")
buildtool                               % lint + tests

p = cdc.snr.defaultInputs("D", 0.2);
r = cdc.snr.calculate(p);
disp(cdc.snr.report(p, r))
```

### Inputs (section 5.1, Annex B values)

| Group | Name | Symbol | Annex B | Unit |
|---|---|---|---|---|
| Operating range | `lam_min`, `lam_max` | λmin, λmax | 0.500e-6, 0.885e-6 | m |
| Imaged region | `sun_elevation`, `rho_L`, `rho_D` | βS, ρL, ρD | 30, 0.25, 0.20 | deg, –, – |
| Atmosphere | `tau_At` | τAt | 0.80 | – |
| Optical system | `tau_Os`, `D`, `f` | τOs, D, f | 0.60, 0.155, 0.860 | –, m, m |
| CCD-line | `dzy`, `dy`, `dx`, `nu_x`, `Kt`, `N_El`, `Hn_CCD`, `RQ`, `KA`, `U_CCD_max` | ∆zy … UCCDmax | 10e-6, 10e-6, 10e-6, 900, 1, 6000, 4e-7, 1.563e18, 3.2e-6, 3.0 | m, m, m, Hz, –, –, J/m², e⁻/J, V/e⁻, V |
| Amplifier | `KU`, `TU`, `R_equ` | KU, TU, Requ | 3, 300, 10000 | –, K, Ω |
| ADC | `U_ADC_max`, `p_ADC` | UADCmax, pADC | 1, 12 | V, bits |
| Digital processor | `p_DP` | pDP | 8 | bits |
| Videopath MTF | `Tx`, `Ty` | Tx, Ty | 0.14, 0.22 | – |

Inputs outside the section 6 ranges are rejected with a list of the broken rules
(e.g. sun elevation must be 10–90°, ρD ≤ ρL, pDP ≤ pADC, ∆y ≤ ∆zy). Saturation in
stages 12–13 (CCD voltage, ADC input range) is applied as in the document and
reported in the output.
