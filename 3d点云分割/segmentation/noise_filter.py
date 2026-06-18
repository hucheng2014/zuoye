import numpy as np
from sklearn.neighbors import NearestNeighbors


def detect_noise(points: np.ndarray, n_neighbors: int = 5, radius: float = 0.5) -> np.ndarray:
    """Returns boolean mask for noise points (isolated)."""
    if len(points) <= n_neighbors:
        return np.zeros(len(points), dtype=bool)
    nbrs = NearestNeighbors(n_neighbors=min(n_neighbors + 1, len(points))).fit(points)
    distances, _ = nbrs.kneighbors(points)
    avg_dist = distances[:, 1:].mean(axis=1)
    threshold = np.percentile(avg_dist, 95) * 2
    return avg_dist > threshold
