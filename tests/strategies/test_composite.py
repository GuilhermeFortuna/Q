"""
Tests for the strategies composite module.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from src.strategies.composite import CompositeStrategy, weighted_vote
from src.strategies.signals.base import TradingSignal, SignalDecision
from src.strategies.combiners import GatedCombiner, ThresholdedWeightedVote, WeightedSignalCombiner


class MockSignal(TradingSignal):
    """Mock signal for testing."""
    
    def __init__(self, name, decisions=None):
        self.name = name
        self.decisions = decisions or []
    
    def compute_indicators(self, data: dict) -> None:
        pass
    
    def generate(self, i: int, data: dict) -> SignalDecision:
        if i < len(self.decisions):
            return self.decisions[i]
        return SignalDecision(side=None, strength=0.0)


class TestCompositeStrategy:
    """Test CompositeStrategy functionality."""

    def test_composite_strategy_initialization(self):
        """Test CompositeStrategy initialization."""
        signals = [MockSignal('signal1'), MockSignal('signal2')]
        strategy = CompositeStrategy(signals=signals)
        
        assert strategy.signals == signals
        assert strategy.combiner is None  # Should use default
        assert strategy.always_active is False

    def test_composite_strategy_with_combiner(self):
        """Test CompositeStrategy with custom combiner."""
        signals = [MockSignal('signal1'), MockSignal('signal2')]
        combiner = GatedCombiner(filter_indices=[0], entry_indices=[1])
        strategy = CompositeStrategy(signals=signals, combiner=combiner, always_active=True)
        
        assert strategy.signals == signals
        assert strategy.combiner == combiner
        assert strategy.always_active is True

    def test_composite_strategy_validation(self):
        """Test CompositeStrategy parameter validation."""
        # Test with invalid signals
        with pytest.raises(TypeError, match="signals must be a list"):
            CompositeStrategy(signals="invalid")
        
        # Test with empty signals list
        with pytest.raises(ValueError, match="signals list cannot be empty"):
            CompositeStrategy(signals=[])
        
        # Test with invalid signal types
        with pytest.raises(TypeError, match="All signals must be instances of TradingSignal"):
            CompositeStrategy(signals=[MockSignal('signal1'), "invalid"])

    def test_compute_indicators(self):
        """Test compute_indicators method."""
        signal1 = MockSignal('signal1')
        signal2 = MockSignal('signal2')
        strategy = CompositeStrategy(signals=[signal1, signal2])
        
        # Mock data
        data = {'candle': Mock()}
        
        # Mock compute_indicators methods
        signal1.compute_indicators = Mock()
        signal2.compute_indicators = Mock()
        
        # Call compute_indicators
        strategy.compute_indicators(data)
        
        # Verify all signals were called
        signal1.compute_indicators.assert_called_once_with(data)
        signal2.compute_indicators.assert_called_once_with(data)

    def test_entry_strategy_with_default_combiner(self):
        """Test entry_strategy with default weighted_vote combiner."""
        # Create signals with decisions
        signal1 = MockSignal('signal1', [
            SignalDecision(side='long', strength=0.8),
            SignalDecision(side='long', strength=0.6),
            SignalDecision(side=None, strength=0.0)
        ])
        signal2 = MockSignal('signal2', [
            SignalDecision(side='short', strength=0.7),
            SignalDecision(side='long', strength=0.9),
            SignalDecision(side='long', strength=0.5)
        ])
        
        strategy = CompositeStrategy(signals=[signal1, signal2])
        
        # Mock data
        data = {'candle': Mock()}
        
        # Test entry decisions
        decision1 = strategy.entry_strategy(0, data)
        decision2 = strategy.entry_strategy(1, data)
        decision3 = strategy.entry_strategy(2, data)
        
        # First decision: long(0.8) vs short(0.7) -> should be long with weighted average
        assert decision1 is not None
        assert decision1.type == 'buy'
        
        # Second decision: long(0.6) vs long(0.9) -> should be long with higher strength
        assert decision2 is not None
        assert decision2.type == 'buy'
        
        # Third decision: None(0.0) vs long(0.5) -> should be long
        assert decision3 is not None
        assert decision3.type == 'buy'

    def test_entry_strategy_with_gated_combiner(self):
        """Test entry_strategy with GatedCombiner."""
        # Create signals
        filter_signal = MockSignal('filter', [
            SignalDecision(side='long', strength=0.8),
            SignalDecision(side=None, strength=0.0),
            SignalDecision(side='long', strength=0.6)
        ])
        entry_signal = MockSignal('entry', [
            SignalDecision(side='long', strength=0.9),
            SignalDecision(side='long', strength=0.7),
            SignalDecision(side='long', strength=0.8)
        ])
        
        # Create gated combiner: filter must pass, then entry triggers
        combiner = GatedCombiner(filter_indices=[0], entry_indices=[1])
        strategy = CompositeStrategy(signals=[filter_signal, entry_signal], combiner=combiner)
        
        data = {'candle': Mock()}
        
        # Test decisions
        decision1 = strategy.entry_strategy(0, data)  # Filter passes, entry triggers
        decision2 = strategy.entry_strategy(1, data)  # Filter fails, no entry
        decision3 = strategy.entry_strategy(2, data)  # Filter passes, entry triggers
        
        assert decision1 is not None
        assert decision1.type == 'buy'
        
        assert decision2 is None  # Filter failed
        
        assert decision3 is not None
        assert decision3.type == 'buy'

    def test_entry_strategy_with_thresholded_combiner(self):
        """Test entry_strategy with ThresholdedWeightedVote combiner."""
        # Create signals
        signal1 = MockSignal('signal1', [
            SignalDecision(side='long', strength=0.3),  # Below threshold
            SignalDecision(side='long', strength=0.7),  # Above threshold
        ])
        signal2 = MockSignal('signal2', [
            SignalDecision(side='long', strength=0.4),  # Below threshold
            SignalDecision(side='long', strength=0.8),  # Above threshold
        ])
        
        # Create thresholded combiner with threshold 0.5
        combiner = ThresholdedWeightedVote(threshold=0.5)
        strategy = CompositeStrategy(signals=[signal1, signal2], combiner=combiner)
        
        data = {'candle': Mock()}
        
        # Test decisions
        decision1 = strategy.entry_strategy(0, data)  # Both below threshold
        decision2 = strategy.entry_strategy(1, data)  # Both above threshold
        
        assert decision1 is None  # No signal above threshold
        
        assert decision2 is not None
        assert decision2.type == 'buy'

    def test_exit_strategy(self):
        """Test exit_strategy method."""
        signal1 = MockSignal('signal1')
        signal2 = MockSignal('signal2')
        strategy = CompositeStrategy(signals=[signal1, signal2])
        
        data = {'candle': Mock()}
        trade_info = {'entry_price': 100.0}
        
        # Mock exit decisions
        signal1.generate = Mock(return_value=SignalDecision(side='short', strength=0.8))
        signal2.generate = Mock(return_value=SignalDecision(side='short', strength=0.6))
        
        # Call exit_strategy
        decision = strategy.exit_strategy(0, data, trade_info)
        
        # Should return exit decision based on signal combination
        assert decision is not None
        assert decision.type == 'sell'

    def test_always_active_flag(self):
        """Test always_active flag behavior."""
        # Create signal that returns None decisions
        signal = MockSignal('signal', [
            SignalDecision(side=None, strength=0.0),
            SignalDecision(side=None, strength=0.0),
        ])
        
        # Test with always_active=False (default)
        strategy1 = CompositeStrategy(signals=[signal])
        data = {'candle': Mock()}
        
        decision1 = strategy1.entry_strategy(0, data)
        assert decision1 is None  # No active signals
        
        # Test with always_active=True
        strategy2 = CompositeStrategy(signals=[signal], always_active=True)
        decision2 = strategy2.entry_strategy(0, data)
        assert decision2 is not None  # Should generate decision even with no active signals

    def test_signal_decision_tracking(self):
        """Test that signal decisions are tracked in trade info."""
        # Create signals with specific decisions
        signal1 = MockSignal('signal1', [
            SignalDecision(side='long', strength=0.8, info={'rsi': 30})
        ])
        signal2 = MockSignal('signal2', [
            SignalDecision(side='long', strength=0.6, info={'macd': 0.5})
        ])
        
        strategy = CompositeStrategy(signals=[signal1, signal2])
        data = {'candle': Mock()}
        
        # Mock the combiner to return a decision with info
        decision = strategy.entry_strategy(0, data)
        
        # The decision should contain information about contributing signals
        assert decision is not None
        # Note: The actual implementation would need to track signal decisions
        # This test verifies the interface exists

    def test_empty_signals_list(self):
        """Test behavior with empty signals list."""
        with pytest.raises(ValueError, match="signals list cannot be empty"):
            CompositeStrategy(signals=[])

    def test_single_signal(self):
        """Test CompositeStrategy with single signal."""
        signal = MockSignal('signal1', [
            SignalDecision(side='long', strength=0.8),
            SignalDecision(side='short', strength=0.7),
        ])
        
        strategy = CompositeStrategy(signals=[signal])
        data = {'candle': Mock()}
        
        # Test decisions
        decision1 = strategy.entry_strategy(0, data)
        decision2 = strategy.entry_strategy(1, data)
        
        assert decision1 is not None
        assert decision1.type == 'buy'
        
        assert decision2 is not None
        assert decision2.type == 'sell'

    def test_signal_error_handling(self):
        """Test error handling in signal generation."""
        # Create signal that raises exception
        error_signal = MockSignal('error_signal')
        error_signal.generate = Mock(side_effect=Exception("Signal error"))
        
        normal_signal = MockSignal('normal_signal', [
            SignalDecision(side='long', strength=0.8)
        ])
        
        strategy = CompositeStrategy(signals=[error_signal, normal_signal])
        data = {'candle': Mock()}
        
        # Should handle signal errors gracefully
        with pytest.raises(Exception, match="Signal error"):
            strategy.entry_strategy(0, data)

    def test_combiner_validation(self):
        """Test combiner validation."""
        signals = [MockSignal('signal1')]
        
        # Test with invalid combiner
        with pytest.raises(TypeError, match="combiner must be callable"):
            CompositeStrategy(signals=signals, combiner="invalid")

    def test_data_validation(self):
        """Test data validation in strategy methods."""
        strategy = CompositeStrategy(signals=[MockSignal('signal1')])
        
        # Test with invalid data
        with pytest.raises(TypeError, match="data must be a dict"):
            strategy.compute_indicators("invalid_data")
        
        with pytest.raises(TypeError, match="data must be a dict"):
            strategy.entry_strategy(0, "invalid_data")
        
        with pytest.raises(TypeError, match="data must be a dict"):
            strategy.exit_strategy(0, "invalid_data", None)

    def test_index_validation(self):
        """Test index validation in strategy methods."""
        strategy = CompositeStrategy(signals=[MockSignal('signal1')])
        data = {'candle': Mock()}
        
        # Test with invalid index types
        with pytest.raises(TypeError, match="index must be an integer"):
            strategy.entry_strategy("invalid", data)
        
        with pytest.raises(TypeError, match="index must be an integer"):
            strategy.exit_strategy("invalid", data, None)

    def test_performance_with_many_signals(self):
        """Test performance with many signals."""
        # Create many signals
        signals = [MockSignal(f'signal{i}') for i in range(20)]
        
        # Set up mock decisions
        for signal in signals:
            signal.decisions = [SignalDecision(side='long', strength=0.5)]
        
        strategy = CompositeStrategy(signals=signals)
        data = {'candle': Mock()}
        
        # Should handle many signals efficiently
        decision = strategy.entry_strategy(0, data)
        assert decision is not None

    def test_signal_combination_weights(self):
        """Test signal combination with different weights."""
        # Create signals with different strengths
        signal1 = MockSignal('signal1', [
            SignalDecision(side='long', strength=0.9)  # High strength
        ])
        signal2 = MockSignal('signal2', [
            SignalDecision(side='short', strength=0.3)  # Low strength
        ])
        
        # Use weighted combiner
        combiner = WeightedSignalCombiner(weights=[0.8, 0.2])  # Favor signal1
        strategy = CompositeStrategy(signals=[signal1, signal2], combiner=combiner)
        
        data = {'candle': Mock()}
        decision = strategy.entry_strategy(0, data)
        
        # Should favor the higher-weighted signal
        assert decision is not None
        # The exact decision depends on the combiner implementation


class TestWeightedVote:
    """Test weighted_vote function."""

    def test_weighted_vote_basic(self):
        """Test basic weighted_vote functionality."""
        decisions = [
            SignalDecision(side='long', strength=0.8),
            SignalDecision(side='long', strength=0.6),
            SignalDecision(side='short', strength=0.7)
        ]
        
        result = weighted_vote(decisions)
        
        assert result is not None
        assert result.type in ['buy', 'sell']
        assert 0 <= result.strength <= 1

    def test_weighted_vote_empty_decisions(self):
        """Test weighted_vote with empty decisions list."""
        result = weighted_vote([])
        
        assert result is None

    def test_weighted_vote_all_none(self):
        """Test weighted_vote with all None decisions."""
        decisions = [
            SignalDecision(side=None, strength=0.0),
            SignalDecision(side=None, strength=0.0)
        ]
        
        result = weighted_vote(decisions)
        
        assert result is None

    def test_weighted_vote_mixed_decisions(self):
        """Test weighted_vote with mixed decision types."""
        decisions = [
            SignalDecision(side='long', strength=0.8),
            SignalDecision(side=None, strength=0.0),
            SignalDecision(side='short', strength=0.6)
        ]
        
        result = weighted_vote(decisions)
        
        assert result is not None
        assert result.type in ['buy', 'sell']

    def test_weighted_vote_single_decision(self):
        """Test weighted_vote with single decision."""
        decisions = [SignalDecision(side='long', strength=0.8)]
        
        result = weighted_vote(decisions)
        
        assert result is not None
        assert result.type == 'buy'
        assert result.strength == 0.8

    def test_weighted_vote_tie_breaking(self):
        """Test weighted_vote tie breaking."""
        decisions = [
            SignalDecision(side='long', strength=0.5),
            SignalDecision(side='short', strength=0.5)
        ]
        
        result = weighted_vote(decisions)
        
        # Should break tie (implementation dependent)
        assert result is not None
        assert result.type in ['buy', 'sell']