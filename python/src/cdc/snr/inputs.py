"""
Input data of the signal/noise ratio calculation.

Section 5.1 of EGS YZH MAN 129 00 lists 27 inputs in 9 groups; section 6 gives
the physical meaning, unit and allowed range of each. Defaults are the Annex B
worked example (Video.mcd).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields


def _in(default, symbol, group, description, unit=""):
    return field(default=default, metadata=dict(symbol=symbol, group=group,
                                                description=description, unit=unit))


G1 = "Operating range of electro-magnetic waves"
G2 = "Characteristics of imaged region and conditions of its illumination"
G3 = "Characteristics of atmosphere"
G4 = "Characteristics of optical system"
G5 = "Characteristics of a photoreceiver (CCD-line)"
G6 = "Amplifier characteristics"
G7 = "Characteristics of analog-digital converter"
G8 = "Characteristics of digital processor"
G9 = "Value of videopath modulation transfer's resultant function"
GROUPS = [G1, G2, G3, G4, G5, G6, G7, G8, G9]


@dataclass(frozen=True)
class SNRInputs:
    lam_min: float = _in(0.500e-6, "λmin", G1, "Left boundary of irradiation range", "m")
    lam_max: float = _in(0.885e-6, "λmax", G1, "Right boundary of irradiation range", "m")
    sun_elevation: float = _in(30.0, "βS", G2, "Sun elevation angle", "deg")
    rho_L: float = _in(0.25, "ρL", G2, "Reflection coefficient (albedo) for the light strip of a test pattern")
    rho_D: float = _in(0.20, "ρD", G2, "Reflection coefficient (albedo) for the dark strip of a test pattern")
    tau_At: float = _in(0.80, "τAt", G3, "Atmospheric transmission coefficient")
    tau_Os: float = _in(0.60, "τOs", G4, "Transmission coefficient")
    D: float = _in(0.155, "D", G4, "Effective diameter of entrance aperture", "m")
    f: float = _in(0.860, "f", G4, "Focal distance", "m")
    dzy: float = _in(10e-6, "∆zy", G5, "Step of photosites", "m")
    dy: float = _in(10e-6, "∆y", G5, "Dimension of a photosite along CCD-line", "m")
    dx: float = _in(10e-6, "∆x", G5, "Dimension of a photosite across CCD-line", "m")
    nu_x: float = _in(900.0, "νx", G5, "Lines' frequency", "Hz")
    Kt: float = _in(1.0, "Kt", G5, "Relative time of line's exposure")
    N_El: int = _in(6000, "NEl", G5, "Number of photosites in a line")
    Hn_CCD: float = _in(4.0e-7, "HnCCD", G5, "Exposure, equivalent to root mean square value of noise", "J/m²")
    RQ: float = _in(1.563e18, "RQ", G5, "Coefficient of irradiation energy transformation into electrons", "electron/J")
    KA: float = _in(3.2e-6, "KA", G5, "Coefficient of electrons' transformation into voltage", "V/electron")
    U_CCD_max: float = _in(3.0, "UCCDmax", G5, "Voltage of saturation", "V")
    KU: float = _in(3.0, "KU", G6, "Coefficient of amplification by voltage")
    TU: float = _in(300.0, "TU", G6, "Temperature", "K")
    R_equ: float = _in(10000.0, "Requ", G6, "Equivalent resistance", "Ω")
    U_ADC_max: float = _in(1.0, "UADCmax", G7, "Maximal allowable input voltage", "V")
    p_ADC: int = _in(12, "pADC", G7, "Number of bits for output code")
    p_DP: int = _in(8, "pDP", G8, "Number of bits for output code")
    Tx: float = _in(0.14, "Tx", G9, "Across CCD-line")
    Ty: float = _in(0.22, "Ty", G9, "Along CCD-line")

    @classmethod
    def from_dict(cls, values: dict) -> "SNRInputs":
        """Annex B defaults overridden by the given values; unknown names are an error."""
        known = {f.name for f in fields(cls)}
        unknown = set(values) - known
        if unknown:
            raise KeyError(f"Unknown input(s): {', '.join(sorted(unknown))}")
        return cls(**values)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def spec() -> list[dict]:
        """Name, symbol, group, description and unit of every input, in PDF order."""
        return [dict(name=f.name, default=f.default, **f.metadata) for f in fields(SNRInputs)]


def validate(p: SNRInputs) -> list[str]:
    """Allowed values from section 6 of the document. Returns the violated rules."""
    e = []

    def rng(name, lo, hi, lo_open=False):
        v = getattr(p, name)
        ok_lo = v > lo if lo_open else v >= lo
        if not (ok_lo and v <= hi):
            e.append(f"{name} = {v:g} must be in {'(' if lo_open else '['}{lo:g}, {hi:g}]")

    def positive(*names):
        for n in names:
            if not getattr(p, n) > 0:
                e.append(f"{n} = {getattr(p, n):g} must be positive")

    def positive_int(name):
        v = getattr(p, name)
        if not (float(v).is_integer() and v >= 1):
            e.append(f"{name} = {v:g} must be a positive integer")

    rng("lam_min", 0.22e-6, 10e-6)
    rng("lam_max", 0.22e-6, 10e-6)
    if p.lam_min > p.lam_max:
        e.append("lam_min must not be greater than lam_max")
    rng("sun_elevation", 10, 90)
    rng("rho_L", 0, 1)
    rng("rho_D", 0, 1)
    if p.rho_D > p.rho_L:
        e.append("rho_D (dark strip) must not be greater than rho_L (light strip)")
    rng("tau_At", 0, 1, lo_open=True)        # 0 would make ln(τAt) and τ^sec(zS) undefined
    rng("tau_Os", 0, 1, lo_open=True)
    positive("D", "f", "dzy", "dy", "dx", "nu_x")
    if p.dy > p.dzy:
        e.append("dy (photosite along CCD-line) must not be greater than dzy (photosite step)")
    rng("Kt", 0, 1, lo_open=True)
    if not (float(p.N_El).is_integer() and p.N_El >= 2):
        e.append(f"N_El = {p.N_El:g} must be an integer not smaller than 2")
    positive("Hn_CCD", "RQ", "KA", "U_CCD_max")
    if not p.KU >= 1:
        e.append(f"KU = {p.KU:g} must not be smaller than 1")
    positive("TU", "R_equ", "U_ADC_max")
    positive_int("p_ADC")
    positive_int("p_DP")
    if p.p_DP > p.p_ADC:
        e.append("p_DP must not be greater than p_ADC")
    rng("Tx", 0, 1)
    rng("Ty", 0, 1)
    return e
