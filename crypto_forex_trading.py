"""
Crypto Trading Module - Adapts the AI bot for cryptocurrency trading
"""

import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional
import requests
import json

sys.path.append('src')
from signal_engine import TradingSignal
from risk_manager import calculate_position_size, apply_risk_controls

logger = logging.getLogger(__name__)

class CryptoTradingEngine:
    """Cryptocurrency trading engine for the AI bot"""
    
    def __init__(self, exchange: str = 'binance', testnet: bool = True):
        self.exchange = exchange
        self.testnet = testnet
        self.base_url = self._get_api_url()
        
        # Crypto-specific configuration
        self.crypto_config = {
            'risk_tolerance': 0.03,      # 3% risk (higher due to crypto volatility)
            'max_position_size': 0.15,   # 15% max position (crypto diversification)
            'confidence_threshold': 0.65, # Lower threshold (crypto moves fast)
            'volatility_adjustment': 2.0, # Account for high crypto volatility
            'trading_pairs': [
                'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 
                'LINKUSDT', 'LTCUSDT', 'BNBUSDT', 'SOLUSDT'
            ]
        }
    
    def _get_api_url(self) -> str:
        """Get appropriate API URL based on exchange and mode"""
        urls = {
            'binance': {
                'live': 'https://api.binance.com',
                'testnet': 'https://testnet.binance.vision'
            },
            'coinbase': {
                'live': 'https://api.pro.coinbase.com',
                'testnet': 'https://api-public.sandbox.pro.coinbase.com'
            }
        }
        mode = 'testnet' if self.testnet else 'live'
        return urls.get(self.exchange, {}).get(mode, '')
    
    def get_crypto_price(self, symbol: str) -> float:
        """Get real-time crypto price from exchange API"""
        try:
            if self.exchange == 'binance':
                url = f"{self.base_url}/api/v3/ticker/price"
                params = {'symbol': symbol}
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return float(data['price'])
                else:
                    logger.error(f"Error fetching {symbol} price: {response.status_code}")
                    return self._get_mock_crypto_price(symbol)
            else:
                return self._get_mock_crypto_price(symbol)
                
        except Exception as e:
            logger.error(f"Error fetching crypto price for {symbol}: {e}")
            return self._get_mock_crypto_price(symbol)
    
    def _get_mock_crypto_price(self, symbol: str) -> float:
        """Mock crypto prices for testing"""
        mock_prices = {
            'BTCUSDT': 67500.00,
            'ETHUSDT': 2650.00,
            'ADAUSDT': 0.45,
            'DOTUSDT': 5.80,
            'LINKUSDT': 12.50,
            'LTCUSDT': 68.00,
            'BNBUSDT': 590.00,
            'SOLUSDT': 140.00
        }
        
        # Add some realistic volatility
        import random
        base_price = mock_prices.get(symbol, 100.0)
        volatility = random.uniform(-0.05, 0.05)  # ±5% volatility
        return base_price * (1 + volatility)
    
    def adapt_signal_for_crypto(self, signal: TradingSignal) -> TradingSignal:
        """Adapt stock signal for crypto trading"""
        
        # Map stock symbols to crypto pairs
        crypto_mapping = {
            'AAPL': 'BTCUSDT',   # Apple → Bitcoin
            'MSFT': 'ETHUSDT',   # Microsoft → Ethereum
            'GOOGL': 'ADAUSDT',  # Google → Cardano
            'NVDA': 'SOLUSDT',   # NVIDIA → Solana
            'AMZN': 'DOTUSDT',   # Amazon → Polkadot
            'TSLA': 'LINKUSDT',  # Tesla → Chainlink
            'SPY': 'BTCUSDT'     # S&P 500 → Bitcoin
        }
        
        crypto_symbol = crypto_mapping.get(signal.symbol, 'BTCUSDT')
        current_price = self.get_crypto_price(crypto_symbol)
        
        # Adjust for crypto volatility
        crypto_confidence = signal.confidence * 0.9  # Slightly reduce due to higher risk
        
        # Create crypto-adapted signal
        crypto_signal = TradingSignal(
            symbol=crypto_symbol,
            action=signal.action,
            confidence=crypto_confidence,
            price_target=current_price * 1.15 if signal.action == 'buy' else current_price * 0.85,
            stop_loss=current_price * 0.92 if signal.action == 'buy' else current_price * 1.08,
            source="Crypto AI Analysis",
            reasoning=f"Crypto adaptation: {signal.reasoning}",
            original_stock_signal=signal.symbol,
            crypto_volatility_adj=True
        )
        
        return crypto_signal
    
    def execute_crypto_trades(self, signals: List[TradingSignal]) -> Dict:
        """Execute crypto trades with appropriate risk management"""
        
        print("🪙 CRYPTO TRADING EXECUTION")
        print("=" * 40)
        
        crypto_signals = []
        
        # Adapt signals for crypto
        for signal in signals:
            crypto_signal = self.adapt_signal_for_crypto(signal)
            crypto_signals.append(crypto_signal)
            
            print(f"📈 {crypto_signal.symbol}: {crypto_signal.action.upper()}")
            print(f"   Price: ${self.get_crypto_price(crypto_signal.symbol):,.2f}")
            print(f"   Confidence: {crypto_signal.confidence:.2f}")
            print(f"   Target: ${crypto_signal.price_target:.2f}")
        
        # Apply crypto-specific risk management
        approved_signals = []
        for signal in crypto_signals:
            position_size = calculate_position_size(
                signal, 
                risk_tolerance=self.crypto_config['risk_tolerance'],
                max_position_size=self.crypto_config['max_position_size']
            )
            
            risk_managed = apply_risk_controls(signal, position_size, self.crypto_config)
            if risk_managed:
                approved_signals.append(risk_managed)
        
        print(f"\n✅ Approved {len(approved_signals)} crypto signals")
        
        # Simulate crypto trading execution
        execution_results = {
            'crypto_trades': len(approved_signals),
            'total_exposure': sum(s['position_size'] for s in approved_signals),
            'avg_confidence': sum(s['confidence'] for s in approved_signals) / len(approved_signals) if approved_signals else 0,
            'pairs_traded': [s['symbol'] for s in approved_signals],
            'timestamp': datetime.now().isoformat()
        }
        
        return execution_results

class ForexTradingEngine:
    """Forex trading engine for the AI bot"""
    
    def __init__(self, broker: str = 'oanda', demo: bool = True):
        self.broker = broker
        self.demo = demo
        
        # Forex-specific configuration
        self.forex_config = {
            'risk_tolerance': 0.02,      # 2% risk per trade
            'max_position_size': 0.10,   # 10% max position
            'confidence_threshold': 0.70, # 70% minimum confidence
            'leverage': 50,              # 50:1 leverage (conservative)
            'currency_pairs': [
                'EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF',
                'AUD_USD', 'USD_CAD', 'NZD_USD', 'EUR_GBP'
            ]
        }
    
    def get_forex_rate(self, pair: str) -> float:
        """Get real-time forex rates"""
        # Mock forex rates for demonstration
        mock_rates = {
            'EUR_USD': 1.0850,
            'GBP_USD': 1.2750, 
            'USD_JPY': 149.50,
            'USD_CHF': 0.9150,
            'AUD_USD': 0.6650,
            'USD_CAD': 1.3750,
            'NZD_USD': 0.6100,
            'EUR_GBP': 0.8500
        }
        
        # Add small forex volatility
        import random
        base_rate = mock_rates.get(pair, 1.0000)
        volatility = random.uniform(-0.002, 0.002)  # ±0.2% (forex is less volatile)
        return base_rate * (1 + volatility)
    
    def adapt_signal_for_forex(self, signal: TradingSignal) -> TradingSignal:
        """Adapt stock signal for forex trading"""
        
        # Map stock sentiment to forex pairs
        forex_mapping = {
            'bullish_USD': ['EUR_USD', 'GBP_USD', 'AUD_USD'],  # Sell these (buy USD)
            'bullish_EUR': ['EUR_USD', 'EUR_GBP'],             # Buy these
            'bullish_GBP': ['GBP_USD', 'EUR_GBP'],             # Buy these
            'general_risk_on': ['AUD_USD', 'NZD_USD'],         # Risk currencies
            'general_risk_off': ['USD_JPY', 'USD_CHF']         # Safe havens
        }
        
        # Simple mapping based on signal strength
        if signal.confidence > 0.8:
            forex_pair = 'EUR_USD'  # Most liquid pair
            forex_action = 'buy' if signal.action == 'buy' else 'sell'
        else:
            forex_pair = 'GBP_USD'  # Second most liquid
            forex_action = signal.action
        
        current_rate = self.get_forex_rate(forex_pair)
        
        # Create forex-adapted signal
        forex_signal = TradingSignal(
            symbol=forex_pair,
            action=forex_action,
            confidence=signal.confidence,
            price_target=current_rate * 1.005 if forex_action == 'buy' else current_rate * 0.995,
            stop_loss=current_rate * 0.998 if forex_action == 'buy' else current_rate * 1.002,
            source="Forex AI Analysis",
            reasoning=f"Forex adaptation: {signal.reasoning}",
            leverage=self.forex_config['leverage'],
            original_stock_signal=signal.symbol
        )
        
        return forex_signal
    
    def execute_forex_trades(self, signals: List[TradingSignal]) -> Dict:
        """Execute forex trades with leverage and pip calculations"""
        
        print("💱 FOREX TRADING EXECUTION") 
        print("=" * 40)
        
        forex_signals = []
        
        # Adapt signals for forex
        for signal in signals:
            forex_signal = self.adapt_signal_for_forex(signal)
            forex_signals.append(forex_signal)
            
            current_rate = self.get_forex_rate(forex_signal.symbol)
            pip_value = self._calculate_pip_value(forex_signal.symbol, current_rate)
            
            print(f"💹 {forex_signal.symbol}: {forex_signal.action.upper()}")
            print(f"   Rate: {current_rate:.5f}")
            print(f"   Confidence: {forex_signal.confidence:.2f}")
            print(f"   Leverage: {self.forex_config['leverage']}:1")
            print(f"   Pip Value: ${pip_value:.2f}")
        
        # Apply forex risk management
        approved_signals = []
        for signal in forex_signals:
            # Adjust position size for leverage
            base_position = calculate_position_size(
                signal,
                risk_tolerance=self.forex_config['risk_tolerance']
            )
            
            # With leverage, effective position is larger
            leveraged_position = base_position * self.forex_config['leverage']
            
            risk_managed = apply_risk_controls(signal, base_position, self.forex_config)
            if risk_managed:
                risk_managed['leveraged_exposure'] = leveraged_position
                approved_signals.append(risk_managed)
        
        print(f"\n✅ Approved {len(approved_signals)} forex signals")
        
        execution_results = {
            'forex_trades': len(approved_signals),
            'currency_pairs': [s['symbol'] for s in approved_signals],
            'total_leverage_exposure': sum(s.get('leveraged_exposure', 0) for s in approved_signals),
            'avg_confidence': sum(s['confidence'] for s in approved_signals) / len(approved_signals) if approved_signals else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        return execution_results
    
    def _calculate_pip_value(self, pair: str, rate: float, position_size: float = 10000) -> float:
        """Calculate pip value for forex pair"""
        # Simplified pip calculation
        if 'JPY' in pair:
            pip_size = 0.01  # JPY pairs have 2 decimal places
        else:
            pip_size = 0.0001  # Most pairs have 4 decimal places
        
        # For USD base pairs, pip value is typically $1 per 10k units
        return 1.0  # Simplified to $1 per pip for 10k position

def demonstrate_multi_asset_trading():
    """Demonstrate trading across stocks, crypto, and forex"""
    
    print("🌐 MULTI-ASSET AI TRADING DEMONSTRATION")
    print("=" * 60)
    
    # Sample signals from the AI bot
    sample_signals = [
        TradingSignal('AAPL', 'buy', 0.85, 160.0, 140.0, reasoning="Strong earnings outlook"),
        TradingSignal('MSFT', 'buy', 0.78, 320.0, 290.0, reasoning="Cloud growth acceleration"),
        TradingSignal('SPY', 'sell', 0.72, 400.0, 430.0, reasoning="Market overvaluation concerns")
    ]
    
    # Initialize trading engines
    crypto_engine = CryptoTradingEngine(testnet=True)
    forex_engine = ForexTradingEngine(demo=True)
    
    print("Original Stock Signals:")
    for signal in sample_signals:
        print(f"  {signal.symbol}: {signal.action.upper()} (confidence: {signal.confidence})")
    
    print("\n" + "="*60)
    
    # Execute crypto trades
    crypto_results = crypto_engine.execute_crypto_trades(sample_signals)
    
    print("\n" + "="*60)
    
    # Execute forex trades
    forex_results = forex_engine.execute_forex_trades(sample_signals)
    
    print(f"\n📊 MULTI-ASSET EXECUTION SUMMARY:")
    print("=" * 40)
    print(f"Crypto Trades: {crypto_results['crypto_trades']}")
    print(f"Forex Trades: {forex_results['forex_trades']}")
    print(f"Crypto Pairs: {', '.join(crypto_results['pairs_traded'])}")
    print(f"Forex Pairs: {', '.join(forex_results['currency_pairs'])}")

if __name__ == "__main__":
    demonstrate_multi_asset_trading()