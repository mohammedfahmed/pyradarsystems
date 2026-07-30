# PyRadarSystems Roadmap

## v0.2 - Research experiment layer

- Batched Monte Carlo runner with parallel workers
- Confidence intervals and seed manifests
- Fair-normalization policies for taper/beamformer comparisons
- Automated figure and table generation
- CRLB utilities

## v0.3 - Hardware bridge

- TI mmWave configuration parser
- DCA1000 binary reader
- ADC cube reordering and calibration
- Synthetic/measured pipeline parity

## v0.4 - Physical impairments

- Chirp nonlinearity
- TX/RX leakage and DC removal
- IQ imbalance
- Per-channel timing skew
- Mutual-coupling matrix interface
- Frequency-dependent element patterns

## v0.5 - Scenes

- Ground clutter and Swerling models
- Multipath path-list interface
- Extended point-cloud targets
- Micro-Doppler primitives
- Inter-radar interference

## v1.0 - Validated research release

- Independent MATLAB/Python cross-validation suite
- Hardware-measurement benchmark dataset
- Stable API and reference documentation
- Performance backends using Numba/CuPy

## Post-v1.0 - General radar systems expansion

- Pulsed, phase-coded, CW, OFDM, and configurable arbitrary waveforms
- Wideband, subarray, conformal-array, polarization, and near-field processing
- Multi-target tracking, data association, and sensor fusion
- Scene geometry, ray-tracing adapters, extended targets, and mesh scattering
- GPU and differentiable backends
- MATLAB migration and cross-validation utilities
