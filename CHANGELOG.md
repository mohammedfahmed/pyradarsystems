# PyRadarSystems Changelog

## 0.2.0 - 2026-07-31

- Added deterministic serial and process-parallel Monte Carlo studies.
- Added stable component-specific seed derivation and CSV seed manifests.
- Added confidence intervals, paired differences, and generated result bundles.
- Added generated CSV and LaTeX summary tables plus YAML/JSON provenance.
- Added uniform, Hann, Hamming, Blackman, Taylor, and Chebyshev tapers.
- Added explicit total-power, peak-power, and broadside-gain normalization policies.
- Added isotropic, cosine-power, and tabulated azimuth element patterns.
- Integrated TX/RX element-pattern voltage scaling into the TDM-FMCW simulator.
- Added array-pattern HPBW, first-null beamwidth, PSLR, and ISLR metrics.
- Added deterministic distributed angular clutter and total-RCS conservation.
- Added single-tone, FMCW range, and Doppler velocity CRLB utilities.
- Extended YAML configuration parsing for element patterns and taper policies.
- Added a paired aperture-taper Monte Carlo example and vector figure output.
- Vectorized array-pattern steering matrices for efficient large Monte Carlo studies.
- Expanded validation from 7 to 18 automated tests.

## 0.1.0 - 2026-07-30

- Initial research-ready 77-GHz FMCW TDM-MIMO release.
- Added waveform, array, point-target, radar-system, and simulation models.
- Added labelled raw and range-Doppler cubes.
- Added Bartlett, Capon, MUSIC, TDM compensation, and CA-CFAR.
- Added reproducibility manifests, CLI demo, tests, and examples.
