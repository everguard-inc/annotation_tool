import numpy as np


def encode_rle(mask: np.ndarray) -> str:
    ...


def decode_rle(encoded: str, width: int, height: int) -> np.ndarray:
    ...


def empty_rle(width: int, height: int) -> str:
    ...
