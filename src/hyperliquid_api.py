# src/hyperliquid_api.py

import os
import time
from dotenv import load_dotenv
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

# Load environment variables from .env file
load_dotenv()

class HyperliquidExecutor:
    def __init__(self, is_testnet=True):
        self.wallet_address = os.getenv("HYPERLIQUID_WALLET_ADDRESS")
        api_wallet_secret = os.getenv("HYPERLIQUID_API_WALLET_SECRET")
        
        if not self.wallet_address or not api_wallet_secret:
            raise ValueError("Hyperliquid credentials not found in .env file")
            
        # Use Testnet or Mainnet URL
        base_url = constants.TESTNET_API_URL if is_testnet else constants.MAINNET_API_URL
        
        self.info = Info(base_url, skip_ws=True)
        self.exchange = Exchange(self.wallet_address, api_wallet_secret, base_url)
        print(f"Hyperliquid Executor initialized for {'Testnet' if is_testnet else 'Mainnet'}.")

    def get_current_price(self, symbol: str) -> float:
        """Fetches the real-time mark price for a given asset."""
        try:
            all_mids = self.info.all_mids()
            return float(all_mids.get(symbol, 0.0))
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return 0.0

    def execute_trade(self, signal: dict):
        """Executes a single trade signal on Hyperliquid."""
        symbol = signal['symbol']
        action = signal['action'] # 'buy' or 'sell'
        position_size_pct = signal['position_size']
        
        # 1. Get user state (portfolio value, positions, etc.)
        user_state = self.info.user_state(self.wallet_address)
        total_portfolio_value = float(user_state["margin_summary"]["account_value"])
        
        # 2. Calculate trade size in USD
        trade_value_usd = total_portfolio_value * position_size_pct
        current_price = self.get_current_price(symbol)
        
        if current_price == 0.0:
            return {"status": "error", "message": f"Could not fetch price for {symbol}"}
            
        trade_size_in_asset = round(trade_value_usd / current_price, 5) # Round to a reasonable precision
        
        # 3. Place the order
        is_buy = True if action == 'buy' else False
        
        # Hyperliquid uses limit orders. To simulate a market order, we can place a limit
        # order with a price slightly favorable to us to ensure it gets filled.
        slippage_factor = 0.005 # 0.5% slippage for market order simulation
        limit_price = round(current_price * (1 + slippage_factor) if is_buy else current_price * (1 - slippage_factor), 2)

        print(f"Placing order: {'BUY' if is_buy else 'SELL'} {trade_size_in_asset} {symbol} @ ${limit_price}")

        try:
            # The SDK's order function handles signing automatically
            order_result = self.exchange.order(
                symbol, is_buy, trade_size_in_asset, limit_price, {"limit": {"tif": "Ioc"}}
            )
            
            # Check the status of the order
            if order_result["status"] == "ok":
                fill_status = order_result["response"]["data"]["statuses"][0]
                if "filled" in fill_status:
                    print(f"SUCCESS: Order filled for {symbol}.")
                    return {"status": "executed", "details": fill_status}
                else:
                    print(f"WARN: Order submitted but not filled immediately (IOC): {fill_status}")
                    return {"status": "rejected", "details": fill_status}
            else:
                print(f"ERROR: Order failed: {order_result}")
                return {"status": "error", "message": order_result.get("response")}

        except Exception as e:
            print(f"An exception occurred while placing order: {e}")
            return {"status": "error", "message": str(e)}

def execute_hyperliquid_trades(signals: list, is_testnet=True):
    """Main function to process a list of signals with Hyperliquid."""
    executor = HyperliquidExecutor(is_testnet=is_testnet)
    results = []
    for signal in signals:
        # Hyperliquid uses coin tickers like "BTC", "ETH". Adapt if your signals use others.
        # For this example, we'll assume the signal's symbol is compatible.
        result = executor.execute_trade(signal)
        results.append(result)
        time.sleep(1) # Add a small delay between trades to avoid rate limiting
    return results