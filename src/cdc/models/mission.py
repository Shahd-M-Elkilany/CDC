"""
Mission performance sheet: system-level outputs that combine several
subsystems (orbit, ADCS, payload). These are the "outputs" compared against
mission requirements on the comparison sheet.
"""
import math

from cdc.framework import Param, Subsystem


def model(p: dict) -> dict:
    h = p["altitude_km"] * 1e3
    th = math.radians(p["max_off_nadir_deg"])

    def ground(deg):                                  # angular error -> ground offset at nadir
        return h * math.tan(math.radians(deg))

    off_along = ground(p["pointing_accuracy_along_deg"])
    off_across = ground(p["pointing_accuracy_across_deg"])
    L = p["scene_length_km"] * 1e3
    W = p["pan_swath_km"] * 1e3
    captured = max(0.0, 1 - off_along / L) * max(0.0, 1 - off_across / W)

    pos = p["position_error_m"]
    gla_along = math.hypot(ground(p["knowledge_along_deg"]), pos)
    gla_across = math.hypot(ground(p["knowledge_across_deg"]), pos)

    imaging_s_day = p["imaging_time_per_orbit_min"] * 60 * p["orbits_per_day"]
    return {
        "pointing_offset_along_m": off_along,
        "pointing_offset_across_m": off_across,
        "captured_scene_pct": 100 * captured,
        "ground_loc_acc_along_m": gla_along,
        "ground_loc_acc_across_m": gla_across,
        "pan_gsd_max_off_nadir_across_m": p["pan_gsd_m"] / math.cos(th) ** 2,
        "pan_gsd_max_off_nadir_along_m": p["pan_gsd_m"] / math.cos(th),
        "ms_gsd_max_off_nadir_across_m": p["ms_gsd_m"] / math.cos(th) ** 2,
        "field_of_regard_km": 2 * h * math.tan(th) / 1e3 + p["pan_swath_km"],
        "daily_coverage_km2": p["pan_swath_km"] * p["ground_speed_ms"] / 1e3 * imaging_s_day,
    }


MISSION = Subsystem(
    name="mission",
    title="Mission performance",
    owner_role="Systems engineer",
    inputs=[
        Param("scene_length_km", 46.6, "km", "Scene length along track (requested scene)", 0, None,
              "Scene", "placeholder (square scene = swath)"),
    ],
    gets={
        "altitude_km": "system.altitude_km",
        "max_off_nadir_deg": "system.max_off_nadir_deg",
        "position_error_m": "system.position_error_m",
        "imaging_time_per_orbit_min": "system.imaging_time_per_orbit_min",
        "orbits_per_day": "system.orbits_per_day",
        "ground_speed_ms": "system.ground_speed_ms",
        "pointing_accuracy_along_deg": "adcs.pointing_accuracy_along_deg",
        "pointing_accuracy_across_deg": "adcs.pointing_accuracy_across_deg",
        "knowledge_along_deg": "adcs.knowledge_along_deg",
        "knowledge_across_deg": "adcs.knowledge_across_deg",
        "pan_gsd_m": "payload.pan_gsd_m",
        "ms_gsd_m": "payload.ms_gsd_m",
        "pan_swath_km": "payload.pan_swath_km",
    },
    sends=[
        Param("pointing_offset_along_m", better="lower", unit="m", desc="Ground reflection of pointing accuracy, along track"),
        Param("pointing_offset_across_m", better="lower", unit="m", desc="Ground reflection of pointing accuracy, across track"),
        Param("captured_scene_pct", better="higher", unit="%", desc="Share of the requested scene actually captured"),
        Param("ground_loc_acc_along_m", better="lower", unit="m", desc="Ground location accuracy w/o GCP refinement, along"),
        Param("ground_loc_acc_across_m", better="lower", unit="m", desc="Ground location accuracy w/o GCP refinement, across"),
        Param("pan_gsd_max_off_nadir_across_m", better="lower", unit="m", desc="PAN GSD across track at max off-nadir"),
        Param("pan_gsd_max_off_nadir_along_m", better="lower", unit="m", desc="PAN GSD along track at max off-nadir"),
        Param("ms_gsd_max_off_nadir_across_m", better="lower", unit="m", desc="MS GSD across track at max off-nadir"),
        Param("field_of_regard_km", better="higher", unit="km", desc="Accessible ground width with off-nadir roll"),
        Param("daily_coverage_km2", better="higher", unit="km²", desc="Daily imaged area (strip mode)"),
    ],
    model=model,
    notes=("First-order flat-Earth geometry at nadir. Captured scene % assumes the pointing error "
           "shifts the footprint by its full 3σ value. Ground location accuracy combines attitude "
           "knowledge and orbit position error (RSS), no ground control points."),
)
