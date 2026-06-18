import numpy as np
from sklearn.linear_model import RANSACRegressor


def extract_ground_ransac(
    points: np.ndarray,
    max_trials: int = 100,
    residual_threshold: float = 0.05,
    min_samples: int = 3,
) -> np.ndarray:
    """Returns boolean mask of ground points."""
    if len(points) < min_samples:
        return np.zeros(len(points), dtype=bool)

    xy = points[:, :2]
    z = points[:, 2]
    ransac = RANSACRegressor(
        max_trials=max_trials,
        residual_threshold=residual_threshold,
        min_samples=min_samples,
    )
    ransac.fit(xy, z)
    return ransac.inlier_mask_
