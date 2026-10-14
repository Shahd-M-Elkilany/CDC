"""Regression test: the Python port must reproduce Video.mcd (Annex B) exactly."""
import pytest

from cdc.models.snr import snr

ANNEX_B_INPUTS = dict(
    lam_min=0.500e-6, lam_max=0.885e-6, sun_elev_deg=30, rho_L=0.25, rho_D=0.20,
    tau_at=0.80, tau_os=0.60, D=0.155, f=0.860, dx=10e-6, dy=10e-6, nu_x=900,
    Kt=1, N_el=6000, Hn_ccd=4.0e-7, RQ=1.563e18, KA=3.2e-6, U_ccd_max=3.0,
    KU=3, TU=300, R_equ=10000, U_adc_max=1, p_adc=12, p_dp=8, Tx=0.14, Ty=0.22,
)

# Values printed in the Mathcad listing, Annex B pages 24-26
ANNEX_B_RESULTS = {
    "W_min": 0.236, "W_max": 0.652, "E_dir": 186.169, "E_dis": 20.447,
    "E_sum": 206.615, "R_L": 51.654, "R_D": 41.323, "E_L1": 0.201349,
    "E_D1": 0.161079, "H_L1": 2.237e-4, "H_D1": 1.79e-4, "Ne_L1": 3.497e4,
    "Ne_D1": 2.797e4, "U_ccd_L1": 0.112, "U_ccd_D1": 0.09, "U_amp_L1": 0.336,
    "U_amp_D1": 0.269, "mE": 0.111, "mPx": 0.016, "mPy": 0.024,
    "U_amp_Lx": 0.307, "U_amp_Dx": 0.297, "U_amp_Ly": 0.31, "U_amp_Dy": 0.295,
    "Un_F": 1.795e-3, "Un_CCD": 6.002e-4, "Un_AMP": 2.99e-5,
    "Un_ADC": 7.048e-5, "Un_DP": 1.057e-3, "Un": 2.203e-3,
    "mu_L": 152.3454, "mu_D": 121.876, "mu_x": 4.266, "mu_y": 6.703,
}


@pytest.mark.parametrize("key,expected", ANNEX_B_RESULTS.items())
def test_matches_mathcad(key, expected):
    r = snr(**ANNEX_B_INPUTS)
    # Mathcad shows 3-4 significant figures; allow for its display rounding
    assert r[key] == pytest.approx(expected, rel=6e-3, abs=5e-4 if key in ("mPx", "mPy") else 0), key
