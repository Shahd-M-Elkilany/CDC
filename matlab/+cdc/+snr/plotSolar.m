function fig = plotSolar(p, file, visible)
%PLOTSOLAR The solar constant in the SNR model: where it comes from and where it goes.
%   cdc.snr.plotSolar()                       Annex B inputs
%   cdc.snr.plotSolar(p)                      p from cdc.snr.defaultInputs(...)
%   cdc.snr.plotSolar(p, "solar.png")         also save the figure
%   fig = cdc.snr.plotSolar(p, "", false)     invisible figure (batch / tests)
%
%   (a) W(λ): the Annex B table (page 23) and its cubic spline - the Mathcad plot - with
%       the operating range λmin..λmax and the two read-outs of stage 3.
%   (b) The solar spectrum above the atmosphere implied by the table, E_SC*dW/dλ. The whole
%       area is E_SC = 1400 W/m² (stage 4, Annex B page 22); the area inside the operating
%       range is E_SC*(Wmax - Wmin), the absolute value that enters stage 4.
%   (c) What becomes of it: solar constant -> in band -> at the ground -> reflected -> CCD-line.
%   (d) System behaviour: SNR µL as the upper band edge λmax moves (other inputs fixed).
%   Same figure as the Python version (cdc.snr.plots.plot_solar).
if nargin < 1 || isempty(p), p = cdc.snr.defaultInputs(); end
if nargin < 2, file = ""; end
if nargin < 3, visible = true; end

TABLE = [235 104 52]/255;   MODEL = [42 120 214]/255;   BAND = [230 229 223]/255;
INK = [31 31 30]/255;       INK2 = [107 106 99]/255;    GRID = [236 235 230]/255;

t = cdc.snr.solarTable();
r = cdc.snr.calculate(p);
lo = p.lam_min * 1e6;   hi = p.lam_max * 1e6;           % µm
eBand = cdc.snr.inBandSolarConstant(p.lam_min, p.lam_max);

fig = figure("Color", "w", "Position", [60 60 1300 900], "Visible", matlab.lang.OnOffSwitchState(visible));
set(fig, "DefaultTextInterpreter", "none", "DefaultAxesTickLabelInterpreter", "none", ...
    "DefaultLegendInterpreter", "none");
tl = tiledlayout(fig, 2, 2, "TileSpacing", "compact", "Padding", "compact");
title(tl, sprintf("Solar constant in the SNR model  -  EGS YZH MAN 129 00, Annex B (λ = %g…%g µm, sun elevation %g°)", ...
    lo, hi, p.sun_elevation), "FontSize", 12, "Color", INK, "Interpreter", "none");

% (a) cumulative fraction W(λ) - the Mathcad plot
a = nexttile(tl); hold(a, "on");
patch(a, [lo hi hi lo], [0 0 1.02 1.02], BAND, "EdgeColor", "none");
x = linspace(t.lambda(1), 5e-6, 1500);
hs = plot(a, x*1e6, cdc.snr.solarFraction(x), "Color", MODEL, "LineWidth", 2);
k = t.lambda <= 5e-6;
ht = plot(a, t.lambda(k)*1e6, t.W(k), "o", "MarkerSize", 5, "MarkerFaceColor", "w", ...
    "MarkerEdgeColor", TABLE, "LineWidth", 1.5);
plot(a, [0 lo lo], [r.W_min r.W_min 0], "--", "Color", INK2);
plot(a, [0 hi hi], [r.W_max r.W_max 0], "--", "Color", INK2);
plot(a, [lo 4.3], [r.W_min r.W_min], ":", "Color", INK2);
plot(a, [hi 4.3], [r.W_max r.W_max], ":", "Color", INK2);
plot(a, [4.3 4.3], [r.W_min r.W_max], "-", "Color", INK);
text(a, lo + 0.08, r.W_min - 0.025, sprintf("W(λmin) = %.4f", r.W_min), "Color", INK, "FontSize", 9);
text(a, hi + 0.08, r.W_max + 0.025, sprintf("W(λmax) = %.4f", r.W_max), "Color", INK, "FontSize", 9);
text(a, 4.38, (r.W_min + r.W_max)/2, sprintf("Wmax − Wmin\n= %.4f", r.W_max - r.W_min), "Color", INK, "FontSize", 9);
text(a, (lo + hi)/2, 0.97, sprintf("operating\nrange"), "HorizontalAlignment", "center", ...
    "VerticalAlignment", "top", "Color", INK2, "FontSize", 8.5);
xlim(a, [0 5]); ylim(a, [0 1.02]);
xlabel(a, "wave length λ, µm"); ylabel(a, "part of solar constant in 0…λ, W(λ)");
legend(a, [hs ht], ["cubic spline (Mathcad cspline)", "table, Annex B p. 23"], "Location", "southeast", "Box", "off");
style(a, "(a) Stage 3 - spectral distribution of the solar constant");

% (b) the spectrum implied by the table; areas = W/m²
b = nexttile(tl); hold(b, "on");
xs = linspace(t.lambda(1), 3e-6, 3000);
ys = cdc.snr.solarSpectralIrradiance(xs);
in = xs >= p.lam_min & xs <= p.lam_max;
fill(b, [xs(in) fliplr(xs(in))]*1e6, [ys(in) zeros(1, nnz(in))], MODEL, "FaceAlpha", 0.18, "EdgeColor", "none");
[L, R, avg] = cdc.snr.solarTableSteps();
m = R <= 3e-6;
sx = reshape([L(m); L(m); R(m); R(m)], 1, []) * 1e6;
sy = reshape([zeros(1, nnz(m)); avg(m); avg(m); zeros(1, nnz(m))], 1, []);
hb = plot(b, sx, sy, "Color", TABLE, "LineWidth", 1.2);
hl = plot(b, xs*1e6, ys, "Color", MODEL, "LineWidth", 2);
text(b, 0.97, 0.95, sprintf(['whole area (0.22…10 µm) = E_SC·W(10 µm) = %.0f W/m²\n' ...
    'shaded area = E_SC·(Wmax − Wmin)\n   = %.0f × (%.4f − %.4f)\n   = %.1f W/m²  ← enters stage 4'], ...
    t.E_SC * t.W(end), t.E_SC, r.W_max, r.W_min, eBand), "Units", "normalized", ...
    "HorizontalAlignment", "right", "VerticalAlignment", "top", "FontName", "Consolas", "FontSize", 9, "Color", INK);
text(b, 0.97, 0.36, sprintf("the spline's wiggles near 0.4 µm come from uneven\ntable steps there; W(λ) itself (panel a) is smooth"), ...
    "Units", "normalized", "HorizontalAlignment", "right", "VerticalAlignment", "top", "FontSize", 8, "Color", INK2);
xlim(b, [0.2 3]); ylim(b, [0 inf]);
xlabel(b, "wave length λ, µm"); ylabel(b, "spectral irradiance above atmosphere, W/(m²·µm)");
legend(b, [hl hb], ["spline: E_SC·dW/dλ", "table: E_SC·ΔW/Δλ per interval"], "Location", "east", "Box", "off");
style(b, sprintf("(b) Where the absolute value comes from: E_SC = %.0f W/m² × table", t.E_SC));

% (c) the chain from the solar constant to the focal plane
c = nexttile(tl); hold(c, "on");
zS = deg2rad(r.zS_deg);
atm = p.tau_At^(1/cos(zS));
steps = {
    "E_SC  solar constant, all λ, top of atmosphere   [p. 22]",                    t.E_SC
    "E_SC·(Wmax−Wmin)  in band, top of atmosphere   [stage 3]",                    eBand
    sprintf("× τAt^sec zS = %.3f  after the atmosphere", atm),                     eBand * atm
    sprintf("× cos zS = %.3f  E_Edir, direct, on the ground   [stage 4]", cos(zS)), r.E_Edir
    "+ E_Edis  EΣ, direct + diffuse, on the ground   [stages 5-6]",                r.E_sum
    sprintf("× ρL = %g  R_L, leaving the light strip   [stage 7]", p.rho_L),        r.R_L
    "× τAt·τOs·(D/f)²/4  E_L1, on the CCD-line   [stage 8]",                       r.E_L1
    };
n = size(steps, 1);
yy = n-1:-1:0;
vals = [steps{:, 2}];
barh(c, yy, vals, 0.55, "FaceColor", MODEL, "EdgeColor", "none", "BaseValue", 1e-2);
set(c, "XScale", "log");
for i = 1:n
    text(c, vals(i) * 1.15, yy(i), sprintf("%.4g W/m²", vals(i)), "Color", INK, "FontSize", 9);
    text(c, 2e-2, yy(i) + 0.3, steps{i, 1}, "Color", INK2, "FontSize", 8.5, "VerticalAlignment", "bottom");
end
xlim(c, [1e-2 2e4]); ylim(c, [-0.6 n - 0.05]); yticks(c, []);
c.XMinorGrid = "off"; c.XMinorTick = "off";
xlabel(c, "irradiance, W/m² (log scale)");
style(c, "(c) What becomes of it - stages 3 to 8");

% (d) system behaviour against the band edge
d = nexttile(tl); hold(d, "on");
lamHi = linspace(max(p.lam_min * 1.05, 0.6e-6), 1.2e-6, 61);
mu = nan(size(lamHi));
for i = 1:numel(lamHi)
    q = p;  q.lam_max = lamHi(i);
    try
        rr = cdc.snr.calculate(q);  mu(i) = rr.mu_L;
    catch
    end
end
plot(d, lamHi*1e6, mu, "Color", MODEL, "LineWidth", 2);
plot(d, hi, r.mu_L, "o", "MarkerSize", 8, "MarkerFaceColor", MODEL, "MarkerEdgeColor", "w", "LineWidth", 2);
text(d, hi + 0.015, r.mu_L - 6, sprintf("design point\nλmax = %g µm, µL = %.1f", hi, r.mu_L), ...
    "Color", INK, "FontSize", 9, "VerticalAlignment", "top");
if ~isempty(r.clipped)
    text(d, 0.02, 0.04, "note: " + strjoin(r.clipped, "; "), "Units", "normalized", "FontSize", 8, "Color", INK2);
end
xlabel(d, "upper band edge λmax, µm"); ylabel(d, "SNR µL (uniform background ρL)");
style(d, "(d) System behaviour - SNR as the band widens (other inputs fixed)");

if strlength(string(file)) > 0
    exportgraphics(fig, file, "Resolution", 150, "BackgroundColor", "white");
end

    function style(ax, ttl)
        title(ax, ttl, "FontSize", 10.5, "Color", INK, "FontWeight", "bold");
        ax.TitleHorizontalAlignment = "left";
        grid(ax, "on"); ax.GridColor = GRID; ax.GridAlpha = 1; ax.Layer = "bottom";
        box(ax, "off"); ax.XColor = INK2; ax.YColor = INK2; ax.FontSize = 8.5;
    end
end
