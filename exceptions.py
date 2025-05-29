import tkinter as tk
import sys
import traceback
from abc import abstractmethod
from tkinter import scrolledtext 


class CommonMessageBoxException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.root = tk.Tk()
        self.root.title("Error")
        self._window_closed = False

        # Create a Text widget with a vertical scrollbar
        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.text_area.insert(tk.INSERT, message)
        self.text_area.config(state=tk.DISABLED)  # Start as disabled to prevent editing

        # Enable text selection and copying while disabling editing
        self.text_area.bind("<Button-1>", self.enable_selection)

        # Button to close the window
        self.close_button = tk.Button(self.root, text="Close", command=self.close_window)
        self.close_button.pack(pady=5, fill=tk.X)

        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        self.root.mainloop()

    def enable_selection(self, event):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.tag_add(tk.SEL, "1.0", tk.END)
        self.root.after(1, self.disable_editing)

    def disable_editing(self):
        self.text_area.config(state=tk.DISABLED)

    def close_window(self):
        if self._window_closed:
            return
        self._window_closed = True
        if self.root.winfo_exists():
            self.root.destroy()


class MessageBoxException(CommonMessageBoxException):

    def close_window(self):
        super().close_window()
        sys.exit(1)


class WarningMessageBoxException(CommonMessageBoxException):
    pass


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    This function is called when an exception is raised and it is not caught anywhere.
    It shows the exception information in a messagebox instead of the console.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # If it's a keyboard interrupt, exit without showing the message box.
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    if isinstance(exc_value, CommonMessageBoxException):
        exc_value.close_window()
        return

    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    MessageBoxException(err_msg)

# Set sys.excepthook to our custom function to catch all unhandled exceptions
sys.excepthook = handle_exception
