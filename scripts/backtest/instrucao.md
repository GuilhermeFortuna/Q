
# Trading Strategy Creation Guide

## Introduction

This guide will teach you how to create trading strategies for our backtesting framework. Don't worry if you're new to programming - we'll explain everything step by step!

## What is a Trading Strategy?

A trading strategy is a set of rules that tells the computer when to:
- **Buy** an asset (like a stock or cryptocurrency)
- **Sell** an asset
- **Close** a position (exit a trade)

Think of it like a recipe for trading - you define the ingredients (market data) and the steps (your rules), and the computer follows them automatically.

## The Basic Structure

Every trading strategy in our system must follow a specific pattern. It's like a template that ensures all strategies work together properly.

### Step 1: Import the Required Components

At the top of your strategy file, you need to import the tools you'll use:

```python
from typing import Union
import pandas_ta as pta
from src.backtester import TradingStrategy, TradeOrder
```



**What these do:**
- `typing.Union` - Helps specify what types of data your functions can return
- `pandas_ta` - A library with many technical indicators (like moving averages)
- `TradingStrategy` - The base template all strategies must follow
- `TradeOrder` - How you tell the system to make a trade

### Step 2: Create Your Strategy Class

```python
class MyStrategy(TradingStrategy):
    def __init__(self, parameter1: float, parameter2: int):
        super().__init__()
        self.parameter1 = parameter1
        self.parameter2 = parameter2
```


**Key points:**
- Your class name should describe your strategy (e.g., `MovingAverageCrossover`, `RSIStrategy`)
- `__init__` is where you set up your strategy's settings
- `super().__init__()` is required - it connects your strategy to the system
- Store your settings as `self.variable_name` so you can use them later

### Step 3: Implement the Three Required Methods

Every strategy must have exactly these three methods:

#### A. `compute_indicators(self, data: dict) -> None`

This method calculates technical indicators (like moving averages, RSI, etc.) that your strategy needs.

```python
def compute_indicators(self, data: dict) -> None:
    candles = data['candle'].data
    
    # Calculate a 20-period simple moving average
    candles['sma_20'] = pta.sma(candles['close'], length=20)
    
    # Calculate RSI
    candles['rsi'] = pta.rsi(candles['close'], length=14)
```


**Important:**
- You get market data through the `data` parameter
- `data['candle'].data` gives you the price data (open, high, low, close, volume)
- Add new columns to store your indicators
- This method runs once before the backtest starts

#### B. `entry_strategy(self, i: int, data: dict) -> Union[TradeOrder, None]`

This method decides when to enter new trades (buy or sell).

```python
def entry_strategy(self, i: int, data: dict) -> Union[TradeOrder, None]:
    candle = data['candle']
    datetime = candle.datetime_index[i]
    
    # Don't trade on the first candle (no previous data to compare)
    if i == 0:
        return None
    
    close_price = candle.close[i]
    sma_20 = candle.sma_20[i]
    rsi = candle.rsi[i]
    
    # Example: Buy when price is above SMA and RSI is oversold
    if close_price > sma_20 and rsi < 30:
        return TradeOrder(
            type='buy',
            price=close_price,
            datetime=datetime,
            amount=1
        )
    
    # Example: Sell when price is below SMA and RSI is overbought
    elif close_price < sma_20 and rsi > 70:
        return TradeOrder(
            type='sell',
            price=close_price,
            datetime=datetime,
            amount=1
        )
    
    return None  # No trade signal
```


**Key concepts:**
- `i` is the current position in the data (like looking at day 50 out of 1000 days)
- Return `None` when you don't want to trade
- Return a `TradeOrder` when you want to make a trade
- Trade types: `'buy'` (go long), `'sell'` (go short)

#### C. `exit_strategy(self, i: int, data: dict) -> Union[TradeOrder, None]`

This method decides when to exit existing trades.

```python
def exit_strategy(self, i: int, data: dict) -> Union[TradeOrder, None]:
    candle = data['candle']
    datetime = candle.datetime_index[i]
    
    close_price = candle.close[i]
    sma_20 = candle.sma_20[i]
    
    # Exit when price crosses back through the moving average
    if close_price < sma_20:  # Exit long positions
        return TradeOrder(
            type='close',
            price=close_price,
            datetime=datetime,
            amount=1
        )
    
    return None  # Keep the position open
```


**Exit types:**
- `'close'` - Close the current position
- `'invert'` - Close current position and open opposite position

## Complete Example Strategy

Here's a simple but complete moving average crossover strategy:

```python
from typing import Union
import pandas_ta as pta
from src.backtester import TradingStrategy, TradeOrder


class SimpleMACrossover(TradingStrategy):
    def __init__(self, fast_period: int = 10, slow_period: int = 20):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period

    def compute_indicators(self, data: dict) -> None:
        candles = data['candle'].data
        
        # Calculate fast and slow moving averages
        candles['fast_ma'] = pta.sma(candles['close'], length=self.fast_period)
        candles['slow_ma'] = pta.sma(candles['close'], length=self.slow_period)

    def entry_strategy(self, i: int, data: dict) -> Union[TradeOrder, None]:
        candle = data['candle']
        datetime = candle.datetime_index[i]
        
        if i == 0:
            return None
            
        close_price = candle.close[i]
        fast_ma = candle.fast_ma[i]
        slow_ma = candle.slow_ma[i]
        prev_fast_ma = candle.fast_ma[i-1]
        prev_slow_ma = candle.slow_ma[i-1]
        
        # Buy when fast MA crosses above slow MA
        if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma:
            return TradeOrder(
                type='buy',
                price=close_price,
                datetime=datetime,
                amount=1
            )
        
        # Sell when fast MA crosses below slow MA
        elif prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma:
            return TradeOrder(
                type='sell',
                price=close_price,
                datetime=datetime,
                amount=1
            )
            
        return None

    def exit_strategy(self, i: int, data: dict) -> Union[TradeOrder, None]:
        candle = data['candle']
        datetime = candle.datetime_index[i]
        
        close_price = candle.close[i]
        fast_ma = candle.fast_ma[i]
        slow_ma = candle.slow_ma[i]
        
        # Exit when the moving averages cross in the opposite direction
        if fast_ma < slow_ma:  # Exit long positions
            return TradeOrder(
                type='close',
                price=close_price,
                datetime=datetime,
                amount=1
            )
        elif fast_ma > slow_ma:  # Exit short positions
            return TradeOrder(
                type='close',
                price=close_price,
                datetime=datetime,
                amount=1
            )
            
        return None
```


## Common Patterns and Tips

### 1. Always Check for Sufficient Data
```python
if i < self.slow_period:  # Make sure we have enough data
    return None
```


### 2. Use Previous Values for Crossover Signals
```python
# Check if condition just became true (crossover)
if prev_value <= threshold and current_value > threshold:
    # This is a bullish crossover
```


### 3. Access Market Data
```python
candle = data['candle']
open_price = candle.open[i]
high_price = candle.high[i]
low_price = candle.low[i]
close_price = candle.close[i]
volume = candle.volume[i]
datetime = candle.datetime_index[i]
```


### 4. Common Technical Indicators
```python
# Moving averages
candles['sma'] = pta.sma(candles['close'], length=20)
candles['ema'] = pta.ema(candles['close'], length=20)

# Oscillators
candles['rsi'] = pta.rsi(candles['close'], length=14)
candles['macd'] = pta.macd(candles['close'])['MACD_12_26_9']

# Bollinger Bands
bb = pta.bbands(candles['close'], length=20)
candles['bb_upper'] = bb['BBU_20_2.0']
candles['bb_lower'] = bb['BBL_20_2.0']
```


## File Organization

Save your strategy in the appropriate folder:
- **Day trading strategies**: `src/strategies/daytrade/your_strategy.py`
- **Swing trading strategies**: `src/strategies/swingtrade/your_strategy.py`

Don't forget to update the `__init__.py` file in the appropriate folder:

```python
from .your_strategy import YourStrategyClass

__all__ = [
    "YourStrategyClass",
]
```


## Testing Your Strategy

Once you create your strategy, you can test it using the backtesting engine. The system will:
1. Call `compute_indicators()` once at the start
2. Loop through each data point, calling `entry_strategy()` and `exit_strategy()`
3. Execute trades and track performance
4. Generate reports and visualizations

## Common Mistakes to Avoid

1. **Forgetting `super().__init__()`** - Always include this in your `__init__` method
2. **Not returning `None`** - When you don't want to trade, return `None`
3. **Looking into the future** - Only use data from index `i` and earlier
4. **Not handling the first few data points** - Check if `i` is large enough for your indicators

## Next Steps

1. Study the existing `MaCrossover` strategy in `src/strategies/swingtrade/ma_crossover.py`
2. Start with a simple strategy using one or two indicators
3. Test it with historical data
4. Gradually add complexity as you become more comfortable

Remember: The best strategies are often the simplest ones. Focus on clear, logical rules rather than trying to use every indicator available!
```
This guide provides your friend with a comprehensive, beginner-friendly introduction to creating trading strategies in your framework's style. It covers all the essential concepts while explaining things in simple terms and providing practical examples they can follow.
```
