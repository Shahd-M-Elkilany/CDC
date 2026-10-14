"""
Step 1 acceptance: the SNR model reproduces Annex B of EGS YZH MAN 129 00
to every digit Mathcad prints. Reads the shared reference/annex_b.json, so the
Python and MATLAB versions are checked against exactly the same numbers.
"""
import json
import os
import subprocess
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from cdc.snr import InvalidInputs, SNRInputs, calculate, format_report, solar_fraction, validate

REF = json.loads((Path(__file__).parents[2] / "reference" / "annex_b.json").read_text(encoding="utf-8"))


def half_ulp(printed: str) -> float:
    """Half a unit in the last printed digit: '2.237e-4' -> 5e-8, '152.3454' -> 5e-5."""
    exp = Decimal(printed).as_tuple().exponent
    return 0.5 * 10.0 ** exp


def test_defaults_are_annex_b_inputs():
    assert SNRInputs().to_dict() == pytest.approx(REF["inputs"])


@pytest.mark.parametrize("name,printed", REF["expected"].items())
def test_matches_every_printed_digit(name, printed):
    r = calculate(SNRInputs.from_dict(REF["inputs"]))
    value = getattr(r, name)
    assert abs(value - float(printed)) <= half_ulp(printed) * (1 + 1e-9), \
        f"{name}: {value:.10g} does not round to the printed {printed}"


def test_spline_matches_mathcad_cspline():
    assert solar_fraction(0.5e-6) == pytest.approx(0.236, abs=1e-12)        # table node
    assert solar_fraction(0.885e-6) == pytest.approx(0.6515550141, abs=1e-9)


def test_annex_b_inputs_are_valid():
    assert validate(SNRInputs()) == []


@pytest.mark.parametrize("change,fragment", [
    (dict(lam_min=0.1e-6), "lam_min"),
    (dict(lam_min=0.9e-6, lam_max=0.8e-6), "must not be greater than lam_max"),
    (dict(sun_elevation=5), "sun_elevation"),
    (dict(rho_D=0.3), "rho_D (dark strip)"),
    (dict(tau_At=0), "tau_At"),
    (dict(dy=12e-6), "dzy"),
    (dict(Kt=1.5), "Kt"),
    (dict(N_El=1), "N_El"),
    (dict(KU=0.5), "KU"),
    (dict(p_ADC=10.5), "p_ADC"),
    (dict(p_DP=14), "p_DP must not be greater than p_ADC"),
    (dict(Tx=1.2), "Tx"),
    (dict(D=-1), "D"),
])
def test_section_6_rules(change, fragment):
    problems = validate(replace(SNRInputs(), **change))
    assert any(fragment in p for p in problems), problems
    with pytest.raises(InvalidInputs):
        calculate(replace(SNRInputs(), **change))


def test_unknown_input_name_is_rejected():
    with pytest.raises(KeyError):
        SNRInputs.from_dict({"aperture": 0.2})


def test_saturation_clips_stage_12_and_13():
    # 10x the exposure saturates the ADC input range first (Uamp > 1 V)
    r = calculate(replace(SNRInputs(), nu_x=90))
    assert r.Uamp_L1 == 1.0 and r.Uamp_D1 == 1.0
    assert any("U_ADC_max" in c for c in r.clipped)
    # a CCD with a low saturation voltage clips at stage 12
    r = calculate(replace(SNRInputs(), U_CCD_max=0.1))
    assert r.Uccd_L1 == 0.1 and any("U_CCD_max" in c for c in r.clipped)


def test_report_has_all_sections():
    text = format_report(SNRInputs(), calculate())
    for part in ["INPUT DATA", "STAGES OF CALCULATION", "CALCULATION RESULTS",
                 "152.3454", "121.8763", "4.2657", "6.7032"]:
        assert part in text


def test_command_line():
    src = str(Path(__file__).resolve().parents[1] / "src")   # works with or without `pip install -e`
    env = {**os.environ, "PYTHONPATH": src + os.pathsep + os.environ.get("PYTHONPATH", "")}
    out = subprocess.run([sys.executable, "-m", "cdc", "snr", "--json", "--set", "D=0.2"],
                         capture_output=True, text=True, check=True, env=env).stdout
    data = json.loads(out)
    assert data["inputs"]["D"] == 0.2
    assert data["results"]["mu_L"] > 152.3454          # bigger aperture -> more signal


def test_report_is_the_shared_reference():
    """Python and MATLAB must print the same report, character for character."""
    expected = (Path(__file__).parents[2] / "reference" / "annex_b_report.txt").read_text(encoding="utf-8")
    assert format_report(SNRInputs(), calculate()) == expected
