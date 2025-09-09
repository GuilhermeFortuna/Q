import warnings
from datetime import datetime

from src.backtester.data import CandleData
from src.backtester.engine import BacktestParameters, Engine
from src.optimizer.engine import Optimizer
from src.strategies.swingtrade import MaCrossover


# Parameters
DATA_PATH = r'F:\New_Backup_03_2025\PyQuant\data\ccm_60min_atualizado.csv'
TIMEFRAME = '60min'
DATE_FROM = datetime(2023, 1, 1)
DATE_TO = datetime(2023, 12, 31)

# Backtest parameters
CASH = 100_000
POINT_VALUE = 450.00
COST_PER_TRADE = 2.50


def run_backtest(
    data_path: str = DATA_PATH,
    timeframe: str = TIMEFRAME,
    date_from: datetime = DATE_FROM,
    date_to: datetime = DATE_TO,
):
    """Runs a backtest for the MaCrossover strategy."""

    # Load data
    candles = CandleData(symbol='CCM', timeframe=timeframe)
    candle_data = candles.import_from_csv(data_path)
    candles.data = candle_data.loc[
        (candle_data.index >= date_from) & (candle_data.index <= date_to)
    ].copy()

    # Strategy Parameters
    STRATEGY_PARAMS = {'tick_value': 0.01, 'always_active': True}

    # Backtest parameters
    BACKTEST_PARAMS = BacktestParameters(
        cash=CASH, point_value=POINT_VALUE, cost_per_trade=COST_PER_TRADE
    )

    # Run backtest
    engine = Engine(
        strategy_class=MaCrossover,
        strategy_params=STRATEGY_PARAMS,
        backtest_params=BACKTEST_PARAMS,
        candle_data=candles,
    )
    trade_registry = engine.run_backtest(display_progress=True)
    trade_registry.get_result()
    return trade_registry, candles


def run_optimization(
    data_path: str = DATA_PATH,
    timeframe: str = TIMEFRAME,
    date_from: datetime = DATE_FROM,
    date_to: datetime = DATE_TO,
):
    """Runs an optimization for the MaCrossover strategy."""
    # Load data
    candles = CandleData(symbol='CCM', timeframe=timeframe)
    candle_data = candles.import_from_csv(data_path)
    candles.data = candle_data.loc[
        (candle_data.index >= date_from) & (candle_data.index <= date_to)
    ].copy()

    # Define the parameter space for optimization
    optimization_config = {
        'parameters': {
            'short_ma_period': {'type': 'int', 'min': 5, 'max': 20},
            'long_ma_period': {'type': 'int', 'min': 21, 'max': 50},
            'delta_tick_factor': {'type': 'float', 'min': 0.5, 'max': 10.0},
            'short_ma_func': {
                'type': 'categorical',
                'choices': ['sma', 'ema', 'dema', 'jma'],
            },
            'long_ma_func': {
                'type': 'categorical',
                'choices': ['sma', 'ema', 'dema', 'jma'],
            },
        },
        'n_trials': 100,
        'metric': 'net_profit',
        'direction': 'maximize',
    }

    # Define settings for the backtest runs within the optimization
    backtest_settings = {
        'parameters': {'point_value': 450.00, 'cost_per_trade': 2.50},
        'strategy_params': {'tick_value': 0.01, 'always_active': True},
    }

    # --- Storage for Optimization and Dashboard (PostgreSQL) ---
    # NOTE: You must have a PostgreSQL server running and the database created.
    # You can easily run one using Docker with the following command:
    # docker run --name optuna-db -e POSTGRES_USER=optuna -e POSTGRES_PASSWORD=test -e POSTGRES_DB=optuna_studies -p 5432:5432 -d postgres

    db_user = "optuna"
    db_password = "test"
    db_host = "localhost"
    db_port = "5432"
    db_name = "optuna_studies"

    study_name = "ma_crossover_ccm_optimization"
    storage_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Print the command to launch the dashboard
    dashboard_command = f"optuna-dashboard {storage_url}"
    print("-" * 60)
    print("Optuna Dashboard is available.")
    print(
        f"To start, run the following command in a new terminal:\n\n  {dashboard_command}\n"
    )
    print("NOTE: Make sure your PostgreSQL server is running.")
    print("-" * 60)

    # Initialize and run the optimizer
    optimizer = Optimizer(
        strategy_class=MaCrossover,
        config=optimization_config,
        backtest_settings=backtest_settings,
        candle_data=candles,
        study_name=study_name,
        storage=storage_url,
    )
    optimizer.run()


if __name__ == '__main__':
    from src.visualizer import show_backtest_summary

    warnings.filterwarnings('ignore')

    RUN_OPTIMIZATION = True

    if RUN_OPTIMIZATION:
        run_optimization()
    else:
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
