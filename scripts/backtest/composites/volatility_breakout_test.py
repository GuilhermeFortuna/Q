from datetime import datetime

from src.backtester.data import CandleData
from src.backtester.engine import BacktestParameters, Engine
from src.backtester.trades import TradeRegistry
from src.strategies.archetypes import create_volatility_breakout_strategy

# Config (Approved specs)
TIMEFRAME = '5min'
DATE_FROM = datetime(2025, 1, 1)
DATE_TO = datetime.today()
MT5_SYMBOL = 'WDO$'
POINT_VALUE = 10.0
COST_PER_TRADE = 1.0


def run_backtest(
    mt5_symbol: str = MT5_SYMBOL,
    timeframe: str = TIMEFRAME,
    date_from: datetime = DATE_FROM,
    date_to: datetime = DATE_TO,
) -> tuple[TradeRegistry, CandleData]:
    candles = CandleData(symbol=mt5_symbol.replace('$', ''), timeframe=timeframe)
    df = CandleData.import_from_mt5(
        mt5_symbol=mt5_symbol, timeframe=timeframe, date_from=date_from, date_to=date_to
    )[['open', 'high', 'low', 'close', 'real_volume']].copy()
    df.rename(columns={'real_volume': 'volume'}, inplace=True)
    candles.data = df.loc[(df.index >= date_from) & (df.index <= date_to)].copy()

    params = BacktestParameters(point_value=POINT_VALUE, cost_per_trade=COST_PER_TRADE)
    strategy = create_volatility_breakout_strategy()

    engine = Engine(parameters=params, strategy=strategy, data={'candle': candles})
    trade_registry = engine.run_backtest(display_progress=True)
    trade_registry.get_result()
    return trade_registry, candles


if __name__ == '__main__':
    from src.visualizer import show_backtest_summary

    tr, candles = run_backtest()
    ohlc = candles.data.copy()
    if 'time' not in ohlc.columns:
        ohlc.insert(0, 'time', list(range(len(ohlc))))
    show_backtest_summary(tr, ohlc_df=ohlc)
