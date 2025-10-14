"""
Trading API - Interface for executing trades and portfolio management
This module provides both paper trading simulation and real trading API integration.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class PaperTradingPortfolio:
    """Simulated portfolio for paper trading."""
    
    def __init__(self, initial_balance: float = 100000.0):
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.positions = {}  # symbol -> {'quantity': float, 'avg_price': float, 'market_value': float}
        self.trade_history = []
        self.created_at = datetime.now()
        
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value."""
        positions_value = sum(pos['market_value'] for pos in self.positions.values())
        return self.cash + positions_value
    
    def get_position(self, symbol: str) -> Dict:
        """Get position info for a symbol."""
        return self.positions.get(symbol, {'quantity': 0, 'avg_price': 0, 'market_value': 0})
    
    def update_market_values(self, prices: Dict[str, float]):
        """Update market values based on current prices."""
        for symbol, position in self.positions.items():
            if symbol in prices:
                position['market_value'] = position['quantity'] * prices[symbol]


class TradeExecutor:
    """Main class for executing trades."""
    
    def __init__(self, mode: str = 'paper', config: Optional[Dict] = None):
        """
        Initialize trade executor.
        
        Args:
            mode: 'paper' for simulation, 'live' for real trading
            config: Configuration dictionary
        """
        self.mode = mode
        self.config = config or {}
        self.portfolio = PaperTradingPortfolio(
            initial_balance=self.config.get('initial_balance', 100000.0)
        )
        self.data_file = self.config.get('data_file', 'trading_data.json')
        
        # Load existing data if available
        self._load_portfolio_data()
        
        logger.info(f"Trade executor initialized in {mode} mode")
    
    def _load_portfolio_data(self):
        """Load portfolio data from file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.portfolio.cash = data.get('cash', self.portfolio.initial_balance)
                    self.portfolio.positions = data.get('positions', {})
                    self.portfolio.trade_history = data.get('trade_history', [])
                    logger.info(f"Loaded portfolio data from {self.data_file}")
        except Exception as e:
            logger.warning(f"Could not load portfolio data: {e}")
    
    def _save_portfolio_data(self):
        """Save portfolio data to file."""
        try:
            data = {
                'cash': self.portfolio.cash,
                'positions': self.portfolio.positions,
                'trade_history': self.portfolio.trade_history,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved portfolio data to {self.data_file}")
        except Exception as e:
            logger.error(f"Could not save portfolio data: {e}")
    
    def _get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.
        In paper trading, this simulates market prices.
        """
        # Simulate prices for common symbols
        base_prices = {
            'AAPL': 150.0,
            'MSFT': 300.0,
            'GOOGL': 2500.0,
            'AMZN': 3200.0,
            'TSLA': 800.0,
            'SPY': 420.0,
            'QQQ': 350.0,
            'IWM': 180.0
        }
        
        # Add some random variation (±2%)
        import random
        base_price = base_prices.get(symbol, 100.0)
        variation = random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + variation)
        
        return round(current_price, 2)
    
    def execute_trade(self, signal: Dict) -> Dict:
        """
        Execute a single trade based on a signal.
        
        Args:
            signal: Risk-managed signal dictionary
        
        Returns:
            Execution result dictionary
        """
        try:
            symbol = signal['symbol']
            action = signal['action']
            position_size_pct = signal['position_size']
            
            # Get current price
            current_price = self._get_current_price(symbol)
            
            # Calculate trade amount
            portfolio_value = self.portfolio.get_portfolio_value()
            trade_value = portfolio_value * position_size_pct
            quantity = trade_value / current_price
            
            # Execute based on action
            if action == 'buy':
                result = self._execute_buy(symbol, quantity, current_price, signal)
            elif action == 'sell':
                result = self._execute_sell(symbol, quantity, current_price, signal)
            else:  # hold
                result = {
                    'status': 'skipped',
                    'message': 'Hold signal - no action taken',
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Save portfolio state
            self._save_portfolio_data()
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing trade for {signal.get('symbol', 'Unknown')}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'symbol': signal.get('symbol', 'Unknown'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _execute_buy(self, symbol: str, quantity: float, price: float, signal: Dict) -> Dict:
        """Execute a buy order."""
        try:
            total_cost = quantity * price
            
            # Check if we have enough cash
            if total_cost > self.portfolio.cash:
                return {
                    'status': 'rejected',
                    'message': f'Insufficient cash. Need ${total_cost:.2f}, have ${self.portfolio.cash:.2f}',
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Execute the buy
            self.portfolio.cash -= total_cost
            
            # Update position
            if symbol in self.portfolio.positions:
                # Average down/up the position
                current_pos = self.portfolio.positions[symbol]
                total_quantity = current_pos['quantity'] + quantity
                avg_price = ((current_pos['quantity'] * current_pos['avg_price']) + 
                           (quantity * price)) / total_quantity
                
                self.portfolio.positions[symbol] = {
                    'quantity': total_quantity,
                    'avg_price': avg_price,
                    'market_value': total_quantity * price
                }
            else:
                # New position
                self.portfolio.positions[symbol] = {
                    'quantity': quantity,
                    'avg_price': price,
                    'market_value': quantity * price
                }
            
            # Record trade
            trade_record = {
                'symbol': symbol,
                'action': 'buy',
                'quantity': quantity,
                'price': price,
                'total_value': total_cost,
                'timestamp': datetime.now().isoformat(),
                'signal_confidence': signal.get('confidence', 0.0),
                'stop_loss': signal.get('stop_loss'),
                'price_target': signal.get('price_target'),
                'reasoning': signal.get('reasoning', '')
            }
            
            self.portfolio.trade_history.append(trade_record)
            
            logger.info(f"BUY executed: {quantity:.2f} shares of {symbol} at ${price:.2f}")
            
            return {
                'status': 'executed',
                'message': f'Successfully bought {quantity:.2f} shares at ${price:.2f}',
                'symbol': symbol,
                'action': 'buy',
                'quantity': quantity,
                'price': price,
                'total_cost': total_cost,
                'timestamp': datetime.now().isoformat(),
                'trade_id': len(self.portfolio.trade_history)
            }
        
        except Exception as e:
            logger.error(f"Error executing buy for {symbol}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            }
    
    def _execute_sell(self, symbol: str, quantity: float, price: float, signal: Dict) -> Dict:
        """Execute a sell order."""
        try:
            # Check if we have the position
            current_position = self.portfolio.get_position(symbol)
            
            if current_position['quantity'] <= 0:
                return {
                    'status': 'rejected',
                    'message': f'No position in {symbol} to sell',
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Limit sell quantity to what we own
            actual_quantity = min(quantity, current_position['quantity'])
            total_value = actual_quantity * price
            
            # Execute the sell
            self.portfolio.cash += total_value
            
            # Update position
            remaining_quantity = current_position['quantity'] - actual_quantity
            
            if remaining_quantity > 0.01:  # Keep position if significant amount remains
                self.portfolio.positions[symbol] = {
                    'quantity': remaining_quantity,
                    'avg_price': current_position['avg_price'],
                    'market_value': remaining_quantity * price
                }
            else:
                # Close position completely
                del self.portfolio.positions[symbol]
            
            # Calculate P&L
            cost_basis = actual_quantity * current_position['avg_price']
            pnl = total_value - cost_basis
            pnl_pct = (pnl / cost_basis) * 100 if cost_basis > 0 else 0
            
            # Record trade
            trade_record = {
                'symbol': symbol,
                'action': 'sell',
                'quantity': actual_quantity,
                'price': price,
                'total_value': total_value,
                'cost_basis': cost_basis,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'timestamp': datetime.now().isoformat(),
                'signal_confidence': signal.get('confidence', 0.0),
                'reasoning': signal.get('reasoning', '')
            }
            
            self.portfolio.trade_history.append(trade_record)
            
            logger.info(f"SELL executed: {actual_quantity:.2f} shares of {symbol} at ${price:.2f} "
                       f"(P&L: ${pnl:.2f}, {pnl_pct:.1f}%)")
            
            return {
                'status': 'executed',
                'message': f'Successfully sold {actual_quantity:.2f} shares at ${price:.2f}',
                'symbol': symbol,
                'action': 'sell',
                'quantity': actual_quantity,
                'price': price,
                'total_value': total_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'timestamp': datetime.now().isoformat(),
                'trade_id': len(self.portfolio.trade_history)
            }
        
        except Exception as e:
            logger.error(f"Error executing sell for {symbol}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            }


def execute_trades(signals: List[Dict], mode: str = 'paper', config: Optional[Dict] = None) -> Dict:
    """
    Execute a batch of trading signals.
    
    Args:
        signals: List of risk-managed signal dictionaries
        mode: Trading mode ('paper' or 'live')
        config: Configuration dictionary
    
    Returns:
        Batch execution results
    """
    try:
        executor = TradeExecutor(mode=mode, config=config)
        
        results = {
            'execution_summary': {
                'total_signals': len(signals),
                'executed': 0,
                'rejected': 0,
                'errors': 0,
                'skipped': 0
            },
            'trade_results': [],
            'portfolio_snapshot': {},
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Starting batch execution of {len(signals)} signals in {mode} mode")
        
        # Execute each signal
        for i, signal in enumerate(signals, 1):
            logger.info(f"Executing signal {i}/{len(signals)}: {signal.get('symbol', 'Unknown')}")
            
            trade_result = executor.execute_trade(signal)
            results['trade_results'].append(trade_result)
            
            # Update counters
            status = trade_result.get('status', 'error')
            if status in results['execution_summary']:
                results['execution_summary'][status] += 1
            else:
                results['execution_summary']['errors'] += 1
        
        # Get final portfolio snapshot
        portfolio_value = executor.portfolio.get_portfolio_value()
        results['portfolio_snapshot'] = {
            'total_value': portfolio_value,
            'cash': executor.portfolio.cash,
            'positions_value': portfolio_value - executor.portfolio.cash,
            'number_of_positions': len(executor.portfolio.positions),
            'positions': executor.portfolio.positions.copy(),
            'total_return': ((portfolio_value - executor.portfolio.initial_balance) / 
                           executor.portfolio.initial_balance) * 100
        }
        
        logger.info(f"Batch execution completed. Portfolio value: ${portfolio_value:,.2f}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in batch trade execution: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def get_portfolio_status(mode: str = 'paper', config: Optional[Dict] = None) -> Dict:
    """
    Get current portfolio status and performance metrics.
    
    Args:
        mode: Trading mode
        config: Configuration dictionary
    
    Returns:
        Portfolio status dictionary
    """
    try:
        executor = TradeExecutor(mode=mode, config=config)
        
        # Update market values with current prices
        current_prices = {}
        for symbol in executor.portfolio.positions.keys():
            current_prices[symbol] = executor._get_current_price(symbol)
        
        executor.portfolio.update_market_values(current_prices)
        
        portfolio_value = executor.portfolio.get_portfolio_value()
        
        # Calculate performance metrics
        total_return = ((portfolio_value - executor.portfolio.initial_balance) / 
                       executor.portfolio.initial_balance) * 100
        
        # Analyze recent trades
        recent_trades = executor.portfolio.trade_history[-10:]  # Last 10 trades
        winning_trades = [t for t in recent_trades if t.get('pnl', 0) > 0]
        win_rate = (len(winning_trades) / len(recent_trades)) * 100 if recent_trades else 0
        
        # Portfolio allocation
        positions_value = sum(pos['market_value'] for pos in executor.portfolio.positions.values())
        cash_allocation = (executor.portfolio.cash / portfolio_value) * 100 if portfolio_value > 0 else 100
        
        return {
            'portfolio_summary': {
                'total_value': portfolio_value,
                'initial_balance': executor.portfolio.initial_balance,
                'cash': executor.portfolio.cash,
                'positions_value': positions_value,
                'total_return_pct': total_return,
                'cash_allocation_pct': cash_allocation
            },
            'positions': executor.portfolio.positions,
            'performance_metrics': {
                'total_trades': len(executor.portfolio.trade_history),
                'recent_win_rate': win_rate,
                'number_of_positions': len(executor.portfolio.positions)
            },
            'recent_trades': recent_trades,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting portfolio status: {e}")
        return {'error': str(e)}


if __name__ == "__main__":
    # Test the trading API
    print("Testing Trading API...")
    
    # Create a mock signal for testing
    test_signal = {
        'symbol': 'AAPL',
        'action': 'buy',
        'confidence': 0.75,
        'position_size': 0.05,  # 5% of portfolio
        'price_target': 160.0,
        'stop_loss': 140.0,
        'reasoning': 'Strong bullish indicators from NLP analysis'
    }
    
    print("\n1. Testing single trade execution:")
    config = {'initial_balance': 100000.0}
    results = execute_trades([test_signal], mode='paper', config=config)
    
    print(f"Execution results:")
    print(f"  Executed: {results['execution_summary']['executed']}")
    print(f"  Rejected: {results['execution_summary']['rejected']}")
    print(f"  Portfolio value: ${results['portfolio_snapshot']['total_value']:,.2f}")
    
    if results['trade_results']:
        trade = results['trade_results'][0]
        print(f"  Trade status: {trade['status']}")
        if trade['status'] == 'executed':
            print(f"  Bought {trade['quantity']:.2f} shares at ${trade['price']:.2f}")
    
    print("\n2. Testing portfolio status:")
    status = get_portfolio_status(mode='paper', config=config)
    
    if 'error' not in status:
        print(f"Portfolio Summary:")
        print(f"  Total Value: ${status['portfolio_summary']['total_value']:,.2f}")
        print(f"  Cash: ${status['portfolio_summary']['cash']:,.2f}")
        print(f"  Positions Value: ${status['portfolio_summary']['positions_value']:,.2f}")
        print(f"  Total Return: {status['portfolio_summary']['total_return_pct']:.2f}%")
        print(f"  Number of Positions: {status['performance_metrics']['number_of_positions']}")
    else:
        print(f"Error: {status['error']}")
    
    print("\nTrading API test completed!")
