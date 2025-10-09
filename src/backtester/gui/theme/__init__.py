"""Minimal theme definitions for the Backtester GUI tests.

This module provides a lightweight theme object that mirrors the interface
expected by the GUI widgets. The production code references a variety of
helper methods and color constants to assemble Qt style sheets. The tests only
require these attributes to exist and return valid strings, so the
implementation focuses on delivering sensible defaults without pulling in
heavy design assets.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class _Palette:
    """Simple color palette used by the theme helpers."""

    BACKGROUND_MAIN: str = "#1e1e1e"
    BACKGROUND_ELEVATED: str = "#252526"
    BORDER_DEFAULT: str = "#3c3c3c"
    ACCENT_PRIMARY: str = "#569cd6"
    ACCENT_SELECTION: str = "#264f78"
    ACCENT_HOVER: str = "#6cb8ff"
    SUCCESS: str = "#4caf50"
    DANGER: str = "#f44747"
    TEXT_PRIMARY: str = "#d4d4d4"


class Theme:
    """Expose helpers for building Qt style sheets used across the GUI."""

    def __init__(self) -> None:
        self.palette = _Palette()

        # Mirror constant attributes accessed by the widgets directly.
        self.BACKGROUND_MAIN = self.palette.BACKGROUND_MAIN
        self.BACKGROUND_ELEVATED = self.palette.BACKGROUND_ELEVATED
        self.BORDER_DEFAULT = self.palette.BORDER_DEFAULT
        self.ACCENT_PRIMARY = self.palette.ACCENT_PRIMARY
        self.ACCENT_SELECTION = self.palette.ACCENT_SELECTION
        self.ACCENT_HOVER = self.palette.ACCENT_HOVER
        self.ERROR = self.palette.DANGER

    def get_main_window_stylesheet(self) -> str:
        return f"
        QMainWindow {{
            background-color: {self.palette.BACKGROUND_MAIN};
            color: {self.palette.TEXT_PRIMARY};
        }}

        QLabel {{
            color: {self.palette.TEXT_PRIMARY};
        }}
        "

    def get_widget_base_stylesheet(self) -> str:
        return f"
        QWidget {{
            background-color: {self.palette.BACKGROUND_ELEVATED};
            color: {self.palette.TEXT_PRIMARY};
        }}
        "

    def get_groupbox_stylesheet(self) -> str:
        return f"
        QGroupBox {{
            border: 1px solid {self.palette.BORDER_DEFAULT};
            border-radius: 4px;
            margin-top: 12px;
            padding: 6px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            padding-left: 4px;
            color: {self.palette.ACCENT_PRIMARY};
        }}
        "

    def get_form_stylesheet(self) -> str:
        return f"
        QLineEdit, QComboBox, QTextEdit {{
            background-color: {self.palette.BACKGROUND_MAIN};
            border: 1px solid {self.palette.BORDER_DEFAULT};
            border-radius: 3px;
            padding: 4px;
            color: {self.palette.TEXT_PRIMARY};
        }}
        QLabel {{
            color: {self.palette.TEXT_PRIMARY};
        }}
        "

    def get_button_stylesheet(self, variant: str = "primary") -> str:
        colors = {
            "primary": self.palette.ACCENT_PRIMARY,
            "secondary": self.palette.BORDER_DEFAULT,
            "success": self.palette.SUCCESS,
            "danger": self.palette.DANGER,
        }
        base_color = colors.get(variant, self.palette.ACCENT_PRIMARY)
        return f"
        QPushButton {{
            background-color: {base_color};
            color: {self.palette.TEXT_PRIMARY};
            border: 1px solid {self.palette.BORDER_DEFAULT};
            border-radius: 3px;
            padding: 4px 10px;
        }}
        QPushButton:hover {{
            background-color: {self.palette.ACCENT_HOVER};
        }}
        QPushButton:disabled {{
            background-color: {self.palette.BORDER_DEFAULT};
            color: rgba(212, 212, 212, 0.4);
        }}
        "

    def get_table_stylesheet(self) -> str:
        return f"
        QTableView {{
            background-color: {self.palette.BACKGROUND_MAIN};
            border: 1px solid {self.palette.BORDER_DEFAULT};
            gridline-color: {self.palette.BORDER_DEFAULT};
            color: {self.palette.TEXT_PRIMARY};
        }}
        QHeaderView::section {{
            background-color: {self.palette.BACKGROUND_ELEVATED};
            border: 1px solid {self.palette.BORDER_DEFAULT};
        }}
        "

    def get_scroll_area_stylesheet(self) -> str:
        return f"
        QScrollArea {{
            background-color: {self.palette.BACKGROUND_ELEVATED};
            border: none;
        }}
        "

    def get_card_stylesheet(self) -> str:
        return f"
        QFrame {{
            background-color: {self.palette.BACKGROUND_ELEVATED};
            border: 1px solid {self.palette.BORDER_DEFAULT};
            border-radius: 6px;
        }}
        "

    def get_dialog_stylesheet(self) -> str:
        return f"
        QDialog {{
            background-color: {self.palette.BACKGROUND_MAIN};
            color: {self.palette.TEXT_PRIMARY};
        }}
        "


theme = Theme()

__all__ = ["theme", "Theme"]

