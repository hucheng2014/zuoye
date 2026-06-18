import struct
import numpy as np
from pathlib import Path

PointCloud = np.ndarray  # shape (N, 3+) with x,y,z in first 3 columns


def parse_pcd_file(path: str) -> PointCloud:
    text = Path(path).read_text(errors="ignore")
    lines = text.splitlines()
    data_start = next(i for i, line in enumerate(lines) if line.startswith("DATA"))
    header = lines[:data_start]
    fields = [line.split()[1:] for line in header if line.startswith("FIELDS")][0]
    sizes = [int(x) for x in [line.split()[1:] for line in header if line.startswith("SIZE")][0]]
    counts = [int(x) for x in [line.split()[1:] for line in header if line.startswith("COUNT")][0]]
    width = int([line.split()[1] for line in header if line.startswith("WIDTH")][0])
    data_type = lines[data_start].split()[1]
    fmt_parts = []
    for s, c in zip(sizes, counts):
        if s == 1:
            code = "b"
        elif s == 2:
            code = "h"
        elif s == 4:
            code = "f"
        else:
            raise ValueError(f"Unsupported size {s}")
        fmt_parts.append(f"{c}{code}")
    fmt = "".join(fmt_parts)

    if data_type == "ascii":
        data = np.loadtxt(lines[data_start + 1:], dtype=np.float32)
    elif data_type == "binary":
        raw = Path(path).read_bytes()
        marker = f"DATA {data_type}\n"
        offset = text.find(marker) + len(marker)
        total = struct.calcsize(fmt) * width
        data = np.array(
            struct.unpack(fmt * width, raw[offset:offset + total]),
            dtype=np.float32,
        ).reshape(width, -1)
    else:
        raise ValueError(f"Unsupported PCD DATA type: {data_type}")
    return data[:, :3]


def parse_bin_file(path: str) -> PointCloud:
    raw = Path(path).read_bytes()
    points = np.frombuffer(raw, dtype=np.float32).reshape(-1, 4)
    return points[:, :3]


def parse_las_file(path: str) -> PointCloud:
    try:
        import laspy
    except ImportError as e:
        raise ImportError("laspy required for .las files") from e
    las = laspy.read(path)
    return np.vstack([las.x, las.y, las.z]).T
