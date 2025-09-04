# src/visualizer/windows/backtest_summary.py
from __future__ import annotations

from typing import Any, Mapping, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtGui import QFontMetrics, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QPlainTextEdit,
    QVBoxLayout,
    QLabel,
)


def _as_dict(results: Any) -> Mapping[str, Any]:
    """
    Normalize incoming results to a dict.
    Supports:
      - dict-like objects
      - objects exposing get_result() -> dict
      - objects exposing .result or .results that are dict-like
    """
    if results is None:
        return {}

    if isinstance(results, Mapping):
        return results

    # Try common TradeRegistry-like APIs
    if hasattr(results, "get_result"):
        try:
            maybe = results.get_result()
            if isinstance(maybe, Mapping):
                return maybe
        except Exception:
            pass

    for attr in ("result", "results"):
        if hasattr(results, attr):
            maybe = getattr(results, attr)
            if isinstance(maybe, Mapping):
                return maybe

    # Fallback: best-effort dict() of __dict__ (filtered)
    if hasattr(results, "__dict__"):
        return {k: v for k, v in vars(results).items() if not k.startswith("_")}

    return {}


def _format_value(v: Any) -> str:
    if v is None:
        return "-"
    # Keep numbers aligned, keep other types stringified plainly
    if isinstance(v, (int, float)):
        # Use default string; caller can pre-format floats if desired
        return f"{v}"
    return f"{v}"


def _format_results_text(results_dict: Mapping[str, Any]) -> str:
    """
    Returns a text block similar to your console output.
    If certain keys are missing, they’ll be skipped.
    """
    preferred_order = [
        "net_balance (BRL)",
        "gross_balance (BRL)",
        "total_tax (BRL)",
        "total_cost (BRL)",
        "total_profit (BRL)",
        "total_loss (BRL)",
        "profit_factor",
        "accuracy (%)",
        "mean_profit (BRL)",
        "mean_loss (BRL)",
        "mean_ratio",
        "standard_deviation",
        "total_trades",
        "positive_trades",
        "negative_trades",
        "maximum_drawdown (BRL)",
        "drawdown_relative (%)",
        "drawdown_final (%)",
        "start_date",
        "end_date",
        "duration",
        "average_monthly_result (BRL)",
    ]

    # Normalize keys to strings for safe lookup/comparison
    keys_available = {str(k): k for k in results_dict.keys()}

    lines = ["--- Results ---"]
    for label in preferred_order:
        if label in keys_available:
            orig_key = keys_available[label]
            val = results_dict.get(orig_key)
            lines.append(f"{label:40s} { _format_value(val) }")

    # Append any additional fields that weren’t listed above
    extra_keys = [k for k in results_dict.keys() if str(k) not in preferred_order]
    if extra_keys:
        lines.append("")
        for k in sorted(extra_keys, key=lambda x: str(x)):
            lines.append(f"{k}: { _format_value(results_dict[k]) }")

    return "\n".join(lines)


class BacktestSummaryDialog(QDialog):
    def __init__(
        self,
        results: Any,
        parent=None,
        title: str = "Backtest Summary",
        initial_size: tuple[int, int] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        data_dict = _as_dict(results)
        text = _format_results_text(data_dict)

        layout = QVBoxLayout(self)

        header = QLabel("Summary of backtest results")
        header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(header)

        self.text_area = QPlainTextEdit(self)
        self.text_area.setReadOnly(True)

        # Monospaced font for aligned columns
        font = QFont("Consolas")
        if not font.exactMatch():
            font = QFont("Courier New")
        font.setStyleHint(QFont.Monospace)
        self.text_area.setFont(font)

        self.text_area.setPlainText(text)
        layout.addWidget(self.text_area)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok, parent=self)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        # If caller provides a size, use it; otherwise, fit to the text contents.
        if initial_size is not None:
            self.resize(initial_size[0], initial_size[1])
        else:
            self._resize_to_fit_text(text)

    def _resize_to_fit_text(self, text: str) -> None:
        """
        Compute a good initial size so that the dialog fits the text with minimal scrollbars,
        but cap to the available screen area.
        """
        # 1) Measure text using the edit's font
        fm = QFontMetrics(self.text_area.font())
        lines = text.splitlines() or [""]
        max_cols = max(len(line) for line in lines)
        line_count = len(lines)

        # Width/height in pixels based on character metrics
        char_w = fm.horizontalAdvance("M")
        line_h = fm.lineSpacing()

        # 2) Compute content size with margins/frames and a small cushion
        frame = self.text_area.frameWidth()
        cushion = 16  # small extra space
        scrollbar_allowance = 20  # if scrollbars appear, give a bit of room

        content_w = (max_cols * char_w) + (frame * 2) + cushion + scrollbar_allowance
        content_h = (line_count * line_h) + (frame * 2) + cushion + scrollbar_allowance

        # 3) Cap to available screen size (minus some margins)
        screen = (
            self.windowHandle().screen()
            if self.windowHandle()
            else QGuiApplication.primaryScreen()
        )
        if screen:
            avail = screen.availableGeometry()
            max_w = int(avail.width() * 0.7)
            max_h = int(avail.height() * 0.7)
            content_w = min(content_w, max_w)
            content_h = min(content_h, max_h)

        # 4) Apply as the minimum size for the text area and let the dialog compute its layout
        self.text_area.setMinimumSize(int(content_w), int(content_h))

        # 5) Let the dialog resize itself to fit current size hints/minimums
        self.adjustSize()


def show_backtest_summary(
    results: Any,
    title: str = "Backtest Summary",
    block: Optional[bool] = None,
    size: Optional[tuple[int, int]] = None,
) -> BacktestSummaryDialog:
    """
    Convenience function to display the summary dialog.
    - If no QApplication exists, one will be created.
    - If block is None, it will block only if we created the app.
    - Pass size=(width, height) to control the initial size.
    """
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication([])
        created_app = True

    dlg = BacktestSummaryDialog(results, title=title, initial_size=size)
    dlg.show()

    if block is None:
        block = created_app

    if block:
        app.exec()
    return dlg
