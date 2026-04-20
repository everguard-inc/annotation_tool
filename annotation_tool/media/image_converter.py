import numpy as np
from PySide6.QtGui import QImage


def bgr_to_rgb(frame: np.ndarray) -> np.ndarray:
    ...


def numpy_to_qimage(frame: np.ndarray) -> QImage:
    ...


def deteriorate_image(frame: np.ndarray) -> np.ndarray:
    ...
