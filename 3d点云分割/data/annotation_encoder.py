import json
import base64
import copy
from typing import Dict, List, Set
import numpy as np


def encode_bitset(indices: np.ndarray) -> Dict[str, str]:
    """Encode a boolean mask or array of point indices into shapeData bitset format.

    Each entry key is '{chunk_index}_P0' and value is a uint64 string where
    bit b (0-63) represents point chunk_index*64 + b.
    """
    if isinstance(indices, np.ndarray) and indices.dtype == bool:
        idx = np.nonzero(indices)[0]
    else:
        idx = np.asarray(indices, dtype=np.int64)

    chunks: Dict[int, int] = {}
    for i in idx:
        chunk = int(i) // 64
        bit = int(i) % 64
        chunks[chunk] = chunks.get(chunk, 0) | (1 << bit)

    result = {}
    for chunk, bits in chunks.items():
        result[f"{chunk}_P0"] = str(bits)
    return result


def build_annotation_result(
    template: dict,
    labels_by_frame: List[Dict[str, np.ndarray]],
    category_map: Dict[str, str],
) -> dict:
    """Build annotation result from template and per-frame segmentation labels.

    category_map maps label name (e.g. 'ground') to instance category id (e.g. '0').
    """
    result = copy.deepcopy(template)
    for frame_idx, labels in enumerate(labels_by_frame):
        if frame_idx >= len(result.get("frames", [])):
            break
        frame = result["frames"][frame_idx]
        frame["instances"] = []
        for label_name, mask in labels.items():
            cat = category_map.get(label_name)
            if cat is None:
                continue
            if isinstance(mask, np.ndarray) and mask.dtype == bool:
                count = int(mask.sum())
            else:
                count = len(mask)
            if count == 0:
                continue
            instance = {
                "number": len(frame["instances"]) + 1,
                "id": f"auto-{label_name}-{frame_idx}",
                "category": cat,
                "createTime": 0,
                "updateTime": 0,
                "shapes": [
                    {
                        "id": f"auto-shape-{label_name}-{frame_idx}",
                        "name": cat,
                        "number": 1,
                        "type": "POINTS",
                        "createTime": 0,
                        "updateTime": 0,
                        "interpolated": False,
                        "shapeData": {"0_P0": {"data": encode_bitset(mask)}},
                    }
                ],
            }
            frame["instances"].append(instance)
    return result


def update_task_data(task_data: dict, annotation_result: dict) -> str:
    """Update taskData with new annotation result and return base64-encoded string."""
    updated = copy.deepcopy(task_data)
    if updated.get("results"):
        source = json.loads(updated["results"][0].get("source", "{}"))
        # Update source counts / stats if needed; keep existing base_url
        source["annotation"] = "data:application/json;base64," + base64.b64encode(
            json.dumps(annotation_result, ensure_ascii=False).encode("utf-8")
        ).decode("utf-8")
        updated["results"][0]["source"] = json.dumps(source, ensure_ascii=False)
    return base64.b64encode(
        json.dumps(updated, ensure_ascii=False).encode("utf-8")
    ).decode("utf-8")
