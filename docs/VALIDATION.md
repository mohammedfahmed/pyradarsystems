# Validation plan

## Implemented in v0.1

1. FMCW range-resolution and beat-frequency formulas.
2. Broadside steering-vector phase.
3. Virtual-array dimensions.
4. End-to-end range, velocity, and azimuth recovery in a noise-free point-target case.
5. CFAR detection of a controlled strong cell.
6. Configuration hashing and seed recording.

## Required before a journal-grade v1.0 claim

- Received-power comparison against an independent radar-equation implementation.
- Empirical thermal-noise variance and distribution tests.
- Empirical CA-CFAR false-alarm calibration over at least 10^7 eligible cells.
- Monte Carlo range/velocity/angle RMSE curves versus SNR and CRLB trends.
- TDM compensation tests across unambiguous velocity.
- Cross-validation against MATLAB and at least one independent Python framework.
- Calibration-error sensitivity tests.
- Measured ADC validation using a named 77-GHz radar front end.

No unimplemented test is represented as completed.
