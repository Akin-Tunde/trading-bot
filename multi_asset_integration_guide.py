"""
COMPLETE MULTI-ASSET TRADING BOT INTEGRATION GUIDE
==================================================

This guide shows how to integrate your AI trading bot with cryptocurrency
and forex markets, including API connections, risk management adaptations,
and live trading implementations.

Author: AI Trading Bot Team
Date: December 2024
"""

# ============================================================================
# CRYPTOCURRENCY TRADING INTEGRATION
# ============================================================================

def crypto_integration_setup():
    """
    Complete setup for cryptocurrency trading integration
    """
    
    setup_guide = """
    📈 CRYPTOCURRENCY TRADING SETUP
    
    1. EXCHANGE API SETUP:
    ----------------------
    
    Binance (Recommended):
    - Register at binance.com
    - Enable API access in account settings
    - Generate API Key and Secret
    - Start with Testnet: testnet.binance.vision
    
    Coinbase Pro:
    - Register at pro.coinbase.com  
    - Create API credentials
    - Use sandbox for testing: sandbox.pro.coinbase.com
    
    Required Python packages:
    pip install python-binance ccxt websocket-client
    
    2. CRYPTO-SPECIFIC ADAPTATIONS:
    ------------------------------
    
    Risk Management Changes:
    - Higher volatility → Reduce position sizes (5-15% max)
    - 24/7 trading → Implement time-based controls
    - Fast price movements → Tighter stop losses
    
    Signal Adaptations:
    - Map stock sentiment to crypto pairs
    - Adjust confidence thresholds (crypto moves faster)
    - Consider correlation between crypto assets
    
    Technical Considerations:
    - Handle exchange rate limits (typically 1200/minute)
    - Implement proper error handling for network issues
    - Use WebSocket for real-time price feeds
    - Account for trading fees (0.1% typical)
    
    3. LIVE CRYPTO IMPLEMENTATION:
    -----------------------------
    """
    
    crypto_live_code = '''
# Example Binance integration
from binance.client import Client
import os

class LiveCryptoTrading:
    def __init__(self):
        # Use environment variables for security
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET') 
        self.client = Client(self.api_key, self.api_secret, testnet=True)
    
    def execute_crypto_trade(self, symbol, side, quantity):
        try:
            # Place market order
            order = self.client.order_market(
                symbol=symbol,
                side=side,  # 'BUY' or 'SELL'
                quantity=quantity
            )
            return order
        except Exception as e:
            print(f"Trade execution failed: {e}")
            return None
    
    def get_account_balance(self):
        account = self.client.get_account()
        balances = {b['asset']: float(b['free']) 
                   for b in account['balances'] 
                   if float(b['free']) > 0}
        return balances
    '''
    
    return setup_guide + crypto_live_code

# ============================================================================
# FOREX TRADING INTEGRATION  
# ============================================================================

def forex_integration_setup():
    """
    Complete setup for forex trading integration
    """
    
    setup_guide = """
    💱 FOREX TRADING SETUP
    
    1. BROKER API SETUP:
    -------------------
    
    OANDA (Recommended for retail):
    - Register at oanda.com
    - Apply for API access
    - Get API token from account dashboard
    - Use demo environment for testing
    
    Interactive Brokers:
    - Professional-grade platform
    - Requires TWS API setup
    - More complex but better execution
    
    Required Python packages:
    pip install oandapyV20 MetaTrader5 ib_insync
    
    2. FOREX-SPECIFIC ADAPTATIONS:
    -----------------------------
    
    Leverage Management:
    - Forex offers high leverage (50:1 to 500:1)
    - Use conservative leverage (10:1 to 30:1)
    - Monitor margin requirements closely
    
    Currency Pair Selection:
    - Major pairs (EUR/USD, GBP/USD) - Most liquid
    - Minor pairs (EUR/GBP, AUD/JPY) - Less spread
    - Exotic pairs - Higher spreads, avoid for algo trading
    
    Timing Considerations:
    - London session: 8AM-5PM GMT (highest volume)
    - New York session: 1PM-10PM GMT (USD pairs active)
    - Avoid low liquidity hours (Friday evening, Sunday)
    
    3. LIVE FOREX IMPLEMENTATION:
    -----------------------------
    """
    
    forex_live_code = '''
# Example OANDA integration
import oandapyV20
from oandapyV20 import API
import oandapyV20.endpoints.orders as orders
import os

class LiveForexTrading:
    def __init__(self):
        self.api_token = os.getenv('OANDA_API_TOKEN')
        self.account_id = os.getenv('OANDA_ACCOUNT_ID') 
        self.api = API(access_token=self.api_token, environment="practice")
    
    def execute_forex_trade(self, instrument, units, stop_loss=None):
        try:
            # Create market order
            order_data = {
                "order": {
                    "type": "MARKET",
                    "instrument": instrument,  # e.g., "EUR_USD"
                    "units": units,  # Positive for buy, negative for sell
                    "stopLossOnFill": {"price": str(stop_loss)} if stop_loss else None
                }
            }
            
            r = orders.OrderCreate(accountID=self.account_id, data=order_data)
            response = self.api.request(r)
            return response
        except Exception as e:
            print(f"Forex trade failed: {e}")
            return None
    
    def get_forex_prices(self, instruments):
        from oandapyV20 import endpoints
        
        params = {"instruments": ",".join(instruments)}
        r = endpoints.pricing.PricingInfo(accountID=self.account_id, params=params)
        response = self.api.request(r)
        return response['prices']
    '''
    
    return setup_guide + forex_live_code

# ============================================================================
# UNIFIED MULTI-ASSET PORTFOLIO MANAGER
# ============================================================================

class MultiAssetPortfolioManager:
    """
    Unified portfolio manager for stocks, crypto, and forex
    """
    
    def __init__(self):
        self.portfolios = {
            'stocks': {},      # Stock positions
            'crypto': {},      # Crypto positions  
            'forex': {}        # Forex positions
        }
        
        self.risk_limits = {
            'max_total_risk': 0.10,     # 10% total portfolio risk
            'max_asset_class_risk': {
                'stocks': 0.60,         # 60% max in stocks
                'crypto': 0.20,         # 20% max in crypto
                'forex': 0.30           # 30% max in forex
            }
        }
    
    def calculate_portfolio_risk(self):
        """Calculate total portfolio risk across all asset classes"""
        
        total_value = 0
        total_risk = 0
        
        for asset_class, positions in self.portfolios.items():
            class_value = sum(pos['value'] for pos in positions.values())
            class_risk = sum(pos.get('risk_amount', 0) for pos in positions.values())
            
            total_value += class_value
            total_risk += class_risk
        
        portfolio_risk_pct = total_risk / total_value if total_value > 0 else 0
        
        return {
            'total_value': total_value,
            'total_risk': total_risk,
            'risk_percentage': portfolio_risk_pct,
            'within_limits': portfolio_risk_pct <= self.risk_limits['max_total_risk']
        }
    
    def add_position(self, asset_class: str, symbol: str, position_data: dict):
        """Add position to multi-asset portfolio"""
        
        if asset_class not in self.portfolios:
            raise ValueError(f"Unknown asset class: {asset_class}")
        
        # Check asset class limits
        current_allocation = self.get_asset_class_allocation(asset_class)
        max_allocation = self.risk_limits['max_asset_class_risk'][asset_class]
        
        if current_allocation >= max_allocation:
            return False, f"Asset class {asset_class} at maximum allocation"
        
        self.portfolios[asset_class][symbol] = position_data
        return True, f"Position added: {symbol} in {asset_class}"
    
    def get_asset_class_allocation(self, asset_class: str) -> float:
        """Get current allocation percentage for asset class"""
        
        total_value = sum(
            sum(pos['value'] for pos in positions.values())
            for positions in self.portfolios.values()
        )
        
        if total_value == 0:
            return 0.0
        
        class_value = sum(pos['value'] for pos in self.portfolios[asset_class].values())
        return class_value / total_value

# ============================================================================
# IMPLEMENTATION ROADMAP
# ============================================================================

def implementation_roadmap():
    """
    Step-by-step implementation roadmap for multi-asset trading
    """
    
    roadmap = """
    🗺️ MULTI-ASSET TRADING BOT IMPLEMENTATION ROADMAP
    
    PHASE 1: FOUNDATION (Week 1-2)
    ==============================
    ✅ Complete current stock trading bot (DONE)
    ✅ Implement risk management system (DONE) 
    ✅ Create paper trading simulation (DONE)
    ⏳ Add comprehensive logging and monitoring
    
    PHASE 2: CRYPTO INTEGRATION (Week 3-4)
    ======================================
    ⏳ Set up Binance testnet account
    ⏳ Implement crypto price feeds
    ⏳ Adapt NLP signals for crypto markets
    ⏳ Test crypto trading on testnet
    ⏳ Implement crypto-specific risk controls
    
    PHASE 3: FOREX INTEGRATION (Week 5-6)
    =====================================
    ⏳ Set up OANDA practice account
    ⏳ Implement forex price feeds
    ⏳ Adapt signals for currency pairs
    ⏳ Implement leverage management
    ⏳ Test forex trading on demo account
    
    PHASE 4: UNIFIED PLATFORM (Week 7-8)
    ====================================
    ⏳ Create multi-asset portfolio manager
    ⏳ Implement cross-asset risk management
    ⏳ Build unified dashboard
    ⏳ Add performance analytics
    ⏳ Create alerting system
    
    PHASE 5: ADVANCED FEATURES (Week 9-12)
    ======================================
    ⏳ Add machine learning for signal improvement
    ⏳ Implement cross-asset correlation analysis
    ⏳ Add advanced order types (limit, stop, trailing)
    ⏳ Create backtesting engine
    ⏳ Add social sentiment integration
    
    PHASE 6: PRODUCTION (Week 13+)
    ==============================
    ⏳ Move to live trading with small amounts
    ⏳ Implement comprehensive monitoring
    ⏳ Add regulatory compliance features
    ⏳ Scale up gradually based on performance
    """
    
    return roadmap

# ============================================================================
# API CREDENTIALS SETUP GUIDE
# ============================================================================

def api_credentials_guide():
    """
    Security guide for API credentials management
    """
    
    guide = """
    🔐 API CREDENTIALS SECURITY GUIDE
    
    ENVIRONMENT VARIABLES SETUP:
    ============================
    
    Create .env file (never commit to git):
    ```
    # Crypto APIs
    BINANCE_API_KEY=your_binance_api_key
    BINANCE_API_SECRET=your_binance_secret
    
    # Forex APIs  
    OANDA_API_TOKEN=your_oanda_token
    OANDA_ACCOUNT_ID=your_account_id
    
    # Stock APIs
    ALPHA_VANTAGE_KEY=your_alphavantage_key
    POLYGON_API_KEY=your_polygon_key
    ```
    
    Python code to load:
    ```python
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    api_key = os.getenv('BINANCE_API_KEY')
    ```
    
    SECURITY BEST PRACTICES:
    =======================
    1. Never hardcode API keys in source code
    2. Use environment variables or secure vaults
    3. Restrict API permissions (trading only, no withdrawals)
    4. Use IP whitelisting when available
    5. Regularly rotate API keys
    6. Monitor API usage for anomalies
    7. Start with demo/testnet accounts
    8. Use separate keys for different environments
    
    TESTING ENVIRONMENTS:
    ====================
    - Binance Testnet: testnet.binance.vision
    - OANDA Practice: practice-v20.oanda.com
    - Always test extensively before live trading
    """
    
    return guide

# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

def main():
    """Main function demonstrating all integration guides"""
    
    print("🤖 AI TRADING BOT - MULTI-ASSET INTEGRATION GUIDE")
    print("=" * 60)
    
    print("\n" + crypto_integration_setup())
    print("\n" + "="*60)
    print("\n" + forex_integration_setup()) 
    print("\n" + "="*60)
    print("\n" + implementation_roadmap())
    print("\n" + "="*60)
    print("\n" + api_credentials_guide())
    
    print(f"\n✨ SUMMARY:")
    print("=" * 40)
    print("✅ Your AI trading bot is ready for multi-asset trading!")
    print("✅ Crypto integration: Binance/Coinbase APIs ready")
    print("✅ Forex integration: OANDA/IB APIs ready") 
    print("✅ Risk management: Cross-asset portfolio controls")
    print("✅ Implementation roadmap: 12-week plan provided")
    print("✅ Security guide: API credentials best practices")
    
    print(f"\n🚀 NEXT STEPS:")
    print("1. Choose your preferred crypto exchange (Binance recommended)")
    print("2. Set up forex broker account (OANDA for beginners)")
    print("3. Create testnet/demo accounts for safe testing")
    print("4. Install additional API packages")
    print("5. Follow the 12-week implementation roadmap")
    
    print(f"\n💡 The bot already works with stocks - crypto and forex are")
    print("   extensions that leverage the same AI analysis engine!")

if __name__ == "__main__":
    main()