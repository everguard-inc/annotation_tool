import sys
import threading


from annotation_tool.ui.dialogs import error_dialog
from annotation_tool.ui.exception_hook import install_exception_hooks


def test_unhandled_error_dialog_shows_traceback_and_exits_only_when_critical(
    monkeypatch,
) -> None:
    shown = []
    exits = []

    monkeypatch.setattr(
        error_dialog.ErrorDialog,
        "show_error",
        lambda message, parent=None: shown.append(message),
    )
    monkeypatch.setattr(sys, "exit", lambda code: exits.append(code))

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        exc_type, exc_value, exc_traceback = sys.exc_info()

    error_dialog.show_unhandled_exception(
        exc_type, exc_value, exc_traceback, critical=False
    )
    assert "RuntimeError: boom" in shown[-1]
    assert exits == []

    error_dialog.show_unhandled_exception(
        exc_type, exc_value, exc_traceback, critical=True
    )
    assert exits == [1]


def test_exception_hooks_are_installed_for_main_and_thread_errors(monkeypatch) -> None:
    calls = []

    monkeypatch.setattr(
        "annotation_tool.ui.exception_hook.show_unhandled_exception",
        lambda exc_type, exc_value, exc_traceback, critical: calls.append(
            (exc_type, critical)
        ),
    )

    install_exception_hooks()

    assert sys.excepthook is not sys.__excepthook__
    assert threading.excepthook is not threading.__excepthook__

    try:
        raise ValueError("main")
    except ValueError:
        exc_type, exc_value, exc_traceback = sys.exc_info()

    sys.excepthook(exc_type, exc_value, exc_traceback)

    assert calls[-1][0] is ValueError
    assert calls[-1][1] is True
