import numpy as np


def classify_by_height(
    points: np.ndarray,
    ground_mask: np.ndarray,
    tolerance: float = 0.10,
) -> dict:
    """Classify points into ground/non-ground/noise based on height relative to fitted plane."""
    ground_pts = points[ground_mask]
    plane = fit_plane(ground_pts)
    heights = points[:, 2] - plane_height(points[:, :2], plane)

    ground = (heights >= -tolerance) & (heights <= tolerance)
    non_ground = heights > tolerance
    negative = heights < -tolerance
    return {
        "ground": ground,
        "non_ground": non_ground | negative,
        "heights": heights,
    }


def fit_plane(points: np.ndarray) -> np.ndarray:
    """Fit ax + by + c = z, returns [a, b, c]."""
    A = np.hstack([points[:, :2], np.ones((len(points), 1))])
    coeffs, *_ = np.linalg.lstsq(A, points[:, 2], rcond=None)
    return coeffs


def plane_height(xy: np.ndarray, plane: np.ndarray) -> np.ndarray:
    return xy @ plane[:2] + plane[2]
