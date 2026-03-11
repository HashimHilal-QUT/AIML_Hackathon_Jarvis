#!/usr/bin/env python3
"""
NEPSE Analysis Runner Script
This script demonstrates different ways to run the NEPSE analysis
"""

import asyncio
import argparse
import json
from datetime import datetime
from nepse_enhanced_agent import NepseEnhancedAgent

async def run_single_stock_analysis(symbol: str):
    """Run analysis for a single stock"""
    print(f"\nAnalyzing {symbol}...")
    agent = NepseEnhancedAgent()
    analysis = await agent.generate_enhanced_signals(symbol)
    
    # Save to file
    filename = f"analysis_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w') as f:
        f.write(f"NEPSE STOCK ANALYSIS REPORT\n")
        f.write(f"Symbol: {symbol}\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        
        # Write technical analysis
        f.write("TECHNICAL ANALYSIS\n")
        f.write("-" * 20 + "\n")
        for indicator, value in analysis['analysis']['technical'].items():
            f.write(f"{indicator}: {value}\n")
        
        # Write fundamental analysis
        f.write("\nFUNDAMENTAL ANALYSIS\n")
        f.write("-" * 20 + "\n")
        for metric, value in analysis['analysis']['fundamental'].items():
            f.write(f"{metric}: {value}\n")
        
        # Write trading signals
        f.write("\nTRADING SIGNALS\n")
        f.write("-" * 20 + "\n")
        if analysis['signals']['valid']:
            signals = analysis['signals']['signals']
            f.write(f"Entry Price: {signals['entry_exit']['entry_price']}\n")
            f.write(f"Stop Loss: {signals['entry_exit']['stop_loss']}\n")
            f.write(f"Take Profit: {signals['entry_exit']['take_profit']}\n")
            f.write(f"Position Size: {signals['position_size']}\n")
            f.write(f"Confidence: {signals['confidence']}\n")
    
    print(f"Analysis saved to {filename}")

async def run_market_analysis():
    """Run analysis for the entire market"""
    print("\nAnalyzing entire market...")
    agent = NepseEnhancedAgent()
    report = await agent.generate_daily_report()
    
    # Save to file
    filename = f"market_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w') as f:
        f.write(f"NEPSE MARKET ANALYSIS REPORT\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        
        # Write market summary
        f.write("MARKET SUMMARY\n")
        f.write("-" * 20 + "\n")
        for key, value in report['market_summary'].items():
            f.write(f"{key}: {value}\n")
        
        # Write top performers
        f.write("\nTOP PERFORMERS\n")
        f.write("-" * 20 + "\n")
        for stock in report['top_gainers']:
            f.write(f"{stock['symbol']}: {stock['price']} ({stock['change']}%)\n")
        
        # Write trading signals
        f.write("\nTRADING SIGNALS\n")
        f.write("-" * 20 + "\n")
        for signal_type, signals in report['trading_signals'].items():
            f.write(f"\n{signal_type.upper()}:\n")
            for signal in signals:
                f.write(f"{signal['symbol']}: {signal['entry_price']}\n")
    
    print(f"Market analysis saved to {filename}")

async def run_scheduled_analysis(interval: int):
    """Run analysis at regular intervals"""
    print(f"\nStarting scheduled analysis every {interval} minutes...")
    while True:
        try:
            await run_market_analysis()
            print(f"Waiting {interval} minutes for next analysis...")
            await asyncio.sleep(interval * 60)
        except Exception as e:
            print(f"Error in scheduled analysis: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

def main():
    parser = argparse.ArgumentParser(description='NEPSE Analysis Runner')
    parser.add_argument('--mode', choices=['single', 'market', 'scheduled'],
                      required=True, help='Analysis mode')
    parser.add_argument('--symbol', help='Stock symbol for single stock analysis')
    parser.add_argument('--interval', type=int, default=60,
                      help='Interval in minutes for scheduled analysis')
    
    args = parser.parse_args()
    
    if args.mode == 'single' and not args.symbol:
        parser.error("--symbol is required for single stock analysis")
    
    if args.mode == 'single':
        asyncio.run(run_single_stock_analysis(args.symbol))
    elif args.mode == 'market':
        asyncio.run(run_market_analysis())
    elif args.mode == 'scheduled':
        asyncio.run(run_scheduled_analysis(args.interval))

if __name__ == "__main__":
    main() 