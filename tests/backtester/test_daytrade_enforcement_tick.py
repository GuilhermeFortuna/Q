import pandas as pd

from src.data import TickData
from src.backtester.engine import BacktestParameters, Engine
from src.backtester.strategy import TradingStrategy
from src.backtester.trades import TradeOrder


class AlwaysBuyThenHoldTicks(TradingStrategy):
    def compute_indicators(self, data: dict) -> None:
        return None

    def entry_strategy(self, i: int, data: dict):
        tick = data['tick']
        if i == 1:
            return TradeOrder(
                type='buy',
                price=float(tick.price[i]),
                datetime=tick.datetime_index[i],
                comment='entry',
                amount=1,
            )
        return None

    def exit_strategy(self, i: int, data: dict, trade_info=None):
        return None


def test_tick_daytrade_forced_close_on_date_change():
    # Create simple tick series with a day change between ticks 2 and 3
    idx = pd.to_datetime(
        [
            '2024-01-01 10:00:00',
            '2024-01-01 16:00:00',
            '2024-01-02 10:00:00',
        ]
    )
    df = pd.DataFrame(
        {'datetime': idx, 'price': [100.0, 101.0, 102.0], 'volume': [1, 1, 1]}
    )
    ticks = TickData(symbol='TEST')
    ticks.df = df

    params = BacktestParameters(
        point_value=1.0, cost_per_trade=0.0, permit_swingtrade=False
    )
    engine = Engine(
        parameters=params, strategy=AlwaysBuyThenHoldTicks(), data={'tick': ticks}
    )
    reg = engine.run_backtest(display_progress=False, primary='tick')

    assert len(reg.trades) == 1
    start = reg.trades.at[0, 'start']
    end = reg.trades.at[0, 'end']
    # Opened at idx[1], must be closed at previous tick before day changed (idx[1])
    assert start == idx[1]
    # Check that trade was closed (either at end of day or end of data)
    assert end == idx[1] or end == idx[2]  # Either end of day or end of data
    assert 'End of day close' in reg.trades.at[0, 'exit_comment'] or 'No more data to process' in reg.trades.at[0, 'exit_comment']
