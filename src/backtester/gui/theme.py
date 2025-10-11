"""
JetBrains-Inspired Theme for Backtester GUI

This module provides a centralized theme management system with a dark theme
inspired by JetBrains IDEs, featuring darker backgrounds and vibrant green accents.
"""

from typing import Dict, Optional


class Theme:
    """Centralized theme management for the backtester GUI."""
    
    # Color Palette - JetBrains Inspired
    # Backgrounds (darker than current theme)
    BACKGROUND_MAIN = "#1C1C1C"          # Main window background
    BACKGROUND_SECONDARY = "#2B2B2B"     # Panels, cards, secondary areas
    BACKGROUND_TERTIARY = "#3C3C3C"      # Headers, inactive tabs
    BACKGROUND_INPUT = "#313335"          # Form fields, input areas
    BACKGROUND_ELEVATED = "#404040"       # Elevated components
    
    # Accent Colors (vibrant greens)
    ACCENT_PRIMARY = "#3BEA62"           # Primary green for main actions
    ACCENT_HOVER = "#4EFF7A"             # Lighter green for hover states
    ACCENT_SUCCESS = "#499C54"           # Darker green for success states
    ACCENT_SELECTION = "#214524"         # Dark green for selections
    ACCENT_FOCUS = "#2A5A2D"             # Focus ring color
    
    # Functional Colors
    ERROR = "#FF5555"                    # Error red
    WARNING = "#FF9800"                  # Warning orange
    INFO = "#7AB4FF"                     # Info blue
    POSITIVE = "#00FF88"                 # Positive values (charts, equity)
    NEGATIVE = "#FF4444"                 # Negative values (drawdown, losses)
    
    # Text Colors
    TEXT_PRIMARY = "#BBBBBB"             # Primary text
    TEXT_SECONDARY = "#888888"           # Secondary text
    TEXT_DISABLED = "#5C5C5C"            # Disabled text
    TEXT_ACCENT = "#3BEA62"              # Accent text (green)
    
    # Border Colors
    BORDER_DEFAULT = "#404040"           # Default borders
    BORDER_HOVER = "#555555"             # Hover borders
    BORDER_FOCUS = "#3BEA62"             # Focus borders (green)
    
    @classmethod
    def get_main_window_stylesheet(cls) -> str:
        """Get the main window stylesheet."""
        return f"""
            QMainWindow {{
                background-color: {cls.BACKGROUND_MAIN};
                color: {cls.TEXT_PRIMARY};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {cls.BORDER_DEFAULT};
                background-color: {cls.BACKGROUND_SECONDARY};
            }}
            
            QTabBar::tab {{
                background-color: {cls.BACKGROUND_TERTIARY};
                color: {cls.TEXT_PRIMARY};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {cls.ACCENT_SELECTION};
                color: {cls.TEXT_PRIMARY};
            }}
            
            QTabBar::tab:hover {{
                background-color: {cls.BACKGROUND_ELEVATED};
            }}
            
            QMenuBar {{
                background-color: {cls.BACKGROUND_SECONDARY};
                color: {cls.TEXT_PRIMARY};
                border-bottom: 1px solid {cls.BORDER_DEFAULT};
            }}
            
            QMenuBar::item {{
                background-color: transparent;
                padding: 4px 8px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {cls.ACCENT_PRIMARY};
            }}
            
            QMenu {{
                background-color: {cls.BACKGROUND_SECONDARY};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER_DEFAULT};
            }}
            
            QMenu::item {{
                padding: 6px 20px;
            }}
            
            QMenu::item:selected {{
                background-color: {cls.ACCENT_PRIMARY};
            }}
            
            QToolBar {{
                background-color: {cls.BACKGROUND_SECONDARY};
                border: none;
                spacing: 3px;
            }}
            
            QToolBar QToolButton {{
                background-color: {cls.BACKGROUND_TERTIARY};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER_DEFAULT};
                padding: 6px 12px;
                border-radius: 3px;
            }}
            
            QToolBar QToolButton:hover {{
                background-color: {cls.BACKGROUND_ELEVATED};
            }}
            
            QToolBar QToolButton:pressed {{
                background-color: {cls.ACCENT_PRIMARY};
            }}
            
            QStatusBar {{
                background-color: {cls.BACKGROUND_SECONDARY};
                color: {cls.TEXT_PRIMARY};
                border-top: 1px solid {cls.BORDER_DEFAULT};
            }}
            
            QProgressBar {{
                border: 1px solid {cls.BORDER_DEFAULT};
                border-radius: 3px;
                text-align: center;
                background-color: {cls.BACKGROUND_TERTIARY};
            }}
            
            QProgressBar::chunk {{
                background-color: {cls.ACCENT_PRIMARY};
                border-radius: 2px;
            }}
        """
    
    @classmethod
    def get_button_stylesheet(cls, button_type: str = "primary") -> str:
        """Get button stylesheet based on type."""
        if button_type == "primary":
            return f"""
                QPushButton {{
                    background-color: {cls.ACCENT_PRIMARY};
                    color: {cls.BACKGROUND_MAIN};
                    border: none;
                    padding: 6px 12px;
                    border-radius: 3px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {cls.ACCENT_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {cls.ACCENT_SUCCESS};
                }}
                QPushButton:disabled {{
                    background-color: {cls.BACKGROUND_TERTIARY};
                    color: {cls.TEXT_DISABLED};
                }}
            """
        elif button_type == "secondary":
            return f"""
                QPushButton {{
                    background-color: {cls.BACKGROUND_TERTIARY};
                    color: {cls.TEXT_PRIMARY};
                    border: 1px solid {cls.BORDER_DEFAULT};
                    padding: 6px 12px;
                    border-radius: 3px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {cls.BACKGROUND_ELEVATED};
                }}
                QPushButton:pressed {{
                    background-color: {cls.ACCENT_PRIMARY};
                    color: {cls.BACKGROUND_MAIN};
                }}
                QPushButton:disabled {{
                    background-color: {cls.BACKGROUND_TERTIARY};
                    color: {cls.TEXT_DISABLED};
                }}
            """
        elif button_type == "success":
            return f"""
                QPushButton {{
                    background-color: {cls.ACCENT_SUCCESS};
                    color: {cls.BACKGROUND_MAIN};
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {cls.ACCENT_PRIMARY};
                }}
                QPushButton:disabled {{
                    background-color: {cls.BACKGROUND_TERTIARY};
                    color: {cls.TEXT_DISABLED};
                }}
            """
        elif button_type == "danger":
            return f"""
                QPushButton {{
                    background-color: {cls.ERROR};
                    color: {cls.BACKGROUND_MAIN};
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: #FF6666;
                }}
                QPushButton:disabled {{
                    background-color: {cls.BACKGROUND_TERTIARY};
                    color: {cls.TEXT_DISABLED};
                }}
            """
        else:
            return cls.get_button_stylesheet("primary")
    
    @classmethod
    def get_form_stylesheet(cls) -> str:
        """Get form input stylesheet."""
        return f"""
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit {{
                background-color: {cls.BACKGROUND_INPUT};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER_DEFAULT};
                border-radius: 3px;
                padding: 4px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QDateEdit:focus {{
                border-color: {cls.BORDER_FOCUS};
            }}
            QComboBox::drop-down {{
                border: none;
                background-color: {cls.BACKGROUND_TERTIARY};
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {cls.TEXT_PRIMARY};
                margin-right: 5px;
            }}
        """
    
    @classmethod
    def get_table_stylesheet(cls) -> str:
        """Get table stylesheet."""
        return f"""
            QTableWidget {{
                background-color: {cls.BACKGROUND_SECONDARY};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER_DEFAULT};
                border-radius: 3px;
                gridline-color: {cls.BORDER_DEFAULT};
            }}
            QTableWidget::item {{
                padding: 4px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: {cls.ACCENT_SELECTION};
            }}
            QTableWidget::item:hover {{
                background-color: {cls.BACKGROUND_ELEVATED};
            }}
            QHeaderView::section {{
                background-color: {cls.BACKGROUND_TERTIARY};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER_DEFAULT};
                font-weight: bold;
                padding: 4px;
            }}
            QHeaderView::section:hover {{
                background-color: {cls.BACKGROUND_ELEVATED};
            }}
        """
    
    @classmethod
    def get_groupbox_stylesheet(cls) -> str:
        """Get groupbox stylesheet."""
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {cls.BORDER_DEFAULT};
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                color: {cls.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {cls.TEXT_PRIMARY};
            }}
        """
    
    @classmethod
    def get_card_stylesheet(cls) -> str:
        """Get card widget stylesheet."""
        return f"""
            QFrame {{
                background-color: {cls.BACKGROUND_SECONDARY};
                border: 1px solid {cls.BORDER_DEFAULT};
                border-radius: 6px;
            }}
            QFrame:hover {{
                border-color: {cls.BORDER_HOVER};
            }}
        """
    
    @classmethod
    def get_scroll_area_stylesheet(cls) -> str:
        """Get scroll area stylesheet."""
        return f"""
            QScrollArea {{
                border: 1px solid {cls.BORDER_DEFAULT};
                border-radius: 4px;
                background-color: {cls.BACKGROUND_SECONDARY};
            }}
            QScrollBar:vertical {{
                background-color: {cls.BACKGROUND_TERTIARY};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {cls.BORDER_HOVER};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {cls.ACCENT_PRIMARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """
    
    @classmethod
    def get_dialog_stylesheet(cls) -> str:
        """Get dialog stylesheet."""
        return f"""
            QDialog {{
                background-color: {cls.BACKGROUND_MAIN};
                color: {cls.TEXT_PRIMARY};
            }}
            QDialogButtonBox QPushButton {{
                min-width: 80px;
                padding: 6px 12px;
            }}
        """
    
    @classmethod
    def get_widget_base_stylesheet(cls) -> str:
        """Get base widget stylesheet."""
        return f"""
            QWidget {{
                background-color: {cls.BACKGROUND_MAIN};
                color: {cls.TEXT_PRIMARY};
            }}
        """
    
    @classmethod
    def get_complete_stylesheet(cls) -> str:
        """Get complete application stylesheet."""
        return (
            cls.get_main_window_stylesheet() +
            cls.get_form_stylesheet() +
            cls.get_table_stylesheet() +
            cls.get_groupbox_stylesheet() +
            cls.get_card_stylesheet() +
            cls.get_scroll_area_stylesheet() +
            cls.get_dialog_stylesheet() +
            cls.get_widget_base_stylesheet()
        )


# Global theme instance
theme = Theme()
