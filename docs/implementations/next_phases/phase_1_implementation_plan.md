# Phase 1: Foundation Stabilization - Test Suite & CI/CD

## Overview

This plan focuses on stabilizing the test infrastructure by fixing critical import errors, implementing comprehensive test coverage for core modules (backtester, strategies, data), and establishing automated testing with GitHub Actions. We'll prioritize the most critical components first and expand coverage systematically.

## Critical Path: Import Error Fixes

### 1. Fix Import Errors in Test Files

**Problem**: Three test files have incorrect import statements causing collection failures.

**Files to fix**:

- `tests/backtester/test_daytrade_enforcement.py` (line 3)
- `tests/backtester/test_daytrade_enforcement_tick.py` (line 3)
- `tests/strategies/test_hybrid_strategy.py` (verify imports)

**Change required**: Update `from src.data.data import` to `from src.data import`

**Status**: These files already have correct imports based on review. Verify by running pytest collection.

## Core Module Testing - Priority Order

### 2. Backtester Module Tests (CRITICAL)

**2.1 TradeRegistry Tests** (`tests/backtester/test_trades.py`)

Current state: Already has comprehensive tests implemented (539 lines)

- TradeOrder creation and validation ✓
- TradeRegistry initialization ✓
- Trade registration and P&L calculation ✓
- Tax calculations ✓
- Edge cases ✓

Action: Verify all tests pass and add any missing edge cases.

**2.2 Engine Tests** (`tests/backtester/test_engine.py`)

Current state: Already has comprehensive tests implemented (489 lines)

- BacktestParameters validation ✓
- EngineData preparation ✓
- Full backtest execution ✓
- Progress tracking ✓

Action: Verify all tests pass and ensure coverage of error conditions.

**2.3 Evaluation Tests** (`tests/backtester/test_evaluation.py`)

Check current implementation and add tests for:

- AcceptanceCriteria validation
- StrategyEvaluator scoring logic
- Composite scoring with multiple criteria
- Edge cases (no trades, perfect strategy, etc.)

**2.4 Strategy Interface Tests** (`tests/backtester/test_strategy.py`)

Add tests for:

- TradingStrategy abstract interface
- compute_indicators method
- entry_strategy and exit_strategy contracts
- Strategy state management

**2.5 Utils Tests** (`tests/backtester/test_utils.py`)

Add tests for utility functions in `src/backtester/utils.py`.

### 3. Data Module Tests (HIGH PRIORITY)

**3.1 CandleData Tests** (`tests/data/test_candle_data.py`)

Add comprehensive tests:

- CandleData initialization with different sources (CSV, Parquet, MT5)
- Data validation (OHLC relationships)
- DataFrame property access
- Symbol and timeframe handling
- Error handling for invalid data

**3.2 TickData Tests** (`tests/data/test_tick_data.py`)

Add tests for:

- TickData initialization
- Tick-level data validation
- Time-based filtering
- Conversion to candle data

**3.3 Store Tests** (`tests/data/test_store.py`)

Add tests for:

- Data storage utilities
- File I/O operations
- Format conversions (CSV ↔ Parquet)
- Data caching mechanisms

### 4. Strategy Framework Tests (HIGH PRIORITY)

**4.1 Composite Strategy Tests** (`tests/strategies/test_composite.py`)

Add tests for:

- CompositeStrategy initialization with multiple signals
- Signal aggregation logic
- Entry/exit decision making
- Signal weight handling

**4.2 Combiner Tests** (`tests/strategies/test_combiners.py`)

Add tests for:

- GatedCombiner (filter + entry logic)
- ThresholdedWeightedVote
- WeightedSignalCombiner
- Edge cases (no signals, conflicting signals)

**4.3 Archetype Tests** (`tests/strategies/test_archetypes.py`)

Add tests for:

- create_momentum_rider_strategy()
- create_range_fader_strategy()
- create_volatility_breakout_strategy()
- Verify each archetype produces valid strategies

**4.4 Signal Tests** (`tests/strategies/signals/`)

Current files:

- `test_base.py` - Base signal interface
- `test_helpers.py` - Helper functions
- `test_all_signals.py` - Comprehensive signal tests

Add tests for all 17 signals:

- RSI mean reversion
- MACD momentum
- Supertrend
- Donchian breakout
- ADX/DMI
- Keltner squeeze
- ATR trailing stop
- VWAP deviation
- Heikin Ashi trend
- MTF MA alignment
- Choppiness filter
- Volume spike/exhaustion
- Bollinger Bands
- MA crossover

Each signal test should verify:

- Initialization with parameters
- compute() method returns valid SignalDecision
- Signal logic correctness with known data
- Edge cases (insufficient data, NaN values)

### 5. Bridge Module Tests

**5.1 Data Manager Tests** (`tests/bridge/test_data_manager.py`)

Add tests for:

- Singleton initialization
- Backtest results storage
- Data retrieval
- Cache management

### 6. Visualizer Module Tests

**6.1 Models Tests** (`tests/visualizer/test_models.py`)

Add tests for:

- Data models for visualization
- Model validation
- Data transformation utilities

**6.2 Plot Tests** (NEW: `tests/visualizer/test_plots.py`)

Create new file with tests for:

- Candlestick plot generation
- Line plot creation
- Indicator overlays
- Trade marker rendering

**6.3 Window Tests** (NEW: `tests/visualizer/test_windows.py`)

Create new file with tests for:

- Chart window creation
- Backtest summary window
- Trade analysis window
- Window lifecycle management

### 7. Indicators Module Tests

**7.1 Market Regime Classifier Tests** (`tests/indicators/test_market_regime_classifier.py`)

Add tests for:

- Regime classifier initialization
- Regime detection on sample data
- Regime transition logic
- Edge cases

### 8. GUI Module Tests

**8.1 Main Window Tests** (`tests/gui/test_main_window.py`)

Current state: Has basic smoke tests with qtbot fixture

Action: Verify tests pass and add coverage for:

- Window initialization
- Tab creation and switching
- Basic UI interactions (non-modal)

**8.2 Model Tests** (NEW: `tests/gui/test_models.py`)

Create new file with tests for:

- StrategyModel signal management
- BacktestModel configuration
- Model state changes

**8.3 Controller Tests** (NEW: `tests/gui/test_controllers.py`)

Create new file with tests for:

- StrategyController logic (no UI dependencies)
- ExecutionController backtest orchestration
- Controller state management

## CI/CD Implementation

### 9. GitHub Actions Workflow

**Create**: `.github/workflows/tests.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, ubuntu-latest]
        python-version: ['3.10']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install uv
      uses: astral-sh/setup-uv@v1
      
    - name: Set up Python ${{ matrix.python-version }}
      run: uv python install ${{ matrix.python-version }}
      
    - name: Install dependencies
      run: uv sync
      
    - name: Run tests
      run: uv run pytest -v --cov=src --cov-report=xml --cov-report=term-missing -m "not mt5 and not slow"
      
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false
```

### 10. Update pytest.ini

**File**: `pytest.ini`

Add coverage configuration:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
    gui: GUI tests (requires PySide6)
    mt5: Tests requiring MetaTrader 5
```

### 11. Verify Test Fixtures

**File**: `tests/conftest.py`

Current state: Already has comprehensive fixtures implemented (401 lines)

- sample_ohlcv_data ✓
- sample_tick_data ✓
- candle_data_fixture ✓
- tick_data_fixture ✓
- backtest_params_fixture ✓
- trade_registry_fixture ✓
- mock_mt5_connection ✓
- simple_strategy ✓
- multi_day_candle_data ✓
- sample_metrics ✓
- acceptance_criteria ✓
- strategy_evaluator ✓

Action: Verify all fixtures work correctly and add any missing fixtures discovered during test implementation.

## Integration Tests

### 12. End-to-End Integration Tests

**Create**: `tests/integration/` directory with:

**12.1 Full Backtest Workflow** (`test_full_backtest.py`)

- Load data → configure strategy → run backtest → evaluate results
- Test with real CSV data from `tests/data/common/`
- Test composite strategies with multiple signals
- Verify trade execution, P&L calculations, and metrics

**12.2 Optimization Workflow** (`test_optimization_workflow.py`)

- Full optimization cycle (defer to Phase 2 after optimizer is complete)

## Documentation Updates

### 13. Update Test Documentation

**File**: `tests/README.md`

Current state: Comprehensive documentation already exists (454 lines)

Action: Update with any new test categories or patterns discovered during implementation.

## Success Criteria

- [ ] All tests pass without import errors
- [ ] No placeholder tests remain (all have real assertions)
- [ ] Code coverage >80% on core modules (backtester, strategies, data)
- [ ] Code coverage >70% on visualizer and bridge modules
- [ ] CI/CD pipeline runs successfully on push/PR
- [ ] Test suite runs in <5 minutes (excluding slow tests)
- [ ] All critical path modules have comprehensive test coverage

## Execution Order

1. **Verify current test state** - Run pytest to identify actual failures
2. **Fix any import errors** - Ensure all tests can be collected
3. **Verify existing tests pass** - test_trades.py, test_engine.py, test_daytrade_enforcement.py
4. **Implement data module tests** - Foundation for everything else
5. **Implement strategy signal tests** - Core business logic
6. **Implement evaluation tests** - Strategy assessment
7. **Implement visualizer tests** - User-facing features
8. **Implement GUI tests** - Application layer
9. **Create integration tests** - End-to-end workflows
10. **Set up CI/CD** - Automated testing pipeline
11. **Generate coverage report** - Identify remaining gaps
12. **Fill coverage gaps** - Achieve >80% target

## Notes

- Use `@pytest.mark.unit` for fast, isolated tests
- Use `@pytest.mark.integration` for tests that combine multiple components
- Use `@pytest.mark.slow` for tests that take >5 seconds
- Use `@pytest.mark.gui` for tests requiring PySide6/Qt
- Use `@pytest.mark.mt5` for tests requiring MetaTrader 5
- Mock external dependencies (MT5, file I/O) in unit tests
- Use real data from `tests/data/common/` for integration tests
