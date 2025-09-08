from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any, Optional, Dict, Mapping
from datetime import datetime, timedelta
import math


class BacktestResultModel:
    """
    Data model for standardizing backtest results input and providing
    cached computed properties for the visualizer components.
    """

    def __init__(
        self,
        registry: Any = None,
        result: Optional[Dict[str, Any]] = None,
        trades_df: Optional[pd.DataFrame] = None,
        ohlc_df: Optional[pd.DataFrame] = None,
    ):
        """
        Initialize the model from either a registry instance or raw data.

        Args:
            registry: Backtest registry instance with get_result() method
            result: Dict of compiled KPIs
            trades_df: DataFrame with trade data
            ohlc_df: Optional DataFrame with OHLC market data
        """
        if registry is not None:
            self._result = self._extract_result_from_registry(registry)
            self._trades_df = self._extract_trades_from_registry(registry)
        else:
            self._result = result or {}
            self._trades_df = trades_df

        self._ohlc_df = ohlc_df

        # Normalize and validate data
        self._normalize_data()

        # Cached properties
        self._balance: Optional[pd.Series] = None
        self._drawdown: Optional[pd.Series] = None
        self._monthly_df: Optional[pd.DataFrame] = None

    def _extract_result_from_registry(self, registry: Any) -> Dict[str, Any]:
        """Extract result dict from registry instance."""
        if hasattr(registry, 'get_result'):
            return registry.get_result()
        elif hasattr(registry, 'result'):
            return registry.result
        return {}

    def _extract_trades_from_registry(self, registry: Any) -> Optional[pd.DataFrame]:
        """Extract trades DataFrame from registry instance."""
        if hasattr(registry, 'get_trades_df'):
            return registry.get_trades_df()
        elif hasattr(registry, 'trades_df'):
            return registry.trades_df
        elif hasattr(registry, 'trades'):
            trades = registry.trades
            if isinstance(trades, pd.DataFrame):
                return trades
        return None

    def _normalize_data(self):
        """Normalize and validate data formats."""
        if self._trades_df is not None:
            # Ensure datetime columns are properly formatted
            for col in ['start', 'end']:
                if col in self._trades_df.columns:
                    if not pd.api.types.is_datetime64_any_dtype(self._trades_df[col]):
                        try:
                            self._trades_df[col] = pd.to_datetime(self._trades_df[col])
                        except:
                            pass

            # Ensure numeric columns are properly typed
            numeric_cols = ['buyprice', 'sellprice', 'amount', 'profit']
            for col in numeric_cols:
                if col in self._trades_df.columns:
                    self._trades_df[col] = pd.to_numeric(
                        self._trades_df[col], errors='coerce'
                    )

    @property
    def result(self) -> Dict[str, Any]:
        """Get the result dict."""
        return self._result

    @property
    def trades_df(self) -> Optional[pd.DataFrame]:
        """Get the trades DataFrame."""
        return self._trades_df

    @property
    def ohlc_df(self) -> Optional[pd.DataFrame]:
        """Get the OHLC DataFrame."""
        return self._ohlc_df

    @property
    def balance(self) -> Optional[pd.Series]:
        """Get the cumulative balance series."""
        if self._balance is None:
            self._balance = self._compute_balance_series()
        return self._balance

    @property
    def drawdown(self) -> Optional[pd.Series]:
        """Get the drawdown series."""
        if self._drawdown is None:
            self._drawdown = self._compute_drawdown_series()
        return self._drawdown

    @property
    def monthly_df(self) -> Optional[pd.DataFrame]:
        """Get the monthly results DataFrame."""
        if self._monthly_df is None:
            self._monthly_df = self._compute_monthly_results()
        return self._monthly_df

    def _compute_balance_series(self) -> Optional[pd.Series]:
        """Compute cumulative balance from trades."""
        if self._trades_df is None or self._trades_df.empty:
            return None

        try:
            # Use profit column if available, otherwise calculate from prices
            if 'profit' in self._trades_df.columns:
                profits = self._trades_df['profit'].fillna(0)
            elif all(
                col in self._trades_df.columns
                for col in ['buyprice', 'sellprice', 'amount']
            ):
                profits = (
                    self._trades_df['sellprice'] - self._trades_df['buyprice']
                ) * self._trades_df['amount']
                profits = profits.fillna(0)
            else:
                return None

            # Get initial balance from result if available
            initial_balance = self._result.get('initial_balance', 0)
            if isinstance(initial_balance, str):
                try:
                    initial_balance = float(
                        initial_balance.replace('BRL', '').replace(',', '')
                    )
                except:
                    initial_balance = 0

            cumulative_balance = initial_balance + profits.cumsum()

            # Use trade end times as index if available
            if 'end' in self._trades_df.columns:
                return pd.Series(
                    cumulative_balance.values, index=self._trades_df['end']
                )
            else:
                return cumulative_balance

        except Exception:
            return None

    def _compute_drawdown_series(self) -> Optional[pd.Series]:
        """Compute drawdown from balance series."""
        balance = self.balance
        if balance is None:
            return None

        try:
            # Handle NaN and infinite values
            balance_clean = balance.replace([np.inf, -np.inf], np.nan).fillna(
                method='ffill'
            )
            if balance_clean.empty:
                return None

            peak = balance_clean.expanding().max()
            drawdown = balance_clean - peak
            return drawdown
        except Exception:
            return None

    def _compute_monthly_results(self) -> Optional[pd.DataFrame]:
        """Compute monthly aggregated results."""
        if self._trades_df is None or self._trades_df.empty:
            return None

        try:
            # Group by month
            if 'end' not in self._trades_df.columns:
                return None

            df = self._trades_df.copy()
            df['month'] = df['end'].dt.to_period('M')

            monthly_stats = []
            balance = self.balance

            for month, group in df.groupby('month'):
                stats = {
                    'month': str(month),
                    'num_trades': len(group),
                    'result': (
                        group.get('profit', 0).sum() if 'profit' in group.columns else 0
                    ),
                    'cost': (
                        group.get('cost', 0).sum() if 'cost' in group.columns else 0
                    ),
                    'tax': group.get('tax', 0).sum() if 'tax' in group.columns else 0,
                    'profit': (
                        group[group.get('profit', 0) > 0]['profit'].sum()
                        if 'profit' in group.columns
                        else 0
                    ),
                }

                # Get end-of-month balance
                if balance is not None:
                    month_end_trades = group['end'].max()
                    month_balance = balance[balance.index <= month_end_trades]
                    stats['balance'] = (
                        month_balance.iloc[-1] if not month_balance.empty else 0
                    )
                else:
                    stats['balance'] = 0

                monthly_stats.append(stats)

            return pd.DataFrame(monthly_stats)
        except Exception:
            return None

    def format_value(self, key: str, value: Any) -> str:
        """Format a value for display based on its key and type."""
        if value is None or (
            isinstance(value, float) and (math.isnan(value) or math.isinf(value))
        ):
            return "—"

        try:
            # Currency values
            if any(
                term in key.lower()
                for term in ['balance', 'profit', 'loss', 'cost', 'tax', 'drawdown']
            ):
                if isinstance(value, (int, float)):
                    return f"{value:,.2f}"
                elif isinstance(value, str) and 'BRL' in value:
                    return value
                else:
                    return f"{float(value):,.2f}"

            # Percentage values
            elif (
                'accuracy' in key.lower()
                or 'drawdown_relative' in key.lower()
                or 'drawdown_final' in key.lower()
            ):
                if isinstance(value, (int, float)):
                    return f"{value:.2f}%"
                elif isinstance(value, str) and '%' in value:
                    return value
                else:
                    return f"{float(value):.2f}%"

            # Ratio values
            elif any(term in key.lower() for term in ['factor', 'ratio']):
                if isinstance(value, (int, float)):
                    return f"{value:.3f}"
                else:
                    return f"{float(value):.3f}"

            # Date values
            elif any(term in key.lower() for term in ['date', 'start', 'end']):
                if isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, str):
                    try:
                        dt_val = pd.to_datetime(value)
                        return dt_val.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        return str(value)
                else:
                    return str(value)

            # Integer values (trades counts)
            elif any(
                term in key.lower()
                for term in ['trades', 'total', 'positive', 'negative']
            ):
                return str(int(float(value)))

            # Duration
            elif 'duration' in key.lower():
                if isinstance(value, (int, float)):
                    return f"{int(value)} days"
                else:
                    return str(value)

            # Default formatting
            else:
                if isinstance(value, float):
                    return f"{value:.6f}"
                else:
                    return str(value)

        except (ValueError, TypeError):
            return str(value) if value is not None else "—"


def compute_balance_series(
    trades_df: pd.DataFrame, initial_balance: float = 0
) -> pd.Series:
    """Pure function to compute balance series from trades DataFrame."""
    if trades_df is None or trades_df.empty:
        return pd.Series(dtype=float)

    if 'profit' in trades_df.columns:
        profits = trades_df['profit'].fillna(0)
    elif all(col in trades_df.columns for col in ['buyprice', 'sellprice', 'amount']):
        profits = (trades_df['sellprice'] - trades_df['buyprice']) * trades_df['amount']
        profits = profits.fillna(0)
    else:
        return pd.Series(dtype=float)

    cumulative_balance = initial_balance + profits.cumsum()

    if 'end' in trades_df.columns:
        return pd.Series(cumulative_balance.values, index=trades_df['end'])
    else:
        return cumulative_balance


def compute_drawdown_series(balance: pd.Series) -> pd.Series:
    """Pure function to compute drawdown from balance series."""
    if balance is None or balance.empty:
        return pd.Series(dtype=float)

    balance_clean = balance.replace([np.inf, -np.inf], np.nan).fillna(method='ffill')
    if balance_clean.empty:
        return pd.Series(dtype=float)

    peak = balance_clean.expanding().max()
    drawdown = balance_clean - peak
    return drawdown


from dataclasses import dataclass
from typing import Any, Literal, Optional


@dataclass
class IndicatorConfig:
    """
    A standardized configuration object for plotting technical indicators.

    This dataclass ensures that all necessary parameters are provided in a
    structured format, improving clarity and reducing errors when defining
    indicators for the `show_chart` function.

    Attributes:
        type (Literal['line', 'scatter', 'histogram']): The type of plot.
        y (pd.Series | np.ndarray): The y-axis data for the indicator.
        name (str): The name of the indicator for legends and titles.
        x (Optional[pd.Series | np.ndarray]): The x-axis data. If None, the
            OHLC data's index will be used. Defaults to None.
        color (str): The color for the plot. Defaults to 'cyan'.
        width (int): The line width (for 'line' type). Defaults to 2.
        size (int): The marker size (for 'scatter' type). Defaults to 10.
        symbol (str): The marker symbol (for 'scatter' type). Defaults to 'o'.
    """

    type: Literal['line', 'scatter', 'histogram']
    y: Any
    name: str
    x: Optional[Any] = None
    color: str = 'cyan'
    width: int = 2
    size: int = 10
    symbol: str = 'o'
