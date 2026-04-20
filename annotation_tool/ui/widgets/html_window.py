from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QTextBrowser


class HtmlWindow(QMainWindow):
    def __init__(
        self,
        title: str,
        html_path: Path | None = None,
        parent=None,
        html_content: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(900, 700)

        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(True)

        if html_content is not None:
            browser.setHtml(html_content)
        elif html_path is not None and html_path.exists():
            browser.setHtml(html_path.read_text(encoding="utf-8"))
        else:
            browser.setHtml(f"<h3>{title}</h3><p>Documentation page is missing.</p>")

        self.setCentralWidget(browser)
