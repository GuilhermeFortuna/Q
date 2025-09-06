import optuna
from typing import Type, Dict, Any
from src.backtester.engine import Engine
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
    ):
        """
        Initializes the Optimizer.

        Args:
            strategy_class: The trading strategy class to be optimized.
            config: A dictionary containing optimization parameters, including:
                    - 'parameters': A dictionary defining the parameter space for Optuna.
                    - 'n_trials': The number of optimization trials to run.
                    - 'metric': The performance metric to optimize (e.g., 'total_profit').
                    - 'direction': The optimization direction ('maximize' or 'minimize').
            backtest_settings: A dictionary with settings for the backtester engine.
        """
        self.strategy_class = strategy_class
        self.config = config
        self.backtest_settings = backtest_settings
        self.param_space = self.config['parameters']
        self.n_trials = self.config.get('n_trials', 100)
        self.metric = self.config.get('metric', 'total_profit')
        self.direction = self.config.get('direction', 'maximize')

    def _objective(self, trial: optuna.trial.Trial) -> float:
        """
        The objective function for Optuna to optimize.
        """
        # Suggest parameters for the strategy for the current trial
        strategy_params = self._suggest_params(trial)

        # Instantiate the strategy with the suggested parameters
        strategy_instance = self.strategy_class(**strategy_params)

        # Assumption: The backtester.engine.Engine is initialized with a strategy
        # instance and backtest settings.
        engine = Engine(strategy_instance, **self.backtest_settings)

        # Assumption: The run() method executes the backtest and returns a
        # registry object that holds the results.
        registry = engine.run()

        # Assumption: The registry object has a method (e.g., get_summary())
        # that returns a dictionary with performance metrics.
        summary = registry.get_summary()

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
        study = optuna.create_study(direction=self.direction)
        study.optimize(self._objective, n_trials=self.n_trials, show_progress_bar=True)

        print("\nOptimization Finished.")
        print("Best trial:")
        trial = study.best_trial
        print(f"  Value ({self.metric}): {trial.value}")
        print("  Params: ")
        for key, value in trial.params.items():
            print(f"    {key}: {value}")

        return study
