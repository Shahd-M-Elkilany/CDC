function plan = buildfile
%BUILDFILE  buildtool        lint, then test (default)
%           buildtool test   tests only
%           buildtool lint   Code Analyzer (fails on errors)
plan = buildplan(localfunctions);
plan.DefaultTasks = ["lint", "test"];
end

function lintTask(~)
% Code Analyzer over the package, scripts and tests; fail on errors.
issues = codeIssues(["+cdc", "tests", "runSnr.m"]);
if ~isempty(issues.Issues)
    disp(issues.Issues(:, ["Location", "Severity", "Description"]));
end
assert(~any(issues.Issues.Severity == "error"), "Code Analyzer found errors.");
end

function testTask(~)
% All tests, including the Annex B digit-by-digit check and the shared report.
results = runtests("tests", "OutputDetail", "concise");
disp(table(results));
assertSuccess(results);
end
