"""
Signal Engine - Convert NLP analysis into actionable trading signals
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class TradingSignal:
    """Class to represent a trading signal."""
    
    def __init__(self, symbol: str, action: str, confidence: float, 
                 price_target: Optional[float] = None, stop_loss: Optional[float] = None,
                 source: str = "NLP Analysis", reasoning: str = "", **kwargs):
        self.symbol = symbol
        self.action = action  # 'buy', 'sell', 'hold'
        self.confidence = confidence  # 0.0 to 1.0
        self.price_target = price_target
        self.stop_loss = stop_loss
        self.source = source
        self.reasoning = reasoning
        self.timestamp = datetime.now()
        self.metadata = kwargs
    
    def to_dict(self) -> Dict:
        """Convert signal to dictionary format."""
        return {
            'symbol': self.symbol,
            'action': self.action,
            'confidence': self.confidence,
            'price_target': self.price_target,
            'stop_loss': self.stop_loss,
            'source': self.source,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


def generate_trading_signals(analysis_result: Dict) -> List[TradingSignal]:
    """
    Generate actionable trading signals from NLP analysis results.
    
    Args:
        analysis_result: Dictionary containing NLP analysis (sentiment, trading_insights, summary)
    
    Returns:
        List of TradingSignal objects
    """
    try:
        signals = []
        
        # Extract components
        sentiment = analysis_result.get('sentiment', {})
        trading_insights = analysis_result.get('trading_insights', {})
        summary = analysis_result.get('summary', '')
        
        # Get potential tickers from trading insights
        tickers = trading_insights.get('potential_tickers', [])
        
        # If no specific tickers, generate market-wide signal
        if not tickers:
            tickers = ['SPY']  # Default to S&P 500 ETF
        
        for ticker in tickers[:5]:  # Limit to 5 tickers per analysis
            signal = _create_signal_for_ticker(ticker, sentiment, trading_insights, summary)
            if signal and signal.confidence > 0.3:  # Only include signals with reasonable confidence
                signals.append(signal)
        
        logger.info(f"Generated {len(signals)} trading signals from analysis")
        return signals
    
    except Exception as e:
        logger.error(f"Error generating trading signals: {e}")
        return []


def _create_signal_for_ticker(ticker: str, sentiment: Dict, trading_insights: Dict, summary: str) -> Optional[TradingSignal]:
    """Create a trading signal for a specific ticker."""
    try:
        # Calculate base confidence from sentiment and trading insights
        sentiment_score = _calculate_sentiment_score(sentiment)
        trading_score = trading_insights.get('signal_strength', 0.0)
        
        # Combine scores with weights
        base_confidence = (sentiment_score * 0.4 + trading_score * 0.6)
        
        # Determine action based on combined analysis
        signal_direction = trading_insights.get('signal_direction', 'neutral')
        
        if signal_direction == 'bullish' and base_confidence > 0.5:
            action = 'buy'
            confidence = min(base_confidence * 1.1, 1.0)  # Slight boost for clear bullish signals
        elif signal_direction == 'bearish' and base_confidence > 0.5:
            action = 'sell'
            confidence = min(base_confidence * 1.1, 1.0)  # Slight boost for clear bearish signals
        else:
            action = 'hold'
            confidence = base_confidence * 0.8  # Lower confidence for neutral signals
        
        # Generate reasoning
        reasoning = _generate_reasoning(sentiment, trading_insights, signal_direction)
        
        # Create price targets (simplified approach)
        price_target = None
        stop_loss = None
        
        if trading_insights.get('price_mentions'):
            try:
                # Extract numeric value from price mention
                price_str = trading_insights['price_mentions'][0].replace('$', '')
                base_price = float(price_str)
                
                if action == 'buy':
                    price_target = base_price * 1.1  # 10% upside target
                    stop_loss = base_price * 0.95   # 5% stop loss
                elif action == 'sell':
                    price_target = base_price * 0.9  # 10% downside target
                    stop_loss = base_price * 1.05   # 5% stop loss
            except (ValueError, IndexError):
                pass  # Keep None values if parsing fails
        
        # Create signal
        signal = TradingSignal(
            symbol=ticker,
            action=action,
            confidence=confidence,
            price_target=price_target,
            stop_loss=stop_loss,
            source="NLP Analysis",
            reasoning=reasoning,
            bullish_indicators=trading_insights.get('bullish_indicators', 0),
            bearish_indicators=trading_insights.get('bearish_indicators', 0),
            sentiment_overall=sentiment.get('overall_sentiment', 'neutral'),
            market_indicators=trading_insights.get('market_indicators_found', [])
        )
        
        return signal
    
    except Exception as e:
        logger.error(f"Error creating signal for {ticker}: {e}")
        return None


def _calculate_sentiment_score(sentiment: Dict) -> float:
    """Calculate a single sentiment score from sentiment analysis results."""
    try:
        positive = sentiment.get('positive', 0.0)
        negative = sentiment.get('negative', 0.0)
        neutral = sentiment.get('neutral', 0.0)
        
        # Calculate net sentiment (positive - negative, normalized)
        if positive + negative > 0:
            net_sentiment = (positive - negative) / (positive + negative)
            # Convert to 0-1 scale where 0.5 is neutral
            return (net_sentiment + 1.0) / 2.0
        else:
            return 0.5  # Neutral if no sentiment detected
    
    except Exception as e:
        logger.error(f"Error calculating sentiment score: {e}")
        return 0.5


def _generate_reasoning(sentiment: Dict, trading_insights: Dict, signal_direction: str) -> str:
    """Generate human-readable reasoning for the trading signal."""
    try:
        reasoning_parts = []
        
        # Add sentiment reasoning
        overall_sentiment = sentiment.get('overall_sentiment', 'neutral')
        reasoning_parts.append(f"Sentiment analysis indicates {overall_sentiment} market outlook")
        
        # Add trading insights reasoning
        bullish_count = trading_insights.get('bullish_indicators', 0)
        bearish_count = trading_insights.get('bearish_indicators', 0)
        
        if bullish_count > bearish_count:
            reasoning_parts.append(f"{bullish_count} bullish indicators vs {bearish_count} bearish indicators")
        elif bearish_count > bullish_count:
            reasoning_parts.append(f"{bearish_count} bearish indicators vs {bullish_count} bullish indicators")
        else:
            reasoning_parts.append("Mixed technical indicators")
        
        # Add market indicators if found
        market_indicators = trading_insights.get('market_indicators_found', [])
        if market_indicators:
            reasoning_parts.append(f"Key factors mentioned: {', '.join(market_indicators[:3])}")
        
        # Add confidence qualifier
        confidence = trading_insights.get('confidence', 0.0)
        if confidence > 0.7:
            reasoning_parts.append("High confidence signal")
        elif confidence > 0.5:
            reasoning_parts.append("Moderate confidence signal")
        else:
            reasoning_parts.append("Low confidence signal")
        
        return ". ".join(reasoning_parts) + "."
    
    except Exception as e:
        logger.error(f"Error generating reasoning: {e}")
        return "Signal generated from NLP analysis."


def filter_signals_by_confidence(signals: List[TradingSignal], threshold: float = 0.6) -> List[TradingSignal]:
    """
    Filter trading signals by confidence threshold.
    
    Args:
        signals: List of TradingSignal objects
        threshold: Minimum confidence threshold (0.0 to 1.0)
    
    Returns:
        Filtered list of high-confidence signals
    """
    try:
        filtered_signals = [signal for signal in signals if signal.confidence >= threshold]
        
        logger.info(f"Filtered {len(signals)} signals to {len(filtered_signals)} high-confidence signals (threshold: {threshold})")
        
        # Sort by confidence (highest first)
        filtered_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return filtered_signals
    
    except Exception as e:
        logger.error(f"Error filtering signals: {e}")
        return []


def consolidate_signals(signals: List[TradingSignal]) -> List[TradingSignal]:
    """
    Consolidate multiple signals for the same symbol.
    
    Args:
        signals: List of TradingSignal objects
    
    Returns:
        List of consolidated signals (one per symbol)
    """
    try:
        symbol_signals = {}
        
        # Group signals by symbol
        for signal in signals:
            symbol = signal.symbol
            if symbol not in symbol_signals:
                symbol_signals[symbol] = []
            symbol_signals[symbol].append(signal)
        
        # Consolidate signals for each symbol
        consolidated = []
        for symbol, symbol_group in symbol_signals.items():
            if len(symbol_group) == 1:
                consolidated.append(symbol_group[0])
            else:
                # Combine multiple signals for the same symbol
                combined_signal = _combine_signals(symbol_group)
                consolidated.append(combined_signal)
        
        logger.info(f"Consolidated {len(signals)} signals into {len(consolidated)} unique symbol signals")
        return consolidated
    
    except Exception as e:
        logger.error(f"Error consolidating signals: {e}")
        return signals


def _combine_signals(signals: List[TradingSignal]) -> TradingSignal:
    """Combine multiple signals for the same symbol into one."""
    try:
        symbol = signals[0].symbol
        
        # Calculate weighted average confidence
        total_confidence = sum(s.confidence for s in signals)
        avg_confidence = total_confidence / len(signals)
        
        # Determine dominant action
        actions = [s.action for s in signals]
        action_counts = {action: actions.count(action) for action in set(actions)}
        dominant_action = max(action_counts, key=action_counts.get)
        
        # Combine reasoning
        reasoning_parts = [s.reasoning for s in signals if s.reasoning]
        combined_reasoning = " | ".join(reasoning_parts[:2])  # Limit to avoid too long text
        
        # Use highest confidence signal's targets as base
        highest_conf_signal = max(signals, key=lambda x: x.confidence)
        
        return TradingSignal(
            symbol=symbol,
            action=dominant_action,
            confidence=avg_confidence,
            price_target=highest_conf_signal.price_target,
            stop_loss=highest_conf_signal.stop_loss,
            source="Combined NLP Analysis",
            reasoning=f"Combined from {len(signals)} signals: {combined_reasoning}",
            signal_count=len(signals),
            original_confidences=[s.confidence for s in signals]
        )
    
    except Exception as e:
        logger.error(f"Error combining signals: {e}")
        return signals[0]  # Return first signal as fallback


def get_signal_summary(signals: List[TradingSignal]) -> Dict:
    """Get a summary of trading signals."""
    try:
        if not signals:
            return {
                'total_signals': 0,
                'by_action': {},
                'avg_confidence': 0.0,
                'symbols': []
            }
        
        # Count by action
        actions = [s.action for s in signals]
        action_counts = {action: actions.count(action) for action in set(actions)}
        
        # Calculate average confidence
        avg_confidence = sum(s.confidence for s in signals) / len(signals)
        
        # Get unique symbols
        symbols = list(set(s.symbol for s in signals))
        
        return {
            'total_signals': len(signals),
            'by_action': action_counts,
            'avg_confidence': round(avg_confidence, 3),
            'symbols': symbols,
            'highest_confidence': max(s.confidence for s in signals),
            'lowest_confidence': min(s.confidence for s in signals)
        }
    
    except Exception as e:
        logger.error(f"Error generating signal summary: {e}")
        return {'error': str(e)}


if __name__ == "__main__":
    # Test the signal engine
    print("Testing Signal Engine...")
    
    # Mock analysis result
    test_analysis = {
        'sentiment': {
            'positive': 0.7,
            'negative': 0.2,
            'neutral': 0.1,
            'overall_sentiment': 'positive'
        },
        'trading_insights': {
            'signal_direction': 'bullish',
            'signal_strength': 0.8,
            'bullish_indicators': 5,
            'bearish_indicators': 1,
            'potential_tickers': ['AAPL', 'MSFT', 'GOOGL'],
            'price_mentions': ['$150.00', '$200.50'],
            'confidence': 0.75,
            'market_indicators_found': ['earnings', 'growth', 'momentum']
        },
        'summary': 'Positive earnings report with strong growth indicators'
    }
    
    # Generate signals
    signals = generate_trading_signals(test_analysis)
    
    print(f"\nGenerated {len(signals)} signals:")
    for i, signal in enumerate(signals, 1):
        print(f"\n{i}. {signal.symbol}: {signal.action.upper()}")
        print(f"   Confidence: {signal.confidence:.2f}")
        print(f"   Reasoning: {signal.reasoning}")
        if signal.price_target:
            print(f"   Price Target: ${signal.price_target:.2f}")
        if signal.stop_loss:
            print(f"   Stop Loss: ${signal.stop_loss:.2f}")
    
    # Test filtering
    print(f"\n--- Filtering by confidence > 0.6 ---")
    high_conf_signals = filter_signals_by_confidence(signals, 0.6)
    print(f"High confidence signals: {len(high_conf_signals)}")
    
    # Summary
    print(f"\n--- Signal Summary ---")
    summary = get_signal_summary(signals)
    print(summary)
