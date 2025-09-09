import warnings
from datetime import datetime


from src.backtester.data import CandleData
from src.backtester.engine import BacktestParameters, Engine
from src.backtester.trades import TradeRegistry
from src.strategies.swingtrade import MaCrossover


# Parameters
DATA_PATH = r'F:\New_Backup_03_2025\PyQuant\data\ccm_60min_atualizado.csv'
TIMEFRAME = '60min'
DATE_FROM = datetime(2020, 1, 1)
DATE_TO = datetime.today()

TICK_VALUE = 0.01
SHORT_MA_FUNC = 'ema'
SHORT_MA_PERIOD = 9
LONG_MA_FUNC = 'sma'
LONG_MA_PERIOD = 12
DELTA_TICK_FACTOR = 7


def run_backtest(
    data_path: str = DATA_PATH,
    timeframe: str = TIMEFRAME,
    date_from: datetime = DATE_FROM,
    date_to: datetime = DATE_TO,
    tick_value: float = TICK_VALUE,
    short_ma_func: str = SHORT_MA_FUNC,
    short_ma_period: int = SHORT_MA_PERIOD,
    long_ma_func: str = LONG_MA_FUNC,
    long_ma_period: int = LONG_MA_PERIOD,
    delta_tick_factor: int = DELTA_TICK_FACTOR,
) -> TradeRegistry:
    #
    candles = CandleData(symbol='CCM', timeframe=timeframe)
    candle_data = CandleData.import_from_mt5(
        mt5_symbol='CCM$', timeframe=timeframe, date_from=date_from, date_to=date_to
    )[['open', 'high', 'low', 'close', 'real_volume']].copy()
    candle_data.rename(columns={'real_volume': 'volume'}, inplace=True)
    candles.data = candle_data.loc[
        (candle_data.index >= date_from) & (candle_data.index <= date_to)
    ].copy()

    #
    params = BacktestParameters(point_value=450.00, cost_per_trade=2.50)
    strategy = MaCrossover(
        tick_value=tick_value,
        short_ma_func=short_ma_func,
        short_ma_period=short_ma_period,
        long_ma_func=long_ma_func,
        long_ma_period=long_ma_period,
        delta_tick_factor=delta_tick_factor,
        always_active=True,
    )

    #
    engine = Engine(parameters=params, strategy=strategy, data=dict(candle=candles))
    trade_registry = engine.run_backtest(display_progress=True)
    trade_registry.get_result()
    return trade_registry, candles


if __name__ == '__main__':
    from src.visualizer import show_backtest_summary

    warnings.filterwarnings('ignore')

    # Run backtest and retrieve results
    trade_registry, candles = run_backtest()
    trades = trade_registry.trades
    result = trade_registry.get_result()

    # Backtest result visualization
    if result is not None:
        # Prepare OHLC data for enhanced summary
        ohlc_data = candles.data.copy()
        # Ensure we have a 'time' column - use numeric index for bar mode
        if 'time' not in ohlc_data.columns:
            ohlc_data.insert(0, 'time', list(range(len(ohlc_data))))

        # Show enhanced summary with full integration
        show_backtest_summary(trade_registry, ohlc_df=ohlc_data)
