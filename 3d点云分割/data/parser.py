import struct
import numpy as np
from pathlib import Path

PointCloud = np.ndarray  # shape (N, 3+) with x,y,z in first 3 columns


def _struct_code(size: int, pcd_type: str) -> str:
    if pcd_type == "F":
        if size == 4:
            return "f"
        if size == 8:
            return "d"
    elif pcd_type == "U":
        if size == 1:
            return "B"
        if size == 2:
            return "H"
        if size == 4:
            return "I"
        if size == 8:
            return "Q"
    elif pcd_type == "I":
        if size == 1:
            return "b"
        if size == 2:
            return "h"
        if size == 4:
            return "i"
        if size == 8:
            return "q"
    raise ValueError(f"Unsupported PCD field size={size} type={pcd_type}")


def parse_pcd_file(path: str) -> PointCloud:
    text = Path(path).read_text(errors="ignore")
    lines = text.splitlines()
    data_start = next(i for i, line in enumerate(lines) if line.startswith("DATA"))
    header = lines[:data_start]
    fields = [line.split()[1:] for line in header if line.startswith("FIELDS")][0]
    sizes = [int(x) for x in [line.split()[1:] for line in header if line.startswith("SIZE")][0]]
    types = [line.split()[1:] for line in header if line.startswith("TYPE")][0]
    counts = [int(x) for x in [line.split()[1:] for line in header if line.startswith("COUNT")][0]]
    width = int([line.split()[1] for line in header if line.startswith("WIDTH")][0])
    data_type = lines[data_start].split()[1]

    if data_type == "ascii":
        data = np.loadtxt(lines[data_start + 1 :], dtype=np.float32)
        return data[:, :3]

    if data_type != "binary":
        raise ValueError(f"Unsupported PCD DATA type: {data_type}")

    # Build per-point struct format using little-endian byte order (PCD binary is LE on x86).
    record_fmt = "".join(
        f"{count}{_struct_code(size, pcd_type)}"
        for size, pcd_type, count in zip(sizes, types, counts)
    )
    record_size = struct.calcsize("<" + record_fmt)
    total = record_size * width

    raw = Path(path).read_bytes()
    marker = f"DATA {data_type}\n"
    offset = text.find(marker) + len(marker)
    full_fmt = "<" + record_fmt * width
    data = np.array(
        struct.unpack(full_fmt, raw[offset : offset + total]),
        dtype=np.float32,
    ).reshape(width, -1)
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
