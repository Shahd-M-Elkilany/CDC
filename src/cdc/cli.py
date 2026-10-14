"""
Command line entry point, installed as `cdc`.

    cdc serve                       start the web app for the team (LAN)
    cdc serve --local               only this PC (http://localhost:8501)
    cdc eval                        print every result for the baseline inputs
    cdc eval -s system.altitude_km=700 -p payload.pan_gsd_m
    cdc check --design baseline     requirement compliance (exit code 1 if any FAIL)
    cdc export --design baseline -o baseline.xlsx
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).with_name("app.py")
DEFAULT_DB = "data/cdc_master.db"


def _db_path(arg: str | None) -> str:
    path = Path(arg or os.environ.get("CDC_DB", DEFAULT_DB)).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def cmd_serve(a) -> int:
    env = {**os.environ, "CDC_DB": _db_path(a.db)}
    host = "localhost" if a.local else a.host
    print(f"Master sheet: {env['CDC_DB']}")
    cmd = [sys.executable, "-m", "streamlit", "run", str(APP),
           "--server.address", host, "--server.port", str(a.port),
           "--server.headless", "true", "--browser.gatherUsageStats", "false"]
    try:
        return subprocess.call(cmd, env=env)
    except KeyboardInterrupt:
        return 0


def _parse_sets(items: list[str]) -> dict[str, float]:
    out = {}
    for item in items or []:
        key, _, val = item.partition("=")
        if not val:
            raise SystemExit(f"--set expects name=value, got {item!r}")
        out[key.strip()] = float(val)
    return out


def cmd_eval(a) -> int:
    from cdc.engine import CATALOGUE, evaluate

    inputs = _parse_sets(a.set)
    unknown = [k for k in inputs if k not in CATALOGUE]
    if unknown:
        raise SystemExit(f"Unknown parameter(s): {', '.join(unknown)}")
    ev = evaluate(inputs)
    keys = a.param or [k for k, m in CATALOGUE.items() if m["kind"] == "result"]
    for k in keys:
        if k not in ev.values:
            raise SystemExit(f"Unknown parameter {k!r}")
        print(f"{k:42s} {ev.values[k]:>14.6g}  {CATALOGUE[k]['param'].unit}")
    for sub, warns in ev.warnings.items():
        for w in warns:
            print(f"WARNING [{sub}] {w}", file=sys.stderr)
    return 0


def cmd_check(a) -> int:
    from cdc.store import MasterSheet

    rows = MasterSheet(_db_path(a.db)).compliance(a.design)
    for c in rows:
        margin = "" if c["margin_pct"] is None else f"{c['margin_pct']:+7.1f} %"
        print(f"{c['status']:9s} {c['requirement']:38s} {c['value']:>12.5g} {c['accepted'][:1]} "
              f"{c['required']:<10g} {c['unit']:5s} {margin}")
    failing = sum(c["status"] == "FAIL" for c in rows)
    print(f"\n{len(rows)} requirements, {failing} failing")
    return 1 if failing else 0


def cmd_export(a) -> int:
    from cdc.excel import export_design
    from cdc.store import MasterSheet

    out = Path(a.output or f"CDC_{a.design}.xlsx")
    out.write_bytes(export_design(MasterSheet(_db_path(a.db)), a.design))
    print(f"Wrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cdc", description="Concurrent Design Center")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("serve", help="start the web app")
    s.add_argument("--host", default="0.0.0.0", help="0.0.0.0 = reachable from the lab network")
    s.add_argument("--port", type=int, default=8501)
    s.add_argument("--local", action="store_true", help="only reachable from this PC")
    s.add_argument("--db", help=f"master sheet file (default $CDC_DB or {DEFAULT_DB})")
    s.set_defaults(func=cmd_serve)

    e = sub.add_parser("eval", help="evaluate the models without the UI or database")
    e.add_argument("-s", "--set", action="append", metavar="NAME=VALUE", help="override an input")
    e.add_argument("-p", "--param", action="append", metavar="NAME", help="result(s) to print")
    e.set_defaults(func=cmd_eval)

    c = sub.add_parser("check", help="requirement compliance of a design in the master sheet")
    c.add_argument("--design", default="baseline")
    c.add_argument("--db")
    c.set_defaults(func=cmd_check)

    x = sub.add_parser("export", help="export a design to Excel")
    x.add_argument("--design", default="baseline")
    x.add_argument("-o", "--output")
    x.add_argument("--db")
    x.set_defaults(func=cmd_export)

    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
