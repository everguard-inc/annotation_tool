import numpy as np


def encode_rle(mask: np.ndarray) -> str:
    flat = mask.astype(np.uint8).flatten()
    if flat.size == 0:
        return ""

    changes = np.where(np.diff(flat) != 0)[0] + 1
    positions = np.concatenate(([0], changes, [flat.size]))
    values = flat[positions[:-1]]
    counts = np.diff(positions)

    return ",".join(f"{int(value)}:{int(count)}" for value, count in zip(values, counts))


def decode_rle(encoded: str, width: int, height: int) -> np.ndarray:
    if not encoded:
        return np.zeros((height, width), dtype=np.uint8)

    values = []
    for chunk in encoded.split(","):
        value, count = chunk.split(":")
        values.extend([int(value)] * int(count))

    return np.array(values, dtype=np.uint8).reshape((height, width))


def empty_rle(width: int, height: int) -> str:
    return f"0:{width * height}"
