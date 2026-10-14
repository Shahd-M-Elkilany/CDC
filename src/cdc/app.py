"""
Concurrent Design Center - web app.

Start it with `cdc serve` (see cli.py); teammates open http://<host-ip>:8501.
The master sheet file is taken from $CDC_DB (set by `cdc serve`).
"""
from __future__ import annotations

import os

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from cdc.engine import (
    BY_NAME,
    CATALOGUE,
    DIRECTION_LABEL,
    direction,
    evaluate,
    requirement_params,
    run_order,
    sweep,
)
from cdc.excel import export_design, read_inputs
from cdc.framework import Requirement
from cdc.models import SUBSYSTEMS
from cdc.store import MasterSheet

st.set_page_config(page_title="CDC - Mission Design", page_icon="🛰️", layout="wide")

STATUS_COLOR = {"PASS": "#c6efce", "MARGINAL": "#ffeb9c", "FAIL": "#ffc7ce", "NO DATA": "#d9d9d9"}


@st.cache_resource
def master() -> MasterSheet:
    return MasterSheet(os.environ.get("CDC_DB", "data/cdc_master.db"))


ms = master()


def unit(p):
    return CATALOGUE[p]["param"].unit


def desc(p):
    return CATALOGUE[p]["param"].desc


def fmt(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:.4g}"


def status_style(col):
    return [f"background-color: {STATUS_COLOR.get(v, '')}" for v in col]


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.title("🛰️ CDC")
    user = st.text_input("Your name / role", value=st.session_state.get("user", ""),
                         placeholder="e.g. Shahd - payload")
    st.session_state["user"] = user
    designs = ms.designs()
    design = st.selectbox("Design option", designs,
                          index=designs.index(st.session_state.get("design", designs[0]))
                          if st.session_state.get("design") in designs else 0)
    st.session_state["design"] = design
    page = st.radio("Sheet", ["Master sheet", "Subsystem sheet", "Comparison sheet",
                              "Trade & sensitivity", "Design options", "Change log"])

    lc = ms.last_change(design)
    if lc:
        st.caption(f"Last change: **{lc[1]}** by {lc[0]} at {lc[2]}")
    if st.button("🔄 Refresh from master sheet", width="stretch"):
        st.rerun()

ev = ms.results(design)
vals = ev.values
compliance = ms.compliance(design)
n_fail = sum(c["status"] == "FAIL" for c in compliance)
n_marg = sum(c["status"] == "MARGINAL" for c in compliance)
n_warn = sum(len(w) for w in ev.warnings.values())


def alert_banner():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Requirements", len(compliance))
    c2.metric("❌ Failing", n_fail)
    c3.metric("⚠️ Marginal (<5 %)", n_marg)
    c4.metric("Model warnings", n_warn)


# ============================================================== MASTER SHEET
if page == "Master sheet":
    st.header(f"Master sheet — {design}")
    st.caption("Every parameter of the design. Inputs are owned by one subsystem sheet; "
               "results are computed by the models and sent here automatically.")
    alert_banner()

    meta = ms.input_meta(design)
    rows = []
    for name, m in CATALOGUE.items():
        p = m["param"]
        by, at = meta.get(name, ("", "")) if m["kind"] == "input" else ("model", "")
        rows.append({"Subsystem": BY_NAME[m["subsystem"]].title, "Parameter": name, "Kind": m["kind"],
                     "Value": vals.get(name), "Unit": p.unit, "Description": p.desc,
                     "Accepted if": DIRECTION_LABEL.get(p.better, ""), "Source": p.source,
                     "Updated by": by, "Updated at": at})
    df = pd.DataFrame(rows)
    c1, c2, c3 = st.columns([2, 2, 3])
    subs = c1.multiselect("Subsystem", [s.title for s in SUBSYSTEMS])
    kinds = c2.multiselect("Kind", ["input", "result"])
    q = c3.text_input("Search", placeholder="gsd, snr, power ...")
    if subs:
        df = df[df.Subsystem.isin(subs)]
    if kinds:
        df = df[df.Kind.isin(kinds)]
    if q:
        df = df[df.Parameter.str.contains(q, case=False) | df.Description.str.contains(q, case=False)]
    st.dataframe(df, hide_index=True, width="stretch", height=600,
                 column_config={"Value": st.column_config.NumberColumn(format="%.5g")})

    st.subheader("Excel")
    c1, c2 = st.columns(2)
    c1.download_button("⬇️ Export master sheet (.xlsx)", export_design(ms, design),
                       file_name=f"CDC_{design}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    up = c2.file_uploader("⬆️ Import edited inputs (Master tab of an exported file)", type="xlsx")
    if up is not None and c2.button("Send imported inputs to master sheet"):
        n = ms.send_parameters(design, read_inputs(up.getvalue()), user or "excel import")
        st.success(f"{n} input(s) changed — all sheets recomputed.")
        st.rerun()

# =========================================================== SUBSYSTEM SHEET
elif page == "Subsystem sheet":
    titles = {s.title: s for s in SUBSYSTEMS}
    sub = titles[st.selectbox("My sheet", list(titles))]
    st.header(f"{sub.title} sheet — {design}")
    st.caption(f"Owner: {sub.owner_role}.  {sub.notes}")

    for w in ev.warnings.get(sub.name, []):
        st.warning(w)

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Inputs  (my parameters)")
        inp = pd.DataFrame([dict(Parameter=p.key, Value=vals[sub.full(p.key)], Unit=p.unit,
                                 Description=p.desc, Group=p.group, Source=p.source)
                            for p in sub.inputs])
        edited = st.data_editor(
            inp, hide_index=True, width="stretch", key=f"ed_{sub.name}_{design}",
            disabled=["Parameter", "Unit", "Description", "Group", "Source"],
            column_config={"Value": st.column_config.NumberColumn(format="%.6g")},
            height=min(40 + 35 * len(inp), 700))
        changes = {sub.full(r.Parameter): r.Value for r in edited.itertuples()
                   if r.Value != vals[sub.full(r.Parameter)]}
        if changes:
            # live preview before publishing
            preview = evaluate({**ms.inputs(design), **changes}).values
            st.info(f"{len(changes)} unsent change(s). Preview of my results below; "
                    f"other sheets update when you send.")
        else:
            preview = vals
        if st.button("📤 Send parameters to master sheet", type="primary", disabled=not changes):
            if not user:
                st.error("Enter your name in the sidebar first.")
            else:
                ms.send_parameters(design, changes, user)
                st.success("Sent — every sheet that gets these parameters was recomputed.")
                st.rerun()

    with right:
        st.subheader("Get parameters  (from other sheets)")
        if sub.gets:
            st.dataframe(pd.DataFrame([dict(Local=k, From=src, Value=vals[src], Unit=unit(src))
                                       for k, src in sub.gets.items()]),
                         hide_index=True, width="stretch",
                         column_config={"Value": st.column_config.NumberColumn(format="%.5g")})
        else:
            st.caption("This sheet gets nothing from other sheets.")

        st.subheader("Send parameters  (my results)")
        res = pd.DataFrame([dict(Result=p.key, Value=preview[sub.full(p.key)], Unit=p.unit,
                                 **{"Accepted if": DIRECTION_LABEL.get(p.better, "")},
                                 Description=p.desc) for p in sub.sends])
        if changes:
            res.insert(2, "Sent value", [vals[sub.full(p.key)] for p in sub.sends])
        st.dataframe(res, hide_index=True, width="stretch",
                     column_config={"Value": st.column_config.NumberColumn(format="%.5g"),
                                    "Sent value": st.column_config.NumberColumn(format="%.5g")})

        users = sorted({s.title for s in SUBSYSTEMS if any(src.startswith(sub.name + ".")
                                                            for src in s.gets.values())})
        if users:
            st.caption("My parameters are used by: " + ", ".join(users))

    mine = [c for c in compliance if c["parameter"].startswith(sub.name + ".")]
    if mine:
        st.subheader("My requirements")
        st.dataframe(pd.DataFrame(mine)[["requirement", "accepted", "required", "value", "unit", "status",
                                         "margin_pct"]].style.apply(status_style, subset=["status"]),
                     hide_index=True, width="stretch")

    if sub.name == "payload":
        st.subheader("SNR calculation stages (Video.mcd method)")
        det = evaluate({**ms.inputs(design), **changes}).details["payload"]
        df = pd.DataFrame(det).T
        show = ["W_min", "W_max", "E_dir", "E_dis", "E_sum", "E_L1", "H_L1", "Ne_L1", "U_amp_L1",
                "U_amp_D1", "mE", "mPx", "mPy", "Un_F", "Un_CCD", "Un_AMP", "Un_ADC", "Un_DP", "Un",
                "mu_L", "mu_D", "mu_x", "mu_y", "ccd_saturated", "adc_saturated"]
        st.dataframe(df[show].T, width="stretch")

# ========================================================== COMPARISON SHEET
elif page == "Comparison sheet":
    st.header(f"Comparison sheet — {design}")
    st.caption("System results compared with mission requirements. Pass/fail follows the nature "
               "of each parameter: higher-is-better parameters (SNR, swath, coverage) fail when "
               "below the required value; lower-is-better ones (GSD, location error, array area) "
               "fail when above it. MARGINAL = compliant with less than 5 % margin.")
    alert_banner()
    for c in compliance:
        if c["status"] == "FAIL":
            word = ("below the minimum" if c["better"] == "higher" else "above the maximum")
            u = "" if c["unit"] in ("-", "") else f" {c['unit']}"
            st.error(f"**{c['requirement']}**: {fmt(c['value'])}{u} is {word} "
                     f"{c['required']:g}{u}  ({c['margin_pct']:+.1f} %)")
    df = pd.DataFrame(compliance)
    st.dataframe(df[["requirement", "parameter", "accepted", "required", "value", "unit", "status",
                     "margin_pct", "source"]].style.apply(status_style, subset=["status"])
                 .format({"value": "{:.4g}", "required": "{:.4g}", "margin_pct": "{:+.1f}"}),
                 hide_index=True, width="stretch", height=min(60 + 35 * len(df), 700))

    with st.expander("✏️ Edit mission requirements"):
        st.caption("Pick a parameter and its threshold only; whether it must be above or below "
                   "comes from the parameter itself (shown under *accepted*). Only parameters "
                   "with a defined nature are listed.")
        options = requirement_params()
        reqs = pd.DataFrame([dict(label=r.label, param=r.param, value=r.value,
                                  accepted=DIRECTION_LABEL[direction(r.param)], source=r.source)
                             for r in ms.requirements()])
        ed = st.data_editor(reqs, num_rows="dynamic", hide_index=True, width="stretch",
                            column_config={
                                "param": st.column_config.SelectboxColumn("parameter", options=options,
                                                                          required=True),
                                "value": st.column_config.NumberColumn("required value", required=True)},
                            disabled=["accepted"])
        if st.button("Save requirements"):
            ed = ed.dropna(subset=["param", "value"])
            ms.set_requirements([Requirement(r.param, float(r.value), r.label or r.param,
                                             r.source or "") for r in ed.itertuples()])
            st.success("Requirements saved for all design options.")
            st.rerun()

# ======================================================= TRADE & SENSITIVITY
elif page == "Trade & sensitivity":
    st.header(f"Trade & sensitivity — {design}")
    st.caption("Change one parameter and see how it reflects on every model and result. "
               "Nothing is sent to the master sheet.")
    inputs = ms.inputs(design)
    in_keys = [k for k, m in CATALOGUE.items() if m["kind"] == "input"]
    res_keys = [k for k, m in CATALOGUE.items() if m["kind"] == "result"]
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    param = c1.selectbox("Parameter to vary", in_keys, index=in_keys.index("system.altitude_km"),
                         format_func=lambda k: f"{k}  [{unit(k)}]")
    v0 = inputs[param]
    lo = c2.number_input("from", value=float(v0) * 0.7, format="%.6g")
    hi = c3.number_input("to", value=float(v0) * 1.3, format="%.6g")
    n = int(c4.number_input("points", 5, 200, 41))
    outs = st.multiselect("Results to watch", res_keys,
                          default=[k for k in ["payload.pan_gsd_m", "payload.pan_snr_uniform",
                                               "payload.pan_snr_x", "power.solar_array_area_m2"]],
                          format_func=lambda k: f"{k}  [{unit(k)}]")
    if outs and hi > lo:
        xs = np.linspace(lo, hi, n)
        if param.endswith("_bits") or param.endswith("n_pixels"):
            xs = np.unique(np.round(xs))
        data = pd.DataFrame(sweep(inputs, param, xs, outs))
        reqs = {r.param: r for r in ms.requirements()}
        cols = st.columns(2)
        for i, o in enumerate(outs):
            # Altair treats "." in field names as nesting, so plot plain x / y columns
            d = pd.DataFrame({"x": data[param], "y": data[o]})
            base = alt.Chart(d).mark_line(point=n <= 41).encode(
                x=alt.X("x:Q", title=f"{param} [{unit(param)}]", scale=alt.Scale(zero=False)),
                y=alt.Y("y:Q", title=f"{o.split('.')[1]} [{unit(o)}]", scale=alt.Scale(zero=False)),
                tooltip=[alt.Tooltip("x:Q", title=param, format=".4g"),
                         alt.Tooltip("y:Q", title=o, format=".4g")])
            layers = [base, alt.Chart(pd.DataFrame({"x": [v0]})).mark_rule(
                strokeDash=[4, 4], color="gray").encode(x="x:Q")]
            if o in reqs:
                layers.append(alt.Chart(pd.DataFrame({"y": [reqs[o].value]})).mark_rule(color="red")
                              .encode(y="y:Q"))
            cols[i % 2].altair_chart(alt.layer(*layers).properties(title=desc(o), height=260),
                                     width="stretch")
        st.caption("Grey dashed line: current value. Red line: requirement.")
        with st.expander("Data"):
            st.dataframe(data, hide_index=True, width="stretch")
            st.download_button("Download CSV", data.to_csv(index=False), "sweep.csv")

# ============================================================ DESIGN OPTIONS
elif page == "Design options":
    st.header("Design options — alternative systems")
    notes = ms.design_notes()
    with st.form("new"):
        c1, c2, c3 = st.columns([2, 2, 3])
        name = c1.text_input("New option name", placeholder="option B - larger aperture")
        base = c2.selectbox("Copy from", designs)
        note = c3.text_input("Note")
        if st.form_submit_button("Create option") and name:
            if name in designs:
                st.error("That name exists.")
            else:
                ms.create_design(name, note, base)
                st.success(f"Created {name}.")
                st.rerun()

    chosen = st.multiselect("Compare", designs, default=designs[:4])
    if chosen:
        evs = {d: ms.results(d).values for d in chosen}
        st.subheader("Inputs that differ")
        rows = [dict(Parameter=k, Unit=unit(k), **{d: ms.inputs(d)[k] for d in chosen})
                for k, m in CATALOGUE.items() if m["kind"] == "input"
                and len({ms.inputs(d)[k] for d in chosen}) > 1]
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        else:
            st.caption("All inputs identical.")
        st.subheader("Requirement compliance")
        table = {}
        for d in chosen:
            for c in ms.compliance(d):
                table.setdefault(c["requirement"], {"accepted": c["accepted"], "required": c["required"]})[d] = \
                    f"{fmt(c['value'])}  {c['status']}"
        df = pd.DataFrame(table).T

        def color(v):
            for s, colr in STATUS_COLOR.items():
                if isinstance(v, str) and v.endswith(s):
                    return f"background-color: {colr}"
            return ""
        st.dataframe(df.style.map(color), width="stretch")
    with st.expander("Delete an option"):
        victim = st.selectbox("Option", [d for d in designs if d != "baseline"] or ["—"])
        if victim != "—" and st.button(f"Delete {victim}", type="secondary"):
            ms.delete_design(victim)
            st.rerun()

# ================================================================ CHANGE LOG
elif page == "Change log":
    st.header(f"Change log — {design}")
    hist = ms.history(design)
    if hist:
        st.dataframe(pd.DataFrame(hist, columns=["When", "Who", "Parameter", "Old", "New"]),
                     hide_index=True, width="stretch")
    else:
        st.caption("No changes yet.")
    st.subheader("Model run order")
    st.write(" → ".join(s.title for s in run_order()))
