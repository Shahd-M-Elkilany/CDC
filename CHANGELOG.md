# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned
- Step 2: payload geometry (GSD, swath, line-rate match) and SNR per spectral band.

## [0.1.0] - 2026-10-19

Step 1 complete: the SNR model of EGS YZH MAN 129 00 in Python and MATLAB.

### Added
- SNR model, stages 1–30 of §5.2, with the 27 inputs of §5.1 and the §6 input rules.
  Python: `cdc.snr`. MATLAB: `+cdc/+snr`.
- Shared reference data (`reference/`): the Annex B inputs, the 38 printed values, and the
  expected report. Both implementations are tested against it.
- Command line `python -m cdc snr` with `--set`, `-i`, `--json` and `--list-inputs`;
  MATLAB entry point `runSnr`.
- Solar-constant figure (`--plot`, `--show`, `runSnr("--plot")`, `cdc.snr.plotSolar`):
  - the Annex B table and its spline
  - the implied spectrum, with the in-band area
  - the irradiance through stages 3–8
  - SNR against the band edge
- Helpers that expose the absolute value behind stage 4: `in_band_solar_constant` /
  `inBandSolarConstant`, `solar_spectral_irradiance`, `solar_table_steps`, `solarTable`.
- VS Code support:
  - `python/examples/solar_figure.py` (Run Cell)
  - launch configurations, workspace settings, recommended extensions
- CI on every push:
  - Python 3.12 on Ubuntu and Windows (ruff, pytest, example script)
  - MATLAB R2023a (code issues, tests)
- MIT license.

### Fixed
- The report now prints on Windows consoles with legacy code pages (e.g. cp1256).
- MATLAB R2023a: `cell2struct` field names.

[Unreleased]: https://github.com/Shahd-M-Elkilany/CDC/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Shahd-M-Elkilany/CDC/releases/tag/v0.1.0
