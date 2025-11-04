#!/usr/bin/env python3
"""
Main orchestrator for the AI Trading Bot.
This script coordinates the entire workflow: PDF extraction → NLP analysis → signal generation → trading execution.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Import our modules
from pdf_extractor import extract_text_from_pdfs
from nlp_processing import summarize_text, analyze_sentiment, extract_trading_signals
from signal_engine import generate_trading_signals, filter_signals_by_confidence
from risk_manager import calculate_position_size, apply_risk_controls
from trading_api import execute_trades, get_portfolio_status
# This import connects to the crypto trading logic
from crypto_forex_trading import CryptoTradingEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingBotOrchestrator:
    """Main orchestrator class for the AI Trading Bot."""

    def __init__(self, pdf_folder: str = "data/pdfs/", config: Optional[Dict] = None):
        """Initialize the trading bot orchestrator.
        
        Args:
            pdf_folder: Path to folder containing PDF documents
            config: Configuration dictionary for the bot
        """
        self.pdf_folder = pdf_folder
        self.config = config or self._get_default_config()
        self.extracted_texts: Dict[str, str] = {}
        self.analysis_results: Dict = {}
        self.trading_signals: List = []
        
        logger.info("Trading Bot Orchestrator initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for the trading bot."""
        return {
            'risk_tolerance': 0.02,  # 2% risk per trade
            'max_position_size': 0.1,  # 10% max position size
            'confidence_threshold': 0.7,  # 70% minimum confidence for signals
            'trading_mode': 'live',  # Set to 'live' for testnet connection
            'max_daily_trades': 10,
        }
    
    def extract_documents(self) -> Dict[str, str]:
        """Extract text from all PDF documents."""
        logger.info(f"Extracting text from PDFs in {self.pdf_folder}")
        
        try:
            self.extracted_texts = extract_text_from_pdfs(self.pdf_folder)
            logger.info(f"Successfully extracted text from {len(self.extracted_texts)} documents")
            
            # Log document info
            for filename, text in self.extracted_texts.items():
                logger.info(f"Document: {filename}, Length: {len(text)} characters")
            
            return self.extracted_texts
        
        except Exception as e:
            logger.error(f"Error extracting documents: {e}")
            raise
    
    def analyze_documents(self) -> Dict:
        """Analyze extracted documents using NLP."""
        logger.info("Starting NLP analysis of documents")
        
        if not self.extracted_texts:
            raise ValueError("No documents to analyze. Run extract_documents() first.")
        
        self.analysis_results = {}
        
        for filename, text in self.extracted_texts.items():
            logger.info(f"Analyzing document: {filename}")
            
            try:
                # Summarize the document
                summary = summarize_text(text)
                
                # Analyze sentiment
                sentiment = analyze_sentiment(text)
                
                # Extract trading signals from the text
                trading_insights = extract_trading_signals(text)
                
                self.analysis_results[filename] = {
                    'summary': summary,
                    'sentiment': sentiment,
                    'trading_insights': trading_insights,
                    'timestamp': datetime.now().isoformat(),
                    'text_length': len(text)
                }
                
                logger.info(f"Analysis complete for {filename}")
                
            except Exception as e:
                logger.error(f"Error analyzing {filename}: {e}")
                continue
        
        logger.info(f"NLP analysis completed for {len(self.analysis_results)} documents")
        return self.analysis_results
    
    def generate_signals(self) -> List:
        """Generate trading signals from analysis results."""
        logger.info("Generating trading signals")
        
        if not self.analysis_results:
            raise ValueError("No analysis results available. Run analyze_documents() first.")
        
        try:
            # Generate signals from all analysis results
            all_signals = []
            for filename, analysis in self.analysis_results.items():
                signals = generate_trading_signals(analysis)
                for signal in signals:
                    # Add source document to metadata
                    if not hasattr(signal, 'metadata'):
                        signal.metadata = {}
                    signal.metadata['source_document'] = filename
                all_signals.extend(signals)
            
            # Filter signals by confidence threshold
            filtered_signals = filter_signals_by_confidence(
                all_signals, 
                threshold=self.config['confidence_threshold']
            )
            
            self.trading_signals = filtered_signals
            logger.info(f"Generated {len(filtered_signals)} high-confidence trading signals")
            
            return self.trading_signals
        
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            raise
    
    def apply_risk_management(self) -> List:
        """Apply risk management to trading signals."""
        logger.info("Applying risk management to signals")
        
        if not self.trading_signals:
            raise ValueError("No trading signals available. Run generate_signals() first.")
        
        try:
            risk_managed_signals = []
            
            for signal in self.trading_signals:
                # Calculate position size based on risk tolerance
                position_size = calculate_position_size(
                    signal, 
                    risk_tolerance=self.config['risk_tolerance'],
                    max_position_size=self.config['max_position_size']
                )
                
                # Apply risk controls
                controlled_signal = apply_risk_controls(signal, position_size, self.config)
                
                if controlled_signal:  # Signal passed risk checks
                    risk_managed_signals.append(controlled_signal)
            
            logger.info(f"Risk management applied: {len(risk_managed_signals)} signals approved")
            return risk_managed_signals
        
        except Exception as e:
            logger.error(f"Error applying risk management: {e}")
            raise
    
    # --- THIS IS THE MODIFIED SECTION ---
    def execute_trading(self, signals: List) -> Dict:
        """Execute trading signals by connecting to the Binance Testnet."""
        logger.info(f"Executing {len(signals)} trading signals in LIVE mode (connecting to Binance Testnet)")
        
        try:
            # Initialize the Crypto Trading Engine for Binance Testnet.
            # The testnet=True flag ensures no real money is used.
            crypto_engine = CryptoTradingEngine(exchange='binance', testnet=True)
            
            # The engine will adapt the bot's stock signals for crypto markets.
            execution_results = crypto_engine.execute_crypto_trades(signals)
            
            logger.info("Crypto testnet trading execution completed")
            return execution_results
            
        except Exception as e:
            logger.error(f"Error executing crypto testnet trades: {e}")
            raise
    # --- END OF MODIFIED SECTION ---

    def run_full_workflow(self) -> Dict:
        """Run the complete trading bot workflow."""
        logger.info("="*50)
        logger.info("Starting AI Trading Bot Full Workflow")
        logger.info("="*50)
        
        try:
            # Step 1: Extract documents
            logger.info("STEP 1: Document Extraction")
            self.extract_documents()
            
            # Step 2: Analyze documents
            logger.info("STEP 2: NLP Analysis")
            self.analyze_documents()
            
            # Step 3: Generate trading signals
            logger.info("STEP 3: Signal Generation")
            self.generate_signals()
            
            # Step 4: Apply risk management
            logger.info("STEP 4: Risk Management")
            risk_managed_signals = self.apply_risk_management()
            
            # Step 5: Execute trades
            logger.info("STEP 5: Trade Execution")
            execution_results = self.execute_trading(risk_managed_signals)
            
            # Prepare final report
            workflow_results = {
                'documents_processed': len(self.extracted_texts),
                'analysis_results': len(self.analysis_results),
                'raw_signals': len(self.trading_signals),
                'risk_approved_signals': len(risk_managed_signals),
                'execution_results': execution_results,
                'timestamp': datetime.now().isoformat(),
                'config': self.config
            }
            
            logger.info("="*50)
            logger.info("AI Trading Bot Workflow Completed Successfully")
            logger.info(f"Documents processed: {workflow_results['documents_processed']}")
            logger.info(f"Signals generated: {workflow_results['raw_signals']}")
            logger.info(f"Trades executed: {len(risk_managed_signals)}")
            logger.info("="*50)
            
            return workflow_results
        
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            raise
    
    def get_status_report(self) -> Dict:
        """Get current status report of the trading bot."""
        return {
            'extracted_documents': len(self.extracted_texts),
            'analysis_completed': len(self.analysis_results),
            'signals_generated': len(self.trading_signals),
            'config': self.config,
            'last_update': datetime.now().isoformat()
        }


def main():
    """Main entry point for the trading bot."""
    try:
        # Initialize the trading bot
        bot = TradingBotOrchestrator()
        
        # Run the full workflow
        results = bot.run_full_workflow()
        
        # Print summary
        print("\n" + "="*50)
        print("TRADING BOT EXECUTION SUMMARY")
        print("="*50)
        print(f"Documents processed: {results.get('documents_processed', 'N/A')}")
        print(f"Raw signals generated: {results.get('raw_signals', 'N/A')}")
        print(f"Risk-approved signals: {results.get('risk_approved_signals', 'N/A')}")
        
        # Check for crypto-specific results
        if 'crypto_trades' in results.get('execution_results', {}):
             print(f"Crypto trades executed: {results['execution_results']['crypto_trades']}")
             print(f"Crypto pairs traded: {results['execution_results'].get('pairs_traded', [])}")
        
        print(f"Trading mode: {results.get('config', {}).get('trading_mode', 'N/A')}")
        print(f"Execution timestamp: {results.get('timestamp', 'N/A')}")
        print("="*50)
        
        return results
    
    except Exception as e:
        logger.error(f"Trading bot execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()