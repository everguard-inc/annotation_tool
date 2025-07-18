import functools
from datetime import datetime
import json
import os
from typing import Tuple, Callable, Union

import requests
from PIL import Image


from exceptions import WarningMessageBoxException
from logging_config import logger


def open_json(detections_file):
    with open(detections_file, "r") as file:
        value = json.load(file)
    return value

def save_json(
    value,
    file_path,
):
    if os.path.islink(file_path):
        os.remove(file_path)
    if os.path.dirname(file_path) != "":
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as filename:
        json.dump(value, filename, indent=4)


class HistoryBuffer:

    def __init__(self, length=10):
        self.history = list()
        self.length = length
        self.position = 0

    def add(self, value):
        if len(self.history) > 0 and value == self.history[-1]:
            return
        if len(self.history) > 0:
            self.history = self.history[:self.position + 1]
        self.history.append(value)
        self.history = self.history[-self.length:]
        self.position = len(self.history) - 1
    
    def get_previous(self):
        if len(self.history) == 0:
            return 
        if self.position - 1 >= 0:
            result = self.history[self.position - 1]
            if self.position > 0:
                self.position -= 1
            return result
    
    def get_next(self):
        if len(self.history) == 0:
            return 
        if self.position + 1 < len(self.history):
            result = self.history[self.position + 1]
            if self.position < self.length:
                self.position += 1
            return result
    
    def clear(self):
        self.history = list()
        self.position = 0


def check_url_rechable(url) -> bool:
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        return False
    return True


def check_correct_json(json_path: str) -> bool:
    try:
        open_json(json_path)
        return True
    except:
        return False
    

def get_datetime_str():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def get_img_size(img_path: str) -> Tuple[int, int]:
    """Returns width and height of img"""
    assert os.path.isfile(img_path), f"{img_path} is not found"
    im = Image.open(img_path)
    frame_width, frame_height = im.size
    return int(frame_width), int(frame_height)



def safe_execution(on_error: Union[Callable, str] = None, message: str = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error in {func.__qualname__} with args={args} and kwargs={kwargs}: {e}",
                    exc_info=True,
                )
                if callable(on_error):
                    on_error(self)

                elif isinstance(on_error, str) and hasattr(self, on_error):
                    getattr(self, on_error)()
                raise WarningMessageBoxException(e)
        return wrapper
    return decorator
