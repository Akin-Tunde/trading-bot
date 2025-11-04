"""
Crypto Trading Module - Adapts the AI bot for cryptocurrency trading
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import requests
import json
from dotenv import load_dotenv

# --- ADDED: Load environment variables from .env file ---
load_dotenv()

# We need to add the parent directory to the path to find the other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.signal_engine import TradingSignal
from src.risk_manager import calculate_position_size, apply_risk_controls

# --- ADDED: Import the Binance Client ---
from binance.client import Client
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

class CryptoTradingEngine:
    """Cryptocurrency trading engine for the AI bot"""
    
    def __init__(self, exchange: str = 'binance', testnet: bool = True):
        self.exchange = exchange
        self.testnet = testnet
        self.base_url = self._get_api_url()
        
        # --- ADDED: API Client Initialization ---
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        if not self.api_key or not self.api_secret:
            logger.error("Binance API Key/Secret not found. Make sure .env file is set up.")
            raise ValueError("API credentials not found")
            
        self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
        # Adjust the base URL for the client library
        if self.testnet:
            self.client.API_URL = 'https://testnet.binance.vision/api'

        # Crypto-specific configuration
        self.crypto_config = {
            'risk_tolerance': 0.03,
            'max_position_size': 0.15,
            'confidence_threshold': 0.65,
            'trading_pairs': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT']
        }
    
    def _get_api_url(self) -> str:
        """Get appropriate API URL based on exchange and mode"""
        urls = {
            'binance': {
                'live': 'https://api.binance.com',
                'testnet': 'https://testnet.binance.vision/api' # Corrected URL
            }
        }
        mode = 'testnet' if self.testnet else 'live'
        return urls.get(self.exchange, {}).get(mode, '')
    
    def get_crypto_price(self, symbol: str) -> float:
        """Get real-time crypto price from exchange API"""
        try:
            return float(self.client.get_symbol_ticker(symbol=symbol)['price'])
        except Exception as e:
            logger.error(f"Error fetching crypto price for {symbol}: {e}")
            return self._get_mock_crypto_price(symbol) # Fallback to mock
    
    def _get_mock_crypto_price(self, symbol: str) -> float:
        """Mock crypto prices for testing if API fails"""
        mock_prices = {'BTCUSDT': 67500.00, 'ETHUSDT': 2650.00, 'ADAUSDT': 0.45, 'SOLUSDT': 140.00}
        import random
        base_price = mock_prices.get(symbol, 100.0)
        return base_price * (1 + random.uniform(-0.05, 0.05))

    # --- THIS IS THE FULLY CORRECTED METHOD ---
    def adapt_signal_for_crypto(self, signal: dict) -> TradingSignal:
        """Adapt a stock signal dictionary for crypto trading"""
        try:
            crypto_mapping = {
                'AAPL': 'BTCUSDT', 'MSFT': 'ETHUSDT', 'GOOGL': 'ADAUSDT',
                'NVDA': 'SOLUSDT', 'AMZN': 'BTCUSDT', 'TSLA': 'ETHUSDT',
                'SPY': 'BTCUSDT'
            }
            
            original_symbol = signal['symbol']
            signal_action = signal['action']
            
            # Use a default if the symbol isn't in our map
            crypto_symbol = crypto_mapping.get(original_symbol, 'BTCUSDT')
            current_price = self.get_crypto_price(crypto_symbol)
            
            crypto_confidence = signal['confidence'] * 0.9
            
            crypto_signal = TradingSignal(
                symbol=crypto_symbol,
                action=signal_action,
                confidence=crypto_confidence,
                price_target=current_price * 1.15 if signal_action == 'buy' else current_price * 0.85,
                stop_loss=current_price * 0.92 if signal_action == 'buy' else current_price * 1.08,
                source="Crypto AI Analysis",
                reasoning=f"Crypto adaptation: {signal['reasoning']}",
                original_stock_signal=original_symbol
            )
            return crypto_signal
        except KeyError as e:
            logger.error(f"Signal dictionary is missing a key: {e}. Signal was: {signal}")
            return None
        except Exception as e:
            logger.error(f"Failed to adapt signal for crypto: {e}")
            return None

    def execute_crypto_trades(self, signals: List[dict]) -> Dict:
        """Execute crypto trades using the received signal dictionaries"""
        print("🪙 CRYPTO TRADING EXECUTION")
        print("=" * 40)
        
        adapted_signals = []
        for signal_dict in signals:
            # The Risk Manager sends dictionaries, so we adapt them
            crypto_signal_obj = self.adapt_signal_for_crypto(signal_dict)
            if crypto_signal_obj:
                adapted_signals.append(crypto_signal_obj)

        approved_trades = 0
        pairs_traded = []
        
        for signal_obj in adapted_signals:
            if self._execute_live_crypto_trade(signal_obj):
                approved_trades += 1
                pairs_traded.append(signal_obj.symbol)
        
        print(f"\n✅ Executed {approved_trades} crypto trades on the testnet.")
        
        return {
            'crypto_trades': approved_trades,
            'pairs_traded': list(set(pairs_traded)),
            'timestamp': datetime.now().isoformat()
        }

    # --- ADDED: New method for live trade execution ---
    def _execute_live_crypto_trade(self, signal: TradingSignal) -> bool:
        """Executes a single, validated trade on the live/testnet exchange."""
        try:
            # Calculate quantity to trade based on USDT value
            usdt_balance = float(self.client.get_asset_balance(asset='USDT')['free'])
            portfolio_value = usdt_balance # Simplified for this example
            
            # Use risk manager to get position size in PERCENT
            position_size_pct = calculate_position_size(
                signal,
                risk_tolerance=self.crypto_config['risk_tolerance'],
                max_position_size=self.crypto_config['max_position_size'],
                portfolio_value=portfolio_value
            )

            # Convert percentage to a dollar amount
            trade_value_usdt = portfolio_value * position_size_pct
            current_price = self.get_crypto_price(signal.symbol)
            quantity = round(trade_value_usdt / current_price, 5) # Round to a reasonable precision for crypto

            print(f"Attempting to {signal.action.upper()} {quantity} of {signal.symbol}...")

            if signal.action == 'buy':
                if trade_value_usdt > usdt_balance:
                    logger.warning(f"Insufficient USDT balance for {signal.symbol}. Needed {trade_value_usdt}, have {usdt_balance}")
                    return False
                
                # Place live testnet order
                self.client.order_market_buy(symbol=signal.symbol, quantity=quantity)
                print(f"   SUCCESS: Placed MARKET BUY order for {quantity} {signal.symbol}.")
                return True

            elif signal.action == 'sell':
                asset = signal.symbol.replace('USDT', '')
                asset_balance = float(self.client.get_asset_balance(asset=asset)['free'])
                
                if quantity > asset_balance:
                    logger.warning(f"Insufficient {asset} balance to sell. Wanted {quantity}, have {asset_balance}")
                    return False

                # Place live testnet order
                self.client.order_market_sell(symbol=signal.symbol, quantity=quantity)
                print(f"   SUCCESS: Placed MARKET SELL order for {quantity} {signal.symbol}.")
                return True
                
        except BinanceAPIException as e:
            logger.error(f"Binance API Error on trade for {signal.symbol}: {e}")
            print(f"   FAILED: Binance API Error - {e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during live trade for {signal.symbol}: {e}")
            print(f"   FAILED: An unexpected error occurred - {e}")
            return False
        return False

# The ForexTradingEngine and demonstrate function can remain as they are for now.
# ... (rest of the file is unchanged) ...
class ForexTradingEngine:
    """Forex trading engine for the AI bot"""
    # ... (no changes needed here)

def demonstrate_multi_asset_trading():
    """Demonstrate trading across stocks, crypto, and forex"""
    # ... (no changes needed here)

if __name__ == "__main__":
    demonstrate_multi_asset_trading()