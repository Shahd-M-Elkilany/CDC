"""
Registry of subsystem sheets. To add a subsystem (thermal, comms, structure...):
copy one of these modules, define inputs / gets / sends / model, and add it here.
"""
from cdc.framework import Requirement
from cdc.models.adcs import ADCS
from cdc.models.mission import MISSION
from cdc.models.payload import PAYLOAD
from cdc.models.power import POWER
from cdc.models.system import SYSTEM

SUBSYSTEMS = [SYSTEM, PAYLOAD, ADCS, POWER, MISSION]

# Example mission requirements (thresholds) - edit them on the Comparison sheet.
# Pass/fail direction comes from each parameter's `better` attribute.
DEFAULT_REQUIREMENTS = [
    Requirement("payload.pan_gsd_m", 8.0, "PAN GSD at nadir"),
    Requirement("payload.ms_gsd_m", 8.0, "MS GSD at nadir"),
    Requirement("payload.pan_swath_km", 45.0, "Swath width"),
    Requirement("payload.pan_snr_uniform", 100.0, "PAN SNR (uniform background)"),
    Requirement("payload.pan_snr_x", 4.0, "PAN SNR, test pattern ⟂ track"),
    Requirement("payload.pan_snr_y", 4.0, "PAN SNR, test pattern ∥ track"),
    Requirement("payload.blue_snr", 100.0, "Blue band SNR"),
    Requirement("payload.green_snr", 100.0, "Green band SNR"),
    Requirement("payload.red_snr", 100.0, "Red band SNR"),
    Requirement("payload.nir_snr", 100.0, "NIR band SNR"),
    Requirement("payload.along_track_sampling_m", 8.0, "Along-track sampling"),
    Requirement("mission.captured_scene_pct", 95.0, "Captured scene percentage"),
    Requirement("mission.ground_loc_acc_along_m", 200.0, "Ground location accuracy, along"),
    Requirement("mission.ground_loc_acc_across_m", 200.0, "Ground location accuracy, across"),
    Requirement("mission.pan_gsd_max_off_nadir_across_m", 12.0, "PAN GSD at max off-nadir"),
    Requirement("mission.daily_coverage_km2", 1.0e6, "Daily coverage area"),
    Requirement("adcs.time_to_max_off_nadir_s", 60.0, "Slew to max off-nadir"),
    Requirement("power.solar_array_area_m2", 2.0, "Solar array area"),
]
