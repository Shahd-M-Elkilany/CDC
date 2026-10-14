"""
Signal/noise ratio model for a CCD-line electro-optical imager.

Direct port of Yuzhnoye "Video.mcd" (EGS YZH MAN 129 00, Issue 1, 19/11/2003),
section 5.2, stages 1-30. Variable names follow the document so the two can be
read side by side. All inputs are SI (metres, seconds, volts, kelvin);
the Sun elevation angle is in degrees.

Verified against the worked example in Annex B (see tests/test_snr.py).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.interpolate import CubicSpline

# Spectral distribution of the solar constant (Annex B, page 23):
# fraction of the solar constant falling in the range 0..lambda.
_LAMBDA_M = np.array([
    0.22, 0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38, 0.40, 0.41, 0.42,
    0.43, 0.44, 0.45, 0.46, 0.48, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80,
    0.90, 1.0, 1.1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0,
    8.0, 10.0]) * 1e-6
_W_FRACTION = np.array([
    0, 0.001, 0.002, 0.005, 0.012, 0.023, 0.037, 0.055, 0.072, 0.091, 0.105,
    0.116, 0.133, 0.146, 0.161, 0.176, 0.206, 0.236, 0.308, 0.377, 0.44,
    0.495, 0.545, 0.59, 0.661, 0.718, 0.766, 0.804, 0.861, 0.899, 0.924,
    0.942, 0.966, 0.979, 0.991, 0.9954, 0.9973, 0.998, 0.9988, 0.9995])
# Mathcad cspline + interp; reproduces the Annex B values (Wmax = 0.652).
_W_SPLINE = CubicSpline(_LAMBDA_M, _W_FRACTION, bc_type="not-a-knot")

E_SC = 1400.0        # solar constant used in the original program, W/m^2
K_B = 1.38e-23       # Boltzmann constant, J/K

LAMBDA_RANGE_M = (0.22e-6, 10e-6)


def solar_fraction(lam_m: float) -> float:
    """W(lambda): fraction of the solar constant between 0 and lambda."""
    return float(_W_SPLINE(lam_m))


def snr(*,
        lam_min, lam_max,                      # operating band, m
        sun_elev_deg, rho_L, rho_D,            # scene & illumination
        tau_at,                                # atmosphere
        tau_os, D, f,                          # optics
        dx, dy, nu_x, Kt, N_el,                # CCD line
        Hn_ccd, RQ, KA, U_ccd_max,
        KU, TU, R_equ,                         # amplifier
        U_adc_max, p_adc,                      # ADC
        p_dp,                                  # digital processor
        Tx, Ty,                                # videopath MTF
        ) -> dict:
    """Run stages 1-30 and return every intermediate and final value."""
    r: dict = {}

    # 1-2  Sun zenith distance, exposure time
    zS = math.pi / 2 - math.radians(sun_elev_deg)
    dt = Kt / nu_x
    # 3    Part of solar constant inside the band
    W_min, W_max = solar_fraction(lam_min), solar_fraction(lam_max)
    # 4-6  Scene irradiance: direct, diffuse (Rayleigh indicatrix), total
    E_dir = E_SC * (W_max - W_min) * tau_at ** (1 / math.cos(zS)) * math.cos(zS)
    E_dis = (-math.log(tau_at) / math.cos(zS)) * E_dir * 3 / 128 * (11 + math.cos(2 * zS))
    E_sum = E_dir + E_dis
    # 7    Radiant emittance of light / dark strips
    R_L, R_D = E_sum * rho_L, E_sum * rho_D
    # 8    Focal-plane irradiance
    k_opt = tau_at * tau_os * 0.25 * (D / f) ** 2
    E_L1, E_D1 = R_L * k_opt, R_D * k_opt
    # 9-11 Exposure, energy per photosite, electrons
    H_L1, H_D1 = E_L1 * dt, E_D1 * dt
    P_L1, P_D1 = H_L1 * dx * dy, H_D1 * dx * dy
    Ne_L1, Ne_D1 = P_L1 * RQ, P_D1 * RQ
    # 12   CCD output voltage (clipped at saturation)
    U_ccd_L1 = min(Ne_L1 * KA, U_ccd_max)
    U_ccd_D1 = min(Ne_D1 * KA, U_ccd_max)
    # 13   Amplifier output voltage (clipped at ADC input limit)
    U_amp_L1 = min(U_ccd_L1 * KU, U_adc_max)
    U_amp_D1 = min(U_ccd_D1 * KU, U_adc_max)
    # 14-16 Modulation of the test pattern and of its image
    mE = (rho_L - rho_D) / (rho_L + rho_D)
    mPx, mPy = mE * Tx, mE * Ty
    # 17-20 Light/dark strip voltages after the videopath MTF
    U_sum = U_amp_L1 + U_amp_D1
    U_amp_Lx, U_amp_Dx = U_sum * (1 + mPx) / 2, U_sum * (1 - mPx) / 2
    U_amp_Ly, U_amp_Dy = U_sum * (1 + mPy) / 2, U_sum * (1 - mPy) / 2
    # 21-25 Noise sources referred to the amplifier output
    Un_F = math.sqrt(Ne_L1) * KA * KU                       # photon noise
    Un_CCD = Hn_ccd * dx * dy * RQ * KA * KU                # CCD read noise
    Un_AMP = math.sqrt(4 * K_B * TU * R_equ * N_el * nu_x)  # amplifier thermal
    Un_ADC = U_adc_max / (2 ** p_adc * math.sqrt(12))       # ADC quantisation
    Un_DP = Un_ADC * (2 ** p_adc / 2 ** p_dp - 1)           # requantisation
    # 26   Total RMS noise
    Un = math.sqrt(Un_F ** 2 + Un_CCD ** 2 + Un_AMP ** 2 + (Un_ADC + Un_DP) ** 2)
    # 27-30 Signal/noise ratios
    mu_L = U_amp_L1 / Un                 # model a), uniform background rho_L
    mu_D = U_amp_D1 / Un                 # model a), uniform background rho_D
    mu_x = (U_amp_Lx - U_amp_Dx) / Un    # model c), strips perpendicular to track
    mu_y = (U_amp_Ly - U_amp_Dy) / Un    # model b), strips parallel to track

    r.update(
        zS_deg=math.degrees(zS), dt=dt, W_min=W_min, W_max=W_max,
        E_dir=E_dir, E_dis=E_dis, E_sum=E_sum, R_L=R_L, R_D=R_D,
        E_L1=E_L1, E_D1=E_D1, H_L1=H_L1, H_D1=H_D1, P_L1=P_L1, P_D1=P_D1,
        Ne_L1=Ne_L1, Ne_D1=Ne_D1, U_ccd_L1=U_ccd_L1, U_ccd_D1=U_ccd_D1,
        U_amp_L1=U_amp_L1, U_amp_D1=U_amp_D1, mE=mE, mPx=mPx, mPy=mPy,
        U_amp_Lx=U_amp_Lx, U_amp_Dx=U_amp_Dx, U_amp_Ly=U_amp_Ly, U_amp_Dy=U_amp_Dy,
        Un_F=Un_F, Un_CCD=Un_CCD, Un_AMP=Un_AMP, Un_ADC=Un_ADC, Un_DP=Un_DP, Un=Un,
        mu_L=mu_L, mu_D=mu_D, mu_x=mu_x, mu_y=mu_y,
        ccd_saturated=Ne_L1 * KA > U_ccd_max,
        adc_saturated=U_ccd_L1 * KU > U_adc_max,
    )
    return r


def check_inputs(p: dict) -> list[str]:
    """Allowed ranges from section 6 of the document."""
    w = []
    lo, hi = LAMBDA_RANGE_M
    if not (lo <= p["lam_min"] <= p["lam_max"] <= hi):
        w.append("Band edges must satisfy 0.22 µm ≤ λmin ≤ λmax ≤ 10 µm")
    if not 10 <= p["sun_elev_deg"] <= 90:
        w.append("Sun elevation must be between 10° and 90°")
    if not 0 <= p["rho_D"] <= p["rho_L"] <= 1:
        w.append("Albedo must satisfy 0 ≤ ρ_dark ≤ ρ_light ≤ 1")
    for k in ("tau_at", "tau_os", "Kt", "Tx", "Ty"):
        if not 0 < p[k] <= 1:
            w.append(f"{k} must be in (0, 1]")
    if p["N_el"] < 2:
        w.append("Number of photosites must be ≥ 2")
    if p["p_dp"] > p["p_adc"]:
        w.append("Digital-processor bits must not exceed ADC bits")
    if p["KU"] < 1:
        w.append("Amplifier gain must be ≥ 1")
    return w
