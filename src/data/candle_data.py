from src.data.base import MarketData
from typing import Optional
import pandas as pd
import MetaTrader5 as mt5


class CandleData(MarketData):
    def __init__(
        self, symbol: str, timeframe: str, data: Optional[pd.DataFrame] = None
    ):
        super().__init__(symbol=symbol, data=data)
        if not isinstance(timeframe, str):
            raise TypeError(
                f'timeframe must be a string. Received obj of type: {type(timeframe)}'
            )

        self.timeframe = timeframe

    def store_data(self) -> None:
        pass

    def load_data(self) -> None:
        pass

    @staticmethod
    def format_candle_data_from_mt5(
        data: np.ndarray, use_tick_volume: Optional[bool] = False
    ) -> pd.DataFrame:
        """
        Formats raw candle data obtained from MetaTrader 5 (MT5) into a structured
        pandas DataFrame. The function processes the input array, converts the
        time column into a datetime format, drops unnecessary columns, and sets
        the datetime column as the DataFrame index.

        :param data: The raw data as a NumPy ndarray containing candle information
                     from MT5. Data must include columns for 'time', 'spread',
                     and other relevant trading information.
        :type data: np.ndarray
        :return: A pandas DataFrame with the formatted candle data. The DataFrame
                 includes trading data indexed by datetime with specific columns
                 retained and unnecessary ones removed.
        :rtype: pd.DataFrame
        :raises ValueError: If no data is provided (None or empty array).
        """
        if data is not None:
            df = pd.DataFrame(data)
            df['datetime'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('datetime', inplace=True, drop=True)

            # Select volume to use
            if 'volume' not in df.columns and any(
                'volume' in col for col in list(df.columns)
            ):
                df['volume'] = (
                    df['real_volume'].copy()
                    if not use_tick_volume
                    else df['tick_volume'].copy()
                )

            df.drop(columns=['time', 'spread'], inplace=True)
            return df

        else:
            raise ValueError('No data provided. Please provide data to format.')

    @staticmethod
    def import_from_mt5(
        mt5_symbol: str,
        timeframe: str,
        date_from: dt.datetime,
        date_to: dt.datetime,
        use_tick_volume: Optional[bool] = False,
    ):
        error_message = f'Error importing data for symbol {mt5_symbol} from MT5.: {mt5.last_error()}'

        # Validate timeframe
        if not isinstance(timeframe, str) or timeframe not in TIMEFRAMES.keys():
            raise ValueError(f'Invalid timeframe: {timeframe}')

        # Initialize connection to mt5 terminal with default credentials
        mt5.initialize()

        try:
            df = CandleData.format_candle_data_from_mt5(
                data=mt5.copy_rates_range(
                    mt5_symbol, TIMEFRAMES[timeframe].mt5, date_from, date_to
                )
            )
        except:
            print(f'Error importing data for symbol {mt5_symbol} from MT5.')
            df = pd.DataFrame()

        finally:
            if df.empty:
                print(error_message)
            mt5.shutdown()

        return df

    @staticmethod
    def import_from_csv(path: str) -> Union[pd.DataFrame, None]:
        errors = []
        for enc in ['utf-8', 'latin-1']:
            try:
                df = pd.read_csv(path, decimal=',', encoding=enc)
                df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
                df['datetime'] = pd.to_datetime(
                    df['datetime'], format='%d/%m/%Y %H:%M', errors='raise'
                )
                df = df.set_index('datetime', inplace=False)[::-1].copy()
                return df

            except Exception as e:
                errors.append(e)
                continue

        for error in errors:
            print(error)
