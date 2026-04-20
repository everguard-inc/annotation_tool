import cv2
import numpy as np
from PySide6.QtGui import QImage


def bgr_to_rgb(frame: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def numpy_to_qimage(frame: np.ndarray) -> QImage:
    if frame.ndim != 3:
        raise ValueError("Expected 3-channel image.")

    rgb = bgr_to_rgb(frame)
    height, width, channels = rgb.shape
    bytes_per_line = channels * width

    image = QImage(
        rgb.data,
        width,
        height,
        bytes_per_line,
        QImage.Format.Format_RGB888,
    )

    return image.copy()


def deteriorate_image(frame: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(frame, (31, 31), sigmaX=0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = hsv[:, :, 1] * 0.5
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
