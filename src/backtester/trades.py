import datetime as dt
import math
import warnings
from collections import OrderedDict
from dataclasses import dataclass
from typing import Union, Optional, Dict

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')


@dataclass
class TradeOrder:
    type: str
    price: float
    datetime: dt.datetime
    comment: str = ''
    amount: Optional[int] = None
    slippage: Optional[float] = None
    info: Optional[dict] = None

    def __post_init__(self):
        if not isinstance(self.type, str):
            raise TypeError("'type' must be a string.")

        if not isinstance(self.price, float):
            raise TypeError("'price' must be a float.")

        if not isinstance(self.datetime, dt.datetime):
            raise TypeError("'datetime' must be a datetime instance.")

        if not isinstance(self.comment, str):
            raise TypeError("'comment' must be a string.")

        if self.amount is not None and not isinstance(self.amount, int):
            raise TypeError("'amount' must be an integer if specified.")

        if self.slippage is not None and not isinstance(self.slippage, float):
            raise TypeError("'slippage' must be a float if specified.")

        if self.info is not None and not isinstance(self.info, dict):
            raise TypeError("'info' must be a dict if specified.")


class TradeRegistry:

    def __init__(self, point_value: float, cost_per_trade: float):
        '''
        Constructor for TradeRegister class.

        :param point_value: float. The value per point of variation in the asset price.
        :param cost_per_trade: float. The cost per trade.
        '''

        if not isinstance(point_value, float):
            raise TypeError('point_value must be a float.')

        if not isinstance(cost_per_trade, float):
            raise TypeError('cost_per_trade must be a float.')

        self.point_value = point_value
        self.cost_per_trade = cost_per_trade
        self.trades = pd.DataFrame(
            columns=[
                'start',
                'end',
                'amount',
                'type',
                'buyprice',
                'sellprice',
                'delta',
                'result',
                'cost',
                'profit',
                'balance',
                'entry_comment',
                'exit_comment',
                'entry_info',
                'exit_info',
            ],
        )
        self.order_history = OrderedDict({})
        self.monthly_result = None
        self.tax_per_month = None
        self.total_tax = None
        self.result = None

    @property
    def net_balance(self) -> float:
        '''
        Returns net balance.
        '''

        # Check if all trades have been processed. If not, process trades.
        if self.trades['balance'].isna().any():
            self._process_trades()

        return round(self.trades['balance'].iat[-1], 2)

    @property
    def num_positive_trades(self) -> int:
        '''
        Returns number of positive trades.
        '''

        # Check if all trades have been processed. If not, process trades.
        if self.trades['result'].isna().any():
            self._process_trades()

        return self.trades.loc[self.trades['result'] > 0, 'result'].count()

    @property
    def num_negative_trades(self) -> int:
        '''
        Returns number of negative trades.
        '''

        # Check if all trades have been processed. If not, process trades.
        if self.trades['result'].isna().any():
            self._process_trades()

        return self.trades.loc[self.trades['result'] < 0, 'result'].count()

    @property
    def positive_trades_sum(self) -> float:
        '''
        Returns sum of positive trades.
        '''

        # Check if all trades have been processed. If not, process trades.
        if self.trades['result'].isna().any():
            self._process_trades()

        return self.trades.loc[self.trades['result'] > 0, 'result'].sum()

    @property
    def negative_trades_sum(self) -> float:
        '''
        Returns sum of negative trades.
        '''

        # Check if all trades have been processed. If not, process trades.
        if self.trades['result'].isna().any():
            self._process_trades()

        return self.trades.loc[self.trades['result'] < 0, 'result'].sum()

    @property
    def profit_factor(self) -> float:
        '''
        Returns profit factor.
        '''

        profit_factor = (
            self.positive_trades_sum / abs(self.negative_trades_sum)
            if self.negative_trades_sum != 0
            else math.inf if self.positive_trades_sum > 0 else 0
        )
        return round(profit_factor, 2)

    @property
    def accuracy(self) -> float:
        '''
        Returns trade accuracy.
        '''

        # Check if trades is not empty.
        if self.trades.empty:
            warnings.warn('Accuracy cannot be calculated as there are no trades.')
            return

        accuracy = (self.num_positive_trades / len(self.trades)) * 100
        return round(accuracy, 2)

    @property
    def mean_profit(self) -> float:
        '''
        Returns mean profit.
        '''

        # Check if trades is not empty.
        if self.trades.empty:
            warnings.warn('Mean profit cannot be calculated as there are no trades.')
            return

        mean_profit = (
            self.positive_trades_sum / self.num_positive_trades
            if self.num_positive_trades != 0
            else 0
        )
        return round(mean_profit, 2)

    @property
    def mean_loss(self) -> float:
        '''
        Returns mean loss.
        '''

        # Check if trades is not empty.
        if self.trades.empty:
            warnings.warn('Mean loss cannot be calculated as there are no trades.')
            return

        mean_loss = (
            self.negative_trades_sum / self.num_negative_trades
            if self.num_negative_trades != 0
            else 0
        )
        return round(mean_loss, 2)

    @property
    def mean_profit_loss_ratio(self) -> float:
        '''
        Returns mean profit to loss ratio.
        '''

        # Check if trades is not empty.
        if self.trades.empty:
            warnings.warn(
                'Mean profit loss ratio cannot be calculated as there are no trades.'
            )
            return

        ratio = (
            self.mean_profit / abs(self.mean_loss)
            if self.mean_loss != 0
            else math.inf if self.mean_profit != 0 else 0
        )
        return round(ratio, 2)

    @property
    def result_standard_deviation(self) -> float:
        '''
        Returns result standard deviation.
        '''

        # Check if trades is not empty.
        if self.trades.empty:
            warnings.warn(
                'Result standard deviation cannot be calculated as there are no trades.'
            )
            return

        return round(self.trades['result'].std(), 2)

    @property
    def _last_trade_index(self) -> int:
        '''
        Returns index of last trade.
        '''
        return len(self.trades.index) - 1 if not self.trades.empty else 0

    @property
    def _new_trade_index(self) -> int:
        '''
        Returns index to register new trade.
        '''
        return len(self.trades.index) if not self.trades.empty else 0

    @property
    def open_trade_info(self) -> Union[dict, None]:
        '''
        Get information on current open trade. Returns None if no trade is open.

        :return: Union[dict, None].
        '''

        # Check if there is an open trade
        last_trade_idx = self._last_trade_index
        if (
            not self.trades.empty
            and isinstance(self.trades.at[last_trade_idx, 'start'], dt.datetime)
            and not isinstance(self.trades.at[last_trade_idx, 'end'], dt.datetime)
        ):

            # Store information from open trade in dictionary
            trade_info = {}
            trade_info['type'] = self.trades.at[last_trade_idx, 'type']
            trade_info['price'] = (
                self.trades.at[last_trade_idx, 'buyprice']
                if trade_info['type'] == 'buy'
                else self.trades.at[last_trade_idx, 'sellprice']
            )
            trade_info['datetime'] = self.trades.at[last_trade_idx, 'start']
            trade_info['comment'] = self.trades.at[last_trade_idx, 'entry_comment']

            return trade_info

    @classmethod
    def join_trades(cls, registries: list) -> 'TradeRegistry':
        '''
        Takes a list of TradeRegistries and joins them into one.

        :param registries: list[TradeRegistry].
        :param combined_registry: bool.
        :return: TradeRegistry.
        '''

        # Check if instances is not empty.
        if len(registries) == 0:
            raise ValueError(
                'Instances must contain at least one instance of TradeRegistry.'
            )

        # Create instance of class.
        reg = registries[0]
        registry = cls(
            point_value=reg.point_value,
            cost_per_trade=reg.cost_per_trade,
            daytrade_tax_rate=reg.daytrade_tax_rate,
            swingtrade_tax_rate=reg.swingtrade_tax_rate,
        )

        # Join trades.
        trades_list = [x.trades for x in registries]
        registry.trades = pd.concat([*trades_list], axis='index', ignore_index=True)
        registry.trades.sort_values(by='end', ignore_index=True, inplace=True)
        registry._process_trades(force_process=True)

        return registry

    def _buy(self, order: TradeOrder) -> None:
        '''
        Register buy trade.

        :param order: TradeOrder.
        :return: None.
        '''

        open_trade = self.open_trade_info
        if isinstance(open_trade, dict):
            raise NotImplementedError('Increasing trades size not yet implemented')

        # Register buy in trades dataframe.
        index = self._new_trade_index
        self.trades.at[index, 'type'] = 'buy'
        self.trades.at[index, 'buyprice'] = (
            order.price if order.slippage is None else order.price + order.slippage
        )
        self.trades.at[index, 'start'] = order.datetime
        self.trades.at[index, 'entry_comment'] = order.comment
        self.trades.at[index, 'amount'] = order.amount
        self.trades.at[index, 'entry_info'] = order.info

    def _sell(self, order: TradeOrder) -> None:
        '''
        Register sell trade.

        :param order: TradeOrder.
        :return: None.
        '''

        # Register sell in trades dataframe.
        index = self._new_trade_index
        self.trades.at[index, 'type'] = 'sell'
        self.trades.at[index, 'sellprice'] = (
            order.price if order.slippage is None else order.price - order.slippage
        )
        self.trades.at[index, 'start'] = order.datetime
        self.trades.at[index, 'entry_comment'] = order.comment
        self.trades.at[index, 'amount'] = order.amount
        self.trades.at[index, 'entry_info'] = order.info

    def _close_position(
        self,
        price: float,
        datetime_val: dt.datetime,
        comment: str = '',
        slippage: Union[float, None] = None,
    ) -> None:
        '''
        Close the last open position.

        :param price:
        :param datetime_val:
        :param comment:
        :param slippage:
        :return: None.
        '''

        # Get info on open trade.
        open_trade = self.open_trade_info
        idx = self._last_trade_index

        # Close an existing buy position.
        if open_trade['type'] == 'buy':
            self.trades.at[idx, 'sellprice'] = (
                price if slippage is None else price + slippage
            )
            self.trades.at[idx, 'end'] = datetime_val

        # Close an existing sell position.
        if open_trade['type'] == 'sell':
            self.trades.at[idx, 'buyprice'] = (
                price if slippage is None else price - slippage
            )
            self.trades.at[idx, 'end'] = datetime_val

        # Register exit comment.
        self.trades.at[idx, 'exit_comment'] = comment

    def trades_today(self, date: dt.datetime) -> int:
        return len(self.trades.loc[self.trades['end'].dt.date == date.date()])

    def register_order(self, order: TradeOrder) -> None:
        '''
        Register order in trades dataframe.

        :param order: TradeOrder.
        :return: None.
        '''

        # Add order to order history.
        order_num = len(self.order_history)
        self.order_history[order_num] = order

        # Open buy position.
        if order.type == 'buy':
            if self.open_trade_info is None:
                self._buy(order)
            else:
                raise RuntimeError(
                    'Attempting to register a buy trade when a position is already open.'
                )

        # Open sell position.
        elif order.type == 'sell':
            if self.open_trade_info is None:
                self._sell(order)
            else:
                raise RuntimeError(
                    'Attempting to register a sell trade when a position is already open.'
                )

        # Close position.
        elif order.type == 'close':
            if self.open_trade_info is None:
                raise RuntimeError(
                    'Attempting to register a close trade when there is no open position.'
                )
            else:
                self._close_position(
                    price=order.price,
                    datetime_val=order.datetime,
                    comment=order.comment,
                    slippage=order.slippage,
                )
                # Store exit info for the closed trade
                self.trades.at[self._last_trade_index, 'exit_info'] = order.info

        # Invert position.
        elif order.type == 'invert':
            if self.open_trade_info is None:
                raise RuntimeError(
                    'Attempting to register an invert trade when there is no open position.'
                )
            else:
                trade_info = self.open_trade_info

                if trade_info['type'] == 'buy':
                    self._close_position(
                        price=order.price,
                        datetime_val=order.datetime,
                        comment=order.comment,
                        slippage=order.slippage,
                    )
                    # Store exit info for the closed trade
                    self.trades.at[self._last_trade_index, 'exit_info'] = order.info
                    self._sell(order)

                elif trade_info['type'] == 'sell':
                    self._close_position(
                        price=order.price,
                        datetime_val=order.datetime,
                        comment=order.comment,
                        slippage=order.slippage,
                    )
                    # Store exit info for the closed trade
                    self.trades.at[self._last_trade_index, 'exit_info'] = order.info
                    self._buy(order)

        # Invalid order type.
        else:
            raise ValueError(f'Invalid order type: {order.type}')

    def _process_trades(self, force_process: bool = False) -> None:
        '''
        Process trades dataframe. Compute results.

        :return: None.
        '''

        # Check if already processed.
        if not self.trades.isna().any().any() and not force_process:
            return

        # Process trade data.
        self.trades['delta'] = (
            (self.trades['sellprice'] - self.trades['buyprice'])
            .astype(float)
            .round(decimals=2)
        )
        self.trades['result'] = (
            (self.trades['delta'] * self.point_value * self.trades['amount'])
            .astype(float)
            .round(decimals=2)
        )

        self.trades['cost'] = self.cost_per_trade * self.trades['amount']
        self.trades['profit'] = (
            (self.trades['result'] - self.trades['cost'])
            .astype(float)
            .round(decimals=2)
        )
        self.trades['balance'] = (
            (self.trades['profit'].cumsum()).astype(float).round(decimals=2)
        )

        self.trades['entry_comment'] = self.trades['entry_comment'].astype(str)
        self.trades['exit_comment'] = self.trades['exit_comment'].astype(str)
        self.trades['entry_comment'] = self.trades['entry_comment'].fillna('')
        self.trades['exit_comment'] = self.trades['exit_comment'].fillna('')

        # Compute monthly result and tax.
        monthly_result = self.compute_monthly_result(return_df=True)
        if monthly_result is not None:
            self.tax_per_month = monthly_result['tax']
            self.total_tax = monthly_result['tax'].sum()

    def _compute_maximum_drawdown(self) -> Dict[str, float]:
        '''
        Compute maximum drawdown.

        :param percentage_method: str. The method to use for computing the drawdown percentage. Options are 'relative'
        and 'final'.
        :return: Tuple[float, float]. The maximum drawdown as a float and as a percentage value.
        '''

        # Check if trades is not empty.
        if self.trades.empty:
            warnings.warn('No registered trades. Unable to get maximum drawdown.')
            return None

        # Compute maximum drawdown.
        dd = self.trades[['balance']].copy()
        dd['max_balance'] = dd['balance'].cummax()
        #        dd['max_balance'] = dd['max_balance'].mask(dd['max_balance'] < 0, 0)
        dd['drawdown'] = dd['max_balance'] - dd['balance']
        max_drawdown = dd['drawdown'].max()

        drawdown_relative = (
            max_drawdown / dd['max_balance'].at[dd['drawdown'].idxmax()]
        ) * 100
        drawdown_final = (max_drawdown / dd['balance'].iat[-1]) * 100
        drawdown_info = {
            'maximum_drawdown': max_drawdown,
            'drawdown_relative': drawdown_relative,
            'drawdown_final': drawdown_final,
        }

        # Replace np.inf values with 0.
        for name, value in drawdown_info.items():
            if value == np.inf:
                drawdown_info[name] = np.nan

        return drawdown_info

    def compute_monthly_result(self, return_df: bool = False) -> Optional[pd.DataFrame]:
        # Check if trades is not empty.
        if self.trades.empty:
            warnings.warn('No registered trades. Unable to get monthly result.')
            return None

        trades = self.trades.copy()
        months, years = (
            trades.set_index('end').index.month,
            trades.set_index('end').index.year,
        )
        month_groups = trades.groupby([years, months])

        swingtrade_credit, daytrade_credit = 0, 0
        month_result = pd.DataFrame()
        for _, group in month_groups:

            group['duration'] = group['end'] - group['start']
            swingtrade = group.loc[
                group['duration'] >= dt.timedelta(hours=9), 'profit'
            ].sum()
            daytrade = group.loc[
                group['duration'] < dt.timedelta(hours=9), 'profit'
            ].sum()

            if swingtrade < 0:
                swingtrade_credit += swingtrade
                swingtrade = 0

            else:
                swingtrade = (
                    swingtrade + swingtrade_credit
                    if swingtrade > -swingtrade_credit
                    else 0
                )
                swingtrade_credit = (
                    swingtrade_credit + swingtrade
                    if swingtrade < -swingtrade_credit
                    else 0
                )

            if daytrade < 0:
                daytrade_credit += daytrade
                daytrade = 0

            else:
                daytrade = (
                    daytrade + daytrade_credit if daytrade > -daytrade_credit else 0
                )
                daytrade_credit = (
                    daytrade_credit + daytrade if daytrade < -daytrade_credit else 0
                )

            tax = (swingtrade * 0.15) + (daytrade * 0.20)

            datetime_idx = group['start'].iat[0].replace(day=1).date()
            month_result.at[datetime_idx, 'num_trades'] = len(group.index)
            month_result.at[datetime_idx, 'result'] = group['result'].sum()
            month_result.at[datetime_idx, 'cost'] = group['cost'].sum()
            month_result.at[datetime_idx, 'tax'] = tax
            month_result.at[datetime_idx, 'profit'] = month_result.at[
                datetime_idx, 'result'
            ].sum() - (month_result.at[datetime_idx, 'cost'].sum() + tax)

        month_result['balance'] = month_result['profit'].cumsum()
        self.monthly_result = month_result

        if return_df:
            return month_result

    def get_result(
        self,
        force_process_trades: bool = False,
        silent_mode: bool = False,
        return_result: bool = False,
    ) -> Union[dict, None]:
        '''
        Get compiled result.

        :param drawdown_method: str. The method to use for computing the maximum drawdown. Options are 'peak_balance'
        and 'final_balance'.
        :param verbose: bool. Whether to print the result.
        :param plot_results: bool. Whether to plot the results.
        :param as_dataframe: bool. Whether to return the result as a pandas DataFrame. Otherwise, returns a dict.
        :param include_monthly_stats: bool. Whether to include monthly stats in the result.
        :param export_to_excel: bool. Whether to export the result to an Excel file. The file will be exported as
        'backtest_result.xlsx' to the current working directory.
        :return: Union[pd.DataFrame, dict].
        '''

        # Check if trades is not empty.
        if self.trades.empty:
            warnings.warn('No registered trades. Unable to get result.')
            return

        self._process_trades(force_process=force_process_trades)
        drawdown_info: dict = self._compute_maximum_drawdown()
        self.compute_monthly_result()
        monthly_result = self.monthly_result
        self.result = {
            'net_balance (BRL)': self.net_balance - self.total_tax,
            'gross_balance (BRL)': self.trades['result'].sum(),
            'total_tax (BRL)': self.total_tax,
            'total_cost (BRL)': self.trades['cost'].sum(),
            'total_profit (BRL)': self.positive_trades_sum,
            'total_loss (BRL)': self.negative_trades_sum,
            'profit_factor': self.profit_factor,
            'accuracy (%)': self.accuracy,
            'mean_profit (BRL)': self.mean_profit,
            'mean_loss (BRL)': self.mean_loss,
            'mean_ratio': self.mean_profit_loss_ratio,
            'standard_deviation': self.result_standard_deviation,
            'total_trades': len(self.trades),
            'positive_trades': self.num_positive_trades,
            'negative_trades': self.num_negative_trades,
            #'maximum_drawup (BRL)': self.compute_maximum_drawup(),
            'maximum_drawdown (BRL)': drawdown_info['maximum_drawdown'],
            'drawdown_relative (%)': drawdown_info['drawdown_relative'],
            'drawdown_final (%)': drawdown_info['drawdown_final'],
            'start_date': self.trades['start'].iat[0],
            'end_date': self.trades['end'].iat[-1],
            'duration': (self.trades['end'].iat[-1] - self.trades['start'].iat[0]).days,
            'average_monthly_result (BRL)': monthly_result['profit'].mean(),
        }

        if not silent_mode:
            print('\n\n--- Results ---\n')
            for metric, value in self.result.items():
                if isinstance(value, (dt.datetime, dt.timedelta)):
                    print(f'{metric}:'.ljust(30), f'{value}'.rjust(25))
                else:
                    print(f'{metric}:'.ljust(30), f'{round(value, 2)}'.rjust(25))

        if return_result:
            return self.result


if __name__ == '__main__':
    pass
    '''
    df = pd.DataFrame()
    df['test'] = pd.date_range(start=dt.datetime(2025, 1,1 ), end=dt.datetime(2025, 2, 1), freq='60min').to_list()
    df['test'].dt.date
    '''
