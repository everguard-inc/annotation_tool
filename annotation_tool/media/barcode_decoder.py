import cv2
import numpy as np


FILTERING_BARCODE_PIXEL_SIZE = 2
MAX_IMAGE_NAME_LENGTH = 100


class BarcodeDecoder:
    def decode_image_name(self, frame: np.ndarray) -> str | None:
        code_height = 8 * FILTERING_BARCODE_PIXEL_SIZE
        code_width = MAX_IMAGE_NAME_LENGTH * FILTERING_BARCODE_PIXEL_SIZE

        image_height = frame.shape[0]
        code = frame[image_height - code_height:image_height, 0:code_width]
        code = cv2.cvtColor(code, cv2.COLOR_BGR2GRAY)
        code = cv2.resize(code, (MAX_IMAGE_NAME_LENGTH, 8))

        binary = np.zeros_like(code, dtype=int)
        binary[code > 150] = 1
        binary = binary.T

        chars = []
        for row in binary:
            value = int("".join(map(str, row)), 2)
            chars.append(chr(value))

        decoded = "".join(chars).lstrip().rstrip("\x00").strip()
        return decoded or None
