from collections import namedtuple
from datetime import timedelta
import MetaTrader5 as mt5

TimeframeInfo = namedtuple('TimeframeInfo', ['mt5', 'delta'])

TIMEFRAMES = {
    '1min': TimeframeInfo(mt5=mt5.TIMEFRAME_M1, delta=timedelta(minutes=1)),
    '5min': TimeframeInfo(mt5=mt5.TIMEFRAME_M5, delta=timedelta(minutes=5)),
    '15min': TimeframeInfo(mt5=mt5.TIMEFRAME_M15, delta=timedelta(minutes=15)),
    '1day': TimeframeInfo(mt5=mt5.TIMEFRAME_D1, delta=timedelta(days=1)),
}
