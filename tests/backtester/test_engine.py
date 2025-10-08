"""
Tests for the backtester engine module.
"""

import datetime as dt
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from src.backtester.engine import BacktestParameters, Engine, EngineData
from src.backtester.strategy import TradingStrategy
from src.backtester.trades import TradeOrder
from src.data import CandleData, TickData


class TestBacktestParameters:
    """Test BacktestParameters validation and functionality."""

    def test_backtest_parameters_creation(self):
        """Test basic BacktestParameters creation."""
        params = BacktestParameters(
            point_value=10.0,
            cost_per_trade=2.50,
            permit_swingtrade=True,
            entry_time_limit=dt.time(9, 0),
            exit_time_limit=dt.time(17, 0),
            max_trade_day=1,
            bypass_first_exit_check=False
        )
        
        assert params.point_value == 10.0
        assert params.cost_per_trade == 2.50
        assert params.permit_swingtrade is True
        assert params.entry_time_limit == dt.time(9, 0)
        assert params.exit_time_limit == dt.time(17, 0)
        assert params.max_trade_day == 1
        assert params.bypass_first_exit_check is False

    def test_backtest_parameters_validation(self):
        """Test BacktestParameters parameter validation."""
        # Test point_value validation
        with pytest.raises(TypeError, match="point_value must be a float"):
            BacktestParameters(point_value="10.0", cost_per_trade=2.50)
        
        # Test cost_per_trade validation
        with pytest.raises(TypeError, match="cost_per_trade must be a float"):
            BacktestParameters(point_value=10.0, cost_per_trade="2.50")
        
        # Test permit_swingtrade validation
        with pytest.raises(TypeError, match="permit_swingtrade must be a bool"):
            BacktestParameters(point_value=10.0, cost_per_trade=2.50, permit_swingtrade="true")
        
        # Test entry_time_limit validation
        with pytest.raises(TypeError, match="entry_time_limit must be a datetime.time"):
            BacktestParameters(point_value=10.0, cost_per_trade=2.50, entry_time_limit="09:00")
        
        # Test exit_time_limit validation
        with pytest.raises(TypeError, match="exit_time_limit must be a datetime.time"):
            BacktestParameters(point_value=10.0, cost_per_trade=2.50, exit_time_limit="17:00")
        
        # Test max_trade_day validation
        with pytest.raises(TypeError, match="max_trade_day must be an int"):
            BacktestParameters(point_value=10.0, cost_per_trade=2.50, max_trade_day="1")
        
        # Test bypass_first_exit_check validation
        with pytest.raises(TypeError, match="bypass_first_exit_check must be a bool"):
            BacktestParameters(point_value=10.0, cost_per_trade=2.50, bypass_first_exit_check="false")

    def test_backtest_parameters_defaults(self):
        """Test BacktestParameters default values."""
        params = BacktestParameters(point_value=10.0, cost_per_trade=2.50)
        
        assert params.permit_swingtrade is False
        assert params.entry_time_limit is None
        assert params.exit_time_limit is None
        assert params.max_trade_day is None
        assert params.bypass_first_exit_check is False


class TestEngineData:
    """Test EngineData functionality."""

    def test_engine_data_initialization(self, candle_data_fixture):
        """Test EngineData initialization with CandleData."""
        engine_data = EngineData(candle_data_fixture)
        
        assert engine_data.symbol == 'TEST'
        assert isinstance(engine_data.data, pd.DataFrame)
        assert len(engine_data.data) > 0

    def test_engine_data_validation(self):
        """Test EngineData validation."""
        # Test with invalid data object
        with pytest.raises(TypeError, match="data must be an instance of a subclass of MarketData"):
            EngineData("invalid_data")
        
        # Test with CandleData that has no data
        empty_candle = CandleData(symbol='TEST', timeframe='60min')
        with pytest.raises(ValueError, match="data must be a pandas DataFrame"):
            EngineData(empty_candle)

    def test_engine_data_prepare(self, candle_data_fixture):
        """Test EngineData prepare method."""
        engine_data = EngineData(candle_data_fixture)
        
        # Set dtype_map
        engine_data.dtype_map = [
            ('datetime', 'int64'),
            ('open', 'float64'),
            ('high', 'float64'),
            ('low', 'float64'),
            ('close', 'float64'),
            ('volume', 'int64')
        ]
        
        # Prepare data
        prepared_data = engine_data.prepare()
        
        assert isinstance(prepared_data, np.ndarray)
        assert len(prepared_data) == len(candle_data_fixture.df)
        assert prepared_data.dtype.names == ('datetime', 'open', 'high', 'low', 'close', 'volume')


class TestEngine:
    """Test Engine functionality."""

    def test_engine_initialization(self, candle_data_fixture, backtest_params_fixture, simple_strategy):
        """Test Engine initialization."""
        engine = Engine(
            parameters=backtest_params_fixture,
            strategy=simple_strategy,
            data={'candle': candle_data_fixture}
        )
        
        assert engine.parameters == backtest_params_fixture
        assert engine.strategy == simple_strategy
        assert 'candle' in engine.data
        assert engine.data['candle'] == candle_data_fixture

    def test_engine_validation(self, candle_data_fixture, backtest_params_fixture):
        """Test Engine parameter validation."""
        # Test with invalid strategy
        with pytest.raises(TypeError, match="strategy must be an instance of TradingStrategy"):
            Engine(
                parameters=backtest_params_fixture,
                strategy="invalid_strategy",
                data={'candle': candle_data_fixture}
            )
        
        # Test with invalid data
        with pytest.raises(TypeError, match="data must be a dict"):
            Engine(
                parameters=backtest_params_fixture,
                strategy=simple_strategy,
                data="invalid_data"
            )

    def test_engine_data_validation(self, backtest_params_fixture, simple_strategy):
        """Test Engine data validation."""
        # Test with invalid data types in data dict
        with pytest.raises(TypeError, match="data values must be instances of MarketData"):
            Engine(
                parameters=backtest_params_fixture,
                strategy=simple_strategy,
                data={'candle': 'invalid_data'}
            )

    def test_engine_run_backtest_candle_data(self, candle_data_fixture, backtest_params_fixture, simple_strategy):
        """Test running backtest with candle data."""
        engine = Engine(
            parameters=backtest_params_fixture,
            strategy=simple_strategy,
            data={'candle': candle_data_fixture}
        )
        
        # Run backtest
        results = engine.run_backtest(display_progress=False, primary='candle')
        
        assert results is not None
        assert hasattr(results, 'trades')
        assert hasattr(results, 'get_result')
        
        # Check that trades were executed
        result_data = results.get_result()
        assert result_data is not None
        assert 'trades' in result_data

    def test_engine_run_backtest_tick_data(self, tick_data_fixture, backtest_params_fixture, simple_strategy):
        """Test running backtest with tick data."""
        engine = Engine(
            parameters=backtest_params_fixture,
            strategy=simple_strategy,
            data={'tick': tick_data_fixture}
        )
        
        # Run backtest
        results = engine.run_backtest(display_progress=False, primary='tick')
        
        assert results is not None
        assert hasattr(results, 'trades')
        assert hasattr(results, 'get_result')

    def test_engine_run_backtest_hybrid_data(self, candle_data_fixture, tick_data_fixture, backtest_params_fixture, simple_strategy):
        """Test running backtest with both candle and tick data."""
        engine = Engine(
            parameters=backtest_params_fixture,
            strategy=simple_strategy,
            data={'candle': candle_data_fixture, 'tick': tick_data_fixture}
        )
        
        # Run backtest
        results = engine.run_backtest(display_progress=False, primary='candle')
        
        assert results is not None
        assert hasattr(results, 'trades')
        assert hasattr(results, 'get_result')

    def test_engine_progress_tracking(self, candle_data_fixture, backtest_params_fixture, simple_strategy):
        """Test progress tracking during backtest."""
        engine = Engine(
            parameters=backtest_params_fixture,
            strategy=simple_strategy,
            data={'candle': candle_data_fixture}
        )
        
        # Mock tqdm to capture progress calls
        with patch('tqdm.tqdm') as mock_tqdm:
            mock_progress = Mock()
            mock_tqdm.return_value = mock_progress
            
            # Run backtest with progress tracking
            results = engine.run_backtest(display_progress=True, primary='candle')
            
            # Verify progress bar was created and updated
            mock_tqdm.assert_called_once()
            mock_progress.update.assert_called()

    def test_engine_daytrade_enforcement(self, multi_day_candle_data, backtest_params_fixture):
        """Test daytrade enforcement."""
        # Create a strategy that holds positions across days
        class HoldStrategy(TradingStrategy):
            def compute_indicators(self, data: dict) -> None:
                pass
            
            def entry_strategy(self, i: int, data: dict):
                if i == 1:  # Enter on second bar
                    return TradeOrder(
                        type='buy',
                        price=float(data['candle'].close[i]),
                        datetime=data['candle'].datetime_index[i],
                        comment='entry'
                    )
                return None
            
            def exit_strategy(self, i: int, data: dict, trade_info=None):
                # Never exit voluntarily
                return None
        
        # Set permit_swingtrade=False to enforce daytrade rules
        params = BacktestParameters(
            point_value=10.0,
            cost_per_trade=2.50,
            permit_swingtrade=False
        )
        
        engine = Engine(
            parameters=params,
            strategy=HoldStrategy(),
            data={'candle': multi_day_candle_data}
        )
        
        # Run backtest
        results = engine.run_backtest(display_progress=False, primary='candle')
        
        # Check that trades were closed at end of day
        trades = results.trades.trades
        assert len(trades) > 0
        
        # All trades should be closed (no open positions)
        for _, trade in trades.iterrows():
            assert pd.notna(trade['end'])
            assert 'End of day close' in trade['exit_comment']

    def test_engine_time_limits(self, candle_data_fixture, backtest_params_fixture):
        """Test entry and exit time limits."""
        class TimeLimitedStrategy(TradingStrategy):
            def compute_indicators(self, data: dict) -> None:
                pass
            
            def entry_strategy(self, i: int, data: dict):
                # Try to enter on every bar
                return TradeOrder(
                    type='buy',
                    price=float(data['candle'].close[i]),
                    datetime=data['candle'].datetime_index[i],
                    comment='entry'
                )
            
            def exit_strategy(self, i: int, data: dict, trade_info=None):
                # Exit on next bar
                if i > 0:
                    return TradeOrder(
                        type='close',
                        price=float(data['candle'].close[i]),
                        datetime=data['candle'].datetime_index[i],
                        comment='exit'
                    )
                return None
        
        # Set time limits
        params = BacktestParameters(
            point_value=10.0,
            cost_per_trade=2.50,
            entry_time_limit=dt.time(10, 0),
            exit_time_limit=dt.time(16, 0)
        )
        
        engine = Engine(
            parameters=params,
            strategy=TimeLimitedStrategy(),
            data={'candle': candle_data_fixture}
        )
        
        # Run backtest
        results = engine.run_backtest(display_progress=False, primary='candle')
        
        # Check that trades respect time limits
        trades = results.trades.trades
        if len(trades) > 0:
            for _, trade in trades.iterrows():
                entry_time = trade['start'].time()
                exit_time = trade['end'].time()
                
                # Entry should be within time limits
                if params.entry_time_limit:
                    assert entry_time >= params.entry_time_limit
                
                # Exit should be within time limits
                if params.exit_time_limit:
                    assert exit_time <= params.exit_time_limit

    def test_engine_max_trade_day_limit(self, multi_day_candle_data, backtest_params_fixture):
        """Test max_trade_day limit."""
        class LongHoldStrategy(TradingStrategy):
            def compute_indicators(self, data: dict) -> None:
                pass
            
            def entry_strategy(self, i: int, data: dict):
                if i == 1:  # Enter on second bar
                    return TradeOrder(
                        type='buy',
                        price=float(data['candle'].close[i]),
                        datetime=data['candle'].datetime_index[i],
                        comment='entry'
                    )
                return None
            
            def exit_strategy(self, i: int, data: dict, trade_info=None):
                # Never exit voluntarily
                return None
        
        # Set max_trade_day=1
        params = BacktestParameters(
            point_value=10.0,
            cost_per_trade=2.50,
            permit_swingtrade=True,
            max_trade_day=1
        )
        
        engine = Engine(
            parameters=params,
            strategy=LongHoldStrategy(),
            data={'candle': multi_day_candle_data}
        )
        
        # Run backtest
        results = engine.run_backtest(display_progress=False, primary='candle')
        
        # Check that trades are closed after max_trade_day
        trades = results.trades.trades
        if len(trades) > 0:
            for _, trade in trades.iterrows():
                trade_duration = trade['end'] - trade['start']
                # Trade duration should not exceed max_trade_day
                assert trade_duration.days <= params.max_trade_day

    def test_engine_data_manager_integration(self, candle_data_fixture, backtest_params_fixture, simple_strategy):
        """Test integration with data_manager."""
        engine = Engine(
            parameters=backtest_params_fixture,
            strategy=simple_strategy,
            data={'candle': candle_data_fixture}
        )
        
        # Mock data_manager
        with patch('src.bridge.data_manager') as mock_data_manager:
            mock_data_manager.store_backtest_result = Mock()
            
            # Run backtest
            results = engine.run_backtest(display_progress=False, primary='candle')
            
            # Verify that results were stored in data_manager
            mock_data_manager.store_backtest_result.assert_called_once()

    def test_engine_error_handling(self, candle_data_fixture, backtest_params_fixture):
        """Test error handling in engine."""
        class FailingStrategy(TradingStrategy):
            def compute_indicators(self, data: dict) -> None:
                raise ValueError("Strategy computation failed")
            
            def entry_strategy(self, i: int, data: dict):
                return None
            
            def exit_strategy(self, i: int, data: dict, trade_info=None):
                return None
        
        engine = Engine(
            parameters=backtest_params_fixture,
            strategy=FailingStrategy(),
            data={'candle': candle_data_fixture}
        )
        
        # Run backtest - should handle errors gracefully
        with pytest.raises(ValueError, match="Strategy computation failed"):
            engine.run_backtest(display_progress=False, primary='candle')

    def test_engine_empty_data(self, backtest_params_fixture, simple_strategy):
        """Test engine with empty data."""
        # Create empty candle data
        empty_candle = CandleData(symbol='TEST', timeframe='60min')
        empty_candle.df = pd.DataFrame()
        
        engine = Engine(
            parameters=backtest_params_fixture,
            strategy=simple_strategy,
            data={'candle': empty_candle}
        )
        
        # Run backtest with empty data
        results = engine.run_backtest(display_progress=False, primary='candle')
        
        # Should complete without errors but with no trades
        assert results is not None
        assert len(results.trades.trades) == 0

    @pytest.mark.slow
    def test_engine_large_dataset(self, backtest_params_fixture, simple_strategy):
        """Test engine performance with large dataset."""
        # Create large dataset
        dates = pd.date_range('2024-01-01', periods=10000, freq='1min')
        np.random.seed(42)
        
        base_price = 100.0
        returns = np.random.normal(0, 0.001, 10000)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        prices = np.array(prices)
        
        data = {
            'open': prices + np.random.normal(0, 0.0001, 10000),
            'high': prices + np.abs(np.random.normal(0, 0.0005, 10000)),
            'low': prices - np.abs(np.random.normal(0, 0.0005, 10000)),
            'close': prices,
            'volume': np.random.randint(100, 1000, 10000)
        }
        
        df = pd.DataFrame(data, index=dates)
        df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
        df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
        
        large_candle = CandleData(symbol='TEST', timeframe='1min')
        large_candle.df = df
        
        engine = Engine(
            parameters=backtest_params_fixture,
            strategy=simple_strategy,
            data={'candle': large_candle}
        )
        
        # Run backtest - should complete successfully
        results = engine.run_backtest(display_progress=False, primary='candle')
        
        assert results is not None
        assert hasattr(results, 'trades')
        assert hasattr(results, 'get_result')