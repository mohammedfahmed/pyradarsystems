# Signal model

Version 0.1 directly generates the dechirped complex baseband samples. For target `k`, transmitter `p`, receiver `q`, chirp `m`, and fast-time sample `n`,

\[
x_{p,q}[m,n] = \sum_k A_k w_p w_q
\exp\{j[2\pi f_{b,k}nT_s + 2\pi f_{D,k}t_{p,m} + \phi_{p,q,k} + \phi_{0,k}]\} + \eta.
\]

The implemented terms are:

\[
f_b = \frac{2SR}{c},\qquad f_D = \frac{2v}{\lambda},
\]

\[
\phi_{p,q,k}=\frac{2\pi}{\lambda}(\mathbf r_{\mathrm{TX},p}+\mathbf r_{\mathrm{RX},q})^T\mathbf u_k,
\]

and the received power follows the monostatic radar equation

\[
P_r = \frac{P_tG_tG_r\lambda^2\sigma}{(4\pi)^3R^4L}.
\]

The TDM chirp time is

\[
t_{p,m}=pT_{\mathrm{PRI}}+mN_{\mathrm{TX}}T_{\mathrm{PRI}}.
\]

Consequently, moving targets acquire a transmitter-dependent phase offset. `extract_virtual_snapshot(..., compensate_tdm=True)` removes the estimated offset before angle estimation.

## Assumptions

- Far-field plane-wave model
- Monostatic equivalent MIMO phase centres
- Constant target range and velocity over one frame
- Narrowband array response at the carrier frequency
- Ideal linear chirp after dechirping
- Independent circular complex Gaussian thermal noise
- No multipath, atmospheric attenuation, mutual coupling, or extended-target scattering in v0.1
