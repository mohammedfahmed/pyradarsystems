# Aperture tapers and element patterns

`make_taper` constructs standard windows. `normalize_taper` makes the comparison policy explicit.

- `constant_total_power`: preserves `sum(|w|^2)` relative to a uniform aperture.
- `constant_peak_power`: preserves the maximum per-element power.
- `constant_broadside_gain`: preserves the coherent broadside sum.
- `none`: applies the coefficients unchanged.

These policies are not interchangeable. A taper with equal total power may exceed the uniform per-element peak power. A taper with equal peak power generally loses total radiated power and broadside gain.

Element patterns return normalized one-way power gain. Available models are isotropic, cosine-power, and tabulated azimuth cuts for measured or electromagnetic-solver data. The simulator converts TX and RX power gains to voltage factors before adding target echoes.

`array_pattern` and `pattern_metrics` calculate normalized patterns, half-power beamwidth, first-null beamwidth, peak sidelobe level, and integrated sidelobe ratio. The mainlobe is bounded by the nearest local minima around the global peak.
