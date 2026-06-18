import numpy as np
from pathlib import Path
from data.parser import parse_bin_file


def test_parse_bin_file(tmp_path):
    points = np.array([[1.0, 2.0, 3.0, 0.0], [4.0, 5.0, 6.0, 0.0]], dtype=np.float32)
    path = tmp_path / "test.bin"
    path.write_bytes(points.tobytes())
    parsed = parse_bin_file(str(path))
    assert parsed.shape == (2, 3)
    assert np.allclose(parsed[0], [1.0, 2.0, 3.0])
