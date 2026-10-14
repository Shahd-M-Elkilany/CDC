function e = validate(p)
%VALIDATE Allowed values from section 6 of EGS YZH MAN 129 00.
%   problems = cdc.snr.validate(p) returns a string array of violated rules
%   (empty when the inputs are valid). Same rules as the Python version.
e = strings(0, 1);
inRange("lam_min", 0.22e-6, 10e-6, false);
inRange("lam_max", 0.22e-6, 10e-6, false);
if p.lam_min > p.lam_max
    e(end+1, 1) = "lam_min must not be greater than lam_max";
end
inRange("sun_elevation", 10, 90, false);
inRange("rho_L", 0, 1, false);
inRange("rho_D", 0, 1, false);
if p.rho_D > p.rho_L
    e(end+1, 1) = "rho_D (dark strip) must not be greater than rho_L (light strip)";
end
inRange("tau_At", 0, 1, true);        % 0 would make ln(τAt) and τ^sec(zS) undefined
inRange("tau_Os", 0, 1, true);
positive("D", "f", "dzy", "dy", "dx", "nu_x");
if p.dy > p.dzy
    e(end+1, 1) = "dy (photosite along CCD-line) must not be greater than dzy (photosite step)";
end
inRange("Kt", 0, 1, true);
if ~(p.N_El == round(p.N_El) && p.N_El >= 2)
    e(end+1, 1) = sprintf("N_El = %g must be an integer not smaller than 2", p.N_El);
end
positive("Hn_CCD", "RQ", "KA", "U_CCD_max");
if ~(p.KU >= 1)
    e(end+1, 1) = sprintf("KU = %g must not be smaller than 1", p.KU);
end
positive("TU", "R_equ", "U_ADC_max");
positiveInt("p_ADC");
positiveInt("p_DP");
if p.p_DP > p.p_ADC
    e(end+1, 1) = "p_DP must not be greater than p_ADC";
end
inRange("Tx", 0, 1, false);
inRange("Ty", 0, 1, false);

% ---- helpers (nested: they append to e) ----
    function inRange(name, lo, hi, loOpen)
        v = p.(name);
        if loOpen, okLo = v > lo; br = "("; else, okLo = v >= lo; br = "["; end
        if ~(okLo && v <= hi)
            e(end+1, 1) = sprintf("%s = %g must be in %s%g, %g]", name, v, br, lo, hi);
        end
    end
    function positive(varargin)
        for i = 1:numel(varargin)
            if ~(p.(varargin{i}) > 0)
                e(end+1, 1) = sprintf("%s = %g must be positive", varargin{i}, p.(varargin{i})); %#ok<AGROW>
            end
        end
    end
    function positiveInt(name)
        v = p.(name);
        if ~(v == round(v) && v >= 1)
            e(end+1, 1) = sprintf("%s = %g must be a positive integer", name, v);
        end
    end
end
