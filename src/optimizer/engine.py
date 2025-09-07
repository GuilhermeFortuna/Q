import optuna
from typing import Type, Dict, Any, Union
from optuna.storages import BaseStorage
from src.backtester.data import CandleData
from src.backtester.engine import Engine, BacktestParameters
from src.backtester.strategy import TradingStrategy


class Optimizer:
    """
    Manages the optimization of a trading strategy using Optuna.
    """

    def __init__(
        self,
        strategy_class: Type[TradingStrategy],
        config: Dict[str, Any],
        backtest_settings: Dict[str, Any],
        candle_data: CandleData,
        study_name: str,
        storage: Union[str, BaseStorage],
    ):
        """
        Initializes the Optimizer.

        Args:
            strategy_class: The trading strategy class to be optimized.
            config: A dictionary containing optimization parameters, including:
                    - 'parameters': A dictionary defining the parameter space for Optuna.
                    - 'n_trials': The number of optimization trials to run.
                    - 'metric': The performance metric to optimize (e.g., 'net_profit').
                    - 'direction': The optimization direction ('maximize' or 'minimize').
            backtest_settings: A dictionary with settings for the backtester engine.
            candle_data: The candle data to be used for the backtests.
            study_name: The name of the study for persistence.
            storage: The storage backend, either a URL string or a storage object.
        """
        self.strategy_class = strategy_class
        self.config = config
        self.backtest_settings = backtest_settings
        self.candle_data = candle_data
        self.study_name = study_name
        self.storage = storage
        self.param_space = self.config['parameters']
        self.n_trials = self.config.get('n_trials', 100)
        self.metric = self.config.get('metric', 'net_profit')
        self.direction = self.config.get('direction', 'maximize')
        self.backtest_params = BacktestParameters(
            **self.backtest_settings.get('parameters', {})
        )
        self.strategy_base_params = self.backtest_settings.get('strategy_params', {})

    def _objective(self, trial: optuna.trial.Trial) -> float:
        """
        The objective function for Optuna to optimize.
        """
        # Suggest parameters for the strategy for the current trial
        strategy_params = self._suggest_params(trial)

        # Combine with base params from backtest_settings
        all_strategy_params = {**self.strategy_base_params, **strategy_params}

        # Instantiate the strategy with the suggested parameters
        strategy_instance = self.strategy_class(**all_strategy_params)

        engine = Engine(
            parameters=self.backtest_params,
            strategy=strategy_instance,
            data={'candle': self.candle_data},
        )

        registry = engine.run_backtest(display_progress=False)
        summary = registry.get_result()

        if summary is None:
            return -1e9  # Return a very low value if backtest fails

        return summary.get(self.metric, 0.0)

    def _suggest_params(self, trial: optuna.trial.Trial) -> Dict[str, Any]:
        """
        Suggests parameters for a trial based on the defined parameter space.
        """
        params = {}
        for name, details in self.param_space.items():
            param_type = details['type']
            if param_type == 'int':
                params[name] = trial.suggest_int(
                    name, details['min'], details['max'], step=details.get('step', 1)
                )
            elif param_type == 'float':
                params[name] = trial.suggest_float(
                    name, details['min'], details['max'], step=details.get('step')
                )
            elif param_type == 'categorical':
                params[name] = trial.suggest_categorical(name, details['choices'])
        return params

    def run(self) -> optuna.study.Study:
        """
        Runs the optimization study and returns the study object.
        """
        study = optuna.create_study(
            study_name=self.study_name,
            storage=self.storage,
            load_if_exists=True,
            direction=self.direction,
        )
        study.optimize(self._objective, n_trials=self.n_trials, show_progress_bar=True)

        print("\nOptimization Finished.")
        print(f"Study: {self.study_name}")
        print("Best trial:")
        trial = study.best_trial
        print(f"  Value ({self.metric}): {trial.value}")
