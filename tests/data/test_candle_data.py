"""
Tests for the CandleData module.
"""

import datetime as dt
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, Mock

from src.data import CandleData
from src.data.base import MarketData


class TestCandleData:
    """Test CandleData functionality."""

    def test_candle_data_initialization(self):
        """Test CandleData initialization."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        assert candle_data.symbol == 'TEST'
        assert candle_data.timeframe == '60min'
        assert isinstance(candle_data.df, pd.DataFrame)
        assert candle_data.df.empty

    def test_candle_data_validation(self):
        """Test CandleData parameter validation."""
        # Test invalid timeframe
        with pytest.raises(ValueError, match="Invalid timeframe"):
            CandleData(symbol='TEST', timeframe='invalid')
        
        # Test valid timeframes
        valid_timeframes = ['1min', '5min', '15min', '30min', '60min', '4hour', '1day']
        for tf in valid_timeframes:
            candle_data = CandleData(symbol='TEST', timeframe=tf)
            assert candle_data.timeframe == tf

    def test_candle_data_data_assignment(self):
        """Test assigning data to CandleData."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Create sample data
        dates = pd.date_range('2024-01-01', periods=10, freq='1H')
        data = pd.DataFrame({
            'open': np.random.rand(10) * 100,
            'high': np.random.rand(10) * 100 + 1,
            'low': np.random.rand(10) * 100 - 1,
            'close': np.random.rand(10) * 100,
            'volume': np.random.randint(100, 1000, 10)
        }, index=dates)
        
        candle_data.df = data
        
        assert len(candle_data.df) == 10
        assert list(candle_data.df.columns) == ['open', 'high', 'low', 'close', 'volume']

    def test_candle_data_inheritance(self):
        """Test that CandleData inherits from MarketData."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        assert isinstance(candle_data, MarketData)

    def test_store_data_validation(self):
        """Test store_data validation."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Test with empty data
        with pytest.raises(ValueError, match="No data to store"):
            candle_data.store_data()
        
        # Test with None data
        candle_data.df = None
        with pytest.raises(ValueError, match="No data to store"):
            candle_data.store_data()
        
        # Test with non-DataFrame data
        candle_data.df = "invalid"
        with pytest.raises(ValueError, match="No data to store"):
            candle_data.store_data()

    def test_store_data_datetime_handling(self):
        """Test store_data datetime handling."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Create data with DatetimeIndex
        dates = pd.date_range('2024-01-01', periods=5, freq='1H')
        data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [100, 110, 120, 130, 140]
        }, index=dates)
        candle_data.df = data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test storing data
            candle_data.store_data(root_dir=temp_dir, mode='overwrite')
            
            # Verify file was created
            expected_path = os.path.join(
                temp_dir, 'candle_data', 'TEST', '60min', 
                'year=2024', 'month=01', 'day=01', 'data.parquet'
            )
            assert os.path.exists(expected_path)

    def test_store_data_datetime_column(self):
        """Test store_data with datetime column."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Create data with datetime column
        data = pd.DataFrame({
            'datetime': pd.date_range('2024-01-01', periods=5, freq='1H'),
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [100, 110, 120, 130, 140]
        })
        candle_data.df = data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            candle_data.store_data(root_dir=temp_dir, mode='overwrite')
            
            # Verify file was created
            expected_path = os.path.join(
                temp_dir, 'candle_data', 'TEST', '60min', 
                'year=2024', 'month=01', 'day=01', 'data.parquet'
            )
            assert os.path.exists(expected_path)

    def test_store_data_upsert_mode(self):
        """Test store_data upsert mode."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Create initial data
        dates = pd.date_range('2024-01-01', periods=3, freq='1H')
        data1 = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5],
            'volume': [100, 110, 120]
        }, index=dates)
        candle_data.df = data1
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Store initial data
            candle_data.store_data(root_dir=temp_dir, mode='overwrite')
            
            # Create updated data with overlap
            dates2 = pd.date_range('2024-01-01 01:00:00', periods=3, freq='1H')
            data2 = pd.DataFrame({
                'open': [101, 102, 103],
                'high': [102, 103, 104],
                'low': [100, 101, 102],
                'close': [101.5, 102.5, 103.5],
                'volume': [110, 120, 130]
            }, index=dates2)
            candle_data.df = data2
            
            # Upsert data
            candle_data.store_data(root_dir=temp_dir, mode='upsert')
            
            # Verify file exists
            expected_path = os.path.join(
                temp_dir, 'candle_data', 'TEST', '60min', 
                'year=2024', 'month=01', 'day=01', 'data.parquet'
            )
            assert os.path.exists(expected_path)

    def test_load_data_basic(self):
        """Test basic load_data functionality."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Create and store test data
        dates = pd.date_range('2024-01-01', periods=5, freq='1H')
        original_data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [100, 110, 120, 130, 140]
        }, index=dates)
        candle_data.df = original_data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Store data
            candle_data.store_data(root_dir=temp_dir, mode='overwrite')
            
            # Load data
            loaded_data = candle_data.load_data(root_dir=temp_dir)
            
            # Verify loaded data
            assert len(loaded_data) == 5
            assert list(loaded_data.columns) == ['datetime', 'open', 'high', 'low', 'close', 'volume']
            assert loaded_data['datetime'].dtype == 'datetime64[ns]'

    def test_load_data_date_range(self):
        """Test load_data with date range."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Create data spanning multiple days
        dates = pd.date_range('2024-01-01', periods=48, freq='1H')  # 2 days
        data = pd.DataFrame({
            'open': np.random.rand(48) * 100,
            'high': np.random.rand(48) * 100 + 1,
            'low': np.random.rand(48) * 100 - 1,
            'close': np.random.rand(48) * 100,
            'volume': np.random.randint(100, 1000, 48)
        }, index=dates)
        candle_data.df = data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Store data
            candle_data.store_data(root_dir=temp_dir, mode='overwrite')
            
            # Load data for specific date range
            start_date = dt.datetime(2024, 1, 1, 12, 0, 0)
            end_date = dt.datetime(2024, 1, 2, 12, 0, 0)
            
            loaded_data = candle_data.load_data(
                date_from=start_date,
                date_to=end_date,
                root_dir=temp_dir
            )
            
            # Verify date range
            assert len(loaded_data) > 0
            assert loaded_data['datetime'].min() >= start_date
            assert loaded_data['datetime'].max() <= end_date

    def test_load_data_columns(self):
        """Test load_data with specific columns."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Create test data
        dates = pd.date_range('2024-01-01', periods=5, freq='1H')
        data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [100, 110, 120, 130, 140]
        }, index=dates)
        candle_data.df = data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Store data
            candle_data.store_data(root_dir=temp_dir, mode='overwrite')
            
            # Load specific columns
            loaded_data = candle_data.load_data(
                columns=['open', 'close'],
                root_dir=temp_dir
            )
            
            # Verify columns
            assert list(loaded_data.columns) == ['datetime', 'open', 'close']

    def test_import_from_csv(self):
        """Test import_from_csv method."""
        # Create test CSV data
        dates = pd.date_range('2024-01-01', periods=5, freq='1H')
        data = pd.DataFrame({
            'datetime': dates,
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [100, 110, 120, 130, 140]
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            # Import from CSV
            imported_data = CandleData.import_from_csv(csv_path)
            
            # Verify imported data
            assert len(imported_data) == 5
            assert list(imported_data.columns) == ['datetime', 'open', 'high', 'low', 'close', 'volume']
            assert imported_data['datetime'].dtype == 'datetime64[ns]'
        finally:
            os.unlink(csv_path)

    def test_import_from_mt5(self, mock_mt5_connection):
        """Test import_from_mt5 method."""
        # Mock MT5 data
        mock_data = np.array([
            (1640995200, 100.0, 101.0, 99.0, 100.5, 1000),  # 2022-01-01 00:00:00
            (1640998800, 100.5, 102.0, 100.0, 101.5, 1200),  # 2022-01-01 01:00:00
            (1641002400, 101.5, 103.0, 101.0, 102.5, 1100),  # 2022-01-01 02:00:00
        ], dtype=[('time', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8'), ('tick_volume', 'i8')])
        
        mock_mt5_connection['copy_rates_range'].return_value = mock_data
        
        # Import from MT5
        imported_data = CandleData.import_from_mt5(
            symbol='EURUSD',
            timeframe='60min',
            date_from=dt.datetime(2022, 1, 1),
            date_to=dt.datetime(2022, 1, 2)
        )
        
        # Verify imported data
        assert len(imported_data) == 3
        assert list(imported_data.columns) == ['datetime', 'open', 'high', 'low', 'close', 'volume']
        assert imported_data['datetime'].dtype == 'datetime64[ns]'

    def test_format_candle_data_from_mt5(self):
        """Test format_candle_data_from_mt5 method."""
        # Create mock MT5 data
        mock_data = np.array([
            (1640995200, 100.0, 101.0, 99.0, 100.5, 1000),
            (1640998800, 100.5, 102.0, 100.0, 101.5, 1200),
        ], dtype=[('time', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8'), ('tick_volume', 'i8')])
        
        # Format data
        formatted_data = CandleData.format_candle_data_from_mt5(mock_data)
        
        # Verify formatted data
        assert len(formatted_data) == 2
        assert list(formatted_data.columns) == ['datetime', 'open', 'high', 'low', 'close', 'volume']
        assert formatted_data['datetime'].dtype == 'datetime64[ns]'
        assert formatted_data['volume'].dtype == 'int64'

    def test_data_validation(self):
        """Test data validation in CandleData."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Test with invalid data structure
        invalid_data = pd.DataFrame({
            'invalid_col': [1, 2, 3]
        })
        
        # This should not raise an error, but data might not be usable
        candle_data.df = invalid_data
        assert candle_data.df is not None

    def test_timezone_handling(self):
        """Test timezone handling in store_data."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Create data with timezone-aware datetime
        dates = pd.date_range('2024-01-01', periods=3, freq='1H', tz='UTC')
        data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5],
            'volume': [100, 110, 120]
        }, index=dates)
        candle_data.df = data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should handle timezone-aware data
            candle_data.store_data(root_dir=temp_dir, mode='overwrite')
            
            # Verify file was created
            expected_path = os.path.join(
                temp_dir, 'candle_data', 'TEST', '60min', 
                'year=2024', 'month=01', 'day=01', 'data.parquet'
            )
            assert os.path.exists(expected_path)

    def test_numeric_data_validation(self):
        """Test numeric data validation and conversion."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Create data with string numeric values
        dates = pd.date_range('2024-01-01', periods=3, freq='1H')
        data = pd.DataFrame({
            'open': ['100.0', '101.0', '102.0'],
            'high': ['101.0', '102.0', '103.0'],
            'low': ['99.0', '100.0', '101.0'],
            'close': ['100.5', '101.5', '102.5'],
            'volume': ['100', '110', '120']
        }, index=dates)
        candle_data.df = data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should convert string numeric values to proper types
            candle_data.store_data(root_dir=temp_dir, mode='overwrite')
            
            # Load and verify data types
            loaded_data = candle_data.load_data(root_dir=temp_dir)
            assert loaded_data['open'].dtype == 'float64'
            assert loaded_data['volume'].dtype == 'int64'

    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrames."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Create empty DataFrame
        candle_data.df = pd.DataFrame()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should handle empty DataFrame gracefully
            with pytest.raises(ValueError, match="No data to store"):
                candle_data.store_data(root_dir=temp_dir, mode='overwrite')

    def test_missing_datetime_column(self):
        """Test handling of missing datetime column."""
        candle_data = CandleData(symbol='TEST', timeframe='60min')
        
        # Create data without datetime column or index
        data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5],
            'volume': [100, 110, 120]
        })
        candle_data.df = data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should raise error for missing datetime
            with pytest.raises(ValueError, match="Data must have a DatetimeIndex or a 'datetime' column"):
                candle_data.store_data(root_dir=temp_dir, mode='overwrite')

