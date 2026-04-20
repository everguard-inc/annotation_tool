from pathlib import Path

from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget


class HtmlWindow(QWidget):
    def __init__(self, title: str, html_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(900, 700)

        self.browser = QTextBrowser(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.browser)

        self.show_file(html_path)

    def show_file(self, html_path: Path) -> None:
        if html_path.exists():
            self.browser.setHtml(html_path.read_text(encoding="utf-8"))
        else:
            self.browser.setPlainText(f"File not found: {html_path}")
