function W = solarFraction(lam)
%SOLARFRACTION W(λ): part of the solar constant within the wave length range 0..λ (λ in m).
%   Table of Annex B (page 23, see cdc.snr.solarTable), interpolated with a not-a-knot
%   cubic spline, which is what Mathcad cspline + interp computes (W(0.885 µm) = 0.652).
t = cdc.snr.solarTable();
W = ppval(t.pp, lam);
end
