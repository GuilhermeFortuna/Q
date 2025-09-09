import warnings
from datetime import datetime, timedelta

import pandas_ta as pta

from src.backtester import CandleData
from src.visualizer.windows import show_chart, IndicatorConfig


warnings.filterwarnings('ignore')

# Data parameters
SYMBOL = 'DOL$'
TIMEFRAME = '5min'
DATE_TO = datetime.today()
DATE_FROM = DATE_TO - timedelta(days=30)

if __name__ == '__main__':
    # Import data into CandleData obj
    candles = CandleData(symbol=SYMBOL, timeframe=TIMEFRAME)
    candle_data = CandleData.import_from_mt5(
        mt5_symbol=SYMBOL, timeframe=TIMEFRAME, date_from=DATE_FROM, date_to=DATE_TO
    )
    candle_data = candle_data[['open', 'high', 'low', 'close', 'real_volume']].copy()
    candle_data.rename(columns={'real_volume': 'volume'}, inplace=True)
    candle_data['volume'] = candle_data['volume'].astype(int)

    # Compute indicators
    candle_data['ma'] = pta.ema(candle_data['close'], length=9)

    indicators = [
        IndicatorConfig(type='line', y=candle_data['ma'], name='MA(9)', color='blue'),
        # IndicatorConfig(type='histogram', y=candle_data['volume'], name='Volume', color='gray'),
    ]

    # Plot data using visualizer package
    show_chart(
        ohlc_data=candle_data,
        indicators=indicators,
        show_volume=True,
        initial_candles=100,
    )
