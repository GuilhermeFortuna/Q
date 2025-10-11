import functools
from datetime import datetime, timedelta

import optuna
import pandas as pd

from src.backtester import Engine, BacktestParameters
from src.data import CandleData
from src.helper import PrintMessage
from src.strategies import __signals__, CompositeStrategy, GatedCombiner

DATA_FILE_PATH = r'/scripts/data_from_profit/raw_data/wdo/wdo_5min.csv'

SYMBOL, TIMEFRAME = 'WDO$', '5min'
POINT_VALUE, COST_PER_TRADE, TICK_VALUE = 10.0, 2.50, 0.5
DATE_TO = datetime.today()
DATE_FROM = DATE_TO - timedelta(days=90)
NUM_TRIALS = 200


def objective(
    trial: optuna.Trial,
    candles: CandleData,
    point_value: float,
    tick_value: float,
    cost_per_trade: float = 2.5,
    permit_swingtrade: bool = False,
    always_active: bool = False,
) -> float | None:
    # Get signal dict
    signals = {}
    for signal in __signals__:
        signals[str(signal)] = (
            signal()
            if str(signal) != 'MaCrossoverSignal'
            else signal(tick_value=tick_value)
        )

    backtest_params = BacktestParameters(point_value, cost_per_trade, permit_swingtrade)

    # Get signal and strategy suggestion
    signal_1_key = trial.suggest_categorical('signal 1', choices=list(signals.keys()))
    signal_2_key = trial.suggest_categorical('signal 2', choices=list(signals.keys()))
    require_all_filters = trial.suggest_categorical(
        'require all filters', choices=[True, False]
    )
    require_entry_agreement = trial.suggest_categorical(
        'require entry agreement', choices=[True, False]
    )

    # Create gated combiner
    gated_combiner = GatedCombiner(
        filter_indices=[0],
        entry_indices=[1],
        require_all_filters=require_all_filters,
        require_entry_agreement=require_entry_agreement,
    )

    # Create strategy
    strategy = CompositeStrategy(
        signals=[signals[signal_1_key], signals[signal_2_key]],
        combiner=gated_combiner,
        always_active=always_active,
    )

    # Run backtest and get results
    engine = Engine(
        parameters=backtest_params, strategy=strategy, data={"candle": candles}
    )
    registry = engine.run_backtest(display_progress=False)
    result = registry.get_result(silent_mode=True, return_result=True)

    if result is not None:
        final_balance = result['net_balance (BRL)']
        print('\n')
        PrintMessage['SUCCESS'](
            message=f'Balance: {final_balance}', title=f'Trial num: {trial.number}'
        )
        return final_balance


if __name__ == '__main__':
    from src.optimizer import DBStorage

    storage = DBStorage()
    path = storage.file_path
    print(storage.study_path)

    # Construct CandleData and get data
    '''candles = CandleData(symbol=SYMBOL, timeframe=TIMEFRAME)
    # candles.import_from_mt5(date_from=date_from, date_to=date_to)
    candles.import_from_csv(DATA_FILE_PATH)
    
    if candles.df is None:
        raise ValueError('No candle data available for optimization.')

    backtest_func = functools.partial(
        objective,
        candles=candles,
        point_value=POINT_VALUE,
        cost_per_trade=COST_PER_TRADE,
        tick_value=TICK_VALUE,
        permit_swingtrade=True,
    )
    study = optuna.create_study(
        direction='maximize',
        study_name='dual_signal_selection',
        load_if_exists=True,
        storage='sqlite:///db.sqlite3',
    )
    # study.optimize(backtest_func, n_trials=NUM_TRIALS)'''
