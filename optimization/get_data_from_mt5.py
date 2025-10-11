import pandas as pd

from src.data import CandleData
from src.helper import PrintMessage
from datetime import datetime
import os

SYMBOL = 'CCM$'
TIMEFRAME = '60min'
DATE_FROM = datetime(2020, 1, 1)
DATE_TO = datetime.today()
SAVE_PATH = os.path.join(os.getcwd(), 'mt5', SYMBOL, TIMEFRAME, 'data.csv')

if __name__ == '__main__':
    candles = CandleData(SYMBOL, TIMEFRAME)
    if not os.path.exists(SAVE_PATH):
        candles.import_from_mt5(date_from=DATE_FROM, date_to=DATE_TO)
        if isinstance(candles.df, pd.DataFrame) and not candles.df.empty:
            candles.df.to_csv(SAVE_PATH)
            PrintMessage['SUCCESS'](
                message=f'File saved successfully: {SAVE_PATH}', title='File Saved'
            )
        else:
            PrintMessage['WARNING'](
                message=f'Unable to import data for {SYMBOL}-{TIMEFRAME}'
            )
    else:
        PrintMessage['WARNING'](
            message=f'File already exists: {SAVE_PATH}', title='File Exists'
        )
