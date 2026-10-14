function r = calculate(p, check)
%CALCULATE Signal/noise ratio - stages 1-30 of section 5.2 of EGS YZH MAN 129 00.
%   r = cdc.snr.calculate()                Annex B worked example
%   r = cdc.snr.calculate(p)               p from cdc.snr.defaultInputs(...)
%   r = cdc.snr.calculate(p, false)        skip the section 6 input checks
%
%   r is a struct with every stage value (names as in the document and as in
%   the Python version) and r.clipped listing any saturation applied in stages 12-13.
if nargin < 1 || isempty(p), p = cdc.snr.defaultInputs(); end
if nargin < 2, check = true; end
if check
    problems = cdc.snr.validate(p);
    if ~isempty(problems)
        error("cdc:snr:invalidInputs", "Invalid SNR inputs:\n  - %s", strjoin(problems, "\n  - "));
    end
end
E_SC = 1400;        % solar constant, W/m² (Annex B)
K_B = 1.38e-23;     % Boltzmann constant, J/K (Annex B)
clipped = strings(0, 1);

zS = pi/2 - deg2rad(p.sun_elevation);                                             % 1
dt = p.Kt / p.nu_x;                                                               % 2
W_min = cdc.snr.solarFraction(p.lam_min);                                         % 3
W_max = cdc.snr.solarFraction(p.lam_max);
E_Edir = E_SC * (W_max - W_min) * p.tau_At^(1/cos(zS)) * cos(zS);                 % 4
E_Edis = -log(p.tau_At) / cos(zS) * E_Edir * 3/128 * (11 + cos(2*zS));            % 5
E_sum = E_Edir + E_Edis;                                                          % 6
R_L = E_sum * p.rho_L;   R_D = E_sum * p.rho_D;                                   % 7
k = p.tau_At * p.tau_Os * 0.25 * (p.D / p.f)^2;
E_L1 = R_L * k;          E_D1 = R_D * k;                                          % 8
H_L1 = E_L1 * dt;        H_D1 = E_D1 * dt;                                        % 9
P_L1 = H_L1 * p.dx * p.dy;   P_D1 = H_D1 * p.dx * p.dy;                           % 10
Ne_L1 = P_L1 * p.RQ;     Ne_D1 = P_D1 * p.RQ;                                     % 11

Uccd_L1 = Ne_L1 * p.KA;  Uccd_D1 = Ne_D1 * p.KA;                                  % 12
if Uccd_L1 > p.U_CCD_max
    Uccd_L1 = p.U_CCD_max; clipped(end+1, 1) = "Uccd_L1 clipped at U_CCD_max (CCD saturation)";
end
if Uccd_D1 > p.U_CCD_max
    Uccd_D1 = p.U_CCD_max; clipped(end+1, 1) = "Uccd_D1 clipped at U_CCD_max (CCD saturation)";
end
Uamp_L1 = Uccd_L1 * p.KU;  Uamp_D1 = Uccd_D1 * p.KU;                              % 13
if Uamp_L1 > p.U_ADC_max
    Uamp_L1 = p.U_ADC_max; clipped(end+1, 1) = "Uamp_L1 clipped at U_ADC_max (ADC input range)";
end
if Uamp_D1 > p.U_ADC_max
    Uamp_D1 = p.U_ADC_max; clipped(end+1, 1) = "Uamp_D1 clipped at U_ADC_max (ADC input range)";
end

mE = (p.rho_L - p.rho_D) / (p.rho_L + p.rho_D);                                   % 14
mPx = mE * p.Tx;                                                                  % 15
mPy = mE * p.Ty;                                                                  % 16
U_sum = Uamp_L1 + Uamp_D1;
Uamp_Lx = U_sum * (1 + mPx) / 2;                                                  % 17
Uamp_Dx = U_sum * (1 - mPx) / 2;                                                  % 18
Uamp_Ly = U_sum * (1 + mPy) / 2;                                                  % 19
Uamp_Dy = U_sum * (1 - mPy) / 2;                                                  % 20

Un_F = sqrt(Ne_L1) * p.KA * p.KU;                                                 % 21
Un_CCD = p.Hn_CCD * p.dx * p.dy * p.RQ * p.KA * p.KU;                             % 22
Un_AMP = sqrt(4 * K_B * p.TU * p.R_equ * p.N_El * p.nu_x);                        % 23
Un_ADC = p.U_ADC_max / (2^p.p_ADC * sqrt(12));                                    % 24
Un_DP = Un_ADC * (2^p.p_ADC / 2^p.p_DP - 1);                                      % 25
Un = sqrt(Un_F^2 + Un_CCD^2 + Un_AMP^2 + (Un_ADC + Un_DP)^2);                     % 26

mu_L = Uamp_L1 / Un;                                                              % 27
mu_D = Uamp_D1 / Un;                                                              % 28
mu_x = (Uamp_Lx - Uamp_Dx) / Un;                                                  % 29
mu_y = (Uamp_Ly - Uamp_Dy) / Un;                                                  % 30

r = struct("zS_deg", rad2deg(zS), "dt", dt, "W_min", W_min, "W_max", W_max, ...
    "E_Edir", E_Edir, "E_Edis", E_Edis, "E_sum", E_sum, "R_L", R_L, "R_D", R_D, ...
    "E_L1", E_L1, "E_D1", E_D1, "H_L1", H_L1, "H_D1", H_D1, "P_L1", P_L1, "P_D1", P_D1, ...
    "Ne_L1", Ne_L1, "Ne_D1", Ne_D1, "Uccd_L1", Uccd_L1, "Uccd_D1", Uccd_D1, ...
    "Uamp_L1", Uamp_L1, "Uamp_D1", Uamp_D1, "mE", mE, "mPx", mPx, "mPy", mPy, ...
    "Uamp_Lx", Uamp_Lx, "Uamp_Dx", Uamp_Dx, "Uamp_Ly", Uamp_Ly, "Uamp_Dy", Uamp_Dy, ...
    "Un_F", Un_F, "Un_CCD", Un_CCD, "Un_AMP", Un_AMP, "Un_ADC", Un_ADC, "Un_DP", Un_DP, ...
    "Un", Un, "mu_L", mu_L, "mu_D", mu_D, "mu_x", mu_x, "mu_y", mu_y);
r.clipped = clipped;
end
