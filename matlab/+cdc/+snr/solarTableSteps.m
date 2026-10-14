function [left, right, avg] = solarTableSteps()
%SOLARTABLESTEPS Average spectral irradiance in each table interval, E_SC*ΔW/Δλ, W/(m²·µm).
%   Read straight from the two arrays of Annex B page 23, no interpolation. λ in m.
t = cdc.snr.solarTable();
left = t.lambda(1:end-1);
right = t.lambda(2:end);
avg = t.E_SC * diff(t.W) ./ (diff(t.lambda) * 1e6);
end
