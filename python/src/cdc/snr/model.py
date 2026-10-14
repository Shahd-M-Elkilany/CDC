"""
Signal/noise ratio of images from a CCD-line electro-optical system.

Stages 1-30 of section 5.2 of EGS YZH MAN 129 00 (the Video.mcd program),
one line per stage, names as in the document.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
from scipy.interpolate import CubicSpline

from cdc.snr.inputs import SNRInputs, validate

E_SC = 1400.0       # solar constant, W/m² (Annex B)
K_B = 1.38e-23      # Boltzmann constant, J/K (Annex B)

# Spectral distribution of the solar constant (Annex B, page 23):
# part of the solar constant falling within the wave length range 0..λ
SOLAR_LAMBDA = np.array([
    0.22, 0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38, 0.40, 0.41, 0.42,
    0.43, 0.44, 0.45, 0.46, 0.48, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80,
    0.90, 1.0, 1.1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0,
    8.0, 10.0]) * 1e-6
SOLAR_W = np.array([
    0, 0.001, 0.002, 0.005, 0.012, 0.023, 0.037, 0.055, 0.072, 0.091, 0.105,
    0.116, 0.133, 0.146, 0.161, 0.176, 0.206, 0.236, 0.308, 0.377, 0.44,
    0.495, 0.545, 0.59, 0.661, 0.718, 0.766, 0.804, 0.861, 0.899, 0.924,
    0.942, 0.966, 0.979, 0.991, 0.9954, 0.9973, 0.998, 0.9988, 0.9995])
# Mathcad cspline + interp = cubic spline with not-a-knot ends
_W = CubicSpline(SOLAR_LAMBDA, SOLAR_W, bc_type="not-a-knot")


def solar_fraction(lam: float) -> float:
    """W(λ): part of the solar constant falling within the wave length range 0..λ."""
    return float(_W(lam))


def in_band_solar_constant(lam_min: float, lam_max: float) -> float:
    """E_SC·(W(λmax) − W(λmin)), W/m²: the part of the 1400 W/m² inside the operating range.

    This is the absolute value behind stage 4: E_Edir = this × τAt^sec(zS) × cos(zS).
    """
    return E_SC * (solar_fraction(lam_max) - solar_fraction(lam_min))


def solar_spectral_irradiance(lam):
    """E_SC·dW/dλ, W/(m²·µm): the solar spectrum above the atmosphere implied by the table
    (derivative of the cubic spline; λ in m)."""
    return E_SC * _W.derivative()(lam) * 1e-6


def solar_table_steps():
    """Average spectral irradiance in each table interval, E_SC·ΔW/Δλ, W/(m²·µm).

    Read straight from the two arrays - no interpolation. Returns (λ_left, λ_right, value), λ in m.
    """
    return SOLAR_LAMBDA[:-1], SOLAR_LAMBDA[1:], E_SC * np.diff(SOLAR_W) / (np.diff(SOLAR_LAMBDA) * 1e6)


class InvalidInputs(ValueError):
    def __init__(self, problems: list[str]):
        super().__init__("Invalid SNR inputs:\n  - " + "\n  - ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class SNRResult:
    """Every stage value; the field comment gives the stage number."""
    zS_deg: float     # 1  zenith distance of the Sun, deg
    dt: float         # 2  line's exposure time, s
    W_min: float      # 3  part of solar constant 0..λmin
    W_max: float      # 3  part of solar constant 0..λmax
    E_Edir: float     # 4  irradiance by direct sun, W/m²
    E_Edis: float     # 5  irradiance by dispersed sun, W/m²
    E_sum: float      # 6  overall irradiance, W/m²
    R_L: float        # 7  radiant emittance, light strip, W/m²
    R_D: float        # 7  radiant emittance, dark strip, W/m²
    E_L1: float       # 8  focal-plane irradiance, ρL, W/m²
    E_D1: float       # 8  focal-plane irradiance, ρD, W/m²
    H_L1: float       # 9  radiant exposure, ρL, J/m²
    H_D1: float       # 9  radiant exposure, ρD, J/m²
    P_L1: float       # 10 energy on a photosite, ρL, J
    P_D1: float       # 10 energy on a photosite, ρD, J
    Ne_L1: float      # 11 electrons in a photosite, ρL
    Ne_D1: float      # 11 electrons in a photosite, ρD
    Uccd_L1: float    # 12 CCD-line output voltage, ρL, V
    Uccd_D1: float    # 12 CCD-line output voltage, ρD, V
    Uamp_L1: float    # 13 amplifier output voltage, ρL, V
    Uamp_D1: float    # 13 amplifier output voltage, ρD, V
    mE: float         # 14 test pattern modulation
    mPx: float        # 15 image modulation, strips ⟂ SC track
    mPy: float        # 16 image modulation, strips ∥ SC track
    Uamp_Lx: float    # 17 light strip ⟂ track, V
    Uamp_Dx: float    # 18 dark strip ⟂ track, V
    Uamp_Ly: float    # 19 light strip ∥ track, V
    Uamp_Dy: float    # 20 dark strip ∥ track, V
    Un_F: float       # 21 photon noise, V
    Un_CCD: float     # 22 photoreceiver noise, V
    Un_AMP: float     # 23 amplifier noise, V
    Un_ADC: float     # 24 ADC quantization noise, V
    Un_DP: float      # 25 digital processor quantization noise, V
    Un: float         # 26 overall noise, V
    mu_L: float       # 27 SNR, uniform background ρL (model a)
    mu_D: float       # 28 SNR, uniform background ρD (model a)
    mu_x: float       # 29 SNR, strips ⟂ SC track (model c)
    mu_y: float       # 30 SNR, strips ∥ SC track (model b)
    clipped: tuple[str, ...] = ()   # saturation applied in stages 12-13

    def to_dict(self) -> dict:
        return asdict(self)


def calculate(p: SNRInputs | None = None, check: bool = True) -> SNRResult:
    """Run stages 1-30 (Annex B inputs if p is None).

    Raises InvalidInputs if an input breaks section 6 (unless check=False).
    """
    p = SNRInputs() if p is None else p
    if check and (problems := validate(p)):
        raise InvalidInputs(problems)
    clipped = []

    zS = math.pi / 2 - math.radians(p.sun_elevation)                                  # 1
    dt = p.Kt / p.nu_x                                                                # 2
    W_min, W_max = solar_fraction(p.lam_min), solar_fraction(p.lam_max)               # 3
    E_Edir = E_SC * (W_max - W_min) * p.tau_At ** (1 / math.cos(zS)) * math.cos(zS)   # 4
    E_Edis = -math.log(p.tau_At) / math.cos(zS) * E_Edir * 3 / 128 * (11 + math.cos(2 * zS))  # 5
    E_sum = E_Edir + E_Edis                                                           # 6
    R_L, R_D = E_sum * p.rho_L, E_sum * p.rho_D                                       # 7
    k = p.tau_At * p.tau_Os * 0.25 * (p.D / p.f) ** 2
    E_L1, E_D1 = R_L * k, R_D * k                                                     # 8
    H_L1, H_D1 = E_L1 * dt, E_D1 * dt                                                 # 9
    P_L1, P_D1 = H_L1 * p.dx * p.dy, H_D1 * p.dx * p.dy                               # 10
    Ne_L1, Ne_D1 = P_L1 * p.RQ, P_D1 * p.RQ                                           # 11

    Uccd_L1, Uccd_D1 = Ne_L1 * p.KA, Ne_D1 * p.KA                                     # 12
    if Uccd_L1 > p.U_CCD_max:
        Uccd_L1 = p.U_CCD_max
        clipped.append("Uccd_L1 clipped at U_CCD_max (CCD saturation)")
    if Uccd_D1 > p.U_CCD_max:
        Uccd_D1 = p.U_CCD_max
        clipped.append("Uccd_D1 clipped at U_CCD_max (CCD saturation)")

    Uamp_L1, Uamp_D1 = Uccd_L1 * p.KU, Uccd_D1 * p.KU                                 # 13
    if Uamp_L1 > p.U_ADC_max:
        Uamp_L1 = p.U_ADC_max
        clipped.append("Uamp_L1 clipped at U_ADC_max (ADC input range)")
    if Uamp_D1 > p.U_ADC_max:
        Uamp_D1 = p.U_ADC_max
        clipped.append("Uamp_D1 clipped at U_ADC_max (ADC input range)")

    mE = (p.rho_L - p.rho_D) / (p.rho_L + p.rho_D)                                    # 14
    mPx = mE * p.Tx                                                                   # 15
    mPy = mE * p.Ty                                                                   # 16
    U_sum = Uamp_L1 + Uamp_D1
    Uamp_Lx = U_sum * (1 + mPx) / 2                                                   # 17
    Uamp_Dx = U_sum * (1 - mPx) / 2                                                   # 18
    Uamp_Ly = U_sum * (1 + mPy) / 2                                                   # 19
    Uamp_Dy = U_sum * (1 - mPy) / 2                                                   # 20

    Un_F = math.sqrt(Ne_L1) * p.KA * p.KU                                             # 21
    Un_CCD = p.Hn_CCD * p.dx * p.dy * p.RQ * p.KA * p.KU                              # 22
    Un_AMP = math.sqrt(4 * K_B * p.TU * p.R_equ * p.N_El * p.nu_x)                    # 23
    Un_ADC = p.U_ADC_max / (2 ** p.p_ADC * math.sqrt(12))                             # 24
    Un_DP = Un_ADC * (2 ** p.p_ADC / 2 ** p.p_DP - 1)                                 # 25
    Un = math.sqrt(Un_F ** 2 + Un_CCD ** 2 + Un_AMP ** 2 + (Un_ADC + Un_DP) ** 2)     # 26

    mu_L = Uamp_L1 / Un                                                               # 27
    mu_D = Uamp_D1 / Un                                                               # 28
    mu_x = (Uamp_Lx - Uamp_Dx) / Un                                                   # 29
    mu_y = (Uamp_Ly - Uamp_Dy) / Un                                                   # 30

    return SNRResult(
        math.degrees(zS), dt, W_min, W_max, E_Edir, E_Edis, E_sum, R_L, R_D, E_L1, E_D1,
        H_L1, H_D1, P_L1, P_D1, Ne_L1, Ne_D1, Uccd_L1, Uccd_D1, Uamp_L1, Uamp_D1,
        mE, mPx, mPy, Uamp_Lx, Uamp_Dx, Uamp_Ly, Uamp_Dy,
        Un_F, Un_CCD, Un_AMP, Un_ADC, Un_DP, Un, mu_L, mu_D, mu_x, mu_y, tuple(clipped))
