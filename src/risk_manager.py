"""
Risk Manager - Implement risk management and position sizing for trading signals
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RiskMetrics:
    """Class to hold risk metrics for a trading signal."""
    
    def __init__(self):
        self.max_position_size = 0.0
        self.recommended_position_size = 0.0
        self.risk_reward_ratio = 0.0
        self.max_loss_amount = 0.0
        self.probability_of_success = 0.0
        self.risk_score = 0.0  # 0-10 scale, 10 being highest risk


def calculate_position_size(signal, risk_tolerance: float = 0.02, 
                          max_position_size: float = 0.1, 
                          portfolio_value: float = 100000) -> float:
    """
    Calculate appropriate position size based on risk tolerance.
    
    Args:
        signal: TradingSignal object
        risk_tolerance: Maximum risk per trade (e.g., 0.02 = 2%)
        max_position_size: Maximum position as % of portfolio (e.g., 0.1 = 10%)
        portfolio_value: Total portfolio value in dollars
    
    Returns:
        Position size as percentage of portfolio (0.0 to 1.0)
    """
    try:
        # Base position size based on confidence
        confidence_factor = signal.confidence
        base_position = confidence_factor * max_position_size
        
        # Adjust for risk tolerance
        if signal.stop_loss and signal.price_target:
            # Calculate risk/reward ratio
            if signal.action == 'buy':
                risk_per_share = abs(signal.price_target - signal.stop_loss) if signal.price_target > signal.stop_loss else 0.05 * signal.price_target
                reward_per_share = abs(signal.price_target - signal.stop_loss) if signal.price_target > signal.stop_loss else 0.1 * signal.price_target
            else:  # sell
                risk_per_share = abs(signal.stop_loss - signal.price_target) if signal.stop_loss > signal.price_target else 0.05 * signal.price_target
                reward_per_share = abs(signal.stop_loss - signal.price_target) if signal.stop_loss > signal.price_target else 0.1 * signal.price_target
            
            if risk_per_share > 0:
                risk_reward_ratio = reward_per_share / risk_per_share
                
                # Adjust position size based on risk/reward
                if risk_reward_ratio >= 2.0:  # Good risk/reward
                    risk_adjusted_position = base_position * 1.2
                elif risk_reward_ratio >= 1.5:
                    risk_adjusted_position = base_position * 1.0
                elif risk_reward_ratio >= 1.0:
                    risk_adjusted_position = base_position * 0.8
                else:
                    risk_adjusted_position = base_position * 0.5
            else:
                risk_adjusted_position = base_position * 0.7  # Reduce if no clear risk/reward
        else:
            # No stop loss/target, use conservative sizing
            risk_adjusted_position = base_position * 0.6
        
        # Apply risk tolerance cap
        max_risk_position = risk_tolerance / 0.05  # Assume 5% max loss per position
        
        # Final position size
        final_position = min(risk_adjusted_position, max_risk_position, max_position_size)
        
        logger.debug(f"Position sizing for {signal.symbol}: base={base_position:.3f}, "
                    f"risk_adjusted={risk_adjusted_position:.3f}, final={final_position:.3f}")
        
        return max(final_position, 0.001)  # Minimum 0.1% position
    
    except Exception as e:
        logger.error(f"Error calculating position size: {e}")
        return max_position_size * 0.5  # Conservative fallback


def apply_risk_controls(signal, position_size: float, config: Dict) -> Optional[Dict]:
    """
    Apply comprehensive risk controls to a trading signal.
    
    Args:
        signal: TradingSignal object
        position_size: Calculated position size
        config: Risk management configuration
    
    Returns:
        Risk-controlled signal dictionary or None if rejected
    """
    try:
        risk_metrics = RiskMetrics()
        
        # Calculate risk metrics
        risk_metrics.recommended_position_size = position_size
        risk_metrics.max_position_size = config.get('max_position_size', 0.1)
        
        # Risk Score Calculation (0-10 scale, 10 = highest risk)
        risk_score = _calculate_risk_score(signal, config)
        risk_metrics.risk_score = risk_score
        
        # Apply risk filters
        risk_checks = _perform_risk_checks(signal, position_size, risk_metrics, config)
        
        if not risk_checks['passed']:
            logger.info(f"Signal for {signal.symbol} rejected: {risk_checks['reason']}")
            return None
        
        # Calculate final parameters
        final_position_size = min(position_size, risk_metrics.max_position_size)
        
        # Add risk-adjusted stop loss if not present
        if not signal.stop_loss and signal.price_target:
            signal.stop_loss = _calculate_dynamic_stop_loss(signal)
        
        # Create risk-managed signal
        risk_managed_signal = {
            'symbol': signal.symbol,
            'action': signal.action,
            'confidence': signal.confidence,
            'position_size': final_position_size,
            'price_target': signal.price_target,
            'stop_loss': signal.stop_loss,
            'reasoning': signal.reasoning,
            'risk_score': risk_score,
            'risk_metrics': risk_metrics.__dict__,
            'risk_controls_applied': True,
            'timestamp': signal.timestamp.isoformat(),
            'source': signal.source,
            'metadata': getattr(signal, 'metadata', {})
        }
        
        logger.info(f"Risk controls applied to {signal.symbol}: "
                   f"position={final_position_size:.3f}, risk_score={risk_score:.1f}")
        
        return risk_managed_signal
    
    except Exception as e:
        logger.error(f"Error applying risk controls to {signal.symbol}: {e}")
        return None


def _calculate_risk_score(signal, config: Dict) -> float:
    """Calculate a risk score for the signal (0-10, 10 = highest risk)."""
    try:
        risk_factors = []
        
        # Confidence factor (lower confidence = higher risk)
        confidence_risk = (1.0 - signal.confidence) * 3.0
        risk_factors.append(confidence_risk)
        
        # Volatility proxy (based on stop loss distance)
        if signal.stop_loss and signal.price_target:
            if signal.action == 'buy' and signal.price_target:
                volatility_risk = abs(signal.stop_loss - signal.price_target) / signal.price_target * 10
            elif signal.action == 'sell' and signal.price_target:
                volatility_risk = abs(signal.stop_loss - signal.price_target) / signal.price_target * 10
            else:
                volatility_risk = 2.0  # Medium risk if no clear targets
        else:
            volatility_risk = 4.0  # Higher risk if no stop loss
        
        risk_factors.append(min(volatility_risk, 4.0))  # Cap at 4.0
        
        # Signal strength factor
        trading_insights = getattr(signal, 'metadata', {})
        signal_strength = trading_insights.get('signal_strength', 0.5)
        strength_risk = (1.0 - signal_strength) * 2.0
        risk_factors.append(strength_risk)
        
        # Market conditions factor (placeholder - could integrate market volatility data)
        market_risk = 1.0  # Neutral market risk
        risk_factors.append(market_risk)
        
        # Calculate weighted average
        weights = [0.3, 0.4, 0.2, 0.1]  # Confidence, volatility, strength, market
        total_risk = sum(factor * weight for factor, weight in zip(risk_factors, weights))
        
        return min(max(total_risk, 0.0), 10.0)  # Clamp between 0-10
    
    except Exception as e:
        logger.error(f"Error calculating risk score: {e}")
        return 5.0  # Medium risk as fallback


def _perform_risk_checks(signal, position_size: float, risk_metrics: RiskMetrics, config: Dict) -> Dict:
    """Perform comprehensive risk checks on the signal."""
    try:
        checks = {
            'passed': True,
            'reason': '',
            'warnings': []
        }
        
        # Check 1: Maximum position size
        if position_size > config.get('max_position_size', 0.1):
            checks['passed'] = False
            checks['reason'] = f"Position size {position_size:.3f} exceeds maximum {config.get('max_position_size', 0.1)}"
            return checks
        
        # Check 2: Minimum confidence threshold
        min_confidence = config.get('confidence_threshold', 0.5)
        if signal.confidence < min_confidence:
            checks['passed'] = False
            checks['reason'] = f"Confidence {signal.confidence:.3f} below minimum {min_confidence}"
            return checks
        
        # Check 3: Risk score threshold
        max_risk_score = config.get('max_risk_score', 8.0)
        if risk_metrics.risk_score > max_risk_score:
            checks['passed'] = False
            checks['reason'] = f"Risk score {risk_metrics.risk_score:.1f} exceeds maximum {max_risk_score}"
            return checks
        
        # Check 4: Daily trading limits
        max_daily_trades = config.get('max_daily_trades', 10)
        # Note: In a real implementation, you'd check against a database of today's trades
        # For now, we'll assume this passes
        
        # Check 5: Sector/Symbol concentration
        # Note: In a real implementation, you'd check current portfolio composition
        
        # Warning checks (don't block but flag for attention)
        if not signal.stop_loss:
            checks['warnings'].append("No stop loss defined")
        
        if not signal.price_target:
            checks['warnings'].append("No price target defined")
        
        if risk_metrics.risk_score > 6.0:
            checks['warnings'].append(f"High risk score: {risk_metrics.risk_score:.1f}")
        
        return checks
    
    except Exception as e:
        logger.error(f"Error performing risk checks: {e}")
        return {
            'passed': False,
            'reason': f"Risk check error: {e}",
            'warnings': []
        }


def _calculate_dynamic_stop_loss(signal) -> Optional[float]:
    """Calculate a dynamic stop loss if none is provided."""
    try:
        if not signal.price_target:
            return None
        
        # Use ATR-like approach (simplified)
        if signal.action == 'buy':
            # Stop loss below current/target price
            stop_loss = signal.price_target * 0.95  # 5% below target
        else:  # sell
            # Stop loss above current/target price
            stop_loss = signal.price_target * 1.05  # 5% above target
        
        return stop_loss
    
    except Exception as e:
        logger.error(f"Error calculating dynamic stop loss: {e}")
        return None


def get_portfolio_risk_metrics(signals: List[Dict], portfolio_value: float = 100000) -> Dict:
    """
    Calculate portfolio-level risk metrics for a list of signals.
    
    Args:
        signals: List of risk-managed signal dictionaries
        portfolio_value: Total portfolio value
    
    Returns:
        Portfolio risk metrics dictionary
    """
    try:
        if not signals:
            return {
                'total_exposure': 0.0,
                'number_of_positions': 0,
                'avg_risk_score': 0.0,
                'max_portfolio_risk': 0.0,
                'diversification_score': 0.0
            }
        
        # Calculate total exposure
        total_exposure = sum(signal.get('position_size', 0.0) for signal in signals)
        
        # Calculate average risk score
        risk_scores = [signal.get('risk_score', 5.0) for signal in signals]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        
        # Calculate maximum portfolio risk (sum of all potential losses)
        max_portfolio_risk = 0.0
        for signal in signals:
            position_size = signal.get('position_size', 0.0)
            if signal.get('stop_loss') and signal.get('price_target'):
                max_loss_pct = abs(signal['stop_loss'] - signal['price_target']) / signal['price_target']
                max_portfolio_risk += position_size * max_loss_pct
            else:
                max_portfolio_risk += position_size * 0.05  # Assume 5% max loss
        
        # Simple diversification score (more positions = better diversification)
        num_positions = len(signals)
        diversification_score = min(num_positions / 5.0, 1.0)  # Perfect at 5+ positions
        
        # Calculate position concentration
        symbols = [signal.get('symbol', '') for signal in signals]
        unique_symbols = len(set(symbols))
        concentration_ratio = unique_symbols / len(symbols) if symbols else 0
        
        return {
            'total_exposure': total_exposure,
            'number_of_positions': num_positions,
            'unique_symbols': unique_symbols,
            'avg_risk_score': avg_risk_score,
            'max_portfolio_risk': max_portfolio_risk,
            'diversification_score': diversification_score,
            'concentration_ratio': concentration_ratio,
            'estimated_portfolio_var': max_portfolio_risk * 0.6,  # Simplified VaR
            'risk_warnings': _generate_portfolio_warnings(total_exposure, max_portfolio_risk, avg_risk_score)
        }
    
    except Exception as e:
        logger.error(f"Error calculating portfolio risk metrics: {e}")
        return {'error': str(e)}


def _generate_portfolio_warnings(total_exposure: float, max_risk: float, avg_risk: float) -> List[str]:
    """Generate portfolio-level risk warnings."""
    warnings = []
    
    if total_exposure > 0.8:
        warnings.append(f"High portfolio exposure: {total_exposure:.1%}")
    
    if max_risk > 0.2:
        warnings.append(f"High portfolio risk: {max_risk:.1%} maximum potential loss")
    
    if avg_risk > 7.0:
        warnings.append(f"High average risk score: {avg_risk:.1f}/10")
    
    return warnings


def validate_risk_limits(signals: List[Dict], config: Dict) -> Tuple[List[Dict], List[str]]:
    """
    Final validation of signals against portfolio-level risk limits.
    
    Returns:
        Tuple of (approved_signals, rejection_reasons)
    """
    try:
        portfolio_metrics = get_portfolio_risk_metrics(signals)
        approved_signals = []
        rejections = []
        
        # Portfolio-level checks
        max_portfolio_exposure = config.get('max_portfolio_exposure', 0.8)
        max_portfolio_risk = config.get('max_portfolio_risk', 0.15)
        
        current_exposure = 0.0
        current_risk = 0.0
        
        # Sort signals by risk score (approve lowest risk first)
        sorted_signals = sorted(signals, key=lambda x: x.get('risk_score', 5.0))
        
        for signal in sorted_signals:
            position_size = signal.get('position_size', 0.0)
            signal_risk = position_size * 0.05  # Simplified risk calculation
            
            # Check if adding this signal would exceed limits
            if current_exposure + position_size <= max_portfolio_exposure:
                if current_risk + signal_risk <= max_portfolio_risk:
                    approved_signals.append(signal)
                    current_exposure += position_size
                    current_risk += signal_risk
                else:
                    rejections.append(f"{signal.get('symbol', 'Unknown')}: Would exceed portfolio risk limit")
            else:
                rejections.append(f"{signal.get('symbol', 'Unknown')}: Would exceed portfolio exposure limit")
        
        logger.info(f"Portfolio validation: {len(approved_signals)} approved, {len(rejections)} rejected")
        
        return approved_signals, rejections
    
    except Exception as e:
        logger.error(f"Error validating risk limits: {e}")
        return signals, []


if __name__ == "__main__":
    # Test the risk manager
    print("Testing Risk Manager...")
    
    # Mock signal for testing
    class MockSignal:
        def __init__(self):
            self.symbol = 'AAPL'
            self.action = 'buy'
            self.confidence = 0.75
            self.price_target = 150.0
            self.stop_loss = 142.5
            self.reasoning = "Strong bullish indicators"
            self.timestamp = datetime.now()
            self.metadata = {'signal_strength': 0.8}
    
    mock_signal = MockSignal()
    
    # Test position sizing
    print("\n1. Position Sizing:")
    position_size = calculate_position_size(mock_signal, risk_tolerance=0.02, max_position_size=0.1)
    print(f"Calculated position size: {position_size:.3f} ({position_size*100:.1f}%)")
    
    # Test risk controls
    print("\n2. Risk Controls:")
    config = {
        'max_position_size': 0.1,
        'confidence_threshold': 0.6,
        'max_risk_score': 8.0,
        'max_daily_trades': 10
    }
    
    risk_managed_signal = apply_risk_controls(mock_signal, position_size, config)
    
    if risk_managed_signal:
        print(f"Signal approved:")
        print(f"  Symbol: {risk_managed_signal['symbol']}")
        print(f"  Position size: {risk_managed_signal['position_size']:.3f}")
        print(f"  Risk score: {risk_managed_signal['risk_score']:.1f}/10")
    else:
        print("Signal rejected by risk controls")
    
    # Test portfolio metrics
    print("\n3. Portfolio Metrics:")
    if risk_managed_signal:
        portfolio_metrics = get_portfolio_risk_metrics([risk_managed_signal])
        print(f"Portfolio exposure: {portfolio_metrics['total_exposure']:.1%}")
        print(f"Max portfolio risk: {portfolio_metrics['max_portfolio_risk']:.1%}")
        print(f"Average risk score: {portfolio_metrics['avg_risk_score']:.1f}")
        
        if portfolio_metrics['risk_warnings']:
            print(f"Warnings: {portfolio_metrics['risk_warnings']}")
    
    print("\nRisk Manager test completed!")
