"""
Comprehensive tests for all trading signals.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from src.strategies.signals.base import SignalDecision
from src.strategies.signals import (
    AdxDmiSignal,
    AtrTrailingStopReversalSignal,
    BollingerBandSignal,
    ChoppinessRegimeFilter,
    DonchianBreakoutSignal,
    HeikinAshiTrendContinuationSignal,
    KeltnerSqueezeBreakoutSignal,
    MaCrossoverSignal,
    MacdMomentumSignal,
    MtfMaAlignmentFilter,
    RsiMeanReversionSignal,
    SupertrendFlipSignal,
    VolumeSpikeExhaustionSignal,
    VwapDeviationReversionSignal,
)


class TestSignalBase:
    """Base test class for all signals."""

    def create_sample_data(self, periods=100):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range('2024-01-01', periods=periods, freq='1H')
        np.random.seed(42)  # For reproducible tests

        # Generate realistic price data
        base_price = 100.0
        returns = np.random.normal(0, 0.02, periods)
        prices = [base_price]

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        prices = np.array(prices)

        data = {
            'open': prices + np.random.normal(0, 0.001, periods),
            'high': prices + np.abs(np.random.normal(0, 0.005, periods)),
            'low': prices - np.abs(np.random.normal(0, 0.005, periods)),
            'close': prices,
            'volume': np.random.randint(100, 1000, periods),
        }

        df = pd.DataFrame(data, index=dates)
        df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
        df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))

        return df

    def create_mock_data(self, df):
        """Create mock data object for signal testing."""
        mock_data = {'candle': Mock()}
        mock_data['candle'].df = df
        mock_data['candle'].close = df['close'].values
        mock_data['candle'].high = df['high'].values
        mock_data['candle'].low = df['low'].values
        mock_data['candle'].open = df['open'].values
        mock_data['candle'].volume = df['volume'].values
        return mock_data

    def test_signal_interface(self, signal_class, **kwargs):
        """Test that signal implements the TradingSignal interface."""
        signal = signal_class(**kwargs)

        # Test compute_indicators method
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        # Should not raise exception
        signal.compute_indicators(data)

        # Test generate method
        decision = signal.generate(0, data)
        assert isinstance(decision, SignalDecision)

        # Test signal properties
        assert hasattr(signal, '__class__')
        assert signal.__class__.__name__ != 'TradingSignal'

    def test_signal_indicators_added(self, signal_class, **kwargs):
        """Test that signal adds indicators to data."""
        signal = signal_class(**kwargs)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        # Count columns before
        initial_columns = len(data['candle'].df.columns)

        # Compute indicators
        signal.compute_indicators(data)

        # Should have added at least one column
        assert len(data['candle'].df.columns) > initial_columns

    def test_signal_generate_consistency(self, signal_class, **kwargs):
        """Test that signal generates consistent decisions."""
        signal = signal_class(**kwargs)
        df = self.create_sample_data(periods=50)
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        # Test multiple calls with same data
        decisions = []
        for i in range(10, 20):  # Test middle range
            decision = signal.generate(i, data)
            decisions.append(decision)

        # All decisions should be SignalDecision instances
        for decision in decisions:
            assert isinstance(decision, SignalDecision)
            assert 0 <= decision.strength <= 1

    def test_signal_parameter_validation(
        self, signal_class, valid_params, invalid_params
    ):
        """Test signal parameter validation."""
        # Test valid parameters
        signal = signal_class(**valid_params)
        assert signal is not None

        # Test invalid parameters
        for param_name, invalid_value in invalid_params.items():
            with pytest.raises((TypeError, ValueError)):
                signal_class(**{**valid_params, param_name: invalid_value})


class TestAdxDmiSignal(TestSignalBase):
    """Test AdxDmiSignal."""

    def test_adx_dmi_signal_creation(self):
        """Test AdxDmiSignal creation."""
        signal = AdxDmiSignal(length=14, adx_thresh=25.0)
        assert signal.length == 14
        assert signal.adx_thresh == 25.0

    def test_adx_dmi_signal_interface(self):
        """Test AdxDmiSignal interface."""
        self.test_signal_interface(AdxDmiSignal, length=14, adx_thresh=25.0)

    def test_adx_dmi_signal_indicators(self):
        """Test AdxDmiSignal indicators."""
        self.test_signal_indicators_added(AdxDmiSignal, length=14, adx_thresh=25.0)

    def test_adx_dmi_signal_generate(self):
        """Test AdxDmiSignal generate method."""
        signal = AdxDmiSignal(length=14, adx_thresh=25.0)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        # Test generate with sufficient data
        decision = signal.generate(20, data)
        assert isinstance(decision, SignalDecision)
        assert decision.side in ['long', 'short', None]

    def test_adx_dmi_signal_parameter_validation(self):
        """Test AdxDmiSignal parameter validation."""
        valid_params = {'length': 14, 'adx_thresh': 25.0}
        invalid_params = {'length': 'invalid', 'adx_thresh': 'invalid'}
        self.test_signal_parameter_validation(
            AdxDmiSignal, valid_params, invalid_params
        )


class TestAtrTrailingStopReversalSignal(TestSignalBase):
    """Test AtrTrailingStopSignal."""

    def test_atr_trailing_stop_signal_creation(self):
        """Test AtrTrailingStopSignal creation."""
        signal = AtrTrailingStopReversalSignal(atr_length=14, atr_mult=2.0)
        assert signal.atr_length == 14
        assert signal.atr_mult == 2.0

    def test_atr_trailing_stop_signal_interface(self):
        """Test AtrTrailingStopSignal interface."""
        self.test_signal_interface(
            AtrTrailingStopReversalSignal, atr_length=14, atr_mult=2.0
        )

    def test_atr_trailing_stop_signal_indicators(self):
        """Test AtrTrailingStopSignal indicators."""
        self.test_signal_indicators_added(
            AtrTrailingStopReversalSignal, atr_length=14, atr_mult=2.0
        )

    def test_atr_trailing_stop_signal_generate(self):
        """Test AtrTrailingStopSignal generate method."""
        signal = AtrTrailingStopReversalSignal(atr_length=14, atr_mult=2.0)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(20, data)
        assert isinstance(decision, SignalDecision)

    def test_atr_trailing_stop_signal_parameter_validation(self):
        """Test AtrTrailingStopSignal parameter validation."""
        valid_params = {'atr_length': 14, 'atr_mult': 2.0}
        invalid_params = {'atr_length': 'invalid', 'atr_mult': 'invalid'}
        self.test_signal_parameter_validation(
            AtrTrailingStopReversalSignal, valid_params, invalid_params
        )


class TestBollingerBandSignal(TestSignalBase):
    """Test BBandsSignal."""

    def test_b_bands_signal_creation(self):
        """Test BBandsSignal creation."""
        signal = BollingerBandSignal(length=20, std=2.0)
        assert signal.length == 20
        assert signal.std == 2.0

    def test_b_bands_signal_interface(self):
        """Test BBandsSignal interface."""
        self.test_signal_interface(BollingerBandSignal, length=20, std=2.0)

    def test_b_bands_signal_indicators(self):
        """Test BBandsSignal indicators."""
        self.test_signal_indicators_added(BollingerBandSignal, length=20, std=2.0)

    def test_b_bands_signal_generate(self):
        """Test BBandsSignal generate method."""
        signal = BollingerBandSignal(length=20, std=2.0)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(25, data)
        assert isinstance(decision, SignalDecision)

    def test_b_bands_signal_parameter_validation(self):
        """Test BBandsSignal parameter validation."""
        valid_params = {'length': 20, 'std': 2.0}
        invalid_params = {'length': 'invalid', 'std': 'invalid'}
        self.test_signal_parameter_validation(
            BollingerBandSignal, valid_params, invalid_params
        )


class TestChoppinessFilterSignal(TestSignalBase):
    """Test ChoppinessFilterSignal."""

    def test_choppiness_filter_signal_creation(self):
        """Test ChoppinessFilterSignal creation."""
        signal = ChoppinessRegimeFilter(length=14, threshold=0.5)
        assert signal.length == 14
        assert signal.threshold == 0.5

    def test_choppiness_filter_signal_interface(self):
        """Test ChoppinessFilterSignal interface."""
        self.test_signal_interface(ChoppinessRegimeFilter, length=14, threshold=0.5)

    def test_choppiness_filter_signal_indicators(self):
        """Test ChoppinessFilterSignal indicators."""
        self.test_signal_indicators_added(
            ChoppinessRegimeFilter, length=14, threshold=0.5
        )

    def test_choppiness_filter_signal_generate(self):
        """Test ChoppinessFilterSignal generate method."""
        signal = ChoppinessRegimeFilter(length=14, threshold=0.5)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(20, data)
        assert isinstance(decision, SignalDecision)

    def test_choppiness_filter_signal_parameter_validation(self):
        """Test ChoppinessFilterSignal parameter validation."""
        valid_params = {'length': 14, 'threshold': 0.5}
        invalid_params = {'length': 'invalid', 'threshold': 'invalid'}
        self.test_signal_parameter_validation(
            ChoppinessRegimeFilter, valid_params, invalid_params
        )


class TestDonchianBreakoutSignal(TestSignalBase):
    """Test DonchianBreakoutSignal."""

    def test_donchian_breakout_signal_creation(self):
        """Test DonchianBreakoutSignal creation."""
        signal = DonchianBreakoutSignal(breakout_len=20, pullback_len=5)
        assert signal.breakout_len == 20
        assert signal.pullback_len == 5

    def test_donchian_breakout_signal_interface(self):
        """Test DonchianBreakoutSignal interface."""
        self.test_signal_interface(
            DonchianBreakoutSignal, breakout_len=20, pullback_len=5
        )

    def test_donchian_breakout_signal_indicators(self):
        """Test DonchianBreakoutSignal indicators."""
        self.test_signal_indicators_added(
            DonchianBreakoutSignal, breakout_len=20, pullback_len=5
        )

    def test_donchian_breakout_signal_generate(self):
        """Test DonchianBreakoutSignal generate method."""
        signal = DonchianBreakoutSignal(breakout_len=20, pullback_len=5)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(25, data)
        assert isinstance(decision, SignalDecision)

    def test_donchian_breakout_signal_parameter_validation(self):
        """Test DonchianBreakoutSignal parameter validation."""
        valid_params = {'breakout_len': 20, 'pullback_len': 5}
        invalid_params = {'breakout_len': 'invalid', 'pullback_len': 'invalid'}
        self.test_signal_parameter_validation(
            DonchianBreakoutSignal, valid_params, invalid_params
        )


class TestHeikinAshiTrendSignal(TestSignalBase):
    """Test HeikinAshiTrendSignal."""

    def test_heikin_ashi_trend_signal_creation(self):
        """Test HeikinAshiTrendSignal creation."""
        signal = HeikinAshiTrendContinuationSignal(length=14)
        assert signal.length == 14

    def test_heikin_ashi_trend_signal_interface(self):
        """Test HeikinAshiTrendSignal interface."""
        self.test_signal_interface(HeikinAshiTrendContinuationSignal, length=14)

    def test_heikin_ashi_trend_signal_indicators(self):
        """Test HeikinAshiTrendSignal indicators."""
        self.test_signal_indicators_added(HeikinAshiTrendContinuationSignal, length=14)

    def test_heikin_ashi_trend_signal_generate(self):
        """Test HeikinAshiTrendSignal generate method."""
        signal = HeikinAshiTrendContinuationSignal(length=14)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(20, data)
        assert isinstance(decision, SignalDecision)

    def test_heikin_ashi_trend_signal_parameter_validation(self):
        """Test HeikinAshiTrendSignal parameter validation."""
        valid_params = {'length': 14}
        invalid_params = {'length': 'invalid'}
        self.test_signal_parameter_validation(
            HeikinAshiTrendContinuationSignal, valid_params, invalid_params
        )


class TestKeltnerSqueezeSignal(TestSignalBase):
    """Test KeltnerSqueezeSignal."""

    def test_keltner_squeeze_signal_creation(self):
        """Test KeltnerSqueezeSignal creation."""
        signal = KeltnerSqueezeBreakoutSignal(length=20, atr_mult=1.5)
        assert signal.length == 20
        assert signal.atr_mult == 1.5

    def test_keltner_squeeze_signal_interface(self):
        """Test KeltnerSqueezeSignal interface."""
        self.test_signal_interface(
            KeltnerSqueezeBreakoutSignal, length=20, atr_mult=1.5
        )

    def test_keltner_squeeze_signal_indicators(self):
        """Test KeltnerSqueezeSignal indicators."""
        self.test_signal_indicators_added(
            KeltnerSqueezeBreakoutSignal, length=20, atr_mult=1.5
        )

    def test_keltner_squeeze_signal_generate(self):
        """Test KeltnerSqueezeSignal generate method."""
        signal = KeltnerSqueezeBreakoutSignal(length=20, atr_mult=1.5)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(25, data)
        assert isinstance(decision, SignalDecision)

    def test_keltner_squeeze_signal_parameter_validation(self):
        """Test KeltnerSqueezeSignal parameter validation."""
        valid_params = {'length': 20, 'atr_mult': 1.5}
        invalid_params = {'length': 'invalid', 'atr_mult': 'invalid'}
        self.test_signal_parameter_validation(
            KeltnerSqueezeBreakoutSignal, valid_params, invalid_params
        )


class TestMaCrossoverSignal(TestSignalBase):
    """Test MaCrossoverSignal."""

    def test_ma_crossover_signal_creation(self):
        """Test MaCrossoverSignal creation."""
        signal = MaCrossoverSignal(short_period=9, long_period=21)
        assert signal.short_period == 9
        assert signal.long_period == 21

    def test_ma_crossover_signal_interface(self):
        """Test MaCrossoverSignal interface."""
        self.test_signal_interface(MaCrossoverSignal, short_period=9, long_period=21)

    def test_ma_crossover_signal_indicators(self):
        """Test MaCrossoverSignal indicators."""
        self.test_signal_indicators_added(
            MaCrossoverSignal, short_period=9, long_period=21
        )

    def test_ma_crossover_signal_generate(self):
        """Test MaCrossoverSignal generate method."""
        signal = MaCrossoverSignal(short_period=9, long_period=21)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(25, data)
        assert isinstance(decision, SignalDecision)

    def test_ma_crossover_signal_parameter_validation(self):
        """Test MaCrossoverSignal parameter validation."""
        valid_params = {'short_period': 9, 'long_period': 21}
        invalid_params = {'short_period': 'invalid', 'long_period': 'invalid'}
        self.test_signal_parameter_validation(
            MaCrossoverSignal, valid_params, invalid_params
        )


class TestMacdMomentumSignal(TestSignalBase):
    """Test MacdMomentumSignal."""

    def test_macd_momentum_signal_creation(self):
        """Test MacdMomentumSignal creation."""
        signal = MacdMomentumSignal(fast=12, slow=26, signal=9)
        assert signal.fast == 12
        assert signal.slow == 26
        assert signal.signal == 9

    def test_macd_momentum_signal_interface(self):
        """Test MacdMomentumSignal interface."""
        self.test_signal_interface(MacdMomentumSignal, fast=12, slow=26, signal=9)

    def test_macd_momentum_signal_indicators(self):
        """Test MacdMomentumSignal indicators."""
        self.test_signal_indicators_added(
            MacdMomentumSignal, fast=12, slow=26, signal=9
        )

    def test_macd_momentum_signal_generate(self):
        """Test MacdMomentumSignal generate method."""
        signal = MacdMomentumSignal(fast=12, slow=26, signal=9)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(30, data)
        assert isinstance(decision, SignalDecision)

    def test_macd_momentum_signal_parameter_validation(self):
        """Test MacdMomentumSignal parameter validation."""
        valid_params = {'fast': 12, 'slow': 26, 'signal': 9}
        invalid_params = {'fast': 'invalid', 'slow': 'invalid', 'signal': 'invalid'}
        self.test_signal_parameter_validation(
            MacdMomentumSignal, valid_params, invalid_params
        )


class TestMtfMaAlignmentSignal(TestSignalBase):
    """Test MtfMaAlignmentSignal."""

    def test_mtf_ma_alignment_signal_creation(self):
        """Test MtfMaAlignmentSignal creation."""
        signal = MtfMaAlignmentFilter(short_period=9, long_period=21)
        assert signal.short_period == 9
        assert signal.long_period == 21

    def test_mtf_ma_alignment_signal_interface(self):
        """Test MtfMaAlignmentSignal interface."""
        self.test_signal_interface(MtfMaAlignmentFilter, short_period=9, long_period=21)

    def test_mtf_ma_alignment_signal_indicators(self):
        """Test MtfMaAlignmentSignal indicators."""
        self.test_signal_indicators_added(
            MtfMaAlignmentFilter, short_period=9, long_period=21
        )

    def test_mtf_ma_alignment_signal_generate(self):
        """Test MtfMaAlignmentSignal generate method."""
        signal = MtfMaAlignmentFilter(short_period=9, long_period=21)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(25, data)
        assert isinstance(decision, SignalDecision)

    def test_mtf_ma_alignment_signal_parameter_validation(self):
        """Test MtfMaAlignmentSignal parameter validation."""
        valid_params = {'short_period': 9, 'long_period': 21}
        invalid_params = {'short_period': 'invalid', 'long_period': 'invalid'}
        self.test_signal_parameter_validation(
            MtfMaAlignmentFilter, valid_params, invalid_params
        )


class TestRsiSignal(TestSignalBase):
    """Test RsiSignal."""

    def test_rsi_signal_creation(self):
        """Test RsiSignal creation."""
        signal = RsiMeanReversionSignal(length=14, oversold=30, overbought=70)
        assert signal.length == 14
        assert signal.oversold == 30
        assert signal.overbought == 70

    def test_rsi_signal_interface(self):
        """Test RsiSignal interface."""
        self.test_signal_interface(
            RsiMeanReversionSignal, length=14, oversold=30, overbought=70
        )

    def test_rsi_signal_indicators(self):
        """Test RsiSignal indicators."""
        self.test_signal_indicators_added(
            RsiMeanReversionSignal, length=14, oversold=30, overbought=70
        )

    def test_rsi_signal_generate(self):
        """Test RsiSignal generate method."""
        signal = RsiMeanReversionSignal(length=14, oversold=30, overbought=70)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(20, data)
        assert isinstance(decision, SignalDecision)

    def test_rsi_signal_parameter_validation(self):
        """Test RsiSignal parameter validation."""
        valid_params = {'length': 14, 'oversold': 30, 'overbought': 70}
        invalid_params = {
            'length': 'invalid',
            'oversold': 'invalid',
            'overbought': 'invalid',
        }
        self.test_signal_parameter_validation(
            RsiMeanReversionSignal, valid_params, invalid_params
        )


class TestSupertrendFlipSignal(TestSignalBase):
    """Test SupertrendFlipSignal."""

    def test_supertrend_flip_signal_creation(self):
        """Test SupertrendFlipSignal creation."""
        signal = SupertrendFlipSignal(atr_length=10, atr_mult=3.0)
        assert signal.atr_length == 10
        assert signal.atr_mult == 3.0

    def test_supertrend_flip_signal_interface(self):
        """Test SupertrendFlipSignal interface."""
        self.test_signal_interface(SupertrendFlipSignal, atr_length=10, atr_mult=3.0)

    def test_supertrend_flip_signal_indicators(self):
        """Test SupertrendFlipSignal indicators."""
        self.test_signal_indicators_added(
            SupertrendFlipSignal, atr_length=10, atr_mult=3.0
        )

    def test_supertrend_flip_signal_generate(self):
        """Test SupertrendFlipSignal generate method."""
        signal = SupertrendFlipSignal(atr_length=10, atr_mult=3.0)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(15, data)
        assert isinstance(decision, SignalDecision)

    def test_supertrend_flip_signal_parameter_validation(self):
        """Test SupertrendFlipSignal parameter validation."""
        valid_params = {'atr_length': 10, 'atr_mult': 3.0}
        invalid_params = {'atr_length': 'invalid', 'atr_mult': 'invalid'}
        self.test_signal_parameter_validation(
            SupertrendFlipSignal, valid_params, invalid_params
        )


class TestVolumeSpikeExhaustionSignal(TestSignalBase):
    """Test VolumeSpikeExhaustionSignal."""

    def test_volume_spike_exhaustion_signal_creation(self):
        """Test VolumeSpikeExhaustionSignal creation."""
        signal = VolumeSpikeExhaustionSignal(volume_period=20, volume_threshold=1.5)
        assert signal.volume_period == 20
        assert signal.volume_threshold == 1.5

    def test_volume_spike_exhaustion_signal_interface(self):
        """Test VolumeSpikeExhaustionSignal interface."""
        self.test_signal_interface(
            VolumeSpikeExhaustionSignal, volume_period=20, volume_threshold=1.5
        )

    def test_volume_spike_exhaustion_signal_indicators(self):
        """Test VolumeSpikeExhaustionSignal indicators."""
        self.test_signal_indicators_added(
            VolumeSpikeExhaustionSignal, volume_period=20, volume_threshold=1.5
        )

    def test_volume_spike_exhaustion_signal_generate(self):
        """Test VolumeSpikeExhaustionSignal generate method."""
        signal = VolumeSpikeExhaustionSignal(volume_period=20, volume_threshold=1.5)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(25, data)
        assert isinstance(decision, SignalDecision)

    def test_volume_spike_exhaustion_signal_parameter_validation(self):
        """Test VolumeSpikeExhaustionSignal parameter validation."""
        valid_params = {'volume_period': 20, 'volume_threshold': 1.5}
        invalid_params = {'volume_period': 'invalid', 'volume_threshold': 'invalid'}
        self.test_signal_parameter_validation(
            VolumeSpikeExhaustionSignal, valid_params, invalid_params
        )


class TestVwapDeviationSignal(TestSignalBase):
    """Test VwapDeviationSignal."""

    def test_vwap_deviation_signal_creation(self):
        """Test VwapDeviationSignal creation."""
        signal = VwapDeviationReversionSignal(vwap_period=20, deviation_threshold=2.0)
        assert signal.vwap_period == 20
        assert signal.deviation_threshold == 2.0

    def test_vwap_deviation_signal_interface(self):
        """Test VwapDeviationSignal interface."""
        self.test_signal_interface(
            VwapDeviationReversionSignal, vwap_period=20, deviation_threshold=2.0
        )

    def test_vwap_deviation_signal_indicators(self):
        """Test VwapDeviationSignal indicators."""
        self.test_signal_indicators_added(
            VwapDeviationReversionSignal, vwap_period=20, deviation_threshold=2.0
        )

    def test_vwap_deviation_signal_generate(self):
        """Test VwapDeviationSignal generate method."""
        signal = VwapDeviationReversionSignal(vwap_period=20, deviation_threshold=2.0)
        df = self.create_sample_data()
        data = self.create_mock_data(df)

        signal.compute_indicators(data)

        decision = signal.generate(25, data)
        assert isinstance(decision, SignalDecision)

    def test_vwap_deviation_signal_parameter_validation(self):
        """Test VwapDeviationSignal parameter validation."""
        valid_params = {'vwap_period': 20, 'deviation_threshold': 2.0}
        invalid_params = {'vwap_period': 'invalid', 'deviation_threshold': 'invalid'}
        self.test_signal_parameter_validation(
            VwapDeviationReversionSignal, valid_params, invalid_params
        )


class TestAllSignalsIntegration:
    """Integration tests for all signals."""

    def test_all_signals_importable(self):
        """Test that all signals can be imported."""
        from src.strategies.signals import (
            AdxDmiSignal,
            AtrTrailingStopReversalSignal,
            BollingerBandSignal,
            ChoppinessRegimeFilter,
            DonchianBreakoutSignal,
            HeikinAshiTrendContinuationSignal,
            KeltnerSqueezeBreakoutSignal,
            MaCrossoverSignal,
            MacdMomentumSignal,
            MtfMaAlignmentFilter,
            RsiMeanReversionSignal,
            SupertrendFlipSignal,
            VolumeSpikeExhaustionSignal,
            VwapDeviationReversionSignal,
        )

        # All signals should be importable
        assert AdxDmiSignal is not None
        assert AtrTrailingStopReversalSignal is not None
        assert BollingerBandSignal is not None
        assert ChoppinessRegimeFilter is not None
        assert DonchianBreakoutSignal is not None
        assert HeikinAshiTrendContinuationSignal is not None
        assert KeltnerSqueezeBreakoutSignal is not None
        assert MaCrossoverSignal is not None
        assert MacdMomentumSignal is not None
        assert MtfMaAlignmentFilter is not None
        assert RsiMeanReversionSignal is not None
        assert SupertrendFlipSignal is not None
        assert VolumeSpikeExhaustionSignal is not None
        assert VwapDeviationReversionSignal is not None

    def test_all_signals_inherit_from_trading_signal(self):
        """Test that all signals inherit from TradingSignal."""
        from src.strategies.signals.base import TradingSignal

        signal_classes = [
            AdxDmiSignal,
            AtrTrailingStopReversalSignal,
            BollingerBandSignal,
            ChoppinessRegimeFilter,
            DonchianBreakoutSignal,
            HeikinAshiTrendContinuationSignal,
            KeltnerSqueezeBreakoutSignal,
            MaCrossoverSignal,
            MacdMomentumSignal,
            MtfMaAlignmentFilter,
            RsiMeanReversionSignal,
            SupertrendFlipSignal,
            VolumeSpikeExhaustionSignal,
            VwapDeviationReversionSignal,
        ]

        for signal_class in signal_classes:
            assert issubclass(signal_class, TradingSignal)

    def test_all_signals_have_required_methods(self):
        """Test that all signals have required methods."""
        signal_classes = [
            AdxDmiSignal,
            AtrTrailingStopReversalSignal,
            BollingerBandSignal,
            ChoppinessRegimeFilter,
            DonchianBreakoutSignal,
            HeikinAshiTrendContinuationSignal,
            KeltnerSqueezeBreakoutSignal,
            MaCrossoverSignal,
            MacdMomentumSignal,
            MtfMaAlignmentFilter,
            RsiMeanReversionSignal,
            SupertrendFlipSignal,
            VolumeSpikeExhaustionSignal,
            VwapDeviationReversionSignal,
        ]

        for signal_class in signal_classes:
            # Check that required methods exist
            assert hasattr(signal_class, 'compute_indicators')
            assert hasattr(signal_class, 'generate')

            # Check that methods are callable
            assert callable(signal_class.compute_indicators)
            assert callable(signal_class.generate)

    def test_all_signals_with_real_data(self):
        """Test all signals with realistic data."""
        # Create realistic trending data
        periods = 200
        dates = pd.date_range('2024-01-01', periods=periods, freq='1H')

        # Create trending price data
        base_price = 100.0
        trend = 0.001  # 0.1% per hour
        volatility = 0.02

        np.random.seed(42)
        returns = np.random.normal(trend, volatility, periods)
        prices = [base_price]

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        prices = np.array(prices)

        data = {
            'open': prices + np.random.normal(0, 0.001, periods),
            'high': prices + np.abs(np.random.normal(0, 0.005, periods)),
            'low': prices - np.abs(np.random.normal(0, 0.005, periods)),
            'close': prices,
            'volume': np.random.randint(100, 1000, periods),
        }

        df = pd.DataFrame(data, index=dates)
        df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
        df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))

        # Test all signals
        signal_configs = [
            (AdxDmiSignal, {'length': 14, 'adx_thresh': 25.0}),
            (AtrTrailingStopReversalSignal, {'atr_length': 14, 'atr_mult': 2.0}),
            (BollingerBandSignal, {'length': 20, 'std': 2.0}),
            (ChoppinessRegimeFilter, {'length': 14, 'threshold': 0.5}),
            (DonchianBreakoutSignal, {'breakout_len': 20, 'pullback_len': 5}),
            (HeikinAshiTrendContinuationSignal, {'length': 14}),
            (KeltnerSqueezeBreakoutSignal, {'length': 20, 'atr_mult': 1.5}),
            (MaCrossoverSignal, {'short_period': 9, 'long_period': 21}),
            (MacdMomentumSignal, {'fast': 12, 'slow': 26, 'signal': 9}),
            (MtfMaAlignmentFilter, {'short_period': 9, 'long_period': 21}),
            (RsiMeanReversionSignal, {'length': 14, 'oversold': 30, 'overbought': 70}),
            (SupertrendFlipSignal, {'atr_length': 10, 'atr_mult': 3.0}),
            (
                VolumeSpikeExhaustionSignal,
                {'volume_period': 20, 'volume_threshold': 1.5},
            ),
            (
                VwapDeviationReversionSignal,
                {'vwap_period': 20, 'deviation_threshold': 2.0},
            ),
        ]

        for signal_class, config in signal_configs:
            signal = signal_class(**config)

            # Create mock data
            mock_data = {'candle': Mock()}
            mock_data['candle'].df = df
            mock_data['candle'].close = df['close'].values
            mock_data['candle'].high = df['high'].values
            mock_data['candle'].low = df['low'].values
            mock_data['candle'].open = df['open'].values
            mock_data['candle'].volume = df['volume'].values

            # Test compute_indicators
            signal.compute_indicators(mock_data)

            # Test generate with sufficient data
            for i in range(50, 100):  # Test middle range
                decision = signal.generate(i, mock_data)
                assert isinstance(decision, SignalDecision)
                assert 0 <= decision.strength <= 1
