function [r, p] = runSnr(varargin)
%RUNSNR Signal/noise ratio of a CCD-line EO imager (EGS YZH MAN 129 00).
%   runSnr                          Annex B example, prints the full report
%   runSnr("D", 0.2, "nu_x", 1000)  override inputs by name (others = Annex B)
%   runSnr("my_inputs.json")        inputs from JSON (same format as the Python CLI)
%   [r, p] = runSnr(...)            return results and inputs, print nothing
%   runSnr("--list")                the 27 input names, units and Annex B defaults
if nargin == 1 && (endsWith(string(varargin{1}), ".json"))
    data = jsondecode(fileread(varargin{1}));
    if isfield(data, "inputs"), data = data.inputs; end
    p = cdc.snr.defaultInputs(data);
elseif nargin == 1 && string(varargin{1}) == "--list"
    for s = cdc.snr.inputSpec()'
        fprintf("%-14s %8s  %-11g %-11s %s\n", s.name, s.symbol, s.default, s.unit, s.description);
    end
    return
else
    p = cdc.snr.defaultInputs(varargin{:});
end
res = cdc.snr.calculate(p);
if nargout == 0
    fprintf("%s", cdc.snr.report(p, res));
else
    r = res;
end
end
