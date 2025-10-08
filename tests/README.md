# Test Suite Documentation

This directory contains comprehensive tests for the q quantitative trading framework.

## Test Organization

The test suite is organized to mirror the source code structure:

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                # Shared fixtures and configuration
├── backtester/                # Backtester engine tests
│   ├── test_engine.py         # Engine and BacktestParameters tests
│   ├── test_trades.py         # TradeRegistry and TradeOrder tests
│   ├── test_evaluation.py     # Strategy evaluation tests
│   ├── test_strategy.py       # TradingStrategy interface tests
│   ├── test_data.py           # Data handling tests
│   ├── test_utils.py          # Utility function tests
│   ├── test_daytrade_enforcement.py      # Daytrade enforcement tests
│   └── test_daytrade_enforcement_tick.py # Tick-level daytrade tests
├── data/                      # Data module tests
│   ├── test_candle_data.py    # CandleData tests
│   ├── test_tick_data.py      # TickData tests
│   └── test_store.py          # Data storage utility tests
├── strategies/                # Strategy framework tests
│   ├── test_composite.py      # CompositeStrategy tests
│   ├── test_combiners.py      # Signal combiner tests
│   ├── test_archetypes.py     # Strategy archetype tests
│   └── signals/               # Individual signal tests
│       ├── test_base.py       # Base signal interface tests
│       ├── test_helpers.py    # Signal helper function tests
│       └── test_all_signals.py # Comprehensive signal tests
├── optimizer/                 # Optimization engine tests
│   └── test_engine.py         # Optimizer and Optuna integration tests
├── visualizer/                # Visualization tests
│   ├── test_models.py         # Data model tests
│   ├── test_plots.py          # Plot component tests
│   └── test_windows.py        # Window component tests
├── bridge/                    # Bridge module tests
│   └── test_data_manager.py   # Data manager tests
├── indicators/                # Indicator tests
│   └── test_market_regime_classifier.py # Market regime tests
└── integration/               # End-to-end integration tests
    ├── test_full_backtest.py  # Complete backtest workflow tests
    └── test_optimization_workflow.py # Optimization workflow tests
```

## Running Tests

### Prerequisites

Ensure you have the required dependencies installed:

```bash
uv sync
```

### Basic Test Execution

Run all tests:
```bash
uv run pytest
```

Run tests with verbose output:
```bash
uv run pytest -v
```

Run tests with coverage:
```bash
uv run pytest --cov=src --cov-report=html
```

### Running Specific Test Categories

Run only unit tests:
```bash
uv run pytest -m unit
```

Run only integration tests:
```bash
uv run pytest -m integration
```

Run only slow tests:
```bash
uv run pytest -m slow
```

Run GUI tests (requires PySide6):
```bash
uv run pytest -m gui
```

Run MT5 tests (requires MetaTrader 5):
```bash
uv run pytest -m mt5
```

### Running Specific Test Files

Run backtester tests:
```bash
uv run pytest tests/backtester/
```

Run data module tests:
```bash
uv run pytest tests/data/
```

Run strategy tests:
```bash
uv run pytest tests/strategies/
```

Run signal tests:
```bash
uv run pytest tests/strategies/signals/
```

### Running Specific Test Functions

Run a specific test:
```bash
uv run pytest tests/backtester/test_engine.py::TestEngine::test_engine_initialization
```

Run tests matching a pattern:
```bash
uv run pytest -k "test_trade"
```

## Test Configuration

### Pytest Configuration

The test configuration is defined in `pytest.ini`:

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
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
    gui: GUI tests (requires PySide6)
    mt5: Tests requiring MetaTrader 5
```

### Test Fixtures

Common test fixtures are defined in `conftest.py`:

- `sample_ohlcv_data`: Basic OHLCV DataFrame for testing
- `sample_tick_data`: Tick-level data for testing
- `candle_data_fixture`: CandleData instance with realistic data
- `tick_data_fixture`: TickData instance for testing
- `backtest_params_fixture`: Standard BacktestParameters
- `trade_registry_fixture`: Pre-populated TradeRegistry
- `mock_mt5_connection`: Mock MT5 connection for data import tests
- `simple_strategy`: Simple test strategy for backtesting
- `multi_day_candle_data`: Multi-day data for daytrade testing
- `sample_metrics`: Sample performance metrics
- `acceptance_criteria`: Standard acceptance criteria
- `strategy_evaluator`: StrategyEvaluator instance

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

Fast, isolated tests that test individual components:

- Individual signal implementations
- Trade order creation and validation
- Parameter validation
- Data format conversions
- Utility functions

### Integration Tests (`@pytest.mark.integration`)

Tests that verify components work together:

- Complete backtest workflows
- Strategy evaluation pipelines
- Data loading and processing
- Signal combination logic

### Slow Tests (`@pytest.mark.slow`)

Tests that take longer to run:

- Large dataset processing
- Performance benchmarks
- Complex optimization scenarios

### GUI Tests (`@pytest.mark.gui`)

Tests requiring GUI components:

- Window creation and interaction
- Plot rendering
- User interface validation

### MT5 Tests (`@pytest.mark.mt5`)

Tests requiring MetaTrader 5:

- Live data import
- MT5 connection validation
- Real-time data processing

## Test Data

### Sample Data

Test data is generated programmatically to ensure reproducibility:

- **OHLCV Data**: Realistic price movements with proper OHLC relationships
- **Tick Data**: High-frequency price updates with volume
- **Multi-day Data**: Data spanning multiple trading days for daytrade testing
- **Trending Data**: Data with clear trends for momentum strategy testing
- **Ranging Data**: Sideways data for mean reversion strategy testing

### Data Validation

All test data is validated to ensure:

- Proper OHLC relationships (High >= max(Open, Close), Low <= min(Open, Close))
- Realistic price movements
- Appropriate volume patterns
- Correct datetime handling

## Writing Tests

### Test Structure

Follow the standard pytest structure:

```python
class TestComponentName:
    """Test component functionality."""
    
    def test_specific_functionality(self):
        """Test specific functionality."""
        # Arrange
        # Act
        # Assert
```

### Test Naming

- Test classes: `TestComponentName`
- Test methods: `test_specific_functionality`
- Use descriptive names that explain what is being tested

### Test Documentation

- Include docstrings for all test classes and methods
- Explain the purpose and expected behavior
- Document any special setup or teardown requirements

### Test Data

- Use fixtures for common test data
- Generate data programmatically for reproducibility
- Validate test data before using it in tests

### Assertions

- Use specific assertions that provide clear error messages
- Test both positive and negative cases
- Verify edge cases and boundary conditions

### Mocking

- Mock external dependencies (MT5, file I/O, network calls)
- Use `unittest.mock` for complex mocking scenarios
- Verify mock interactions when necessary

## Coverage Goals

### Target Coverage

- **Core modules**: >90% coverage
- **Backtester engine**: >95% coverage
- **Strategy framework**: >90% coverage
- **Data modules**: >85% coverage
- **Overall project**: >80% coverage

### Coverage Reports

Generate coverage reports:

```bash
# Terminal report
uv run pytest --cov=src --cov-report=term-missing

# HTML report
uv run pytest --cov=src --cov-report=html
```

View HTML coverage report:
```bash
open htmlcov/index.html
```

## Continuous Integration

### GitHub Actions

Tests are automatically run on:

- Push to main branch
- Pull request creation
- Pull request updates

### Test Matrix

Tests run on:

- Python 3.10
- Windows, macOS, Linux
- Different dependency versions

### Pre-commit Hooks

Recommended pre-commit hooks:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed with `uv sync`
2. **MT5 Tests Failing**: Install MetaTrader 5 or skip MT5 tests with `-m "not mt5"`
3. **GUI Tests Failing**: Install PySide6 or skip GUI tests with `-m "not gui"`
4. **Slow Tests**: Skip slow tests with `-m "not slow"`

### Debug Mode

Run tests in debug mode:

```bash
uv run pytest --pdb
```

### Verbose Output

Get detailed test output:

```bash
uv run pytest -v -s
```

### Test Discovery

Check which tests would be run:

```bash
uv run pytest --collect-only
```

## Contributing

### Adding New Tests

1. Create test file in appropriate directory
2. Follow naming conventions
3. Include comprehensive docstrings
4. Use appropriate fixtures
5. Add proper markers if needed

### Test Requirements

- All tests must pass
- New code must have corresponding tests
- Tests must be deterministic and reproducible
- Tests should run in reasonable time
- Use appropriate test markers

### Review Process

- All test changes require review
- Ensure tests cover edge cases
- Verify test data is realistic
- Check for proper cleanup
- Validate error handling

## Performance Considerations

### Test Speed

- Unit tests should run quickly (< 1 second each)
- Use mocking to avoid slow operations
- Mark slow tests appropriately
- Consider parallel execution for independent tests

### Memory Usage

- Clean up large test data
- Use fixtures for data reuse
- Avoid loading unnecessary data
- Monitor memory usage in CI

### Test Isolation

- Tests should not depend on each other
- Use fresh data for each test
- Avoid shared state
- Clean up after tests

## Best Practices

1. **Test Early and Often**: Write tests as you develop
2. **Test Behavior, Not Implementation**: Focus on what the code does, not how
3. **Use Descriptive Names**: Make test names self-documenting
4. **Keep Tests Simple**: One concept per test
5. **Use Fixtures**: Reuse common test setup
6. **Mock External Dependencies**: Isolate units under test
7. **Test Edge Cases**: Include boundary conditions and error cases
8. **Maintain Test Data**: Keep test data realistic and up-to-date
9. **Document Test Purpose**: Explain why tests exist
10. **Review Test Coverage**: Ensure adequate coverage of critical paths
