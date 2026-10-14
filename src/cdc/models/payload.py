"""
Payload sheet: electro-optical imager.

Radiometry is the Video.mcd SNR model (cdc.models.snr) run once for the
panchromatic channel and once per multispectral band. Geometry (GSD, swath,
line-rate match) uses the same optics and detector parameters.
"""
from cdc.framework import Param, Subsystem
from cdc.models import snr as snr_model

VM = "Video.mcd"
MS_BANDS = ("blue", "green", "red", "nir")


def _snr_args(p: dict, lam_min_um, lam_max_um, pitch_m, Tx, Ty) -> dict:
    return dict(
        lam_min=lam_min_um * 1e-6, lam_max=lam_max_um * 1e-6,
        sun_elev_deg=p["sun_elevation_deg"], rho_L=p["albedo_light"], rho_D=p["albedo_dark"],
        tau_at=p["atm_transmission"], tau_os=p["optics_transmission"],
        D=p["aperture_m"], f=p["focal_length_m"],
        dx=pitch_m, dy=pitch_m, nu_x=p["line_rate_hz"], Kt=p["exposure_ratio"],
        N_el=p["n_pixels"], Hn_ccd=p["noise_equiv_exposure"], RQ=p["RQ"], KA=p["KA"],
        U_ccd_max=p["ccd_sat_v"], KU=p["amp_gain"], TU=p["amp_temp_k"], R_equ=p["amp_r_ohm"],
        U_adc_max=p["adc_vmax"], p_adc=int(p["adc_bits"]), p_dp=int(p["dp_bits"]),
        Tx=Tx, Ty=Ty,
    )


def model(p: dict) -> dict:
    h = p["altitude_km"] * 1e3
    pan_pitch = p["pan_pitch_um"] * 1e-6
    ms_pitch = p["ms_pitch_um"] * 1e-6
    f = p["focal_length_m"]
    vg = p["ground_speed_ms"]

    pan_gsd = h * pan_pitch / f
    ms_gsd = h * ms_pitch / f
    out = {
        "pan_gsd_m": pan_gsd,
        "ms_gsd_m": ms_gsd,
        "pan_swath_km": pan_gsd * p["n_pixels"] / 1e3,
        "ms_swath_km": ms_gsd * p["n_pixels"] / 1e3,
        "along_track_sampling_m": vg / p["line_rate_hz"],
        "line_rate_for_square_px_hz": vg / pan_gsd,
        "f_number": f / p["aperture_m"],
    }
    out["line_rate_mismatch_pct"] = 100 * (p["line_rate_hz"] / out["line_rate_for_square_px_hz"] - 1)

    details, warnings = {}, []
    pan_args = _snr_args(p, p["pan_lmin_um"], p["pan_lmax_um"], pan_pitch, p["pan_mtf_x"], p["pan_mtf_y"])
    warnings += [f"PAN: {w}" for w in snr_model.check_inputs(pan_args)]
    pan = snr_model.snr(**pan_args)
    details["PAN"] = pan
    out.update(pan_snr_uniform=pan["mu_L"], pan_snr_x=pan["mu_x"], pan_snr_y=pan["mu_y"])
    if pan["ccd_saturated"] or pan["adc_saturated"]:
        warnings.append("PAN signal saturates (CCD or ADC) - SNR is clipped")

    for b in MS_BANDS:
        args = _snr_args(p, p[f"{b}_lmin_um"], p[f"{b}_lmax_um"], ms_pitch, p["ms_mtf_x"], p["ms_mtf_y"])
        warnings += [f"{b.upper()}: {w}" for w in snr_model.check_inputs(args)]
        r = snr_model.snr(**args)
        details[b.upper()] = r
        out[f"{b}_snr"] = r["mu_L"]
        if r["ccd_saturated"] or r["adc_saturated"]:
            warnings.append(f"{b.upper()} signal saturates - SNR is clipped")

    if abs(out["line_rate_mismatch_pct"]) > 5:
        warnings.append(f"Line rate is {out['line_rate_mismatch_pct']:+.1f}% off square pixels "
                        f"(needs {out['line_rate_for_square_px_hz']:.0f} Hz)")
    out["_details"], out["_warnings"] = details, warnings
    return out


def _band(b, lmin, lmax):
    return [Param(f"{b}_lmin_um", lmin, "µm", f"{b.upper()} band lower edge", 0.22, 10,
                  "Multispectral bands", "placeholder"),
            Param(f"{b}_lmax_um", lmax, "µm", f"{b.upper()} band upper edge", 0.22, 10,
                  "Multispectral bands", "placeholder")]


PAYLOAD = Subsystem(
    name="payload",
    title="Payload (EO imager)",
    owner_role="Payload engineer",
    inputs=[
        Param("pan_lmin_um", 0.500, "µm", "PAN band lower edge", 0.22, 10, "PAN band", VM),
        Param("pan_lmax_um", 0.885, "µm", "PAN band upper edge", 0.22, 10, "PAN band", VM),
        *_band("blue", 0.45, 0.52), *_band("green", 0.52, 0.60),
        *_band("red", 0.63, 0.69), *_band("nir", 0.76, 0.90),
        Param("optics_transmission", 0.60, "-", "Optics transmission coefficient", 0, 1, "Optics", VM),
        Param("aperture_m", 0.155, "m", "Effective entrance aperture diameter", 0, None, "Optics", VM),
        Param("focal_length_m", 0.860, "m", "Focal length", 0, None, "Optics", VM),
        Param("pan_mtf_x", 0.14, "-", "PAN videopath MTF across CCD-line (Tx)", 0, 1, "Optics", VM),
        Param("pan_mtf_y", 0.22, "-", "PAN videopath MTF along CCD-line (Ty)", 0, 1, "Optics", VM),
        Param("ms_mtf_x", 0.14, "-", "MS videopath MTF across CCD-line", 0, 1, "Optics", "placeholder"),
        Param("ms_mtf_y", 0.22, "-", "MS videopath MTF along CCD-line", 0, 1, "Optics", "placeholder"),
        Param("pan_pitch_um", 10, "µm", "PAN photosite step (= photosite size)", 0, None, "Detector", VM),
        Param("ms_pitch_um", 10, "µm", "MS photosite step (= photosite size)", 0, None, "Detector", "placeholder"),
        Param("line_rate_hz", 900, "Hz", "Line frequency νx", 0, None, "Detector", VM),
        Param("exposure_ratio", 1.0, "-", "Relative exposure time Kt", 0, 1, "Detector", VM),
        Param("n_pixels", 6000, "-", "Photosites per line", 2, None, "Detector", VM),
        Param("noise_equiv_exposure", 4.0e-7, "J/m²", "Exposure equivalent to RMS CCD noise", 0, None, "Detector", VM),
        Param("RQ", 1.563e18, "e⁻/J", "Radiant energy → electrons", 0, None, "Detector", VM),
        Param("KA", 3.2e-6, "V/e⁻", "Electrons → voltage", 0, None, "Detector", VM),
        Param("ccd_sat_v", 3.0, "V", "CCD saturation voltage", 0, None, "Detector", VM),
        Param("amp_gain", 3, "-", "Amplifier voltage gain", 1, None, "Electronics", VM),
        Param("amp_temp_k", 300, "K", "Amplifier temperature", 0, None, "Electronics", VM),
        Param("amp_r_ohm", 10000, "Ω", "Amplifier equivalent resistance", 0, None, "Electronics", VM),
        Param("adc_vmax", 1.0, "V", "ADC max input voltage", 0, None, "Electronics", VM),
        Param("adc_bits", 12, "bit", "ADC output bits", 1, 24, "Electronics", VM),
        Param("dp_bits", 8, "bit", "Digital processor output bits", 1, 24, "Electronics", VM),
        Param("payload_power_w", 40, "W", "Payload power while imaging", 0, None, "Budgets", "placeholder"),
    ],
    gets={
        "altitude_km": "system.altitude_km",
        "ground_speed_ms": "system.ground_speed_ms",
        "sun_elevation_deg": "system.sun_elevation_deg",
        "albedo_light": "system.albedo_light",
        "albedo_dark": "system.albedo_dark",
        "atm_transmission": "system.atm_transmission",
    },
    sends=[
        Param("pan_gsd_m", better="lower", unit="m", desc="PAN ground sample distance at nadir"),
        Param("ms_gsd_m", better="lower", unit="m", desc="MS ground sample distance at nadir"),
        Param("pan_swath_km", better="higher", unit="km", desc="PAN swath width at nadir"),
        Param("ms_swath_km", better="higher", unit="km", desc="MS swath width at nadir"),
        Param("along_track_sampling_m", better="lower", unit="m", desc="Along-track sampling (ground speed / line rate)"),
        Param("line_rate_for_square_px_hz", unit="Hz", desc="Line rate giving square PAN pixels"),
        Param("line_rate_mismatch_pct", unit="%", desc="Actual vs square-pixel line rate"),
        Param("f_number", unit="-", desc="Optics f-number"),
        Param("pan_snr_uniform", better="higher", unit="-", desc="PAN SNR, uniform background ρ_light (µL)"),
        Param("pan_snr_x", better="higher", unit="-", desc="PAN SNR, strips ⟂ to track (µx)"),
        Param("pan_snr_y", better="higher", unit="-", desc="PAN SNR, strips ∥ to track (µy)"),
        *[Param(f"{b}_snr", better="higher", unit="-", desc=f"{b.upper()} band SNR, uniform background (µL)") for b in MS_BANDS],
    ],
    model=model,
    notes=("SNR: Yuzhnoye Video.mcd method (EGS YZH MAN 129 00), verified against Annex B. "
           "MS bands reuse the PAN detector constants (RQ, KA, noise) as band-averaged values; "
           "replace with per-band detector data when available. MTF values are inputs for now."),
)
