import numpy as np


class BarcodeDecoder:
    def decode_image_name(self, frame: np.ndarray) -> str | None:
        ...
