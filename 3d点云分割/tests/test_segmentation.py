import numpy as np
from segmentation.ground_ransac import extract_ground_ransac
from segmentation.height_filter import classify_by_height


def test_ground_extraction_on_plane():
    ground = np.random.rand(100, 3)
    ground[:, 2] = 0.0
    non_ground = np.random.rand(20, 3) + np.array([0, 0, 1.0])
    points = np.vstack([ground, non_ground])
    mask = extract_ground_ransac(points, residual_threshold=0.1)
    assert mask[:100].sum() >= 80
    assert mask[100:].sum() <= 5


def test_height_classification():
    points = np.array([
        [0, 0, 0.0],
        [1, 1, 0.05],
        [2, 2, 1.0],
        [3, 3, -0.5],
    ])
    mask = np.array([True, True, False, False])
    result = classify_by_height(points, mask, tolerance=0.10)
    assert result["ground"][0] and result["ground"][1]
    assert result["non_ground"][2] and result["non_ground"][3]
