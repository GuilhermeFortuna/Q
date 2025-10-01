import functools
from datetime import datetime

import optuna

from src.backtester import Engine, BacktestParameters
from src.data import CandleData
from src.helper import PrintMessage
from src.strategies import MaCrossoverSignal, CompositeStrategy


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
) -> float | None:
    params = BacktestParameters(
        point_value=point_value,
        cost_per_trade=cost_per_trade,
        permit_swingtrade=permit_swingtrade,
    )
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

    # Run backtest
    engine = Engine(parameters=params, strategy=strategy, data=dict(candle=candles))
    trade_registry = engine.run_backtest(display_progress=True)
    result = trade_registry.get_result(return_result=True, silent_mode=True)

    if result is not None:
        net_balance = result['net_balance (BRL)']
        return net_balance


def objective(
    trial: optuna.Trial,
    candles: CandleData,
    point_value: float,
    cost_per_trade: float,
    tick_value: float,
) -> float | None:
    ma_types = list(MaCrossoverSignal.MA_FUNCS.keys())
    strategy_params = {
        'short_ma_func': trial.suggest_categorical('Short Ma Func', choices=ma_types),
        'short_ma_period': trial.suggest_float(
            'Short Ma Period', low=6, high=14, step=2
        ),
        'long_ma_func': trial.suggest_categorical('Long Ma Func', choices=ma_types),
        'long_ma_period': trial.suggest_float('Long Ma Period', low=9, high=22, step=3),
        'delta_tick_factor': 0.0,
        'permit_swingtrade': True,
    }
    result = run_backtest(
        candles=candles,
        point_value=point_value,
        cost_per_trade=cost_per_trade,
        tick_value=tick_value,
        **strategy_params,
    )

    if result is not None:
        print('\n')
        PrintMessage['SUCCESS'](
            message=f'\n{result}\n', title=f'Trial num: {trial.number}'
        )

    return result


if __name__ == '__main__':

    # Parameters
    symbol, timeframe = 'CCM$', '60min'
    point_value, cost_per_trade, tick_value = 450.0, 2.50, 0.01
    date_from, date_to = datetime(2025, 1, 1), datetime.today()
    num_trials = 5

    # Construct CandleData and get data
    candles = CandleData(symbol=symbol, timeframe=timeframe)
    candles.import_from_mt5(date_from=date_from, date_to=date_to)

    if candles.df is None:
        raise ValueError('No candle data available for optimization.')

    backtest_func = functools.partial(
        objective,
        candles=candles,
        point_value=point_value,
        cost_per_trade=cost_per_trade,
        tick_value=tick_value,
    )
    study = optuna.create_study(
        direction='maximize',
        study_name='MA Crossover Optimization',
        load_if_exists=True,
    )
    study.optimize(backtest_func, n_trials=num_trials)
