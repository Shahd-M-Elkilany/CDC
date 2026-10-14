"""ADCS sheet: pointing performance and agility."""
from cdc.framework import Param, Subsystem


def model(p: dict) -> dict:
    return {
        "time_to_max_off_nadir_s": p["max_off_nadir_deg"] / p["slew_rate_deg_s"] + p["settling_time_s"],
    }


ADCS = Subsystem(
    name="adcs",
    title="ADCS",
    owner_role="ADCS engineer",
    inputs=[
        Param("pointing_accuracy_along_deg", 0.1, "deg", "Pointing accuracy along track (3σ)", 0, 10,
              "Pointing", "placeholder"),
        Param("pointing_accuracy_across_deg", 0.1, "deg", "Pointing accuracy across track (3σ)", 0, 10,
              "Pointing", "placeholder"),
        Param("knowledge_along_deg", 0.01, "deg", "Attitude knowledge error along track (3σ)", 0, 10,
              "Pointing", "placeholder"),
        Param("knowledge_across_deg", 0.01, "deg", "Attitude knowledge error across track (3σ)", 0, 10,
              "Pointing", "placeholder"),
        Param("slew_rate_deg_s", 1.0, "deg/s", "Slew rate (degree / time)", 0, None, "Agility", "placeholder"),
        Param("settling_time_s", 10, "s", "Settling time after slew", 0, None, "Agility", "placeholder"),
        Param("adcs_power_w", 15, "W", "ADCS average power", 0, None, "Budgets", "placeholder"),
    ],
    gets={"max_off_nadir_deg": "system.max_off_nadir_deg"},
    sends=[
        Param("time_to_max_off_nadir_s", better="lower", unit="s", desc="Slew + settle time to max off-nadir angle"),
    ],
    model=model,
    notes="Rest-to-rest slew approximated as constant rate plus settling time.",
)
