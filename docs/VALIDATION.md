# Validation status

## Automated in v0.2

1. FMCW range-resolution and beat-frequency formulas.
2. Invalid waveform sampling configuration rejection.
3. Broadside steering-vector phase.
4. Virtual-array dimensions.
5. End-to-end range, velocity, and azimuth recovery for a moving point target.
6. CA-CFAR detection and 2D output dimensions.
7. Empirical 1D CA-CFAR false-alarm rate on exponential noise.
8. Constant-total-power taper normalization.
9. Uniform 16-element half-wavelength ULA HPBW and PSLR reference values.
10. Cosine element-pattern normalization and off-boresight attenuation.
11. TX/RX element-pattern voltage scaling in the simulator.
12. Distributed-clutter deterministic sampling and total-RCS conservation.
13. Stable, stream-specific seed derivation.
14. Reproducible Monte Carlo records.
15. CSV, LaTeX, YAML, JSON, and seed-manifest export.
16. Confidence-interval construction.
17. Paired-difference evaluation using matched trials.
18. Range and velocity CRLB monotonic trends with SNR and sample count.

## Required before a journal-grade v1.0 claim

- Received-power comparison against an independent radar-equation implementation.
- Thermal-noise variance and distribution tests over large sample counts.
- CA-CFAR calibration over at least 10^7 eligible cells and several PFA values.
- Monte Carlo range, velocity, and angle RMSE curves versus SNR and CRLB.
- TDM compensation tests across the full unambiguous velocity interval.
- Cross-validation against MATLAB and an independent Python framework.
- Calibration-error sensitivity benchmarks.
- Measured ADC validation using a named 77-GHz radar front end.

No planned validation is represented as completed.
