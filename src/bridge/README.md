# Bridge

A tiny package that helps share data between components (primarily the backtester and the visualizer). It currently provides a simple in-memory DataManager and a convenient module-level singleton instance, data_manager.

## What it does

- Stores a single backtest result object in memory (e.g., a TradeRegistry from backtester)
- Lets other parts of the app retrieve that result later (e.g., for visualization)

## Installation

This package is part of the workspace. From the project root:

```
uv sync
```

## Quick start

```python
from src.bridge import data_manager

# Somewhere after a backtest finishes
data_manager.set_backtest_results(registry)  # registry can be a TradeRegistry or similar

# Somewhere else (e.g., before showing a summary window)
results = data_manager.get_backtest_results()
if results is not None:
    # pass results to a visualizer component, or read KPIs from it
    print(results.get_result())
```

## API

- DataManager
  - set_backtest_results(results): Store or update the current backtest results object
  - get_backtest_results() -> TradeRegistry | None: Retrieve the stored results
- data_manager: a shared instance of DataManager for convenience

## Notes

- This is deliberately minimal. If you need to hold multiple results, add IDs, persist to disk, or broadcast updates, extend DataManager accordingly.
