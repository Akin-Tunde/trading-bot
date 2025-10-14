import re
import logging
from typing import Dict, List, Optional, Tuple
from transformers import pipeline

logger = logging.getLogger(__name__)

def summarize_text(text: str, max_length: int = 150, min_length: int = 40) -> str:
    """
    Summarize a given text using BART model.
    
    Args:
        text: Input text to summarize
        max_length: Maximum length of summary
        min_length: Minimum length of summary
    
    Returns:
        Summarized text
    """
    try:
        # Handle very long texts by chunking
        if len(text) > 1024:
            # Split into chunks and summarize each
            chunks = [text[i:i+1024] for i in range(0, len(text), 1024)]
            summaries = []
            
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            
            for chunk in chunks[:3]:  # Limit to first 3 chunks to avoid overload
                if len(chunk.strip()) > 50:  # Only summarize meaningful chunks
                    summary = summarizer(chunk, max_length=100, min_length=20, do_sample=False)
                    summaries.append(summary[0]['summary_text'])
            
            # Combine and re-summarize if needed
            combined_summary = " ".join(summaries)
            if len(combined_summary) > max_length * 2:
                final_summary = summarizer(combined_summary, max_length=max_length, min_length=min_length, do_sample=False)
                return final_summary[0]['summary_text']
            else:
                return combined_summary
        else:
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            return summary[0]['summary_text']
    
    except Exception as e:
        logger.error(f"Error in text summarization: {e}")
        # Fallback to simple truncation
        return text[:max_length] + "..." if len(text) > max_length else text


def analyze_sentiment(text: str) -> Dict[str, float]:
    """
    Analyze sentiment of the given text.
    
    Args:
        text: Input text for sentiment analysis
    
    Returns:
        Dictionary with sentiment scores
    """
    try:
        sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
        
        # Handle long texts by analyzing chunks
        if len(text) > 512:
            chunks = [text[i:i+512] for i in range(0, min(len(text), 2048), 512)]  # Limit analysis
            sentiments = []
            
            for chunk in chunks:
                if len(chunk.strip()) > 20:
                    result = sentiment_analyzer(chunk)[0]
                    sentiments.append({
                        'label': result['label'],
                        'score': result['score']
                    })
            
            # Aggregate sentiments
            if sentiments:
                positive_scores = [s['score'] for s in sentiments if s['label'] in ['LABEL_2', 'positive']]
                negative_scores = [s['score'] for s in sentiments if s['label'] in ['LABEL_0', 'negative']]
                neutral_scores = [s['score'] for s in sentiments if s['label'] in ['LABEL_1', 'neutral']]
                
                return {
                    'positive': sum(positive_scores) / len(positive_scores) if positive_scores else 0.0,
                    'negative': sum(negative_scores) / len(negative_scores) if negative_scores else 0.0,
                    'neutral': sum(neutral_scores) / len(neutral_scores) if neutral_scores else 0.0,
                    'overall_sentiment': 'positive' if len(positive_scores) > len(negative_scores) else 'negative' if len(negative_scores) > len(positive_scores) else 'neutral'
                }
        else:
            result = sentiment_analyzer(text)[0]
            label_mapping = {'LABEL_0': 'negative', 'LABEL_1': 'neutral', 'LABEL_2': 'positive'}
            sentiment = label_mapping.get(result['label'], result['label'].lower())
            
            return {
                'positive': result['score'] if sentiment == 'positive' else 0.0,
                'negative': result['score'] if sentiment == 'negative' else 0.0,
                'neutral': result['score'] if sentiment == 'neutral' else 0.0,
                'overall_sentiment': sentiment
            }
    
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return {
            'positive': 0.0,
            'negative': 0.0,
            'neutral': 1.0,
            'overall_sentiment': 'neutral'
        }


def extract_trading_signals(text: str) -> Dict[str, List]:
    """
    Extract trading-related signals and insights from text.
    
    Args:
        text: Input text to analyze for trading signals
    
    Returns:
        Dictionary containing extracted trading insights
    """
    try:
        text_lower = text.lower()
        
        # Define trading-related keywords and patterns
        bullish_keywords = [
            'buy', 'bullish', 'upward', 'increase', 'growth', 'rise', 'gain',
            'positive outlook', 'strong performance', 'outperform', 'upgrade',
            'momentum', 'breakout', 'support level', 'rally'
        ]
        
        bearish_keywords = [
            'sell', 'bearish', 'downward', 'decrease', 'decline', 'fall', 'drop',
            'negative outlook', 'weak performance', 'underperform', 'downgrade',
            'resistance level', 'correction', 'pullback', 'crash'
        ]
        
        market_indicators = [
            'volatility', 'volume', 'price target', 'earnings', 'revenue',
            'profit', 'loss', 'dividend', 'market cap', 'pe ratio',
            'technical analysis', 'fundamental analysis'
        ]
        
        # Extract company/ticker mentions (simple pattern)
        ticker_pattern = r'\b[A-Z]{2,5}\b'  # 2-5 uppercase letters
        potential_tickers = re.findall(ticker_pattern, text)
        
        # Count keyword occurrences
        bullish_count = sum(1 for keyword in bullish_keywords if keyword in text_lower)
        bearish_count = sum(1 for keyword in bearish_keywords if keyword in text_lower)
        
        # Extract numerical values (prices, percentages)
        price_pattern = r'\$\d+(?:\.\d{2})?'
        percentage_pattern = r'\d+(?:\.\d+)?%'
        
        prices = re.findall(price_pattern, text)
        percentages = re.findall(percentage_pattern, text)
        
        # Determine overall signal
        if bullish_count > bearish_count:
            signal_direction = 'bullish'
            signal_strength = min(bullish_count / (bullish_count + bearish_count + 1), 1.0)
        elif bearish_count > bullish_count:
            signal_direction = 'bearish'  
            signal_strength = min(bearish_count / (bullish_count + bearish_count + 1), 1.0)
        else:
            signal_direction = 'neutral'
            signal_strength = 0.5
        
        return {
            'signal_direction': signal_direction,
            'signal_strength': signal_strength,
            'bullish_indicators': bullish_count,
            'bearish_indicators': bearish_count,
            'potential_tickers': list(set(potential_tickers))[:10],  # Limit to 10 unique tickers
            'price_mentions': prices[:5],  # Limit to 5 prices
            'percentage_mentions': percentages[:5],  # Limit to 5 percentages
            'market_indicators_found': [indicator for indicator in market_indicators if indicator in text_lower],
            'confidence': signal_strength * 0.8 if signal_direction != 'neutral' else 0.3  # Lower confidence for rule-based approach
        }
    
    except Exception as e:
        logger.error(f"Error extracting trading signals: {e}")
        return {
            'signal_direction': 'neutral',
            'signal_strength': 0.0,
            'bullish_indicators': 0,
            'bearish_indicators': 0,
            'potential_tickers': [],
            'price_mentions': [],
            'percentage_mentions': [],
            'market_indicators_found': [],
            'confidence': 0.0
        }


if __name__ == "__main__":
    # Example text - replace with your extracted PDF text
    sample_text = (
        "In this paper, we study the estimation of a rank-one spiked tensor in the presence of "
        "heavy tailed noise. Our results highlight some of the fundamental similarities and differences "
        "in the tradeoff between statistical and computational efficiencies under heavy "
        "tailed and Gaussian noise. In particular, the stock market shows bullish momentum "
        "with AAPL showing strong buy signals at $150 with a 15% upside potential."
    )
    
    print("Testing NLP Processing Functions:")
    print("=" * 40)
    
    print("1. Summary:")
    summary = summarize_text(sample_text)
    print(summary)
    print()
    
    print("2. Sentiment Analysis:")
    sentiment = analyze_sentiment(sample_text)
    print(sentiment)
    print()
    
    print("3. Trading Signals:")
    trading_signals = extract_trading_signals(sample_text)
    print(trading_signals)