from collections import namedtuple
from datetime import timedelta
import MetaTrader5 as mt5

TimeframeInfo = namedtuple('TimeframeInfo', ['mt5', 'delta'])

TIMEFRAMES = {
    '1min': TimeframeInfo(mt5=mt5.TIMEFRAME_M1, delta=timedelta(minutes=1)),
    '5min': TimeframeInfo(mt5=mt5.TIMEFRAME_M5, delta=timedelta(minutes=5)),
    '10min': TimeframeInfo(mt5=mt5.TIMEFRAME_M10, delta=timedelta(minutes=10)),
    '15min': TimeframeInfo(mt5=mt5.TIMEFRAME_M15, delta=timedelta(minutes=15)),
    '30min': TimeframeInfo(mt5=mt5.TIMEFRAME_M30, delta=timedelta(minutes=30)),
    '60min': TimeframeInfo(mt5=mt5.TIMEFRAME_H1, delta=timedelta(minutes=60)),
    '1day': TimeframeInfo(mt5=mt5.TIMEFRAME_D1, delta=timedelta(days=1)),
}
