"""System sheet: orbit and imaging conditions shared by every subsystem."""
import math

from cdc.framework import Param, Subsystem

MU = 3.986004418e14      # Earth gravitational parameter, m^3/s^2
R_E = 6378.137e3         # Earth equatorial radius, m
DAY_S = 86400.0


def model(p: dict) -> dict:
    h = p["altitude_km"] * 1e3
    r = R_E + h
    v = math.sqrt(MU / r)
    period = 2 * math.pi * math.sqrt(r ** 3 / MU)
    # worst-case eclipse (beta angle = 0), circular orbit, cylindrical shadow
    ecl_frac = math.asin(R_E / r) / math.pi
    return {
        "orbit_radius_km": r / 1e3,
        "orbital_velocity_ms": v,
        "ground_speed_ms": v * R_E / r,          # sub-satellite point speed
        "period_min": period / 60,
        "orbits_per_day": DAY_S / period,
        "eclipse_fraction": ecl_frac,
        "eclipse_time_min": ecl_frac * period / 60,
        "sunlight_time_min": (1 - ecl_frac) * period / 60,
    }


SYSTEM = Subsystem(
    name="system",
    title="System / Mission",
    owner_role="Systems engineer",
    inputs=[
        Param("altitude_km", 668, "km", "Orbit altitude (circular)", 200, 2000, "Orbit",
              "EgyptSat-1 class orbit; altitude reproduces its 7.8 m GSD with Video.mcd optics"),
        Param("sun_elevation_deg", 30, "deg", "Sun elevation angle over the imaged area", 10, 90,
              "Imaging conditions", "Video.mcd"),
        Param("albedo_light", 0.25, "-", "Albedo of light strip / uniform background", 0, 1,
              "Imaging conditions", "Video.mcd"),
        Param("albedo_dark", 0.20, "-", "Albedo of dark strip of the test pattern", 0, 1,
              "Imaging conditions", "Video.mcd"),
        Param("atm_transmission", 0.80, "-", "Atmospheric transmission coefficient (vertical)", 0, 1,
              "Imaging conditions", "Video.mcd"),
        Param("imaging_time_per_orbit_min", 10, "min", "Imaging time per orbit", 0, 100,
              "Operations", "placeholder"),
        Param("max_off_nadir_deg", 30, "deg", "Maximum off-nadir (roll) angle for imaging", 0, 60,
              "Operations", "placeholder"),
        Param("position_error_m", 20, "m", "On-board orbit position knowledge error (1σ)", 0, None,
              "Operations", "placeholder"),
        Param("lifetime_yr", 5, "yr", "Design lifetime", 0, 30, "Operations", "placeholder"),
    ],
    gets={},
    sends=[
        Param("orbit_radius_km", unit="km", desc="Orbit radius"),
        Param("orbital_velocity_ms", unit="m/s", desc="Orbital velocity"),
        Param("ground_speed_ms", unit="m/s", desc="Ground-track speed (no Earth rotation)"),
        Param("period_min", unit="min", desc="Orbital period"),
        Param("orbits_per_day", unit="-", desc="Orbits per day"),
        Param("eclipse_fraction", unit="-", desc="Worst-case eclipse fraction (β = 0)"),
        Param("eclipse_time_min", unit="min", desc="Worst-case eclipse duration"),
        Param("sunlight_time_min", unit="min", desc="Sunlit time per orbit"),
    ],
    model=model,
    checks=lambda p: (["Dark albedo must not exceed light albedo"]
                      if p["albedo_dark"] > p["albedo_light"] else []),
    notes="Two-body circular orbit, spherical Earth. Eclipse is the worst case (β = 0).",
)
