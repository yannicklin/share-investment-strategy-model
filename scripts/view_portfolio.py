"""
Portfolio Status Viewer

Quick utility to view current portfolio status across all markets.

Usage:
    python scripts/view_portfolio.py
    python scripts/view_portfolio.py ASX
    python scripts/view_portfolio.py --transactions

Author: Yannick
Copyright (c) 2026 Yannick
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bot import create_app, db
from app.bot.services.portfolio_service import PortfolioService
from app.bot.shared.models import Transaction, Position, Portfolio


def print_separator(char="=", length=60):
    """Print a separator line."""
    print(char * length)


def view_portfolio_summary(market):
    """Display portfolio summary for a market."""
    service = PortfolioService(market)
    summary = service.get_portfolio_summary()
    
    print_separator()
    print(f"{market} PORTFOLIO SUMMARY")
    print_separator()
    print(f"💵 Cash Balance: ${summary['cash']:,.2f}")
    print(f"📦 Total Positions: {len(summary['positions'])}")
    
    if summary['positions']:
        print("\n📊 Holdings:")
        for ticker, details in summary['positions'].items():
            qty = details['quantity']
            avg = details['avg_price']
            value = qty * avg
            print(f"   • {ticker:8s}: {qty:8.2f} units @ ${avg:8.2f} avg = ${value:12,.2f}")
    
    print(f"\n💰 Total Portfolio Value: ${summary['total_value']:,.2f}")
    print_separator()


def view_recent_transactions(market, days=7):
    """Display recent transactions for a market."""
    since = datetime.now() - timedelta(days=days)
    
    transactions = Transaction.for_market(market).filter(
        Transaction.created_at >= since
    ).order_by(Transaction.created_at.desc()).all()
    
    print_separator()
    print(f"{market} RECENT TRANSACTIONS (Last {days} days)")
    print_separator()
    
    if not transactions:
        print("No transactions found.")
    else:
        print(f"{'Date':<12} {'Action':<6} {'Ticker':<8} {'Qty':>8} {'Price':>10} {'Total':>12} {'Cash After':>12}")
        print("-" * 80)
        
        for tx in transactions:
            total = tx.quantity * tx.price
            print(f"{str(tx.date):<12} {tx.action:<6} {tx.ticker:<8} {tx.quantity:8.2f} "
                  f"${tx.price:9.2f} ${total:11,.2f} ${tx.cash_after:11,.2f}")
    
    print_separator()


def main():
    """Main entry point."""
    app = create_app()
    
    with app.app_context():
        # Parse arguments
        show_transactions = '--transactions' in sys.argv or '-t' in sys.argv
        
        # Get market filter
        market_filter = None
        for arg in sys.argv[1:]:
            if arg.upper() in ['ASX', 'USA', 'TWN']:
                market_filter = arg.upper()
                break
        
        # Determine which markets to show
        markets = [market_filter] if market_filter else ['ASX', 'USA', 'TWN']
        
        print("\n")
        print_separator("=", 80)
        print("🤖 AI TRADING BOT - PORTFOLIO STATUS VIEWER")
        print_separator("=", 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_separator("=", 80)
        print("\n")
        
        for market in markets:
            # Check if portfolio exists
            portfolio = Portfolio.for_market(market).first()
            
            if portfolio is None:
                print_separator()
                print(f"{market} PORTFOLIO")
                print_separator()
                print(f"⚠️  Portfolio not initialized. Run: python scripts/init_portfolio.py")
                print_separator()
                print("\n")
                continue
            
            # Show portfolio summary
            view_portfolio_summary(market)
            print("\n")
            
            # Show transactions if requested
            if show_transactions:
                view_recent_transactions(market, days=30)
                print("\n")
        
        print("✅ Portfolio status check complete!\n")


if __name__ == '__main__':
    main()
