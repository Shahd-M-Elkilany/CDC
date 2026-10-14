"""
Evaluates the whole design: runs every subsystem model in dependency order,
so a change on one sheet propagates to every sheet that gets its parameters.
Pure in-memory - used by the master sheet, sensitivity sweeps and scripts.
"""
from __future__ import annotations

from graphlib import TopologicalSorter

from cdc.framework import Evaluation, Requirement, Subsystem
from cdc.models import SUBSYSTEMS

BY_NAME = {s.name: s for s in SUBSYSTEMS}


def catalogue(subsystems: list[Subsystem] = SUBSYSTEMS) -> dict[str, dict]:
    """Every parameter in the design: owner, kind (input/result), unit, description."""
    cat = {}
    for s in subsystems:
        for p in s.inputs:
            cat[s.full(p.key)] = dict(subsystem=s.name, kind="input", param=p)
        for p in s.sends:
            cat[s.full(p.key)] = dict(subsystem=s.name, kind="result", param=p)
    return cat


CATALOGUE = catalogue()


def default_inputs(subsystems: list[Subsystem] = SUBSYSTEMS) -> dict[str, float]:
    return {s.full(p.key): p.default for s in subsystems for p in s.inputs}


def run_order(subsystems: list[Subsystem] = SUBSYSTEMS) -> list[Subsystem]:
    """Topological order: a sheet runs after every sheet whose results it gets."""
    producers = {k: s.name for s in subsystems for k in s.send_keys}
    graph = {s.name: {producers[src] for src in s.gets.values()
                      if src in producers and producers[src] != s.name}
             for s in subsystems}
    order = TopologicalSorter(graph).static_order()   # raises CycleError on loops
    by = {s.name: s for s in subsystems}
    return [by[n] for n in order]


def _range_warnings(s: Subsystem, values: dict) -> list[str]:
    w = []
    for p in s.inputs:
        v = values.get(s.full(p.key))
        if v is None:
            w.append(f"{p.key}: missing value")
            continue
        if p.lo is not None and v < p.lo or p.hi is not None and v > p.hi:
            w.append(f"{p.desc} = {v:g} outside allowed range [{p.lo}, {p.hi}]")
    return w


def evaluate(inputs: dict[str, float], subsystems: list[Subsystem] = SUBSYSTEMS) -> Evaluation:
    """Run all sheets. `inputs` maps "<subsystem>.<key>" -> value."""
    values = dict(default_inputs(subsystems))
    values.update({k: v for k, v in inputs.items() if v is not None})
    ev = Evaluation(values=values)
    for s in run_order(subsystems):
        local = {p.key: values[s.full(p.key)] for p in s.inputs}
        local.update({k: values[src] for k, src in s.gets.items()})      # Get parameter
        warns = _range_warnings(s, values)
        if s.checks:
            warns += s.checks(local)
        try:
            out = s.model(local)
        except Exception as exc:                                         # keep other sheets running
            warns.append(f"Model error: {exc!r}")
            out = {p.key: float("nan") for p in s.sends}
        ev.details[s.name] = out.pop("_details", {})
        warns += out.pop("_warnings", [])
        for p in s.sends:                                                # Send parameter
            values[s.full(p.key)] = out[p.key]
        ev.warnings[s.name] = warns
    return ev


DIRECTION_LABEL = {"higher": "≥  (higher is better)", "lower": "≤  (lower is better)"}


def direction(param: str) -> str | None:
    """Nature of a parameter: 'higher' or 'lower' is acceptable, None if not requirement-able."""
    return CATALOGUE[param]["param"].better


def requirement_params() -> list[str]:
    """Parameters that can carry a requirement (their nature is defined)."""
    return [k for k in CATALOGUE if direction(k)]


def check(req: Requirement, value: float) -> dict:
    """Compare a value to its requirement using the parameter's own nature:
    'higher' (SNR, swath...) fails when below; 'lower' (GSD, error...) fails when above.
    Margin > 0 means compliant."""
    better = direction(req.param)
    if better is None:
        return dict(status="NO DIRECTION", margin_pct=None, better=None)
    if value is None or value != value:
        return dict(status="NO DATA", margin_pct=None, better=better)
    if better == "higher":
        ok, margin = value >= req.value, (value - req.value) / abs(req.value or 1)
    else:
        ok, margin = value <= req.value, (req.value - value) / abs(req.value or 1)
    status = "PASS" if ok else "FAIL"
    if ok and margin < 0.05:
        status = "MARGINAL"            # compliant but < 5 % margin
    return dict(status=status, margin_pct=100 * margin, better=better)


def sweep(inputs: dict, param: str, values, outputs: list[str]) -> list[dict]:
    """Sensitivity: vary one input, return the chosen outputs for each value."""
    rows = []
    for v in values:
        ev = evaluate({**inputs, param: v})
        rows.append({param: v, **{o: ev.values[o] for o in outputs}})
    return rows
