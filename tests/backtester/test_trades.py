"""
Tests for the backtester trades module.
"""

import datetime as dt
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

from src.backtester.trades import TradeOrder, TradeRegistry


class TestTradeOrder:
    """Test TradeOrder creation and validation."""

    def test_trade_order_creation(self):
        """Test basic TradeOrder creation."""
        order = TradeOrder(
            type='buy',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0),
            comment='test entry',
            amount=1,
            slippage=0.1,
            info={'signal': 'rsi_oversold'}
        )
        
        assert order.type == 'buy'
        assert order.price == 100.0
        assert order.datetime == dt.datetime(2024, 1, 1, 10, 0, 0)
        assert order.comment == 'test entry'
        assert order.amount == 1
        assert order.slippage == 0.1
        assert order.info == {'signal': 'rsi_oversold'}

    def test_trade_order_validation(self):
        """Test TradeOrder parameter validation."""
        # Test type validation
        with pytest.raises(TypeError, match="'type' must be a string"):
            TradeOrder(type=123, price=100.0, datetime=dt.datetime.now())
        
        # Test price validation
        with pytest.raises(TypeError, match="'price' must be a float"):
            TradeOrder(type='buy', price="100.0", datetime=dt.datetime.now())
        
        # Test datetime validation
        with pytest.raises(TypeError, match="'datetime' must be a datetime instance"):
            TradeOrder(type='buy', price=100.0, datetime="2024-01-01")
        
        # Test comment validation
        with pytest.raises(TypeError, match="'comment' must be a string"):
            TradeOrder(type='buy', price=100.0, datetime=dt.datetime.now(), comment=123)
        
        # Test amount validation
        with pytest.raises(TypeError, match="'amount' must be an integer if specified"):
            TradeOrder(type='buy', price=100.0, datetime=dt.datetime.now(), amount="1")
        
        # Test slippage validation
        with pytest.raises(TypeError, match="'slippage' must be a float if specified"):
            TradeOrder(type='buy', price=100.0, datetime=dt.datetime.now(), slippage="0.1")
        
        # Test info validation
        with pytest.raises(TypeError, match="'info' must be a dict if specified"):
            TradeOrder(type='buy', price=100.0, datetime=dt.datetime.now(), info="invalid")

    def test_trade_order_optional_parameters(self):
        """Test TradeOrder with optional parameters."""
        order = TradeOrder(
            type='sell',
            price=105.0,
            datetime=dt.datetime(2024, 1, 1, 11, 0, 0)
        )
        
        assert order.comment == ''
        assert order.amount is None
        assert order.slippage is None
        assert order.info is None


class TestTradeRegistry:
    """Test TradeRegistry functionality."""

    def test_trade_registry_initialization(self):
        """Test TradeRegistry initialization."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        assert registry.point_value == 10.0
        assert registry.cost_per_trade == 2.50
        assert registry.trades.empty
        assert len(registry.order_history) == 0
        assert registry.monthly_result is None
        assert registry.tax_per_month is None
        assert registry.total_tax is None
        assert registry.result is None

    def test_trade_registry_validation(self):
        """Test TradeRegistry parameter validation."""
        # Test point_value validation
        with pytest.raises(TypeError, match="point_value must be a float"):
            TradeRegistry(point_value="10.0", cost_per_trade=2.50)
        
        # Test cost_per_trade validation
        with pytest.raises(TypeError, match="cost_per_trade must be a float"):
            TradeRegistry(point_value=10.0, cost_per_trade="2.50")

    def test_register_buy_order(self):
        """Test registering buy orders."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        order = TradeOrder(
            type='buy',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0),
            comment='entry',
            amount=1,
            info={'signal': 'rsi_oversold'}
        )
        
        registry.register_order(order)
        
        assert len(registry.trades) == 1
        assert registry.trades.at[0, 'type'] == 'buy'
        assert registry.trades.at[0, 'buyprice'] == 100.0
        assert registry.trades.at[0, 'start'] == dt.datetime(2024, 1, 1, 10, 0, 0)
        assert registry.trades.at[0, 'entry_comment'] == 'entry'
        assert registry.trades.at[0, 'amount'] == 1
        assert registry.trades.at[0, 'entry_info'] == {'signal': 'rsi_oversold'}
        assert pd.isna(registry.trades.at[0, 'end'])  # Trade not closed yet

    def test_register_sell_order(self):
        """Test registering sell orders."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        order = TradeOrder(
            type='sell',
            price=105.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0),
            comment='short entry',
            amount=1,
            info={'signal': 'rsi_overbought'}
        )
        
        registry.register_order(order)
        
        assert len(registry.trades) == 1
        assert registry.trades.at[0, 'type'] == 'sell'
        assert registry.trades.at[0, 'sellprice'] == 105.0
        assert registry.trades.at[0, 'start'] == dt.datetime(2024, 1, 1, 10, 0, 0)
        assert registry.trades.at[0, 'entry_comment'] == 'short entry'
        assert registry.trades.at[0, 'amount'] == 1
        assert registry.trades.at[0, 'entry_info'] == {'signal': 'rsi_overbought'}

    def test_register_close_order(self):
        """Test registering close orders."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # First register a buy order
        buy_order = TradeOrder(
            type='buy',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0),
            comment='entry'
        )
        registry.register_order(buy_order)
        
        # Then close the position
        close_order = TradeOrder(
            type='close',
            price=105.0,
            datetime=dt.datetime(2024, 1, 1, 11, 0, 0),
            comment='exit',
            info={'signal': 'take_profit'}
        )
        registry.register_order(close_order)
        
        assert len(registry.trades) == 1
        assert registry.trades.at[0, 'sellprice'] == 105.0
        assert registry.trades.at[0, 'end'] == dt.datetime(2024, 1, 1, 11, 0, 0)
        assert registry.trades.at[0, 'exit_comment'] == 'exit'
        assert registry.trades.at[0, 'exit_info'] == {'signal': 'take_profit'}

    def test_register_invert_order(self):
        """Test registering invert orders."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # First register a buy order
        buy_order = TradeOrder(
            type='buy',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0),
            comment='entry'
        )
        registry.register_order(buy_order)
        
        # Then invert to sell
        invert_order = TradeOrder(
            type='invert',
            price=105.0,
            datetime=dt.datetime(2024, 1, 1, 11, 0, 0),
            comment='invert to short',
            info={'signal': 'trend_change'}
        )
        registry.register_order(invert_order)
        
        # Should have closed the buy and opened a sell
        assert len(registry.trades) == 2
        assert registry.trades.at[0, 'type'] == 'buy'
        assert registry.trades.at[0, 'sellprice'] == 105.0  # Closed at 105
        assert registry.trades.at[1, 'type'] == 'sell'
        assert registry.trades.at[1, 'sellprice'] == 105.0  # New short at 105

    def test_register_order_errors(self):
        """Test error conditions for register_order."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # Test buy when position already open
        buy_order1 = TradeOrder(
            type='buy',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0)
        )
        registry.register_order(buy_order1)
        
        buy_order2 = TradeOrder(
            type='buy',
            price=101.0,
            datetime=dt.datetime(2024, 1, 1, 10, 30, 0)
        )
        with pytest.raises(RuntimeError, match="Attempting to register a buy trade when a position is already open"):
            registry.register_order(buy_order2)
        
        # Test close when no position open
        close_order = TradeOrder(
            type='close',
            price=105.0,
            datetime=dt.datetime(2024, 1, 1, 11, 0, 0)
        )
        registry.register_order(close_order)  # Close the first position
        
        with pytest.raises(RuntimeError, match="Attempting to register a close trade when there is no open position"):
            registry.register_order(close_order)
        
        # Test invalid order type
        invalid_order = TradeOrder(
            type='invalid',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0)
        )
        with pytest.raises(ValueError, match="Invalid order type: invalid"):
            registry.register_order(invalid_order)

    def test_pnl_calculation(self):
        """Test P&L calculations."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # Profitable trade
        buy_order = TradeOrder(
            type='buy',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0),
            amount=1
        )
        registry.register_order(buy_order)
        
        sell_order = TradeOrder(
            type='close',
            price=105.0,
            datetime=dt.datetime(2024, 1, 1, 11, 0, 0),
            amount=1
        )
        registry.register_order(sell_order)
        
        # Process trades to calculate P&L
        registry._process_trades()
        
        # Delta = 105 - 100 = 5
        # Result = 5 * 10.0 * 1 = 50.0
        # Cost = 2.50 * 1 = 2.50
        # Profit = 50.0 - 2.50 = 47.50
        assert registry.trades.at[0, 'delta'] == 5.0
        assert registry.trades.at[0, 'result'] == 50.0
        assert registry.trades.at[0, 'cost'] == 2.50
        assert registry.trades.at[0, 'profit'] == 47.50
        assert registry.trades.at[0, 'balance'] == 47.50

    def test_short_trade_pnl(self):
        """Test P&L calculation for short trades."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # Short trade (sell first, then buy to close)
        sell_order = TradeOrder(
            type='sell',
            price=105.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0),
            amount=1
        )
        registry.register_order(sell_order)
        
        buy_order = TradeOrder(
            type='close',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 11, 0, 0),
            amount=1
        )
        registry.register_order(buy_order)
        
        registry._process_trades()
        
        # For short: delta = buyprice - sellprice = 100 - 105 = -5
        # Result = -5 * 10.0 * 1 = -50.0 (but this should be positive for short)
        # The actual calculation should be: (sellprice - buyprice) * point_value
        # Delta = 105 - 100 = 5, Result = 5 * 10.0 * 1 = 50.0
        assert registry.trades.at[0, 'delta'] == 5.0
        assert registry.trades.at[0, 'result'] == 50.0
        assert registry.trades.at[0, 'profit'] == 47.50

    def test_performance_metrics(self):
        """Test performance metrics calculations."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # Add multiple trades
        trades = [
            # Profitable trade
            (TradeOrder('buy', 100.0, dt.datetime(2024, 1, 1, 10, 0, 0), amount=1),
             TradeOrder('close', 105.0, dt.datetime(2024, 1, 1, 11, 0, 0), amount=1)),
            # Losing trade
            (TradeOrder('buy', 105.0, dt.datetime(2024, 1, 1, 12, 0, 0), amount=1),
             TradeOrder('close', 102.0, dt.datetime(2024, 1, 1, 13, 0, 0), amount=1)),
            # Another profitable trade
            (TradeOrder('buy', 102.0, dt.datetime(2024, 1, 1, 14, 0, 0), amount=1),
             TradeOrder('close', 108.0, dt.datetime(2024, 1, 1, 15, 0, 0), amount=1)),
        ]
        
        for entry, exit in trades:
            registry.register_order(entry)
            registry.register_order(exit)
        
        registry._process_trades()
        
        # Check metrics
        assert registry.num_positive_trades == 2
        assert registry.num_negative_trades == 1
        assert registry.positive_trades_sum == 50.0 + 60.0 - 2.5 - 2.5  # 105.0 (after costs)
        assert registry.negative_trades_sum == -30.0 - 2.5  # -32.5 (after costs)
        assert registry.profit_factor == pytest.approx(105.0 / 32.5, rel=1e-2)
        assert registry.accuracy == pytest.approx(66.67, rel=1e-2)  # 2 out of 3 trades profitable

    def test_empty_trades_metrics(self):
        """Test metrics calculation with no trades."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # Test metrics with empty trades
        with pytest.warns(UserWarning, match="Accuracy cannot be calculated as there are no trades"):
            assert registry.accuracy is None
        
        with pytest.warns(UserWarning, match="Mean profit cannot be calculated as there are no trades"):
            assert registry.mean_profit is None
        
        with pytest.warns(UserWarning, match="Mean loss cannot be calculated as there are no trades"):
            assert registry.mean_loss is None

    def test_slippage_handling(self):
        """Test slippage handling in orders."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # Buy order with slippage
        buy_order = TradeOrder(
            type='buy',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0),
            slippage=0.5  # 0.5 point slippage
        )
        registry.register_order(buy_order)
        
        # Sell order with slippage
        sell_order = TradeOrder(
            type='close',
            price=105.0,
            datetime=dt.datetime(2024, 1, 1, 11, 0, 0),
            slippage=0.3  # 0.3 point slippage
        )
        registry.register_order(sell_order)
        
        # Buy price should be adjusted for slippage (100.0 + 0.5 = 100.5)
        # Sell price should be adjusted for slippage (105.0 + 0.3 = 105.3)
        assert registry.trades.at[0, 'buyprice'] == 100.5
        assert registry.trades.at[0, 'sellprice'] == 105.3

    def test_entry_exit_info_persistence(self):
        """Test that entry_info and exit_info are properly stored."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        entry_info = {
            'signals': [
                {'name': 'RSI', 'side': 'long', 'strength': 0.8},
                {'name': 'MACD', 'side': 'long', 'strength': 0.6}
            ],
            'timestamp': dt.datetime(2024, 1, 1, 10, 0, 0)
        }
        
        exit_info = {
            'signals': [
                {'name': 'RSI', 'side': 'short', 'strength': 0.7}
            ],
            'timestamp': dt.datetime(2024, 1, 1, 11, 0, 0)
        }
        
        buy_order = TradeOrder(
            type='buy',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0),
            info=entry_info
        )
        registry.register_order(buy_order)
        
        sell_order = TradeOrder(
            type='close',
            price=105.0,
            datetime=dt.datetime(2024, 1, 1, 11, 0, 0),
            info=exit_info
        )
        registry.register_order(sell_order)
        
        # Check that info is properly stored
        assert registry.trades.at[0, 'entry_info'] == entry_info
        assert registry.trades.at[0, 'exit_info'] == exit_info

    def test_open_trade_info(self):
        """Test open_trade_info property."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # No open trade initially
        assert registry.open_trade_info is None
        
        # Open a buy position
        buy_order = TradeOrder(
            type='buy',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0),
            comment='test entry'
        )
        registry.register_order(buy_order)
        
        # Check open trade info
        open_info = registry.open_trade_info
        assert open_info is not None
        assert open_info['type'] == 'buy'
        assert open_info['price'] == 100.0
        assert open_info['datetime'] == dt.datetime(2024, 1, 1, 10, 0, 0)
        assert open_info['comment'] == 'test entry'
        
        # Close the position
        sell_order = TradeOrder(
            type='close',
            price=105.0,
            datetime=dt.datetime(2024, 1, 1, 11, 0, 0)
        )
        registry.register_order(sell_order)
        
        # No open trade after closing
        assert registry.open_trade_info is None

    def test_trades_today(self):
        """Test trades_today method."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # Add trades on different days
        trades = [
            # Day 1 trades
            (TradeOrder('buy', 100.0, dt.datetime(2024, 1, 1, 10, 0, 0)),
             TradeOrder('close', 105.0, dt.datetime(2024, 1, 1, 11, 0, 0))),
            (TradeOrder('buy', 105.0, dt.datetime(2024, 1, 1, 12, 0, 0)),
             TradeOrder('close', 108.0, dt.datetime(2024, 1, 1, 13, 0, 0))),
            # Day 2 trades
            (TradeOrder('buy', 108.0, dt.datetime(2024, 1, 2, 10, 0, 0)),
             TradeOrder('close', 110.0, dt.datetime(2024, 1, 2, 11, 0, 0))),
        ]
        
        for entry, exit in trades:
            registry.register_order(entry)
            registry.register_order(exit)
        
        # Check trades per day
        assert registry.trades_today(dt.datetime(2024, 1, 1, 15, 0, 0)) == 2
        assert registry.trades_today(dt.datetime(2024, 1, 2, 15, 0, 0)) == 1
        assert registry.trades_today(dt.datetime(2024, 1, 3, 15, 0, 0)) == 0

    def test_net_balance_property(self):
        """Test net_balance property."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # Add a profitable trade
        buy_order = TradeOrder(
            type='buy',
            price=100.0,
            datetime=dt.datetime(2024, 1, 1, 10, 0, 0),
            amount=1
        )
        registry.register_order(buy_order)
        
        sell_order = TradeOrder(
            type='close',
            price=105.0,
            datetime=dt.datetime(2024, 1, 1, 11, 0, 0),
            amount=1
        )
        registry.register_order(sell_order)
        
        # Net balance should be calculated automatically
        assert registry.net_balance == 47.50  # 50.0 - 2.50

    @pytest.mark.slow
    def test_large_number_of_trades(self):
        """Test performance with large number of trades."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # Add 1000 trades
        for i in range(1000):
            buy_order = TradeOrder(
                type='buy',
                price=100.0 + i * 0.01,
                datetime=dt.datetime(2024, 1, 1, 10, 0, 0) + dt.timedelta(minutes=i),
                amount=1
            )
            registry.register_order(buy_order)
            
            sell_order = TradeOrder(
                type='close',
                price=105.0 + i * 0.01,
                datetime=dt.datetime(2024, 1, 1, 10, 1, 0) + dt.timedelta(minutes=i),
                amount=1
            )
            registry.register_order(sell_order)
        
        # Should be able to process all trades
        registry._process_trades()
        assert len(registry.trades) == 1000
        assert registry.net_balance == 47500.0  # 1000 * (50.0 - 2.50)