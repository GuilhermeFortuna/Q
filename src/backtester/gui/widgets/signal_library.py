"""
Signal Library Widget

This widget provides a comprehensive library of available trading signals,
including their descriptions, parameters, and usage examples.
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
from ..models.strategy_model import StrategyModel, SignalType, SignalRole
    QFormLayout,
    QTextEdit,
    QSplitter,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..models.strategy_model import StrategyModel, SignalRole


class SignalLibraryWidget(QWidget):
    signal_selected = Signal(SignalType)  # signal_type

    This widget provides:
    - Complete library of available signals
    - Detailed descriptions and parameter information
        self.current_signal_type = None
    - Integration with strategy building
    """

    # Emit the signal class name string
    signal_selected = Signal(str)  # signal_class_name

    def __init__(self, strategy_model: StrategyModel, parent=None):
        super().__init__(parent)
        self.strategy_model = strategy_model
        self.current_signal_type: Optional[str] = None

        self._setup_ui()
        self._populate_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Signal Library"))
        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Signal list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Available signals
        signals_group = QGroupBox("Available Signals")
        signals_layout = QVBoxLayout(signals_group)

        self.signals_list = QListWidget()
        self.signals_list.itemSelectionChanged.connect(self._on_signal_selected)
        signals_layout.addWidget(self.signals_list)

        # Add to strategy button
        self.add_to_strategy_btn = QPushButton("Add to Strategy")
        self.add_to_strategy_btn.setEnabled(False)
        self.add_to_strategy_btn.clicked.connect(self._on_add_to_strategy)
        signals_layout.addWidget(self.add_to_strategy_btn)

        left_layout.addWidget(signals_group)
        left_layout.addStretch()

        splitter.addWidget(left_panel)

        # Right panel - Signal details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Signal information
        self.signal_info_group = QGroupBox("Signal Information")
        info_layout = QVBoxLayout(self.signal_info_group)

        # Signal name and type
        self.signal_name_label = QLabel("Select a signal to view details")
        self.signal_name_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_layout.addWidget(self.signal_name_label)

        # Signal description
        self.signal_description = QTextEdit()
        self.signal_description.setMaximumHeight(100)
        self.signal_description.setReadOnly(True)
        self.signal_description.setPlainText("No signal selected")
        info_layout.addWidget(self.signal_description)

        # Parameters section
        self.parameters_group = QGroupBox("Parameters")
        self.parameters_layout = QVBoxLayout(self.parameters_group)

        # Scroll area for parameters
        params_scroll = QScrollArea()
        params_scroll.setWidgetResizable(True)
        params_scroll.setMaximumHeight(200)

        self.parameters_container = QWidget()
        self.parameters_container_layout = QVBoxLayout(self.parameters_container)
        params_scroll.setWidget(self.parameters_container)

        self.parameters_layout.addWidget(params_scroll)
        info_layout.addWidget(self.parameters_group)

        # Usage examples
        self.examples_group = QGroupBox("Usage Examples")
        examples_layout = QVBoxLayout(self.examples_group)

        self.usage_examples = QTextEdit()
        self.usage_examples.setMaximumHeight(150)
        self.usage_examples.setReadOnly(True)
        self.usage_examples.setPlainText("No signal selected")
        examples_layout.addWidget(self.usage_examples)

        info_layout.addWidget(self.examples_group)

        right_layout.addWidget(self.signal_info_group)

        splitter.addWidget(right_panel)

        for signal_type, signal_info in available_signals.items():
        splitter.setSizes([300, 500])
            item.setData(Qt.UserRole, signal_type)
        layout.addWidget(splitter)

    def _populate_signals(self):
        """Populate the list of available signals."""
        self.signals_list.clear()

        available_signals = self.strategy_model.get_available_signals()
        for class_name, signal_info in available_signals.items():
            item = QListWidgetItem(signal_info["name"])
            item.setData(Qt.UserRole, class_name)
        signal_type = current_item.data(Qt.UserRole)
        self.current_signal_type = signal_type
        self._update_signal_details(signal_type)
    def _on_signal_selected(self):
        """Handle signal selection change."""
    def _update_signal_details(self, signal_type: SignalType):
        if not current_item:
            self._clear_signal_details()
            return

        class_name = current_item.data(Qt.UserRole)
        self.current_signal_type = class_name
        self._update_signal_details(class_name)
        self.add_to_strategy_btn.setEnabled(True)
        # Update signal name
        self.signal_name_label.setText(f"{signal_info['name']} ({signal_type.value.upper()})")
        """Update the signal details display."""
        available_signals = self.strategy_model.get_available_signals()
        signal_info = available_signals.get(signal_type)

        if not signal_info:
            self._clear_signal_details()
            return
        # Update usage examples
        # Update signal name: show friendly name and class name


        # Update description
        self.signal_description.setPlainText(signal_info["description"])

        # Update parameters
        self._update_parameters_display(signal_info.get("parameters", {}))

        # Update usage examples by mapping class name to a category
        self._update_usage_examples(signal_type)

    def _update_parameters_display(self, parameters: Dict[str, Any]):
        """Update the parameters display."""
        # Clear existing parameter widgets
        for i in reversed(range(self.parameters_container_layout.count())):
            child = self.parameters_container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        if not parameters:
            no_params_label = QLabel("No parameters required")
            no_params_label.setStyleSheet("color: gray; font-style: italic;")
            self.parameters_container_layout.addWidget(no_params_label)
            return

        for param_name, param_config in parameters.items():
            param_widget = self._create_parameter_widget(param_name, param_config)
            self.parameters_container_layout.addWidget(param_widget)

    def _create_parameter_widget(self, param_name: str, param_config) -> QWidget:
        """Create a widget for displaying parameter information."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setStyleSheet(
            "QFrame { border: 1px solid #ccc; border-radius: 3px; padding: 5px; }"
        )

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Parameter name and type
        name_label = QLabel(f"<b>{param_name}</b> ({param_config.parameter_type})")
        layout.addWidget(name_label)

        # Description
        if param_config.description:
            desc_label = QLabel(param_config.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            layout.addWidget(desc_label)

        # Value range or options
        value_info = []
        if param_config.min_value is not None and param_config.max_value is not None:
            value_info.append(
                f"Range: {param_config.min_value} - {param_config.max_value}"
            )
        elif param_config.options:
    def _update_usage_examples(self, signal_type: SignalType):

        if param_config.required:
            value_info.append("Required")
        else:
    def _get_usage_examples(self, signal_type: SignalType) -> str:
        """Get usage examples for a signal type."""
        examples = {
            SignalType.RSI: """RSI (Relative Strength Index) Usage Examples:
            return "MACD"
        if "bollinger" in name or "bbands" in name:
            return "BOLLINGER_BANDS"
        if "stoch" in name:
            return "STOCHASTIC"
        if "moving" in name or "sma" in name or "ema" in name or "ma" in name:
            return "MOVING_AVERAGE"
        return None

    def _get_usage_examples(self, signal_type: str) -> str:
        """Get usage examples for a signal class name by category mapping."""
        category = self._class_category_from_name(signal_type)
        if category == "RSI":
            return """RSI (Relative Strength Index) Usage Examples:

1. Overbought/Oversold Signals:
- Avoid trading in sideways markets with RSI alone""",

            SignalType.MACD: """MACD (Moving Average Convergence Divergence) Usage Examples:
2. Divergence Signals:
   - Price makes higher highs, RSI makes lower highs: Bearish divergence
   - Price makes lower lows, RSI makes higher lows: Bullish divergence

3. Centerline Crossovers:
   - RSI crosses above 50: Potential bullish momentum
   - RSI crosses below 50: Potential bearish momentum

Best Practices:
- Use RSI in conjunction with other indicators
- Consider market conditions and timeframe
- Avoid trading in sideways markets with RSI alone"""
        if category == "MACD":
            return """MACD (Moving Average Convergence Divergence) Usage Examples:

1. Signal Line Crossovers:
- Consider the histogram for additional signals""",

            SignalType.MOVING_AVERAGE: """Moving Average Usage Examples:
2. Zero Line Crossovers:
   - MACD crosses above zero: Bullish momentum
   - MACD crosses below zero: Bearish momentum

3. Divergence Signals:
   - Price higher highs, MACD lower highs: Bearish divergence
   - Price lower lows, MACD higher lows: Bullish divergence

Best Practices:
- Use with trend-following strategies
- Combine with other momentum indicators
- Consider the histogram for additional signals"""
        if category == "MOVING_AVERAGE":
            return """Moving Average Usage Examples:

1. Price Crossovers:
- Consider MA slope for trend strength""",

            SignalType.BOLLINGER_BANDS: """Bollinger Bands Usage Examples:
2. MA Crossovers:
   - Fast MA crosses above slow MA: Golden cross (bullish)
   - Fast MA crosses below slow MA: Death cross (bearish)

3. Support/Resistance:
   - MA acts as dynamic support in uptrends
   - MA acts as dynamic resistance in downtrends

Best Practices:
- Use appropriate period for your timeframe
- Combine multiple MAs for better signals
- Consider MA slope for trend strength"""
        if category == "BOLLINGER_BANDS":
            return """Bollinger Bands Usage Examples:

1. Price Touches:
- Combine with other indicators for confirmation""",

            SignalType.STOCHASTIC: """Stochastic Oscillator Usage Examples:
2. Band Squeeze:
   - Narrowing bands: Low volatility, potential breakout
   - Expanding bands: High volatility, trend continuation

3. Band Breakouts:
   - Price breaks above upper band: Strong bullish momentum
   - Price breaks below lower band: Strong bearish momentum

Best Practices:
- Use with mean reversion strategies
- Consider band width for volatility assessment
- Combine with other indicators for confirmation"""
        if category == "STOCHASTIC":
            return """Stochastic Oscillator Usage Examples:

1. Overbought/Oversold:
   - %K > 80: Overbought conditions
        }

        return examples.get(signal_type, "No usage examples available for this signal type.")

2. Crossovers:
   - %K crosses above %D: Bullish signal
   - %K crosses below %D: Bearish signal

3. Divergence:
   - Price higher highs, Stochastic lower highs: Bearish divergence
   - Price lower lows, Stochastic higher lows: Bullish divergence

Best Practices:
- Use in ranging markets
- Combine with trend indicators
- Consider the smoothing period (%D) for signals"""
        return "No usage examples available for this signal type."

    def _clear_signal_details(self):
        """Clear the signal details display."""
        self.current_signal_type = None
        self.signal_name_label.setText("Select a signal to view details")
        self.signal_description.setPlainText("No signal selected")
        self.usage_examples.setPlainText("No signal selected")

        # Clear parameters
        for i in reversed(range(self.parameters_container_layout.count())):
            child = self.parameters_container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.add_to_strategy_btn.setEnabled(False)

    def _on_add_to_strategy(self):
        """Handle add to strategy button click."""
        if self.current_signal_type:
            self.signal_selected.emit(self.current_signal_type)

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        self._populate_signals()
        self._clear_signal_details()
