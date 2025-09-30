from src.backtester import Engine, BacktestParameters
from src.data import CandleData
from src.strategies import MaCrossoverSignal, CompositeStrategy
from datetime import datetime


def run_backtest(
    candles: CandleData,
    point_value: float,
    cost_per_trade: float,
    tick_value: float,
    short_ma_func: str,
    short_ma_period: int,
    long_ma_func: str,
    long_ma_period: int,
    delta_tick_factor: int,
    permit_swingtrade: bool = True,
):

    #
    params = BacktestParameters(
        point_value=point_value,
        cost_per_trade=cost_per_trade,
        permit_swingtrade=permit_swingtrade,
    )
    # Old (pre-migration) approach:
    # from src.strategies.swingtrade import MaCrossover
    # strategy = MaCrossover(
    #     tick_value=tick_value,
    #     short_ma_func=short_ma_func,
    #     short_ma_period=short_ma_period,
    #     long_ma_func=long_ma_func,
    #     long_ma_period=long_ma_period,
    #     delta_tick_factor=delta_tick_factor,
    #     always_active=True,
    # )

    # New composable approach (identical behavior):
    strategy = CompositeStrategy(
        signals=[
            MaCrossoverSignal(
                tick_value=tick_value,
                short_ma_func=short_ma_func,
                short_ma_period=short_ma_period,
                long_ma_func=long_ma_func,
                long_ma_period=long_ma_period,
                delta_tick_factor=delta_tick_factor,
            )
        ],
        always_active=True,
    )

    #
    engine = Engine(parameters=params, strategy=strategy, data=dict(candle=candles))
    trade_registry = engine.run_backtest(display_progress=True)
    result = trade_registry.get_result(return_result=True, silent_mode=True)

    if result is not None:
        net_balance = result['net_balance (BRL)']
        return net_balance


if __name__ == '__main__':
    from src.helper import
    symbol, timeframe = 'CCM$', '60min'
    date_from, date_to = datetime(2025, 1, 1), datetime.today()
    candles = CandleData(symbol=symbol, timeframe=timeframe)
    candle_data = candles.import_from_mt5(date_from=date_from, date_to=date_to)

    final_balance = run_backtest(
        candles=candles,
        point_value=450.0,
        cost_per_trade=2.5,
        tick_value=0.01,
        short_ma_func='ema',
        long_ma_func='sma',
        long_ma_period=12,
        short_ma_period=9,
        delta_tick_factor=7,
        permit_swingtrade=True,
    )
