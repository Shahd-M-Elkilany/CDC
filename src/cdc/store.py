"""
Master sheet: the single shared store every subsystem sheet reads from and
writes to. SQLite file, so it needs no server or licence; the web app (one
server on the lab network) is the only process that writes to it.

    ms = MasterSheet("data/cdc_master.db")
    ms.get_parameter("baseline", "payload.pan_gsd_m")
    ms.send_parameter("baseline", "system.altitude_km", 700, user="Shahd")

Supports several design options ("baseline", "option B", ...) for the
alternative-system trade studies.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from cdc.engine import CATALOGUE, DIRECTION_LABEL, check, default_inputs, direction, evaluate
from cdc.framework import Evaluation, Requirement
from cdc.models import DEFAULT_REQUIREMENTS

SCHEMA = """
CREATE TABLE IF NOT EXISTS designs (
    name TEXT PRIMARY KEY, note TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS inputs (
    design TEXT, param TEXT, value REAL, updated_by TEXT, updated_at TEXT,
    PRIMARY KEY (design, param));
CREATE TABLE IF NOT EXISTS results (
    design TEXT PRIMARY KEY, values_json TEXT, warnings_json TEXT, computed_at TEXT);
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT, design TEXT, param TEXT,
    old REAL, new REAL, user TEXT, at TEXT);
CREATE TABLE IF NOT EXISTS requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT, param TEXT, value REAL,
    label TEXT, source TEXT);
"""


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


class MasterSheet:
    def __init__(self, path: str = "data/cdc_master.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self._db() as db:
            db.executescript(SCHEMA)
            if not db.execute("SELECT 1 FROM designs").fetchone():
                self._create(db, "baseline", "Video.mcd / EgyptSat-1 class baseline", None)
            if not db.execute("SELECT 1 FROM requirements").fetchone():
                db.executemany(
                    "INSERT INTO requirements (param, value, label, source) VALUES (?,?,?,?)",
                    [(r.param, r.value, r.label, r.source) for r in DEFAULT_REQUIREMENTS])
        for d in self.designs():
            if self._cached(d) is None:
                self.recompute(d)

    @contextmanager
    def _db(self):
        con = sqlite3.connect(self.path, timeout=10)
        con.execute("PRAGMA journal_mode=WAL")
        try:
            yield con
            con.commit()
        finally:
            con.close()

    # ---------------------------------------------------------------- designs
    def _create(self, db, name, note, copy_from):
        src = self.inputs(copy_from) if copy_from else default_inputs()
        db.execute("INSERT INTO designs VALUES (?,?,?)", (name, note, _now()))
        db.executemany("INSERT INTO inputs VALUES (?,?,?,?,?)",
                       [(name, k, v, "default" if not copy_from else f"copy of {copy_from}", _now())
                        for k, v in src.items()])

    def designs(self) -> list[str]:
        with self._db() as db:
            return [r[0] for r in db.execute("SELECT name FROM designs ORDER BY created_at")]

    def design_notes(self) -> dict[str, str]:
        with self._db() as db:
            return dict(db.execute("SELECT name, note FROM designs"))

    def create_design(self, name: str, note: str = "", copy_from: str | None = "baseline"):
        with self._db() as db:
            self._create(db, name, note, copy_from)
        self.recompute(name)

    def delete_design(self, name: str):
        with self._db() as db:
            for t in ("designs", "inputs", "results", "history"):
                db.execute(f"DELETE FROM {t} WHERE {'name' if t == 'designs' else 'design'}=?", (name,))

    # ------------------------------------------------------------- parameters
    def inputs(self, design: str) -> dict[str, float]:
        vals = default_inputs()          # new parameters added to models get defaults
        with self._db() as db:
            vals.update(dict(db.execute("SELECT param, value FROM inputs WHERE design=?", (design,))))
        return {k: v for k, v in vals.items() if k in CATALOGUE}

    def input_meta(self, design: str) -> dict[str, tuple[str, str]]:
        with self._db() as db:
            return {p: (u, t) for p, u, t in db.execute(
                "SELECT param, updated_by, updated_at FROM inputs WHERE design=?", (design,))}

    def get_parameter(self, design: str, param: str) -> float:
        """Get parameter: read any input or result from the master sheet."""
        if param not in CATALOGUE:
            raise KeyError(f"Unknown parameter {param!r}")
        if CATALOGUE[param]["kind"] == "input":
            return self.inputs(design)[param]
        return self.results(design).values[param]

    def send_parameter(self, design: str, param: str, value: float, user: str = "anonymous"):
        """Send parameter: publish a value to the master sheet; every sheet updates."""
        self.send_parameters(design, {param: value}, user)

    def send_parameters(self, design: str, updates: dict[str, float], user: str = "anonymous") -> int:
        current = self.inputs(design)
        changed = 0
        with self._db() as db:
            for param, value in updates.items():
                if param not in CATALOGUE or CATALOGUE[param]["kind"] != "input":
                    raise ValueError(f"{param} is not an editable input (results are computed)")
                value = float(value)
                old = current.get(param)
                if old is not None and abs(value - old) <= 1e-12 * max(1.0, abs(old)):
                    continue
                db.execute("INSERT OR REPLACE INTO inputs VALUES (?,?,?,?,?)",
                           (design, param, value, user, _now()))
                db.execute("INSERT INTO history (design, param, old, new, user, at) VALUES (?,?,?,?,?,?)",
                           (design, param, old, value, user, _now()))
                changed += 1
        if changed:
            self.recompute(design)
        return changed

    # ---------------------------------------------------------------- results
    def recompute(self, design: str) -> Evaluation:
        ev = evaluate(self.inputs(design))
        with self._db() as db:
            db.execute("INSERT OR REPLACE INTO results VALUES (?,?,?,?)",
                       (design, json.dumps(ev.values), json.dumps(ev.warnings), _now()))
        return ev

    def _cached(self, design):
        with self._db() as db:
            return db.execute("SELECT values_json, warnings_json, computed_at FROM results WHERE design=?",
                              (design,)).fetchone()

    def results(self, design: str) -> Evaluation:
        row = self._cached(design)
        if row is None or set(json.loads(row[0])) != set(CATALOGUE):   # model set changed
            return self.recompute(design)
        return Evaluation(values=json.loads(row[0]), warnings=json.loads(row[1]))

    def last_change(self, design: str) -> tuple | None:
        with self._db() as db:
            return db.execute("SELECT user, param, at FROM history WHERE design=? ORDER BY id DESC LIMIT 1",
                              (design,)).fetchone()

    def history(self, design: str, limit: int = 500) -> list[tuple]:
        with self._db() as db:
            return db.execute("SELECT at, user, param, old, new FROM history WHERE design=? "
                              "ORDER BY id DESC LIMIT ?", (design, limit)).fetchall()

    # ----------------------------------------------------------- requirements
    def requirements(self) -> list[Requirement]:
        with self._db() as db:
            return [Requirement(p, v, lbl, src, i) for i, p, v, lbl, src in
                    db.execute("SELECT id, param, value, label, source FROM requirements ORDER BY id")]

    def set_requirements(self, reqs: list[Requirement]):
        for r in reqs:
            if r.param not in CATALOGUE:
                raise ValueError(f"Unknown parameter {r.param!r}")
            if direction(r.param) is None:
                raise ValueError(f"{r.param} has no defined nature (higher/lower is better); "
                                 "set `better=` on it in its model file first")
        with self._db() as db:
            db.execute("DELETE FROM requirements")
            db.executemany("INSERT INTO requirements (param, value, label, source) VALUES (?,?,?,?)",
                           [(r.param, r.value, r.label, r.source) for r in reqs])

    def compliance(self, design: str) -> list[dict]:
        vals = self.results(design).values
        rows = []
        for r in self.requirements():
            v = vals.get(r.param)
            c = check(r, v)
            rows.append(dict(requirement=r.label, parameter=r.param,
                             accepted=DIRECTION_LABEL.get(c["better"], "—"), required=r.value,
                             value=v, unit=CATALOGUE[r.param]["param"].unit, source=r.source, **c))
        return rows
