"""Power sheet: solar array and battery sizing (SMAD method)."""
import math

from cdc.framework import Param, Subsystem

SOLAR_FLUX = 1367.0  # W/m^2


def model(p: dict) -> dict:
    period = p["eclipse_time_min"] + p["sunlight_time_min"]
    duty = min(1.0, p["imaging_time_per_orbit_min"] / period)
    load = p["bus_power_w"] + p["adcs_power_w"] + p["payload_power_w"] * duty
    Te, Td = p["eclipse_time_min"], p["sunlight_time_min"]
    # Array power needed in sunlight to run loads and recharge for eclipse
    p_sa = (load * Te / p["xe"] + load * Td / p["xd"]) / Td
    p_bol = SOLAR_FLUX * p["cell_efficiency"] * p["inherent_degradation"] * math.cos(
        math.radians(p["sun_incidence_deg"]))
    life_deg = (1 - p["degradation_per_yr"]) ** p["lifetime_yr"]
    p_eol = p_bol * life_deg
    batt_wh = load * (Te / 60) / (p["battery_dod"] * p["battery_efficiency"])
    return {
        "imaging_duty_cycle": duty,
        "orbit_avg_load_w": load,
        "solar_array_power_w": p_sa,
        "array_power_density_eol_wm2": p_eol,
        "solar_array_area_m2": p_sa / p_eol,
        "battery_capacity_wh": batt_wh,
    }


POWER = Subsystem(
    name="power",
    title="Power",
    owner_role="Power engineer",
    inputs=[
        Param("bus_power_w", 50, "W", "Bus (platform) average power excl. ADCS & payload", 0, None,
              "Loads", "placeholder"),
        Param("xd", 0.85, "-", "Path efficiency, daylight (direct energy transfer)", 0, 1, "Efficiencies", "SMAD"),
        Param("xe", 0.65, "-", "Path efficiency, eclipse (direct energy transfer)", 0, 1, "Efficiencies", "SMAD"),
        Param("cell_efficiency", 0.28, "-", "Solar cell efficiency (triple junction)", 0, 1, "Solar array", "placeholder"),
        Param("inherent_degradation", 0.77, "-", "Inherent degradation", 0, 1, "Solar array", "SMAD"),
        Param("sun_incidence_deg", 0, "deg", "Worst-case Sun incidence angle", 0, 89, "Solar array", "placeholder"),
        Param("degradation_per_yr", 0.005, "-", "Array degradation per year", 0, 1, "Solar array", "placeholder"),
        Param("battery_dod", 0.20, "-", "Battery depth of discharge", 0, 1, "Battery", "placeholder"),
        Param("battery_efficiency", 0.90, "-", "Battery-to-load transmission efficiency", 0, 1, "Battery", "SMAD"),
    ],
    gets={
        "eclipse_time_min": "system.eclipse_time_min",
        "sunlight_time_min": "system.sunlight_time_min",
        "imaging_time_per_orbit_min": "system.imaging_time_per_orbit_min",
        "lifetime_yr": "system.lifetime_yr",
        "payload_power_w": "payload.payload_power_w",
        "adcs_power_w": "adcs.adcs_power_w",
    },
    sends=[
        Param("imaging_duty_cycle", unit="-", desc="Payload duty cycle per orbit"),
        Param("orbit_avg_load_w", better="lower", unit="W", desc="Orbit-average load"),
        Param("solar_array_power_w", better="lower", unit="W", desc="Required solar array power (EOL)"),
        Param("array_power_density_eol_wm2", better="higher", unit="W/m²", desc="Array output per m² at EOL"),
        Param("solar_array_area_m2", better="lower", unit="m²", desc="Required solar array area"),
        Param("battery_capacity_wh", better="lower", unit="Wh", desc="Required battery capacity"),
    ],
    model=model,
    notes="SMAD (Wertz & Larson) sizing: orbit-average load applied in both daylight and eclipse.",
)
