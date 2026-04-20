import sys
import threading
import traceback

from PySide6.QtWidgets import QApplication

from annotation_tool.ui.dialogs.error_dialog import show_unhandled_exception


class ErrorAwareApplication(QApplication):
    def notify(self, receiver, event):
        try:
            return super().notify(receiver, event)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            show_unhandled_exception(exc_type, exc_value, exc_traceback, critical=False)
            return False


def install_exception_hooks() -> None:
    def handle_exception(exc_type, exc_value, exc_traceback):
        show_unhandled_exception(exc_type, exc_value, exc_traceback, critical=True)

    def handle_thread_exception(args: threading.ExceptHookArgs):
        show_unhandled_exception(
            args.exc_type,
            args.exc_value,
            args.exc_traceback,
            critical=False,
        )

    sys.excepthook = handle_exception
    threading.excepthook = handle_thread_exception
