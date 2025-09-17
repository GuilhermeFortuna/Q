from datetime import datetime

from src.backtester.data import CandleData
from src.backtester.engine import BacktestParameters, Engine
from src.backtester.trades import TradeRegistry
from src.strategies.archetypes import create_momentum_rider_strategy

# Config (Approved specs)
TIMEFRAME_LT = '15min'  # trading timeframe
TIMEFRAME_HT = '60min'  # higher timeframe for regime alignment
DATE_FROM = datetime(2024, 1, 1)
DATE_TO = datetime.today()
MT5_SYMBOL = 'WDO$'
POINT_VALUE = 10.0
COST_PER_TRADE = 1.0


def run_backtest(
    mt5_symbol: str = MT5_SYMBOL,
    timeframe_lt: str = TIMEFRAME_LT,
    timeframe_ht: str = TIMEFRAME_HT,
    date_from: datetime = DATE_FROM,
    date_to: datetime = DATE_TO,
) -> tuple[TradeRegistry, CandleData]:
    # Lower timeframe candles (15m)
    candles_15m = CandleData(symbol=mt5_symbol.replace('$', ''), timeframe=timeframe_lt)
    df15 = CandleData.import_from_mt5(
        mt5_symbol=mt5_symbol,
        timeframe=timeframe_lt,
        date_from=date_from,
        date_to=date_to,
    )[['open', 'high', 'low', 'close', 'real_volume']].copy()
    df15.rename(columns={'real_volume': 'volume'}, inplace=True)
    candles_15m.data = df15.loc[
        (df15.index >= date_from) & (df15.index <= date_to)
    ].copy()

    # Higher timeframe candles (60m)
    candles_60m = CandleData(symbol=mt5_symbol.replace('$', ''), timeframe=timeframe_ht)
    df60 = CandleData.import_from_mt5(
        mt5_symbol=mt5_symbol,
        timeframe=timeframe_ht,
        date_from=date_from,
        date_to=date_to,
    )[['open', 'high', 'low', 'close', 'real_volume']].copy()
    df60.rename(columns={'real_volume': 'volume'}, inplace=True)
    candles_60m.data = df60.loc[
        (df60.index >= date_from) & (df60.index <= date_to)
    ].copy()

    params = BacktestParameters(point_value=POINT_VALUE, cost_per_trade=COST_PER_TRADE)
    strategy = create_momentum_rider_strategy()

    # Pass both LT and HT candles to the engine
    engine = Engine(
        parameters=params,
        strategy=strategy,
        data={'candle': candles_15m, 'ht_candle': candles_60m},
    )
    trade_registry = engine.run_backtest(display_progress=True)
    trade_registry.get_result()
    return trade_registry, candles_15m


if __name__ == '__main__':
    from src.visualizer import show_backtest_summary

    tr, candles = run_backtest()
    ohlc = candles.data.copy()
    if 'time' not in ohlc.columns:
        ohlc.insert(0, 'time', list(range(len(ohlc))))
    show_backtest_summary(tr, ohlc_df=ohlc)


# --- Signal Contribution Analysis ---
print("\n--- Signal Contribution Analysis ---")
trades_df = tr.trades
for idx, row in trades_df.iterrows():
    # Retrieve entry decisions stored with the trade
    entry_info = row.get('entry_info') if hasattr(row, 'get') else None
    decisions = []
    if isinstance(entry_info, dict):
        decisions = entry_info.get('decisions') or []
    side = row['type']
    entry_price = row['buyprice'] if side == 'buy' else row['sellprice']
    try:
        print(f"        Trade #{idx + 1} ({side} @ {float(entry_price):.4f}):")
    except Exception:
        print(f"        Trade #{idx + 1} ({side} @ {entry_price}):")
    for d in decisions:
        if isinstance(d, dict):
            label = d.get('label', 'UnknownSignal')
            d_side = d.get('side') or 'neutral'
            d_strength = float(d.get('strength', 0.0) or 0.0)
        else:
            label = getattr(d, 'name', None) or getattr(d, 'source', None) or d.__class__.__name__
            d_side = getattr(d, 'side', None) or 'neutral'
            d_strength = float(getattr(d, 'strength', 0.0) or 0.0)
        print(f"          - {label}: {d_side} (strength: {d_strength:.2f})")
    print()
