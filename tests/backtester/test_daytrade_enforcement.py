import pandas as pd

from src.data import CandleData
from src.backtester.engine import BacktestParameters, Engine
from src.backtester.strategy import TradingStrategy
from src.backtester.trades import TradeOrder


class AlwaysBuyThenHoldStrategy(TradingStrategy):
    def compute_indicators(self, data: dict) -> None:
        return None

    def entry_strategy(self, i: int, data: dict):
        # Enter at the first opportunity (i == 1) using candle close
        candle = data['candle']
        if i == 1:
            return TradeOrder(
                type='buy',
                price=float(candle.close[i]),
                datetime=candle.datetime_index[i],
                comment='entry',
                amount=1,
            )
        return None

    def exit_strategy(self, i: int, data: dict, trade_info=None):
        # Never exit voluntarily; engine should enforce EOD close in daytrade mode
        return None


def test_daytrade_forced_close_on_date_change():
    # Build minimal 3-bar candle data spanning a day change
    idx = pd.to_datetime(
        [
            '2024-01-01 10:00:00',
            '2024-01-01 16:00:00',
            '2024-01-02 10:00:00',
        ]
    )
    df = pd.DataFrame(
        {
            'open': [100.0, 100.5, 101.5],
            'high': [101.0, 101.5, 102.5],
            'low': [99.5, 100.0, 101.0],
            'close': [100.2, 101.0, 102.0],
            'volume': [100, 120, 110],
        },
        index=idx,
    )

    candle = CandleData(symbol='TEST', timeframe='60min', data=df)

    params = BacktestParameters(
        point_value=1.0, cost_per_trade=0.0, permit_swingtrade=False
    )
    strategy = AlwaysBuyThenHoldStrategy()

    engine = Engine(parameters=params, strategy=strategy, data={'candle': candle})
    reg = engine.run_backtest(display_progress=False, primary='candle')

    # Exactly one trade should be opened and then closed by EOD on the same bar as entry (index 1)
    assert len(reg.trades) == 1
    start = reg.trades.at[0, 'start']
    end = reg.trades.at[0, 'end']
    assert start == idx[1]
    assert end == idx[1]
    assert 'End of day close' in reg.trades.at[0, 'exit_comment']
