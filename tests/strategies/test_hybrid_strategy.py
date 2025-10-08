from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.data import CandleData, TickData
from src.backtester import BacktestParameters, Engine
from src.strategies import HybridCandleTickStrategy, HybridExecutionConfig
from src.strategies.signals.base import TradingSignal, SignalDecision


class DummyEnterLongAtIndex1(TradingSignal):
    def compute_indicators(self, data: dict) -> None:
        # No indicators needed
        return None

    def generate(self, i: int, data: dict) -> SignalDecision:
        if i == 1:
            return SignalDecision(side='long', strength=1.0)
        return SignalDecision(side=None, strength=0.0)


def make_candles(start: datetime) -> CandleData:
    # Create three 1-minute candles
    times = [start + timedelta(minutes=k) for k in range(3)]
    df = pd.DataFrame(
        {
            'open': [100.0, 100.5, 101.0],
            'high': [100.8, 101.0, 101.5],
            'low': [99.8, 100.2, 100.9],
            'close': [100.6, 100.9, 101.2],
            'volume': [10, 12, 9],
        },
        index=pd.DatetimeIndex(times),
    )
    return CandleData(symbol='TEST', timeframe='1min', data=df)


def make_ticks_between(t0: datetime, t1: datetime, prices: list[float]) -> TickData:
    n = len(prices)
    # Evenly spaced within [t0, t1), avoid equality at t1
    deltas = [k * (t1 - t0) / (n + 1) for k in range(1, n + 1)]
    times = [t0 + d for d in deltas]
    df = pd.DataFrame({'datetime': times, 'price': prices, 'volume': [1] * n})
    return TickData(symbol='TEST', data=df)


def run_engine(candles: CandleData, ticks: TickData, strategy) -> Engine:
    params = BacktestParameters(point_value=10.0, cost_per_trade=0.0)
    eng = Engine(
        parameters=params, strategy=strategy, data={'candle': candles, 'tick': ticks}
    )
    eng.run_backtest(display_progress=False, primary='candle')
    return eng


def test_hybrid_breakout_enters_on_first_tick_breaking_high():
    start = datetime(2025, 1, 1, 9, 0, 0)
    candles = make_candles(start)
    # Window is [t1, t2). Candle[1].high == 101.0
    t1, t2 = candles.data.index[1], candles.data.index[2]
    # Prices below high, then cross above
    ticks = make_ticks_between(t1, t2, prices=[100.7, 100.9, 101.1, 101.2])

    # Strategy: long on i==1, breakout mode
    exec_cfg = HybridExecutionConfig(mode='breakout', tick_value=0.1)
    strat = HybridCandleTickStrategy(
        signals=[DummyEnterLongAtIndex1()], execution=exec_cfg
    )

    eng = run_engine(candles, ticks, strat)

    # Verify a trade exists and entry matches first tick >= 101.0
    assert len(eng.trades.trades) >= 1
    row = eng.trades.trades.iloc[0]
    # Entry time should match the third tick (first >= 101.0)
    expected_entry_time = ticks.data['datetime'].iloc[2]
    expected_entry_price = float(ticks.data['price'].iloc[2])
    assert row['start'] == expected_entry_time
    assert row['buyprice'] == expected_entry_price


def test_hybrid_pullback_enters_after_open_minus_delta():
    start = datetime(2025, 1, 1, 9, 0, 0)
    candles = make_candles(start)
    # Candle[1].open == 100.5, with tick_value=0.1 and pullback_ticks=3 => level = 100.2
    t1, t2 = candles.data.index[1], candles.data.index[2]
    ticks = make_ticks_between(t1, t2, prices=[100.45, 100.35, 100.25, 100.15, 100.30])

    exec_cfg = HybridExecutionConfig(mode='pullback', pullback_ticks=3, tick_value=0.1)
    strat = HybridCandleTickStrategy(
        signals=[DummyEnterLongAtIndex1()], execution=exec_cfg
    )

    eng = run_engine(candles, ticks, strat)

    # First tick <= 100.2 is 100.15 (fourth tick)
    row = eng.trades.trades.iloc[0]
    expected_entry_time = ticks.data['datetime'].iloc[3]
    expected_entry_price = float(ticks.data['price'].iloc[3])
    assert row['start'] == expected_entry_time
    assert row['buyprice'] == expected_entry_price
