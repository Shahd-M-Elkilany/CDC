"""Plain-text report laid out like Annex B: input data, stages 1-30, calculation results."""
from __future__ import annotations

from cdc.snr.inputs import GROUPS, SNRInputs
from cdc.snr.model import SNRResult

# (stage, symbol, result field, description, unit) - section 5.2 order
STAGES = [
    (1, "zS", "zS_deg", "Zenith distance of the Sun", "deg"),
    (2, "∆t", "dt", "Line's exposure time", "s"),
    (3, "Wmin", "W_min", "Part of solar constant within 0..λmin", ""),
    (3, "Wmax", "W_max", "Part of solar constant within 0..λmax", ""),
    (4, "EEdir", "E_Edir", "Region's irradiance with direct solar irradiation", "W/m²"),
    (5, "EEdis", "E_Edis", "Region's irradiance with dispersed solar irradiation", "W/m²"),
    (6, "EΣ", "E_sum", "Overall irradiance of a region", "W/m²"),
    (7, "RL", "R_L", "Radiant emittance of a test pattern's light strip", "W/m²"),
    (7, "RD", "R_D", "Radiant emittance of a test pattern's dark strip", "W/m²"),
    (8, "EL1", "E_L1", "Irradiance in photoreceiver plane, uniform background ρL", "W/m²"),
    (8, "ED1", "E_D1", "Irradiance in photoreceiver plane, uniform background ρD", "W/m²"),
    (9, "HL1", "H_L1", "Photoreceiver plane's exposure, ρL", "J/m²"),
    (9, "HD1", "H_D1", "Photoreceiver plane's exposure, ρD", "J/m²"),
    (10, "PL1", "P_L1", "Irradiation energy on a photosite, ρL", "J"),
    (10, "PD1", "P_D1", "Irradiation energy on a photosite, ρD", "J"),
    (11, "NeL1", "Ne_L1", "Number of electrons in a photosite, ρL", ""),
    (11, "NeD1", "Ne_D1", "Number of electrons in a photosite, ρD", ""),
    (12, "UccdL1", "Uccd_L1", "Voltage on the output of CCD-line, ρL", "V"),
    (12, "UccdD1", "Uccd_D1", "Voltage on the output of CCD-line, ρD", "V"),
    (13, "UampL1", "Uamp_L1", "Voltage on the output of amplifier, ρL", "V"),
    (13, "UampD1", "Uamp_D1", "Voltage on the output of amplifier, ρD", "V"),
    (14, "mE", "mE", "Modulation of the test pattern in the region", ""),
    (15, "mPx", "mPx", "Image modulation, strips perpendicular to SC track", ""),
    (16, "mPy", "mPy", "Image modulation, strips parallel to SC track", ""),
    (17, "UampLx", "Uamp_Lx", "Amplifier output, light strip perpendicular to track", "V"),
    (18, "UampDx", "Uamp_Dx", "Amplifier output, dark strip perpendicular to track", "V"),
    (19, "UampLy", "Uamp_Ly", "Amplifier output, light strip parallel to track", "V"),
    (20, "UampDy", "Uamp_Dy", "Amplifier output, dark strip parallel to track", "V"),
    (21, "UnF", "Un_F", "Photon noise (RMS) at amplifier output", "V"),
    (22, "UnCCD", "Un_CCD", "Photoreceiver noise (RMS) at amplifier output", "V"),
    (23, "UnAMP", "Un_AMP", "Amplifier noise (RMS)", "V"),
    (24, "UnADC", "Un_ADC", "ADC quantization noise (RMS), at amplifier output", "V"),
    (25, "UnDP", "Un_DP", "Digital processor quantization noise (RMS)", "V"),
    (26, "Un", "Un", "Overall noise (RMS) at amplifier output", "V"),
]

RESULTS = [
    (27, "µL", "mu_L", "Uniform background with albedo ρL (model a)"),
    (28, "µD", "mu_D", "Uniform background with albedo ρD (model a)"),
    (29, "µx", "mu_x", "Test pattern, strips perpendicular to SC track (model c)"),
    (30, "µy", "mu_y", "Test pattern, strips parallel to SC track (model b)"),
]


def _num(v) -> str:
    return f"{v:.6g}"


def format_report(p: SNRInputs, r: SNRResult) -> str:
    out = ["SIGNAL/NOISE RATIO  -  EGS YZH MAN 129 00 (Video.mcd method)", ""]
    out.append("INPUT DATA")
    spec = SNRInputs.spec()
    for g in GROUPS:
        out.append(f"  {g}")
        for s in (s for s in spec if s["group"] == g):
            out.append(f"    {s['description']:<70} {s['symbol']:>8} = "
                       f"{_num(getattr(p, s['name'])):>11} {s['unit']}")
    out += ["", "STAGES OF CALCULATION (section 5.2)"]
    for n, sym, key, desc, unit in STAGES:
        out.append(f"  {n:>2}  {desc:<58} {sym:>7} = {_num(getattr(r, key)):>11} {unit}")
    out += ["", "CALCULATION RESULTS - signal/noise ratio"]
    for n, sym, key, desc in RESULTS:
        out.append(f"  {n:>2}  {desc:<58} {sym:>7} = {getattr(r, key):>11.4f}")
    for c in r.clipped:
        out.append(f"  note: {c}")
    return "\n".join(line.rstrip() for line in out) + "\n"
