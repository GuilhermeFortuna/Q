"""
Tests for the TickData module.
"""

import datetime as dt
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, Mock

from src.data import TickData
from src.data.base import MarketData


class TestTickData:
    """Test TickData functionality."""

    def test_tick_data_initialization(self):
        """Test TickData initialization."""
        tick_data = TickData(symbol='TEST')
        
        assert tick_data.symbol == 'TEST'
        assert isinstance(tick_data.df, pd.DataFrame)
        assert tick_data.df.empty

    def test_tick_data_inheritance(self):
        """Test that TickData inherits from MarketData."""
        tick_data = TickData(symbol='TEST')
        assert isinstance(tick_data, MarketData)

    def test_tick_data_data_assignment(self):
        """Test assigning data to TickData."""
        tick_data = TickData(symbol='TEST')
        
        # Create sample tick data
        times = pd.date_range('2024-01-01', periods=100, freq='30S')
        data = pd.DataFrame({
            'datetime': times,
            'price': np.random.rand(100) * 100,
            'volume': np.random.randint(1, 10, 100)
        })
        
        tick_data.df = data
        
        assert len(tick_data.df) == 100
        assert list(tick_data.df.columns) == ['datetime', 'price', 'volume']

    def test_import_from_mt5(self, mock_mt5_connection):
        """Test import_from_mt5 method."""
        # Mock MT5 tick data
        mock_ticks = np.array([
            (1640995200, 100.0, 1.0, 0, 0, 0),  # time, bid, ask, last, volume, flags
            (1640995201, 100.1, 1.0, 0, 0, 0),
            (1640995202, 100.2, 1.0, 0, 0, 0),
        ], dtype=[('time', 'i8'), ('bid', 'f8'), ('ask', 'f8'), ('last', 'f8'), ('volume', 'i8'), ('flags', 'i8')])
        
        mock_mt5_connection['copy_ticks_range'].return_value = mock_ticks
        
        # Import from MT5
        imported_data = TickData.import_from_mt5(
            symbol='EURUSD',
            date_from=dt.datetime(2022, 1, 1),
            date_to=dt.datetime(2022, 1, 2)
        )
        
        # Verify imported data
        assert len(imported_data) == 3
        assert list(imported_data.columns) == ['datetime', 'price', 'volume']
        assert imported_data['datetime'].dtype == 'datetime64[ns]'

    def test_import_from_mt5_batch(self, mock_mt5_connection):
        """Test import_from_mt5 with batch processing."""
        # Mock MT5 tick data for multiple batches
        mock_ticks = np.array([
            (1640995200, 100.0, 1.0, 0, 0, 0),
            (1640995201, 100.1, 1.0, 0, 0, 0),
        ], dtype=[('time', 'i8'), ('bid', 'f8'), ('ask', 'f8'), ('last', 'f8'), ('volume', 'i8'), ('flags', 'i8')])
        
        mock_mt5_connection['copy_ticks_range'].return_value = mock_ticks
        
        # Import with batch processing
        imported_data = TickData.import_from_mt5(
            symbol='EURUSD',
            date_from=dt.datetime(2022, 1, 1),
            date_to=dt.datetime(2022, 1, 2),
            batch_size=1  # Small batch size for testing
        )
        
        # Verify imported data
        assert len(imported_data) == 2
        assert list(imported_data.columns) == ['datetime', 'price', 'volume']

    def test_format_tick_data_from_mt5(self):
        """Test format_tick_data_from_mt5 method."""
        # Create mock MT5 tick data
        mock_ticks = np.array([
            (1640995200, 100.0, 100.1, 100.05, 1.0, 0),  # time, bid, ask, last, volume, flags
            (1640995201, 100.1, 100.2, 100.15, 1.5, 0),
        ], dtype=[('time', 'i8'), ('bid', 'f8'), ('ask', 'f8'), ('last', 'f8'), ('volume', 'f8'), ('flags', 'i8')])
        
        # Format data
        formatted_data = TickData.format_tick_data_from_mt5(mock_ticks)
        
        # Verify formatted data
        assert len(formatted_data) == 2
        assert list(formatted_data.columns) == ['datetime', 'price', 'volume']
        assert formatted_data['datetime'].dtype == 'datetime64[ns]'
        assert formatted_data['price'].dtype == 'float64'
        assert formatted_data['volume'].dtype == 'float64'

    def test_format_tick_data_mid_price(self):
        """Test format_tick_data_from_mt5 with mid price calculation."""
        # Create mock MT5 tick data with bid/ask
        mock_ticks = np.array([
            (1640995200, 100.0, 100.2, 100.1, 1.0, 0),  # bid=100.0, ask=100.2, mid=100.1
            (1640995201, 100.1, 100.3, 100.2, 1.5, 0),  # bid=100.1, ask=100.3, mid=100.2
        ], dtype=[('time', 'i8'), ('bid', 'f8'), ('ask', 'f8'), ('last', 'f8'), ('volume', 'f8'), ('flags', 'i8')])
        
        # Format data
        formatted_data = TickData.format_tick_data_from_mt5(mock_ticks)
        
        # Verify mid price calculation
        assert formatted_data['price'].iloc[0] == 100.1  # (100.0 + 100.2) / 2
        assert formatted_data['price'].iloc[1] == 100.2  # (100.1 + 100.3) / 2

    def test_format_tick_data_last_price(self):
        """Test format_tick_data_from_mt5 with last price when no bid/ask."""
        # Create mock MT5 tick data with only last price
        mock_ticks = np.array([
            (1640995200, 0.0, 0.0, 100.05, 1.0, 0),  # bid=0, ask=0, last=100.05
            (1640995201, 0.0, 0.0, 100.15, 1.5, 0),  # bid=0, ask=0, last=100.15
        ], dtype=[('time', 'i8'), ('bid', 'f8'), ('ask', 'f8'), ('last', 'f8'), ('volume', 'f8'), ('flags', 'i8')])
        
        # Format data
        formatted_data = TickData.format_tick_data_from_mt5(mock_ticks)
        
        # Verify last price usage
        assert formatted_data['price'].iloc[0] == 100.05
        assert formatted_data['price'].iloc[1] == 100.15

    def test_import_from_csv(self):
        """Test import_from_csv method."""
        # Create test CSV data
        times = pd.date_range('2024-01-01', periods=5, freq='1min')
        data = pd.DataFrame({
            'datetime': times,
            'price': [100.0, 100.1, 100.2, 100.15, 100.3],
            'volume': [1.0, 1.5, 2.0, 1.2, 1.8]
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            # Import from CSV
            imported_data = TickData.import_from_csv(csv_path)
            
            # Verify imported data
            assert len(imported_data) == 5
            assert list(imported_data.columns) == ['datetime', 'price', 'volume']
            assert imported_data['datetime'].dtype == 'datetime64[ns]'
        finally:
            os.unlink(csv_path)

    def test_batch_import_step_days(self):
        """Test DEFAULT_BATCH_IMPORT_STEP_DAYS constant."""
        from src.data.tick_data import DEFAULT_BATCH_IMPORT_STEP_DAYS
        
        assert isinstance(DEFAULT_BATCH_IMPORT_STEP_DAYS, int)
        assert DEFAULT_BATCH_IMPORT_STEP_DAYS > 0

    def test_data_validation(self):
        """Test data validation in TickData."""
        tick_data = TickData(symbol='TEST')
        
        # Test with invalid data structure
        invalid_data = pd.DataFrame({
            'invalid_col': [1, 2, 3]
        })
        
        # This should not raise an error, but data might not be usable
        tick_data.df = invalid_data
        assert tick_data.df is not None

    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrames."""
        tick_data = TickData(symbol='TEST')
        
        # Create empty DataFrame
        tick_data.df = pd.DataFrame()
        
        # Should handle empty DataFrame gracefully
        assert tick_data.df.empty

    def test_datetime_column_handling(self):
        """Test datetime column handling."""
        tick_data = TickData(symbol='TEST')
        
        # Create data with datetime column
        times = pd.date_range('2024-01-01', periods=3, freq='1min')
        data = pd.DataFrame({
            'datetime': times,
            'price': [100.0, 100.1, 100.2],
            'volume': [1.0, 1.5, 2.0]
        })
        tick_data.df = data
        
        # Verify datetime handling
        assert tick_data.df['datetime'].dtype == 'datetime64[ns]'
        assert len(tick_data.df) == 3

    def test_price_volume_columns(self):
        """Test price and volume column handling."""
        tick_data = TickData(symbol='TEST')
        
        # Create data with price and volume
        times = pd.date_range('2024-01-01', periods=3, freq='1min')
        data = pd.DataFrame({
            'datetime': times,
            'price': [100.0, 100.1, 100.2],
            'volume': [1.0, 1.5, 2.0]
        })
        tick_data.df = data
        
        # Verify column types
        assert tick_data.df['price'].dtype == 'float64'
        assert tick_data.df['volume'].dtype == 'float64'

    def test_mt5_connection_error_handling(self):
        """Test error handling when MT5 connection fails."""
        with patch('MetaTrader5.initialize') as mock_init, \
             patch('MetaTrader5.copy_ticks_range') as mock_copy_ticks, \
             patch('MetaTrader5.shutdown') as mock_shutdown:
            
            # Mock connection failure
            mock_init.return_value = False
            
            # Should handle connection failure gracefully
            with pytest.raises(ConnectionError, match="Failed to initialize MT5"):
                TickData.import_from_mt5(
                    symbol='EURUSD',
                    date_from=dt.datetime(2022, 1, 1),
                    date_to=dt.datetime(2022, 1, 2)
                )

    def test_mt5_data_retrieval_error(self):
        """Test error handling when MT5 data retrieval fails."""
        with patch('MetaTrader5.initialize') as mock_init, \
             patch('MetaTrader5.copy_ticks_range') as mock_copy_ticks, \
             patch('MetaTrader5.shutdown') as mock_shutdown:
            
            # Mock successful connection but failed data retrieval
            mock_init.return_value = True
            mock_copy_ticks.return_value = None
            
            # Should handle data retrieval failure gracefully
            with pytest.raises(ValueError, match="No tick data retrieved from MT5"):
                TickData.import_from_mt5(
                    symbol='EURUSD',
                    date_from=dt.datetime(2022, 1, 1),
                    date_to=dt.datetime(2022, 1, 2)
                )

    def test_large_dataset_handling(self):
        """Test handling of large datasets."""
        tick_data = TickData(symbol='TEST')
        
        # Create large dataset
        times = pd.date_range('2024-01-01', periods=10000, freq='1S')
        data = pd.DataFrame({
            'datetime': times,
            'price': np.random.rand(10000) * 100,
            'volume': np.random.randint(1, 10, 10000)
        })
        tick_data.df = data
        
        # Should handle large dataset without issues
        assert len(tick_data.df) == 10000
        assert tick_data.df['price'].dtype == 'float64'
        assert tick_data.df['volume'].dtype == 'int64'

    def test_timezone_handling(self):
        """Test timezone handling in tick data."""
        tick_data = TickData(symbol='TEST')
        
        # Create data with timezone-aware datetime
        times = pd.date_range('2024-01-01', periods=3, freq='1min', tz='UTC')
        data = pd.DataFrame({
            'datetime': times,
            'price': [100.0, 100.1, 100.2],
            'volume': [1.0, 1.5, 2.0]
        })
        tick_data.df = data
        
        # Should handle timezone-aware data
        assert tick_data.df['datetime'].dtype == 'datetime64[ns, UTC]'

    def test_numeric_data_validation(self):
        """Test numeric data validation and conversion."""
        tick_data = TickData(symbol='TEST')
        
        # Create data with string numeric values
        times = pd.date_range('2024-01-01', periods=3, freq='1min')
        data = pd.DataFrame({
            'datetime': times,
            'price': ['100.0', '100.1', '100.2'],
            'volume': ['1.0', '1.5', '2.0']
        })
        tick_data.df = data
        
        # Should handle string numeric values
        assert tick_data.df['price'].dtype == 'object'  # String type
        assert tick_data.df['volume'].dtype == 'object'  # String type

    def test_missing_columns_handling(self):
        """Test handling of missing required columns."""
        tick_data = TickData(symbol='TEST')
        
        # Create data with missing required columns
        times = pd.date_range('2024-01-01', periods=3, freq='1min')
        data = pd.DataFrame({
            'datetime': times,
            'price': [100.0, 100.1, 100.2]
            # Missing volume column
        })
        tick_data.df = data
        
        # Should handle missing columns gracefully
        assert len(tick_data.df) == 3
        assert 'volume' not in tick_data.df.columns
