function p = defaultInputs(varargin)
%DEFAULTINPUTS Inputs of the SNR calculation: Annex B values, optionally overridden.
%   p = cdc.snr.defaultInputs()                      Annex B worked example
%   p = cdc.snr.defaultInputs("D", 0.2, "nu_x", 1000) override by name
%   p = cdc.snr.defaultInputs(s)                     override with the fields of struct s
spec = cdc.snr.inputSpec();
p = struct();
for k = 1:numel(spec)
    p.(spec(k).name) = spec(k).default;
end
if nargin == 1 && isstruct(varargin{1})
    over = varargin{1};
    names = string(fieldnames(over))';
    vals = cellfun(@(n) over.(n), cellstr(names), "UniformOutput", false);
else
    if mod(nargin, 2) ~= 0
        error("cdc:snr:args", "Give name, value pairs.");
    end
    names = string(varargin(1:2:end));
    vals = varargin(2:2:end);
end
for k = 1:numel(names)
    if ~isfield(p, names(k))
        error("cdc:snr:unknownInput", "Unknown input ""%s"". Known: %s", names(k), ...
            strjoin(string({spec.name}), ", "));
    end
    p.(names(k)) = double(vals{k});
end
end
