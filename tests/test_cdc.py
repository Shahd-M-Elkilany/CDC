"""Master sheet behaviour: get/send, propagation, history, requirements, Excel round-trip."""
import pytest

from cdc.engine import evaluate, run_order
from cdc.excel import export_design, read_inputs
from cdc.store import MasterSheet


@pytest.fixture
def ms(tmp_path):
    return MasterSheet(str(tmp_path / "test.db"))


def test_baseline_reproduces_video_mcd(ms):
    assert ms.get_parameter("baseline", "payload.pan_snr_uniform") == pytest.approx(152.345, rel=1e-4)
    assert ms.get_parameter("baseline", "payload.pan_snr_x") == pytest.approx(4.266, rel=1e-3)


def test_run_order_respects_dependencies():
    order = [s.name for s in run_order()]
    assert order.index("system") < order.index("payload") < order.index("mission")
    assert order.index("adcs") < order.index("power")


def test_send_parameter_propagates_to_other_sheets(ms):
    gsd0 = ms.get_parameter("baseline", "payload.pan_gsd_m")
    area0 = ms.get_parameter("baseline", "power.solar_array_area_m2")
    ms.send_parameter("baseline", "system.altitude_km", 700, user="systems")
    assert ms.get_parameter("baseline", "payload.pan_gsd_m") == pytest.approx(gsd0 * 700 / 668)
    ms.send_parameter("baseline", "payload.payload_power_w", 80, user="payload")
    assert ms.get_parameter("baseline", "power.solar_array_area_m2") > area0
    hist = ms.history("baseline")
    assert [h[1] for h in hist] == ["payload", "systems"]


def test_results_are_not_editable(ms):
    with pytest.raises(ValueError):
        ms.send_parameter("baseline", "payload.pan_gsd_m", 1.0)


def test_design_options_are_independent(ms):
    ms.create_design("option B", copy_from="baseline")
    ms.send_parameter("option B", "payload.focal_length_m", 1.2)
    assert ms.get_parameter("option B", "payload.pan_gsd_m") < ms.get_parameter("baseline", "payload.pan_gsd_m")


def test_comparison_alerts(ms):
    status = {c["parameter"]: c["status"] for c in ms.compliance("baseline")}
    assert status["payload.pan_snr_uniform"] == "PASS"
    assert status["payload.blue_snr"] == "FAIL"          # narrow band vs SNR >= 100
    ms.send_parameter("baseline", "system.altitude_km", 800)
    status = {c["parameter"]: c["status"] for c in ms.compliance("baseline")}
    assert status["payload.pan_gsd_m"] == "FAIL"          # GSD grows past 8 m


def test_out_of_range_input_warns():
    ev = evaluate({"system.sun_elevation_deg": 5})
    assert any("Sun elevation" in w for w in ev.warnings["payload"])


def test_excel_round_trip(ms):
    data = export_design(ms, "baseline")
    inputs = read_inputs(data)
    assert inputs["payload.focal_length_m"] == pytest.approx(0.86)
    assert len(inputs) == len(ms.inputs("baseline"))


def test_direction_comes_from_parameter_nature():
    from cdc.engine import check
    from cdc.framework import Requirement
    # SNR: higher is better -> below threshold fails, above passes
    assert check(Requirement("payload.pan_snr_uniform", 100), 90)["status"] == "FAIL"
    assert check(Requirement("payload.pan_snr_uniform", 100), 150)["status"] == "PASS"
    # GSD: lower is better -> above threshold fails, below passes
    assert check(Requirement("payload.pan_gsd_m", 8), 9)["status"] == "FAIL"
    assert check(Requirement("payload.pan_gsd_m", 8), 5)["status"] == "PASS"


def test_requirement_on_parameter_without_nature_is_rejected(ms):
    from cdc.framework import Requirement
    with pytest.raises(ValueError):
        ms.set_requirements([Requirement("system.period_min", 100)])
