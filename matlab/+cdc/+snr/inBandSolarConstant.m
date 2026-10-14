function E = inBandSolarConstant(lamMin, lamMax)
%INBANDSOLARCONSTANT E_SC*(W(λmax) - W(λmin)), W/m²: the part of the 1400 W/m² inside the
%   operating range. The absolute value behind stage 4:
%   E_Edir = inBandSolarConstant(λmin, λmax) * τAt^sec(zS) * cos(zS).
t = cdc.snr.solarTable();
E = t.E_SC * (cdc.snr.solarFraction(lamMax) - cdc.snr.solarFraction(lamMin));
end
