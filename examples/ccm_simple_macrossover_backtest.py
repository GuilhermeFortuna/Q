from datetime import datetime

import pandas as pd

from src.backtester import Engine, BacktestParameters
from src.data import CandleData
from src.strategies import MaCrossoverSignal, CompositeStrategy
from src.visualizer import show_backtest_summary


EXAMPLE_DATA_PATH = 'data/ccm_60min.csv'
SYMBOL = 'CCM'
TIMEFRAME = '60min'
DATE_FROM = datetime(2020, 1, 1)
DATE_TO = datetime.today()

SHORT_MA_FUNC = 'ema'
SHORT_MA_PERIOD = 9

LONG_MA_FUNC = 'sma'
LONG_MA_PERIOD = 12

DELTA_TICK_FACTOR = 7
TICK_VALUE = 0.01

if __name__ == '__main__':

    # Load data
    candles = CandleData(symbol=SYMBOL, timeframe=TIMEFRAME)
    candles.df = pd.read_csv(EXAMPLE_DATA_PATH)
    # candle_data = candles.import_from_mt5(date_from=DATE_FROM, date_to=DATE_TO)

    # Define backtest parameters
    params = BacktestParameters(
        point_value=450.00, cost_per_trade=2.50, permit_swingtrade=True
    )

    # Create signal
    ma_crossover_signal = MaCrossoverSignal(
        tick_value=TICK_VALUE,
        short_ma_func=SHORT_MA_FUNC,
        short_ma_period=SHORT_MA_PERIOD,
        long_ma_func=LONG_MA_FUNC,
        long_ma_period=LONG_MA_PERIOD,
        delta_tick_factor=DELTA_TICK_FACTOR,
    )

    # Define strategy using the new composable architecture
    strategy = CompositeStrategy(
        signals=[ma_crossover_signal],
        always_active=True,
    )

    # Run backtest
    engine = Engine(parameters=params, strategy=strategy, data=dict(candle=candles))
    trades = engine.run_backtest()
    result = trades.get_result(return_result=True, silent_mode=False)

    # Backtest result visualization
    if result is not None:
        # Prepare OHLC data for enhanced summary
        ohlc_data = candles.df.copy()
        show_backtest_summary(results=trades, ohlc_df=ohlc_data)
