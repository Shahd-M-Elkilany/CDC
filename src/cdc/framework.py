"""
Building blocks of a subsystem sheet.

Each subsystem sheet (System, Payload, Power, ...) has, as in the notes:
  inputs  - parameters the subsystem engineer owns and edits
  gets    - "Get parameter": values called from other subsystems' sheets
  model   - the mathematical model
  sends   - "Send parameter": results published to the master sheet,
            where every other sheet can get them

Parameters are addressed as "<subsystem>.<key>", e.g. "system.altitude_km".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Param:
    key: str
    default: float | None = None
    unit: str = ""
    desc: str = ""
    lo: float | None = None          # allowed range (warning when outside)
    hi: float | None = None
    group: str = ""                  # heading on the subsystem sheet
    source: str = ""                 # where the default value comes from
    better: str | None = None        # nature of the parameter: "higher" (e.g. SNR, swath)
                                     # or "lower" (e.g. GSD, location error) is acceptable


@dataclass
class Subsystem:
    name: str                        # short id used in parameter names
    title: str
    owner_role: str                  # e.g. "Payload engineer"
    inputs: list[Param]
    gets: dict[str, str]             # local name -> "<subsystem>.<key>"
    sends: list[Param]
    model: Callable[[dict], dict]    # (inputs + gets) -> dict with every send key
    checks: Callable[[dict], list[str]] | None = None   # extra sanity checks
    notes: str = ""

    def full(self, key: str) -> str:
        return f"{self.name}.{key}"

    @property
    def input_keys(self) -> list[str]:
        return [self.full(p.key) for p in self.inputs]

    @property
    def send_keys(self) -> list[str]:
        return [self.full(p.key) for p in self.sends]


@dataclass
class Requirement:
    """Threshold on a parameter. Whether a value must be above or below it is not
    stored here: it comes from the parameter's own nature (Param.better)."""
    param: str                       # "<subsystem>.<key>"
    value: float
    label: str = ""
    source: str = "example - replace with mission requirement"
    id: int | None = None


@dataclass
class Evaluation:
    values: dict[str, float]                       # every parameter, inputs + results
    warnings: dict[str, list[str]] = field(default_factory=dict)   # by subsystem
    details: dict[str, dict] = field(default_factory=dict)         # model intermediates
