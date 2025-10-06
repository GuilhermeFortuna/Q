#!/usr/bin/env python3
"""
Backtester GUI Example

This script demonstrates how to use the Backtester GUI application.
It shows how to launch the GUI and perform basic operations.
"""

import sys
import os

from PySide6.QtWidgets import QApplication
from src.backtester.gui.main_window import BacktesterMainWindow


def main():
    """Main entry point for the Backtester GUI example."""
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Backtester GUI Example")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Quantitative Trading Research")

    # Create and show main window
    window = BacktesterMainWindow()
    window.show()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
