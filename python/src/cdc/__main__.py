"""
Command line:

    python -m cdc snr                     Annex B example, full report
    python -m cdc snr -i my_inputs.json   your inputs (JSON: any of the 27 names; others = Annex B)
    python -m cdc snr --set D=0.2 --set nu_x=1000
    python -m cdc snr --json              machine-readable results
    python -m cdc snr --list-inputs       the 27 input names, units and Annex B defaults
"""
from __future__ import annotations

import argparse
import json
import sys

from cdc.snr import InvalidInputs, SNRInputs, calculate, format_report


def snr_command(a) -> int:
    values = {}
    if a.input:
        with open(a.input, encoding="utf-8") as fh:
            data = json.load(fh)
        values.update(data.get("inputs", data))      # accepts {"inputs": {...}} or a flat object
    for item in a.set or []:
        name, _, v = item.partition("=")
        values[name.strip()] = float(v)
    if a.list_inputs:
        for s in SNRInputs.spec():
            print(f"{s['name']:<14} {s['symbol']:>8}  {s['default']:<11g} {s['unit']:<11} {s['description']}")
        return 0
    try:
        p = SNRInputs.from_dict(values)
        r = calculate(p)
    except (KeyError, InvalidInputs) as e:
        print(e, file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps({"inputs": p.to_dict(), "results": r.to_dict()}, indent=2))
    else:
        print(format_report(p, r), end="")
    return 0


def main(argv=None) -> int:
    # the report uses λ, ρ, τ, Ω ...: print UTF-8 even on consoles with a legacy code page (e.g. cp1256)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="cdc", description="Concurrent Design Center")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snr", help="signal/noise ratio (EGS YZH MAN 129 00)")
    s.add_argument("-i", "--input", help="JSON file with inputs")
    s.add_argument("-s", "--set", action="append", metavar="NAME=VALUE", help="override one input")
    s.add_argument("--json", action="store_true", help="print JSON instead of the report")
    s.add_argument("--list-inputs", action="store_true", help="list the 27 inputs")
    s.set_defaults(func=snr_command)
    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
