"""
TUI Log Handler — routes Python logging records into the Textual
right-pane RichLog widget in real time.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.widgets import RichLog


class TUILogHandler(logging.Handler):
    """
    A logging.Handler that writes formatted records to a Textual
    RichLog widget instead of stdout/file.

    The widget reference is set after the App is mounted so the
    handler can be registered on the root logger at import time.
    """

    def __init__(self) -> None:
        super().__init__()
        self._widget: "RichLog | None" = None
        self.setFormatter(
            logging.Formatter(
                "%(asctime)s  %(levelname)-8s  %(message)s",
                datefmt="%H:%M:%S",
            )
        )

    def attach(self, widget: "RichLog") -> None:
        """Bind the handler to a live RichLog widget."""
        self._widget = widget

    def emit(self, record: logging.LogRecord) -> None:
        if self._widget is None:
            return
        try:
            msg = self.format(record)
            # Colour by level
            if record.levelno >= logging.ERROR:
                markup = f"[bold red]{msg}[/]"
            elif record.levelno >= logging.WARNING:
                markup = f"[yellow]{msg}[/]"
            else:
                markup = f"[dim]{msg}[/]"
            # call_from_thread is safe when called from a worker thread
            self._widget.app.call_from_thread(self._widget.write, markup)
        except Exception:
            self.handleError(record)
