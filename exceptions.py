import tkinter as tk
import sys
import traceback
from tkinter import scrolledtext 
from logging_config import logger


class ExceptionWindow:
    def __init__(self, parent=None, message: str = "Something went wrong", is_critical: bool = True):
        self._is_root = False
        self.is_critical = is_critical
        self.parent = parent
        if parent is None or not isinstance(parent, tk.Tk):
            self._is_root = True
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(parent)

        self.root.title("Error")
        self.root.geometry("500x500")
        self.root.resizable(True, True)

        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.text_area.insert(tk.END, f'{message}')
        self.text_area.config(state=tk.DISABLED)
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        self.text_area.bind("<Button-1>", self._enable_selection)

        button = tk.Button(self.root, text="Close", command=self.close_window)
        button.pack(pady=10)
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

        if self._is_root:
            self.root.mainloop()

    def _enable_selection(self, event):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.tag_add(tk.SEL, "1.0", tk.END)
        self.root.after(1, self._disable_editing)

    def _disable_editing(self):
        self.text_area.config(state=tk.DISABLED)

    def close_window(self):
        self.root.destroy()
        if self._is_root:  # If error intercepted outside the App cycle.
            sys.exit(1)  # Exit program
        else:
            if hasattr(self.parent, "annotation_widget") and self.is_critical:
                if self.parent.annotation_widget:
                    self.parent.annotation_widget.destroy()


class AppError(Exception):
    pass


class DrawingError(AppError):
    pass


class FileUploadError(AppError):
    pass


class FileDownloadError(AppError):
    pass


class AnnotationsMismatchError(AppError):
    pass


class WebServerApiError(AppError):
    pass


def handle_exception(exc_type, exc_value, exc_traceback, app_root=None):
    """
    This function is called when an exception is raised and it is not caught anywhere.
    It shows the exception information in a messagebox instead of the console.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # If it's a keyboard interrupt, exit without showing the message box.
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    is_critical = not isinstance(exc_value, (DrawingError, WebServerApiError))

    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ExceptionWindow(parent=app_root, message=err_msg, is_critical=is_critical)

    if is_critical:
        logger.critical(f"CRITICAL exception occurred: {exc_type.__name__}: {exc_value}", exc_info=(exc_type, exc_value, exc_traceback))
    else:
        logger.error(
            f"Non-critical exception caught: {exc_type.__name__}: {exc_value}", exc_info=(exc_type, exc_value, exc_traceback))

# Set sys.excepthook to our custom function to catch all unhandled exceptions
sys.excepthook = handle_exception
