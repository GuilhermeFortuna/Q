import pandas as pd
from src.helper import PrintMessage
from src.backtester.data import CandleData
from datetime import datetime, timedelta
import pytest
import functools
import os

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'common')


@pytest.fixture
def candle_data_60min():
    pass


if __name__ == "__main__":
    NUM_CANDLES = 1000
    DATE_TO = datetime.now()
    candle_test_data = {
        'candle_data_60min': functools.partial(
            CandleData.import_from_mt5,
            mt5_symbol='CCM$',
            timeframe='60min',
            num_candles=NUM_CANDLES,
        ),
        'candle_data_15min': functools.partial(
            CandleData.import_from_mt5,
            mt5_symbol='VALE3',
            timeframe='15min',
            num_candles=NUM_CANDLES,
        ),
        'candle_data_5min': functools.partial(
            CandleData.import_from_mt5,
            mt5_symbol='WIN$',
            timeframe='5min',
            num_candles=NUM_CANDLES,
        ),
    }
    for key, import_data in candle_test_data.items():
        data = import_data()
        PrintMessage['INFO'](f'Imported {len(data)} candles for {key}')

        match isinstance(data, pd.DataFrame):
            case True:
                CandleData.store_data(
                    data=data,
                    path=os.path.join(
                        TEST_DATA_PATH,
                        f'{key}.csv',
                    ),
                )
            case False:
                PrintMessage['ERROR'](f'Failed to import candle data for {key}')
