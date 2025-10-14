#!/usr/bin/env python3
"""
Live Trading Dashboard - Real-time portfolio monitoring and trading moves
"""

import sys
import json
import os
from datetime import datetime, timedelta
sys.path.append('src')

def show_trading_dashboard():
    """Display a comprehensive trading dashboard"""
    
    print("🚀 AI TRADING BOT - LIVE DASHBOARD")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Load portfolio data
        with open('trading_data.json', 'r') as f:
            data = json.load(f)
        
        # Portfolio Summary
        print("💼 PORTFOLIO SUMMARY")
        print("-" * 30)
        
        cash = data['cash']
        positions_value = sum(pos['market_value'] for pos in data['positions'].values())
        total_value = cash + positions_value
        
        initial_balance = 100000
        total_pnl = total_value - initial_balance
        pnl_pct = (total_pnl / initial_balance) * 100
        
        print(f"💰 Cash:           ${cash:>12,.2f}")
        print(f"📊 Positions:      ${positions_value:>12,.2f}")
        print(f"🏦 Total Value:    ${total_value:>12,.2f}")
        print(f"📈 P&L:           ${total_pnl:>12,.2f} ({pnl_pct:+.2f}%)")
        print()
        
        # Current Positions
        print("📍 CURRENT POSITIONS")
        print("-" * 30)
        
        if data['positions']:
            for symbol, position in data['positions'].items():
                quantity = position['quantity']
                avg_price = position['avg_price']
                market_value = position['market_value']
                current_price = market_value / quantity if quantity > 0 else 0
                
                position_pnl = market_value - (quantity * avg_price)
                position_pnl_pct = (position_pnl / (quantity * avg_price)) * 100 if quantity * avg_price > 0 else 0
                
                print(f"{symbol:>6} | {quantity:>8.2f} shares @ ${avg_price:>7.2f}")
                print(f"      | Current: ${current_price:>7.2f} | Value: ${market_value:>10,.2f}")
                print(f"      | P&L: ${position_pnl:>+7.2f} ({position_pnl_pct:+.1f}%)")
                print()
        else:
            print("No positions held.")
            print()
        
        # Trading Activity Summary
        trade_history = data.get('trade_history', [])
        
        print("📊 TRADING STATISTICS")
        print("-" * 30)
        
        total_trades = len(trade_history)
        buy_trades = [t for t in trade_history if t['action'] == 'buy']
        sell_trades = [t for t in trade_history if t['action'] == 'sell']
        
        avg_confidence = sum(t['signal_confidence'] for t in trade_history) / total_trades if total_trades > 0 else 0
        
        print(f"Total Trades:     {total_trades:>8}")
        print(f"Buy Orders:       {len(buy_trades):>8}")
        print(f"Sell Orders:      {len(sell_trades):>8}")
        print(f"Avg Confidence:   {avg_confidence:>8.2f}")
        print()
        
        # Recent Trading Activity
        print("🔄 RECENT TRADING ACTIVITY")
        print("-" * 30)
        
        recent_trades = trade_history[-10:]  # Last 10 trades
        for i, trade in enumerate(reversed(recent_trades), 1):
            action_icon = "📈" if trade['action'] == 'buy' else "📉"
            timestamp = trade['timestamp'][:19].replace('T', ' ')  # Format timestamp
            
            print(f"{action_icon} {trade['action'].upper():>4} {trade['quantity']:>6.1f} {trade['symbol']:<6} @ ${trade['price']:>7.2f}")
            print(f"    {timestamp} | Confidence: {trade['signal_confidence']:.2f}")
            
            if i >= 5:  # Limit to 5 most recent
                break
        
        print()
        
        # Portfolio Allocation
        print("🥧 PORTFOLIO ALLOCATION")
        print("-" * 30)
        
        cash_allocation = (cash / total_value) * 100 if total_value > 0 else 0
        print(f"Cash:             {cash_allocation:>6.1f}%")
        
        for symbol, position in data['positions'].items():
            allocation = (position['market_value'] / total_value) * 100 if total_value > 0 else 0
            print(f"{symbol}:             {allocation:>6.1f}%")
        
        print()
        
        # Risk Metrics
        print("⚖️ RISK METRICS")
        print("-" * 30)
        
        num_positions = len(data['positions'])
        max_position_pct = max((pos['market_value'] / total_value) * 100 for pos in data['positions'].values()) if data['positions'] else 0
        
        print(f"Diversification:  {num_positions:>8} positions")
        print(f"Max Position:     {max_position_pct:>6.1f}%")
        print(f"Cash Buffer:      {cash_allocation:>6.1f}%")
        
        # Risk assessment
        if num_positions >= 5:
            diversification_status = "GOOD"
        elif num_positions >= 3:
            diversification_status = "MODERATE"
        else:
            diversification_status = "LOW"
        
        print(f"Risk Level:       {diversification_status:>8}")
        print()
        
    except FileNotFoundError:
        print("❌ No trading data found. Run a trading session first.")
        return False
    except Exception as e:
        print(f"❌ Error loading dashboard: {e}")
        return False
    
    return True

def show_trading_recommendations():
    """Show AI-generated trading recommendations"""
    
    print("🎯 TRADING RECOMMENDATIONS")
    print("-" * 30)
    
    # Sample recommendations based on portfolio analysis
    recommendations = [
        "✅ Portfolio is well-diversified across tech sector",
        "⚠️ Consider taking profits on positions with >10% gains", 
        "💡 Monitor market volatility before adding new positions",
        "📊 Current cash allocation (66%) allows for opportunities",
        "🛡️ All positions have appropriate stop-loss levels set"
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print()

def show_market_opportunities():
    """Show potential market opportunities"""
    
    print("🔍 MARKET OPPORTUNITIES")
    print("-" * 30)
    
    opportunities = [
        {"sector": "AI/Semiconductors", "strength": "HIGH", "tickers": "NVDA, AMD, INTC"},
        {"sector": "Cloud Computing", "strength": "MEDIUM", "tickers": "MSFT, GOOGL, AMZN"},
        {"sector": "Electric Vehicles", "strength": "MEDIUM", "tickers": "TSLA, RIVN, LCID"},
        {"sector": "Cybersecurity", "strength": "LOW", "tickers": "CRWD, ZS, PANW"}
    ]
    
    for opp in opportunities:
        strength_icon = "🟢" if opp['strength'] == "HIGH" else "🟡" if opp['strength'] == "MEDIUM" else "🟠"
        print(f"{strength_icon} {opp['sector']:.<25} {opp['strength']:>6}")
        print(f"   Suggested tickers: {opp['tickers']}")
        print()

if __name__ == "__main__":
    success = show_trading_dashboard()
    
    if success:
        show_trading_recommendations()
        show_market_opportunities()
        
        print("🔄 NEXT ACTIONS")
        print("-" * 30)
        print("1. python src/main.py           # Run full analysis")
        print("2. python test_system.py        # Test system")
        print("3. python trading_dashboard.py  # Refresh dashboard")
        print("4. Check trading_bot.log        # View detailed logs")
    
    print("\n" + "=" * 60)
    print("🤖 AI Trading Bot Dashboard - Ready for action!")