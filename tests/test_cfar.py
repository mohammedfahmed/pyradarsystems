import numpy as np

from pyradarsystems.detection import ca_cfar_1d, ca_cfar_2d


def test_cfar_detects_strong_target() -> None:
    power = np.ones(256)
    power[128] = 1000.0
    detections, threshold = ca_cfar_1d(power, training_cells=12, guard_cells=3, pfa=1e-4)
    assert detections[128]
    assert np.isfinite(threshold[128])


def test_2d_cfar_shapes() -> None:
    power = np.ones((64, 32))
    power[30, 16] = 1e5
    detections, threshold = ca_cfar_2d(power, training=(4, 3), guard=(1, 1), pfa=1e-4)
    assert detections.shape == power.shape
    assert threshold.shape == power.shape
    assert detections[30, 16]
