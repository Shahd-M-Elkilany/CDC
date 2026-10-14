function t = solarTable()
%SOLARTABLE Where the solar constant in the SNR model comes from.
%   t = cdc.snr.solarTable() returns a struct:
%     t.E_SC    solar constant, 1400 W/m² - the ABSOLUTE value
%               (section 5.2 stage 4, page 13; "Constants used in the program", Annex B page 22)
%     t.lambda  wave length, m      } "Spectral distribution of solar constant", Annex B page 23:
%     t.W       part of E_SC in 0..λ } RELATIVE values (0..1), interpolated by cubic spline (stage 3)
%   The irradiance in the operating range is t.E_SC * (W(λmax) - W(λmin)).
persistent T
if isempty(T)
    T.E_SC = 1400;
    T.lambda = [0.22 0.24 0.26 0.28 0.30 0.32 0.34 0.36 0.38 0.40 0.41 0.42 ...
                0.43 0.44 0.45 0.46 0.48 0.50 0.55 0.60 0.65 0.70 0.75 0.80 ...
                0.90 1.0 1.1 1.2 1.4 1.6 1.8 2.0 2.5 3.0 4.0 5.0 6.0 7.0 8.0 10.0] * 1e-6;
    T.W = [0 0.001 0.002 0.005 0.012 0.023 0.037 0.055 0.072 0.091 0.105 ...
           0.116 0.133 0.146 0.161 0.176 0.206 0.236 0.308 0.377 0.44 ...
           0.495 0.545 0.59 0.661 0.718 0.766 0.804 0.861 0.899 0.924 ...
           0.942 0.966 0.979 0.991 0.9954 0.9973 0.998 0.9988 0.9995];
    T.pp = spline(T.lambda, T.W);          % not-a-knot = Mathcad cspline + interp
end
t = T;
end
