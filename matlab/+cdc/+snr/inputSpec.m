function s = inputSpec()
%INPUTSPEC The 27 inputs of section 5.1 of EGS YZH MAN 129 00, in document order.
%   s = cdc.snr.inputSpec() returns a struct array with fields
%   name, symbol, group, description, unit, default (Annex B worked example).
%   Same names as the Python version (cdc.snr.SNRInputs).
G1 = "Operating range of electro-magnetic waves";
G2 = "Characteristics of imaged region and conditions of its illumination";
G3 = "Characteristics of atmosphere";
G4 = "Characteristics of optical system";
G5 = "Characteristics of a photoreceiver (CCD-line)";
G6 = "Amplifier characteristics";
G7 = "Characteristics of analog-digital converter";
G8 = "Characteristics of digital processor";
G9 = "Value of videopath modulation transfer's resultant function";
c = {
%   name           symbol      group  description                                                              unit          default
    "lam_min",     "λmin",     G1, "Left boundary of irradiation range",                                    "m",          0.500e-6
    "lam_max",     "λmax",     G1, "Right boundary of irradiation range",                                   "m",          0.885e-6
    "sun_elevation","βS",      G2, "Sun elevation angle",                                                   "deg",        30
    "rho_L",       "ρL",       G2, "Reflection coefficient (albedo) for the light strip of a test pattern", "",           0.25
    "rho_D",       "ρD",       G2, "Reflection coefficient (albedo) for the dark strip of a test pattern",  "",           0.20
    "tau_At",      "τAt",      G3, "Atmospheric transmission coefficient",                                  "",           0.80
    "tau_Os",      "τOs",      G4, "Transmission coefficient",                                              "",           0.60
    "D",           "D",        G4, "Effective diameter of entrance aperture",                               "m",          0.155
    "f",           "f",        G4, "Focal distance",                                                        "m",          0.860
    "dzy",         "∆zy",      G5, "Step of photosites",                                                    "m",          10e-6
    "dy",          "∆y",       G5, "Dimension of a photosite along CCD-line",                               "m",          10e-6
    "dx",          "∆x",       G5, "Dimension of a photosite across CCD-line",                              "m",          10e-6
    "nu_x",        "νx",       G5, "Lines' frequency",                                                      "Hz",         900
    "Kt",          "Kt",       G5, "Relative time of line's exposure",                                      "",           1
    "N_El",        "NEl",      G5, "Number of photosites in a line",                                        "",           6000
    "Hn_CCD",      "HnCCD",    G5, "Exposure, equivalent to root mean square value of noise",               "J/m²",       4.0e-7
    "RQ",          "RQ",       G5, "Coefficient of irradiation energy transformation into electrons",       "electron/J", 1.563e18
    "KA",          "KA",       G5, "Coefficient of electrons' transformation into voltage",                 "V/electron", 3.2e-6
    "U_CCD_max",   "UCCDmax",  G5, "Voltage of saturation",                                                 "V",          3.0
    "KU",          "KU",       G6, "Coefficient of amplification by voltage",                               "",           3
    "TU",          "TU",       G6, "Temperature",                                                           "K",          300
    "R_equ",       "Requ",     G6, "Equivalent resistance",                                                 "Ω",          10000
    "U_ADC_max",   "UADCmax",  G7, "Maximal allowable input voltage",                                       "V",          1
    "p_ADC",       "pADC",     G7, "Number of bits for output code",                                        "",           12
    "p_DP",        "pDP",      G8, "Number of bits for output code",                                        "",           8
    "Tx",          "Tx",       G9, "Across CCD-line",                                                       "",           0.14
    "Ty",          "Ty",       G9, "Along CCD-line",                                                        "",           0.22
    };
s = cell2struct(c, {'name', 'symbol', 'group', 'description', 'unit', 'default'}, 2);
end
