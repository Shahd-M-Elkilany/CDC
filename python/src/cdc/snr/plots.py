"""
Figures for the SNR model: where the solar constant comes from and where it goes.

    from cdc.snr.plots import plot_solar
    fig = plot_solar()                      # Annex B inputs
    fig = plot_solar(SNRInputs(lam_max=1e-6), path="solar.png")

Needs matplotlib (pip install -e ".[plot]").

(a) W(λ), the Annex B table (page 23) and its cubic spline - the Mathcad plot, with the
    operating range λmin..λmax and the two read-outs of stage 3.
(b) The solar spectrum above the atmosphere implied by the table, E_SC·dW/dλ. The whole area
    is E_SC = 1400 W/m² (§5.2 stage 4, Annex B page 22); the area inside the operating range is
    E_SC·(Wmax − Wmin), the absolute value that enters stage 4.
(c) What becomes of it: solar constant → in band → at the ground → reflected → focal plane.
(d) System behaviour: SNR µL as the upper band edge λmax moves (all other inputs fixed).
"""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from cdc.snr.inputs import SNRInputs
from cdc.snr.model import (
    E_SC,
    SOLAR_LAMBDA,
    SOLAR_W,
    calculate,
    in_band_solar_constant,
    solar_fraction,
    solar_spectral_irradiance,
    solar_table_steps,
)

# colours (one meaning each): orange = the table as printed, blue = the spline / model
TABLE = "#eb6834"
MODEL = "#2a78d6"
BAND = "#e6e5df"
INK = "#1f1f1e"
INK2 = "#6b6a63"
GRID = "#ecebe6"


def _style(ax, title):
    ax.set_title(title, loc="left", fontsize=10.5, color=INK, fontweight="bold")
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8.5)
    ax.xaxis.label.set_color(INK2)
    ax.yaxis.label.set_color(INK2)


def plot_solar(p: SNRInputs | None = None, path: str | None = None):
    """Build the four-panel figure; save it when `path` is given. Returns the Figure."""
    from matplotlib.figure import Figure

    p = p or SNRInputs()
    r = calculate(p)
    lo, hi = p.lam_min * 1e6, p.lam_max * 1e6          # µm
    e_band = in_band_solar_constant(p.lam_min, p.lam_max)

    fig = Figure(figsize=(13, 9), layout="constrained")
    fig.suptitle("Solar constant in the SNR model  -  EGS YZH MAN 129 00, Annex B "
                 f"(λ = {lo:g}…{hi:g} µm, sun elevation {p.sun_elevation:g}°)",
                 fontsize=12, color=INK, x=0.01, ha="left")
    (a, b), (c, d) = fig.subplots(2, 2)

    # (a) cumulative fraction W(λ) - the Mathcad plot
    x = np.linspace(SOLAR_LAMBDA[0], 5e-6, 1500)
    a.axvspan(lo, hi, color=BAND, zorder=0)
    a.plot(x * 1e6, [solar_fraction(v) for v in x], color=MODEL, lw=2, label="cubic spline (Mathcad cspline)")
    keep = SOLAR_LAMBDA <= 5e-6
    a.plot(SOLAR_LAMBDA[keep] * 1e6, SOLAR_W[keep], "o", ms=5, mfc="white", mec=TABLE, mew=1.5,
           label="table, Annex B p. 23")
    for lam, w, name in ((lo, r.W_min, "W(λmin)"), (hi, r.W_max, "W(λmax)")):
        a.plot([0, lam, lam], [w, w, 0], ls="--", lw=1, color=INK2)
        a.annotate(f"{name} = {w:.4f}", (lam, w), xytext=(8, -12 if name == "W(λmin)" else 6),
                   textcoords="offset points", fontsize=9, color=INK)
    a.annotate("", xy=(4.3, r.W_max), xytext=(4.3, r.W_min),
               arrowprops=dict(arrowstyle="<->", color=INK, lw=1))
    a.text(4.38, (r.W_min + r.W_max) / 2, f"Wmax − Wmin\n= {r.W_max - r.W_min:.4f}",
           va="center", fontsize=9, color=INK)
    a.plot([hi, 4.3], [r.W_max] * 2, ls=":", lw=1, color=INK2)
    a.plot([lo, 4.3], [r.W_min] * 2, ls=":", lw=1, color=INK2)
    a.text((lo + hi) / 2, 0.985, "operating\nrange", ha="center", va="top", fontsize=8.5, color=INK2)
    a.set(xlim=(0, 5), ylim=(0, 1.02), xlabel="wave length λ, µm",
          ylabel="part of solar constant in 0…λ, W(λ)")
    a.legend(loc="lower right", fontsize=8.5, frameon=False)
    _style(a, "(a) Stage 3 - spectral distribution of the solar constant")

    # (b) the spectrum implied by the table; areas = W/m²
    left, right, avg = solar_table_steps()
    m = right <= 3e-6
    b.bar(left[m] * 1e6, avg[m], width=(right[m] - left[m]) * 1e6, align="edge",
          color="none", edgecolor=TABLE, lw=1.2, label="table: E_SC·ΔW/Δλ per interval")
    xs = np.linspace(SOLAR_LAMBDA[0], 3e-6, 3000)
    ys = solar_spectral_irradiance(xs)
    b.plot(xs * 1e6, ys, color=MODEL, lw=2, label="spline: E_SC·dW/dλ")
    inb = (xs >= p.lam_min) & (xs <= p.lam_max)
    b.fill_between(xs[inb] * 1e6, 0, ys[inb], color=MODEL, alpha=0.18, lw=0)
    b.text(0.97, 0.95,
           f"whole area (0.22…10 µm) = E_SC·W(10 µm) = {E_SC * SOLAR_W[-1]:.0f} W/m²\n"
           f"shaded area = E_SC·(Wmax − Wmin)\n"
           f"   = {E_SC:.0f} × ({r.W_max:.4f} − {r.W_min:.4f})\n"
           f"   = {e_band:.1f} W/m²  ← enters stage 4",
           transform=b.transAxes, ha="right", va="top", fontsize=9, color=INK, family="monospace")
    b.text(0.97, 0.62, "the spline's wiggles near 0.4 µm come from uneven\n"
           "table steps there; W(λ) itself (panel a) is smooth",
           transform=b.transAxes, ha="right", va="top", fontsize=8, color=INK2)
    b.set(xlim=(0.2, 3), ylim=(0, None), xlabel="wave length λ, µm",
          ylabel="spectral irradiance above atmosphere, W/(m²·µm)")
    b.legend(loc=(0.55, 0.32), fontsize=8.5, frameon=False)
    _style(b, f"(b) Where the absolute value comes from: E_SC = {E_SC:.0f} W/m² × table")

    # (c) the chain from the solar constant to the focal plane
    zS = math.radians(r.zS_deg)
    steps = [
        ("E_SC  solar constant, all λ, top of atmosphere", E_SC, "p. 22"),
        ("E_SC·(Wmax−Wmin)  in band, top of atmosphere", e_band, "stage 3"),
        (f"× τAt^sec zS = {p.tau_At ** (1 / math.cos(zS)):.3f}  after the atmosphere",
         e_band * p.tau_At ** (1 / math.cos(zS)), ""),
        (f"× cos zS = {math.cos(zS):.3f}  E_Edir, direct, on the ground", r.E_Edir, "stage 4"),
        ("+ E_Edis  EΣ, direct + diffuse, on the ground", r.E_sum, "stages 5-6"),
        (f"× ρL = {p.rho_L:g}  R_L, leaving the light strip", r.R_L, "stage 7"),
        ("× τAt·τOs·(D/f)²/4  E_L1, on the CCD-line", r.E_L1, "stage 8"),
    ]
    yy = np.arange(len(steps))[::-1]
    c.barh(yy, [s[1] for s in steps], height=0.55, color=MODEL)
    for y, (label, v, where) in zip(yy, steps, strict=True):
        c.text(v * 1.15, y, f"{v:.4g} W/m²", va="center", fontsize=9, color=INK)
        c.text(2e-2, y + 0.42, label + (f"   [{where}]" if where else ""), fontsize=8.5, color=INK2)
    c.set_xscale("log")
    c.set(xlim=(1e-2, 2e4), ylim=(-0.6, len(steps) - 0.1), yticks=[], xlabel="irradiance, W/m² (log scale)")
    _style(c, "(c) What becomes of it - stages 3 to 8")

    # (d) system behaviour against the band edge
    lam_hi = np.linspace(max(p.lam_min * 1.05, 0.6e-6), 1.2e-6, 61)
    mu = []
    for v in lam_hi:
        try:
            mu.append(calculate(replace(p, lam_max=float(v))).mu_L)
        except ValueError:
            mu.append(np.nan)
    d.plot(lam_hi * 1e6, mu, color=MODEL, lw=2)
    d.plot([hi], [r.mu_L], "o", ms=8, color=MODEL, mec="white", mew=2, zorder=3)
    d.annotate(f"design point\nλmax = {hi:g} µm, µL = {r.mu_L:.1f}", (hi, r.mu_L),
               xytext=(12, -28), textcoords="offset points", fontsize=9, color=INK)
    if r.clipped:
        d.text(0.02, 0.04, "note: " + "; ".join(r.clipped), transform=d.transAxes, fontsize=8, color=INK2)
    d.set(xlabel="upper band edge λmax, µm", ylabel="SNR µL (uniform background ρL)")
    _style(d, "(d) System behaviour - SNR as the band widens (other inputs fixed)")

    if path:
        fig.savefig(path, dpi=150, facecolor="white")
    return fig
