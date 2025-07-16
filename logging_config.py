import json
import logging
import os.path
import re
import traceback

from pythonjsonlogger import json as json_logger


class CustomJsonFormatter(json_logger.JsonFormatter):

    STRIP_PATH_FROM = "annotation_tool/"

    def formatException(self, exc_info):
        formatted = "".join(traceback.format_exception(*exc_info))
        pattern = rf".*?(?={re.escape(self.STRIP_PATH_FROM)})"
        masked = re.sub(pattern, "*****", formatted)
        return masked

    def process_log_record(self, record):
        log_data = {
            "asctime": self.formatTime(record, self.datefmt),
            "levelname": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        # Include traceback if present
        if record.exc_info:
            log_data["traceback"] = self.formatException(record.exc_info)

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)

        return log_data

    def format(self, record: logging.LogRecord) -> str:
        log_record = self.process_log_record(record)
        return json.dumps(log_record, indent=2) + "\n"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(BASE_DIR, "app_error_logs.json")

logger = logging.getLogger("Annotation Tool")
logger.setLevel(logging.ERROR)

file_handler = logging.FileHandler(LOG_FILE_PATH)
file_handler.setLevel(logging.ERROR)

json_formatter = CustomJsonFormatter(
    fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
file_handler.setFormatter(json_formatter)

logger.addHandler(file_handler)
