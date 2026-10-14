classdef TestSNR < matlab.unittest.TestCase
    %TESTSNR Step 1 acceptance: the SNR model reproduces Annex B of EGS YZH MAN 129 00
    %   to every digit Mathcad prints, and prints the same report as the Python
    %   version. Reads the shared ../reference files.

    properties (TestParameter)
        % every value printed in Annex B (same keys as reference/annex_b.json "expected")
        stage = {'zS_deg', 'dt', 'W_min', 'W_max', 'E_Edir', 'E_Edis', 'E_sum', 'R_L', 'R_D', ...
                 'E_L1', 'E_D1', 'H_L1', 'H_D1', 'P_L1', 'P_D1', 'Ne_L1', 'Ne_D1', ...
                 'Uccd_L1', 'Uccd_D1', 'Uamp_L1', 'Uamp_D1', 'mE', 'mPx', 'mPy', ...
                 'Uamp_Lx', 'Uamp_Dx', 'Uamp_Ly', 'Uamp_Dy', 'Un_F', 'Un_CCD', 'Un_AMP', ...
                 'Un_ADC', 'Un_DP', 'Un', 'mu_L', 'mu_D', 'mu_x', 'mu_y'}
    end

    properties
        Ref     % decoded reference/annex_b.json
        Root    % repository root
    end

    methods (TestClassSetup)
        function setup(tc)
            here = fileparts(mfilename("fullpath"));            % .../matlab/tests
            tc.applyFixture(matlab.unittest.fixtures.PathFixture(fileparts(here)));
            tc.Root = fileparts(fileparts(here));
            tc.Ref = jsondecode(readUtf8(fullfile(tc.Root, "reference", "annex_b.json")));
        end
    end

    methods (Test)
        function referenceListsEveryStage(tc)
            tc.verifyEqual(sort(string(fieldnames(tc.Ref.expected))), sort(string(tc.stage')));
        end

        function defaultsAreAnnexBInputs(tc)
            p = cdc.snr.defaultInputs();
            for n = string(fieldnames(tc.Ref.inputs))'
                tc.verifyEqual(p.(n), tc.Ref.inputs.(n), "RelTol", 1e-12, n);
            end
            tc.verifyEqual(numel(fieldnames(p)), 27);
        end

        function matchesEveryPrintedDigit(tc, stage)
            r = cdc.snr.calculate(cdc.snr.defaultInputs(tc.Ref.inputs));
            printed = string(tc.Ref.expected.(stage));
            tol = halfUlp(printed) * (1 + 1e-9);
            tc.verifyLessThanOrEqual(abs(r.(stage) - str2double(printed)), tol, ...
                sprintf("%s = %.10g does not round to the printed %s", stage, r.(stage), printed));
        end

        function splineMatchesMathcadCspline(tc)
            tc.verifyEqual(cdc.snr.solarFraction(0.5e-6), 0.236, "AbsTol", 1e-12);
            tc.verifyEqual(cdc.snr.solarFraction(0.885e-6), 0.6515550141, "AbsTol", 1e-9);
        end

        function annexBInputsAreValid(tc)
            tc.verifyEmpty(cdc.snr.validate(cdc.snr.defaultInputs()));
        end

        function section6Rules(tc)
            cases = {
                {"lam_min", 0.1e-6},                    "lam_min"
                {"lam_min", 0.9e-6, "lam_max", 0.8e-6}, "must not be greater than lam_max"
                {"sun_elevation", 5},                   "sun_elevation"
                {"rho_D", 0.3},                         "rho_D (dark strip)"
                {"tau_At", 0},                          "tau_At"
                {"dy", 12e-6},                          "dzy"
                {"Kt", 1.5},                            "Kt"
                {"N_El", 1},                            "N_El"
                {"KU", 0.5},                            "KU"
                {"p_ADC", 10.5},                        "p_ADC"
                {"p_DP", 14},                           "p_DP must not be greater than p_ADC"
                {"Tx", 1.2},                            "Tx"
                {"D", -1},                              "D"
                };
            for k = 1:size(cases, 1)
                p = cdc.snr.defaultInputs(cases{k, 1}{:});
                problems = cdc.snr.validate(p);
                tc.verifyTrue(any(contains(problems, cases{k, 2})), ...
                    sprintf("case %d: expected a problem mentioning ""%s""", k, cases{k, 2}));
                tc.verifyError(@() cdc.snr.calculate(p), "cdc:snr:invalidInputs");
            end
        end

        function unknownInputNameIsRejected(tc)
            tc.verifyError(@() cdc.snr.defaultInputs("aperture", 0.2), "cdc:snr:unknownInput");
        end

        function saturationClipsStages12And13(tc)
            r = cdc.snr.calculate(cdc.snr.defaultInputs("nu_x", 90));
            tc.verifyEqual([r.Uamp_L1, r.Uamp_D1], [1 1]);
            tc.verifyTrue(any(contains(r.clipped, "U_ADC_max")));
            r = cdc.snr.calculate(cdc.snr.defaultInputs("U_CCD_max", 0.1));
            tc.verifyEqual(r.Uccd_L1, 0.1);
            tc.verifyTrue(any(contains(r.clipped, "U_CCD_max")));
        end

        function reportIsTheSharedReference(tc)
            % Python and MATLAB must print the same report, character for character
            expected = string(readUtf8(fullfile(tc.Root, "reference", "annex_b_report.txt")));
            expected = erase(expected, char(13));                 % tolerate CRLF checkouts
            actual = cdc.snr.report(cdc.snr.defaultInputs(), cdc.snr.calculate());
            tc.verifyEqual(actual, expected);
        end

        function inBandSolarConstantIsBehindStage4(tc)
            % where the absolute value comes from: E_SC = 1400 W/m² x the Annex B table
            p = cdc.snr.defaultInputs();
            r = cdc.snr.calculate(p);
            t = cdc.snr.solarTable();
            e = cdc.snr.inBandSolarConstant(p.lam_min, p.lam_max);
            tc.verifyEqual(t.E_SC, 1400);
            tc.verifyEqual(e, t.E_SC * (r.W_max - r.W_min), "RelTol", 1e-12);
            tc.verifyEqual(e, 581.777, "AbsTol", 5e-4);
            zS = deg2rad(r.zS_deg);
            tc.verifyEqual(r.E_Edir, e * p.tau_At^(1/cos(zS)) * cos(zS), "RelTol", 1e-12);
        end

        function spectrumIntegratesBackToTheTable(tc)
            x = linspace(0.5e-6, 0.885e-6, 20001);
            tc.verifyEqual(trapz(x * 1e6, cdc.snr.solarSpectralIrradiance(x)), 581.777, "AbsTol", 1e-3);
            [L, R, avg] = cdc.snr.solarTableSteps();
            t = cdc.snr.solarTable();
            tc.verifyEqual(sum(avg .* (R - L) * 1e6), t.E_SC * t.W(end), "RelTol", 1e-12);
        end

        function solarFigure(tc)
            f = fullfile(tempdir, "cdc_solar_test.png");
            fig = cdc.snr.plotSolar(cdc.snr.defaultInputs("lam_max", 1.0e-6), f, false);
            tc.addTeardown(@() close(fig));
            tc.verifyEqual(numel(findobj(fig, "Type", "axes")), 4);
            info = dir(f);
            tc.verifyGreaterThan(info.bytes, 10000);
        end

        function runSnrReturnsResults(tc)
            [r, p] = runSnr("D", 0.2);
            tc.verifyEqual(p.D, 0.2);
            tc.verifyGreaterThan(r.mu_L, 152.3454);              % bigger aperture -> more signal
        end
    end
end

function t = halfUlp(printed)
% half a unit in the last printed digit: "2.237e-4" -> 5e-8, "152.3454" -> 5e-5
parts = split(lower(printed), "e");
mant = parts(1);
ex = 0;
if numel(parts) > 1, ex = str2double(parts(2)); end
dec = 0;
if contains(mant, "."), dec = strlength(extractAfter(mant, ".")); end
t = 0.5 * 10^(ex - dec);
end

function txt = readUtf8(file)
fid = fopen(file, "r", "n", "UTF-8");
c = onCleanup(@() fclose(fid));
txt = fread(fid, "*char")';
end
