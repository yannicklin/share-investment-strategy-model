"""
Portfolio Initialization Script

This script initializes the portfolio with starting capital for each market.
Run this after database migration to set up initial cash balances.

Usage:
    python scripts/init_portfolio.py

Author: Yannick
Copyright (c) 2026 Yannick
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bot import create_app, db
from app.bot.services.portfolio_service import PortfolioService

# Initial capital per market (AUD/USD/TWD)
INITIAL_CAPITAL = {
    'ASX': 10000.0,   # AUD 10,000
    'USA': 10000.0,   # USD 10,000
    'TWN': 300000.0,  # TWD 300,000 (~AUD 13,000)
}


def init_portfolios():
    """Initialize portfolios with starting capital for all markets."""
    app = create_app()
    
    with app.app_context():
        print("🔧 Initializing portfolios...")
        
        for market, capital in INITIAL_CAPITAL.items():
            print(f"\n📊 {market} Market:")
            
            service = PortfolioService(market)
            portfolio = service.get_or_create_portfolio(initial_cash=capital)
            
            print(f"   ✅ Portfolio initialized")
            print(f"   💵 Starting capital: ${capital:,.2f}")
            
            # Display summary
            summary = service.get_portfolio_summary()
            print(f"   📈 Cash: ${summary['cash']:,.2f}")
            print(f"   📦 Positions: {len(summary['positions'])}")
        
        print("\n✅ All portfolios initialized successfully!")


if __name__ == '__main__':
    init_portfolios()
