import numpy as np

from annotation_tool.media.barcode_decoder import BarcodeDecoder


def _frame_with_barcode(text: str) -> np.ndarray:
    frame = np.zeros((32, 220, 3), dtype=np.uint8)

    for char_id, char in enumerate(text.ljust(100)):
        bits = f"{ord(char):08b}"
        for bit_id, bit in enumerate(bits):
            value = 255 if bit == "1" else 0
            y1 = 32 - 16 + bit_id * 2
            y2 = y1 + 2
            x1 = char_id * 2
            x2 = x1 + 2
            frame[y1:y2, x1:x2] = value

    return frame


def test_barcode_decoder_returns_image_name_or_none() -> None:
    """Covers FR-153, FR-154."""
    decoder = BarcodeDecoder()

    assert decoder.decode_image_name(_frame_with_barcode("img_001.jpg")) == "img_001.jpg"
    assert decoder.decode_image_name(np.zeros((8, 8, 3), dtype=np.uint8)) is None
