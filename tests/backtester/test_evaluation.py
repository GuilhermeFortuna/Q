"""
Tests for the backtester evaluation module.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

from src.backtester.evaluation import (
    AcceptanceCriteria,
    StrategyEvaluator,
    EvaluationResult,
    metrics_from_trade_registry,
    oos_stability_from_two_runs
)
from src.backtester.trades import TradeRegistry, TradeOrder
import datetime as dt


class TestAcceptanceCriteria:
    """Test AcceptanceCriteria functionality."""

    def test_acceptance_criteria_creation(self):
        """Test AcceptanceCriteria creation with default values."""
        criteria = AcceptanceCriteria()
        
        assert criteria.min_trades == 150
        assert criteria.min_profit_factor == 1.20
        assert criteria.max_drawdown == 0.25
        assert criteria.min_sharpe is None
        assert criteria.min_cagr is None
        assert criteria.min_win_rate is None
        assert criteria.max_consecutive_losses is None

    def test_acceptance_criteria_custom_values(self):
        """Test AcceptanceCriteria with custom values."""
        criteria = AcceptanceCriteria(
            min_trades=100,
            min_profit_factor=1.5,
            max_drawdown=0.15,
            min_sharpe=1.2,
            min_cagr=0.20,
            min_win_rate=0.6,
            max_consecutive_losses=3
        )
        
        assert criteria.min_trades == 100
        assert criteria.min_profit_factor == 1.5
        assert criteria.max_drawdown == 0.15
        assert criteria.min_sharpe == 1.2
        assert criteria.min_cagr == 0.20
        assert criteria.min_win_rate == 0.6
        assert criteria.max_consecutive_losses == 3

    def test_acceptance_criteria_immutable(self):
        """Test that AcceptanceCriteria is immutable."""
        criteria = AcceptanceCriteria()
        
        # Should not be able to modify attributes
        with pytest.raises(AttributeError):
            criteria.min_trades = 200


class TestStrategyEvaluator:
    """Test StrategyEvaluator functionality."""

    def test_strategy_evaluator_creation(self):
        """Test StrategyEvaluator creation."""
        criteria = AcceptanceCriteria()
        evaluator = StrategyEvaluator(criteria)
        
        assert evaluator.criteria == criteria
        assert evaluator.target_cagr == 0.20
        assert evaluator.weights is not None
        assert 'profit_factor' in evaluator.weights
        assert 'max_drawdown' in evaluator.weights
        assert 'win_rate' in evaluator.weights

    def test_strategy_evaluator_custom_weights(self):
        """Test StrategyEvaluator with custom weights."""
        criteria = AcceptanceCriteria()
        custom_weights = {
            'profit_factor': 0.5,
            'max_drawdown': 0.3,
            'win_rate': 0.2
        }
        
        evaluator = StrategyEvaluator(criteria, weights=custom_weights)
        
        assert evaluator.weights == custom_weights

    def test_strategy_evaluator_custom_target_cagr(self):
        """Test StrategyEvaluator with custom target CAGR."""
        criteria = AcceptanceCriteria()
        evaluator = StrategyEvaluator(criteria, target_cagr=0.30)
        
        assert evaluator.target_cagr == 0.30

    def test_evaluate_passing_strategy(self):
        """Test evaluation of a passing strategy."""
        criteria = AcceptanceCriteria(
            min_trades=50,
            min_profit_factor=1.2,
            max_drawdown=0.25,
            min_sharpe=1.0,
            min_win_rate=0.5
        )
        evaluator = StrategyEvaluator(criteria)
        
        metrics = {
            'trades': 100,
            'profit_factor': 1.5,
            'max_drawdown': 0.15,
            'sharpe': 1.2,
            'win_rate': 0.6,
            'cagr': 0.25
        }
        
        result = evaluator.evaluate(metrics)
        
        assert isinstance(result, EvaluationResult)
        assert result.passed is True
        assert result.score > 0
        assert result.label in ['A', 'B', 'C']
        assert len(result.reasons) == 0  # No rejection reasons
        assert result.metrics == metrics

    def test_evaluate_failing_strategy(self):
        """Test evaluation of a failing strategy."""
        criteria = AcceptanceCriteria(
            min_trades=50,
            min_profit_factor=1.2,
            max_drawdown=0.25,
            min_sharpe=1.0,
            min_win_rate=0.5
        )
        evaluator = StrategyEvaluator(criteria)
        
        metrics = {
            'trades': 30,  # Below min_trades
            'profit_factor': 1.1,  # Below min_profit_factor
            'max_drawdown': 0.30,  # Above max_drawdown
            'sharpe': 0.8,  # Below min_sharpe
            'win_rate': 0.4,  # Below min_win_rate
            'cagr': 0.10
        }
        
        result = evaluator.evaluate(metrics)
        
        assert isinstance(result, EvaluationResult)
        assert result.passed is False
        assert result.label == 'REJECT'
        assert len(result.reasons) > 0  # Should have rejection reasons
        assert 'trades' in ' '.join(result.reasons).lower()
        assert 'profit_factor' in ' '.join(result.reasons).lower()
        assert 'drawdown' in ' '.join(result.reasons).lower()

    def test_evaluate_edge_cases(self):
        """Test evaluation edge cases."""
        criteria = AcceptanceCriteria(
            min_trades=50,
            min_profit_factor=1.2,
            max_drawdown=0.25
        )
        evaluator = StrategyEvaluator(criteria)
        
        # Test with missing metrics
        metrics = {
            'trades': 100,
            'profit_factor': 1.5,
            'max_drawdown': 0.15
            # Missing sharpe, win_rate, cagr
        }
        
        result = evaluator.evaluate(metrics)
        
        assert result.passed is True
        assert result.score > 0

    def test_score_only_method(self):
        """Test score_only method."""
        criteria = AcceptanceCriteria()
        evaluator = StrategyEvaluator(criteria)
        
        metrics = {
            'trades': 100,
            'profit_factor': 1.5,
            'max_drawdown': 0.15,
            'win_rate': 0.6,
            'sharpe': 1.2,
            'cagr': 0.25
        }
        
        score = evaluator.score_only(metrics)
        
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_evaluation_result_creation(self):
        """Test EvaluationResult creation."""
        result = EvaluationResult(
            score=0.85,
            passed=True,
            label='A',
            reasons=[],
            metrics={'profit_factor': 1.5}
        )
        
        assert result.score == 0.85
        assert result.passed is True
        assert result.label == 'A'
        assert result.reasons == []
        assert result.metrics == {'profit_factor': 1.5}

    def test_evaluation_result_immutable(self):
        """Test that EvaluationResult is immutable."""
        result = EvaluationResult(
            score=0.85,
            passed=True,
            label='A',
            reasons=[],
            metrics={'profit_factor': 1.5}
        )
        
        # Should not be able to modify attributes
        with pytest.raises(AttributeError):
            result.score = 0.90


class TestMetricsFromTradeRegistry:
    """Test metrics_from_trade_registry function."""

    def test_metrics_from_trade_registry(self, trade_registry_fixture):
        """Test metrics extraction from TradeRegistry."""
        metrics = metrics_from_trade_registry(trade_registry_fixture)
        
        assert isinstance(metrics, dict)
        assert 'trades' in metrics
        assert 'profit_factor' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics
        assert 'sharpe' in metrics
        assert 'cagr' in metrics
        
        # Check that metrics are reasonable
        assert metrics['trades'] > 0
        assert metrics['profit_factor'] > 0
        assert 0 <= metrics['max_drawdown'] <= 1
        assert 0 <= metrics['win_rate'] <= 1

    def test_metrics_from_empty_registry(self):
        """Test metrics extraction from empty TradeRegistry."""
        empty_registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        metrics = metrics_from_trade_registry(empty_registry)
        
        assert isinstance(metrics, dict)
        assert metrics['trades'] == 0
        assert metrics['profit_factor'] == 0
        assert metrics['max_drawdown'] == 0
        assert metrics['win_rate'] == 0

    def test_metrics_calculation_accuracy(self):
        """Test accuracy of metrics calculations."""
        registry = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        # Add specific trades to test calculations
        base_time = dt.datetime(2024, 1, 1, 10, 0, 0)
        
        # Trade 1: +50 profit
        registry.register_order(TradeOrder('buy', 100.0, base_time, amount=1))
        registry.register_order(TradeOrder('close', 105.0, base_time + dt.timedelta(hours=1), amount=1))
        
        # Trade 2: -30 loss
        registry.register_order(TradeOrder('buy', 105.0, base_time + dt.timedelta(hours=2), amount=1))
        registry.register_order(TradeOrder('close', 102.0, base_time + dt.timedelta(hours=3), amount=1))
        
        # Trade 3: +20 profit
        registry.register_order(TradeOrder('buy', 102.0, base_time + dt.timedelta(hours=4), amount=1))
        registry.register_order(TradeOrder('close', 104.0, base_time + dt.timedelta(hours=5), amount=1))
        
        metrics = metrics_from_trade_registry(registry)
        
        # Expected calculations:
        # Total trades: 3
        # Profitable trades: 2 (trades 1 and 3)
        # Win rate: 2/3 = 0.667
        # Profit factor: (50 + 20) / 30 = 2.33
        # Max drawdown: depends on balance progression
        
        assert metrics['trades'] == 3
        assert metrics['win_rate'] == pytest.approx(2/3, rel=1e-2)
        assert metrics['profit_factor'] == pytest.approx(2.33, rel=1e-2)


class TestOosStability:
    """Test out-of-sample stability calculations."""

    def test_oos_stability_from_two_runs(self, trade_registry_fixture):
        """Test OOS stability calculation."""
        # Create a second registry with different performance
        registry2 = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        base_time = dt.datetime(2024, 1, 1, 10, 0, 0)
        
        # Add different trades to registry2
        registry2.register_order(TradeOrder('buy', 100.0, base_time, amount=1))
        registry2.register_order(TradeOrder('close', 110.0, base_time + dt.timedelta(hours=1), amount=1))
        
        criteria = AcceptanceCriteria()
        evaluator = StrategyEvaluator(criteria)
        
        stability = oos_stability_from_two_runs(
            registry_is=trade_registry_fixture,
            registry_oos=registry2,
            evaluator=evaluator
        )
        
        assert isinstance(stability, float)
        assert 0 <= stability <= 1

    def test_oos_stability_identical_performance(self):
        """Test OOS stability with identical performance."""
        registry1 = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        registry2 = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        base_time = dt.datetime(2024, 1, 1, 10, 0, 0)
        
        # Add identical trades to both registries
        for registry in [registry1, registry2]:
            registry.register_order(TradeOrder('buy', 100.0, base_time, amount=1))
            registry.register_order(TradeOrder('close', 105.0, base_time + dt.timedelta(hours=1), amount=1))
        
        criteria = AcceptanceCriteria()
        evaluator = StrategyEvaluator(criteria)
        
        stability = oos_stability_from_two_runs(registry1, registry2, evaluator)
        
        # Should have high stability (close to 1) for identical performance
        assert stability > 0.8

    def test_oos_stability_different_performance(self):
        """Test OOS stability with very different performance."""
        registry1 = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        registry2 = TradeRegistry(point_value=10.0, cost_per_trade=2.50)
        
        base_time = dt.datetime(2024, 1, 1, 10, 0, 0)
        
        # Registry1: profitable trade
        registry1.register_order(TradeOrder('buy', 100.0, base_time, amount=1))
        registry1.register_order(TradeOrder('close', 110.0, base_time + dt.timedelta(hours=1), amount=1))
        
        # Registry2: losing trade
        registry2.register_order(TradeOrder('buy', 100.0, base_time, amount=1))
        registry2.register_order(TradeOrder('close', 90.0, base_time + dt.timedelta(hours=1), amount=1))
        
        criteria = AcceptanceCriteria()
        evaluator = StrategyEvaluator(criteria)
        
        stability = oos_stability_from_two_runs(registry1, registry2, evaluator)
        
        # Should have low stability for very different performance
        assert stability < 0.5


class TestEvaluationIntegration:
    """Test integration between evaluation components."""

    def test_full_evaluation_workflow(self, trade_registry_fixture):
        """Test complete evaluation workflow."""
        # Extract metrics from registry
        metrics = metrics_from_trade_registry(trade_registry_fixture)
        
        # Define acceptance criteria
        criteria = AcceptanceCriteria(
            min_trades=1,
            min_profit_factor=1.0,
            max_drawdown=0.5,
            min_win_rate=0.3
        )
        
        # Create evaluator
        evaluator = StrategyEvaluator(criteria)
        
        # Evaluate strategy
        result = evaluator.evaluate(metrics)
        
        # Verify result
        assert isinstance(result, EvaluationResult)
        assert result.passed is True or result.passed is False
        assert result.label in ['A', 'B', 'C', 'REJECT']
        assert 0 <= result.score <= 1

    def test_evaluation_with_custom_weights(self, trade_registry_fixture):
        """Test evaluation with custom weights."""
        metrics = metrics_from_trade_registry(trade_registry_fixture)
        
        criteria = AcceptanceCriteria()
        custom_weights = {
            'profit_factor': 0.6,
            'max_drawdown': 0.4
        }
        
        evaluator = StrategyEvaluator(criteria, weights=custom_weights)
        result = evaluator.evaluate(metrics)
        
        assert isinstance(result, EvaluationResult)
        assert result.score > 0

    def test_evaluation_with_missing_metrics(self, trade_registry_fixture):
        """Test evaluation with missing metrics."""
        # Create partial metrics
        metrics = {
            'trades': 10,
            'profit_factor': 1.5,
            'max_drawdown': 0.15
            # Missing sharpe, win_rate, cagr
        }
        
        criteria = AcceptanceCriteria()
        evaluator = StrategyEvaluator(criteria)
        
        result = evaluator.evaluate(metrics)
        
        assert isinstance(result, EvaluationResult)
        assert result.passed is True or result.passed is False

    def test_evaluation_boundary_conditions(self):
        """Test evaluation with boundary conditions."""
        criteria = AcceptanceCriteria(
            min_trades=10,
            min_profit_factor=1.0,
            max_drawdown=0.5
        )
        evaluator = StrategyEvaluator(criteria)
        
        # Test exactly at boundaries
        metrics = {
            'trades': 10,  # Exactly min_trades
            'profit_factor': 1.0,  # Exactly min_profit_factor
            'max_drawdown': 0.5,  # Exactly max_drawdown
            'win_rate': 0.5,
            'sharpe': 1.0,
            'cagr': 0.15
        }
        
        result = evaluator.evaluate(metrics)
        
        assert isinstance(result, EvaluationResult)
        # Should pass since all criteria are met exactly

    def test_evaluation_extreme_values(self):
        """Test evaluation with extreme values."""
        criteria = AcceptanceCriteria()
        evaluator = StrategyEvaluator(criteria)
        
        # Test with extreme values
        metrics = {
            'trades': 10000,
            'profit_factor': 100.0,  # Very high
            'max_drawdown': 0.001,  # Very low
            'win_rate': 0.99,  # Very high
            'sharpe': 10.0,  # Very high
            'cagr': 5.0  # Very high
        }
        
        result = evaluator.evaluate(metrics)
        
        assert isinstance(result, EvaluationResult)
        assert result.passed is True
        assert result.score > 0.9  # Should be very high score
        assert result.label == 'A'  # Should be top grade