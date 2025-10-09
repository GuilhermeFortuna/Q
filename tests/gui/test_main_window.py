"""GUI interaction smoke tests for the Backtester main window."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QMessageBox, QWidget

import src.backtester.gui.main_window as main_window_module
from src.backtester.gui.main_window import BacktesterMainWindow


pytestmark = pytest.mark.gui


@pytest.fixture(autouse=True)
def suppress_modal_dialogs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent modal dialogs from blocking the GUI test run."""

    def _return_ok(*args, **kwargs):  # type: ignore[unused-argument]
        return QMessageBox.StandardButton.Ok

    def _return_no(*args, **kwargs):  # type: ignore[unused-argument]
        return QMessageBox.StandardButton.No

    monkeypatch.setattr(main_window_module.QMessageBox, "warning", _return_ok)
    monkeypatch.setattr(main_window_module.QMessageBox, "critical", _return_ok)
    monkeypatch.setattr(main_window_module.QMessageBox, "information", _return_ok)
    monkeypatch.setattr(main_window_module.QMessageBox, "question", _return_no)


@pytest.fixture
def main_window(qtbot, monkeypatch: pytest.MonkeyPatch) -> BacktesterMainWindow:
    """Build a main window instance registered for automatic cleanup."""

    # Keep the widgets lightweight to avoid relying on optional assets.
    class _PlaceholderWidget(QWidget):
        def __init__(self, *args, **kwargs):  # type: ignore[unused-argument]
            super().__init__()

    monkeypatch.setattr(main_window_module, "StrategyBuilderWidget", _PlaceholderWidget)
    monkeypatch.setattr(main_window_module, "DataConfigWidget", _PlaceholderWidget)
    monkeypatch.setattr(main_window_module, "BacktestConfigWidget", _PlaceholderWidget)
    monkeypatch.setattr(main_window_module, "ExecutionMonitorWidget", _PlaceholderWidget)

    show_results_calls: list[object] = []

    def _capture_results(self: BacktesterMainWindow, results: object) -> None:
        show_results_calls.append(results)

    monkeypatch.setattr(BacktesterMainWindow, "_show_results", _capture_results)

    window = BacktesterMainWindow()
    qtbot.addWidget(window)
    window._recorded_results = show_results_calls  # type: ignore[attr-defined]
    return window


def _tab_titles(window: BacktesterMainWindow) -> list[str]:
    return [window.tab_widget.tabText(i) for i in range(window.tab_widget.count())]


def test_main_window_initial_state(main_window: BacktesterMainWindow) -> None:
    """The constructor wires up the expected tabs and default state."""

    assert main_window.windowTitle().startswith(
        "Backtester - Quantitative Trading Research Toolkit"
    )

    assert _tab_titles(main_window) == [
        "Strategy Builder",
        "Data Configuration",
        "Backtest Configuration",
        "Execution & Monitoring",
    ]

    assert main_window.status_label.text() == "Ready"
    assert not main_window.run_backtest_action.isEnabled()
    assert not main_window.stop_backtest_action.isEnabled()
    assert not main_window.progress_bar.isVisible()


def test_update_run_button_state_enables_when_models_ready(
    main_window: BacktesterMainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run button toggles based on model readiness."""

    monkeypatch.setattr(main_window.strategy_model, "has_strategy", lambda: True)
    monkeypatch.setattr(main_window.backtest_model, "has_data", lambda: True)
    monkeypatch.setattr(main_window.backtest_model, "has_config", lambda: True)

    main_window._update_run_button_state()
    assert main_window.run_backtest_action.isEnabled()

    monkeypatch.setattr(main_window.backtest_model, "has_config", lambda: False)
    main_window._update_run_button_state()
    assert not main_window.run_backtest_action.isEnabled()


def test_run_backtest_delegates_to_execution_controller(
    main_window: BacktesterMainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Starting a backtest hands the payload to the execution controller."""

    sentinel_strategy = object()
    sentinel_data = {"candle": object()}
    sentinel_config = object()

    monkeypatch.setattr(main_window.strategy_model, "get_strategy", lambda: sentinel_strategy)
    monkeypatch.setattr(main_window.backtest_model, "get_data", lambda: sentinel_data)
    monkeypatch.setattr(main_window.backtest_model, "get_config", lambda: sentinel_config)

    run_mock = MagicMock()
    monkeypatch.setattr(main_window.execution_controller, "run_backtest", run_mock)

    main_window._run_backtest()

    run_mock.assert_called_once_with(sentinel_strategy, sentinel_data, sentinel_config)


def test_execution_signals_update_ui_state(
    main_window: BacktesterMainWindow,
    qtbot,
) -> None:
    """Controller signals toggle toolbar actions and the progress display."""

    exec_controller = main_window.execution_controller

    exec_controller.backtest_started.emit()
    assert not main_window.run_backtest_action.isEnabled()
    assert main_window.stop_backtest_action.isEnabled()
    assert main_window.progress_bar.isVisible()
    assert main_window.progress_bar.value() == 0
    assert main_window.status_label.text() == "Running backtest..."

    exec_controller.progress_updated.emit(42)
    assert main_window.progress_bar.value() == 42

    results = object()
    exec_controller.backtest_finished.emit(results)
    assert main_window.run_backtest_action.isEnabled()
    assert not main_window.stop_backtest_action.isEnabled()
    assert not main_window.progress_bar.isVisible()
    assert main_window.status_label.text() == "Backtest completed"
    assert main_window._recorded_results == [results]  # type: ignore[attr-defined]

    exec_controller.backtest_started.emit()
    exec_controller.backtest_error.emit("Boom")
    assert main_window.run_backtest_action.isEnabled()
    assert not main_window.stop_backtest_action.isEnabled()
    assert not main_window.progress_bar.isVisible()
    assert main_window.status_label.text() == "Backtest error: Boom"

