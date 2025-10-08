# src/helper/__init__.py
from __future__ import annotations

import shutil
import textwrap
from typing import Dict

from .files import get_parent_directory


# Try modern rendering with `rich`; gracefully degrade if unavailable.
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich import box

    _RICH_AVAILABLE = True
    _console = Console(soft_wrap=True)
except Exception:
    _RICH_AVAILABLE = False
    _console = None  # type: ignore

# ANSI styles for fallback (Windows 10+ supports ANSI in most terminals).
_RESET = "\033[0m"
_STYLES: Dict[str, str] = {
    "info": "\033[38;5;39m",  # cyan/blue
    "error": "\033[38;5;196m",  # red
    "warning": "\033[38;5;214m",  # amber
    "success": "\033[38;5;82m",  # green
    "border": "\033[37m",  # light gray
}

_RICH_BORDER_STYLE: Dict[str, str] = {
    "info": "cyan",
    "error": "red",
    "warning": "yellow3",
    "success": "green",
}

_ICONS: Dict[str, str] = {
    "info": "ℹ",
    "error": "✖",
    "warning": "⚠",
    "success": "✔",
}


def _print_rich(message: str, title: str, kind: str) -> None:
    icon = _ICONS.get(kind, "")
    border_style = _RICH_BORDER_STYLE.get(kind, "white")
    text = Text(message, no_wrap=False)
    panel = Panel.fit(
        text,
        title=f"{icon} {title}",
        border_style=border_style,
        box=box.ROUNDED,
    )
    _console.print(panel)  # type: ignore[arg-type]


def _print_ansi(message: str, title: str, kind: str) -> None:
    icon = _ICONS.get(kind, "")
    color = _STYLES.get(kind, "")
    border = _STYLES.get("border", "")
    cols = min(shutil.get_terminal_size(fallback=(80, 20)).columns, 120)

    # Compute content width with some padding.
    lines = message.splitlines() or [""]
    longest = max(
        [len(title) + 2 + len(icon)] + [len(line) for line in lines]
    )  # rough estimate
    content_w = min(max(30, longest), cols - 4)

    # Top border.
    print(f"{border}╭{'─' * (content_w + 2)}╮{_RESET}")

    # Title row.
    title_text = f"{icon} {title}".strip()
    print(
        f"{border}│{_RESET} {color}{title_text.ljust(content_w)}{_RESET} {border}│{_RESET}"
    )

    # Separator.
    print(f"{border}├{'─' * (content_w + 2)}┤{_RESET}")

    # Body with wrapping.
    for line in lines or [""]:
        wrapped = textwrap.wrap(line, width=content_w) or [""]
        for chunk in wrapped:
            print(f"{border}│{_RESET} {chunk.ljust(content_w)} {border}│{_RESET}")

    # Bottom border.
    print(f"{border}╰{'─' * (content_w + 2)}╯{_RESET}")


def _print_message(message: str, title: str, kind: str) -> None:
    if _RICH_AVAILABLE:
        _print_rich(message, title, kind)
    else:
        _print_ansi(message, title, kind)


def print_info(message: str, title: str = "INFO") -> None:
    _print_message(message, title, "info")


def print_error(message: str, title: str = "ERROR") -> None:
    _print_message(message, title, "error")


def print_warning(message: str, title: str = "WARNING") -> None:
    _print_message(message, title, "warning")


def print_success(message: str, title: str = "SUCCESS") -> None:
    _print_message(message, title, "success")


PrintMessage = {
    'INFO': print_info,
    'ERROR': print_error,
    'WARNING': print_warning,
    'SUCCESS': print_success,
}

# Project root
PROJECT_ROOT = get_parent_directory(any_subdir='src')

__all__ = ['PrintMessage', 'PROJECT_ROOT']

if __name__ == "__main__":
    PrintMessage['INFO']('This is an informational message.')
    PrintMessage['SUCCESS']('Operation completed successfully.')
    PrintMessage['WARNING']('This is a warning.\nProceed with caution.')
    PrintMessage['ERROR']('This is an error message.\nPlease check the details.')
