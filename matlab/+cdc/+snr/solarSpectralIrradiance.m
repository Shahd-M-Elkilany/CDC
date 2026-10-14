function S = solarSpectralIrradiance(lam)
%SOLARSPECTRALIRRADIANCE E_SC*dW/dλ, W/(m²·µm): the solar spectrum above the atmosphere
%   implied by the table (derivative of the cubic spline; λ in m). Base MATLAB only.
t = cdc.snr.solarTable();
[breaks, coefs] = unmkpp(t.pp);
dpp = mkpp(breaks, coefs(:, 1:3) .* [3 2 1]);
S = t.E_SC * ppval(dpp, lam) * 1e-6;
end
