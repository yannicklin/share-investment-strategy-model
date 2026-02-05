#!/usr/bin/env python3
"""
Initialize Default ASX Profile

This script loads the default trading configuration from the ASX branch
and creates the initial ConfigProfile in the database.

Source: asx:core/config.py (ASX branch default configuration)

Usage:
    python scripts/init_default_profile.py
    
Prerequisites:
    - DATABASE_URL environment variable set
    - Flask app initialized (run_bot.py)
    - Database tables created (via db.create_all())
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bot import create_app, db
from app.bot.shared.models import ConfigProfile


def init_asx_default_profile():
    """
    Create default ASX trading profile based on ASX branch configuration
    
    Default stocks from asx:core/config.py:
    - ABB.AX: Aussie Broadband
    - SIG.AX: Sigma Healthcare
    - IOZ.AX: iShares Core S&P/ASX 200 ETF
    - INR.AX: Ioneer
    - IMU.AX: Imugene
    - MQG.AX: Macquarie Group
    - PLS.AX: Pilbara Minerals
    - XRO.AX: Xero
    - TCL.AX: Transurban Group
    - SHL.AX: Sonic Healthcare
    """
    
    # Default configuration from ASX branch
    DEFAULT_STOCKS = [
        "ABB",  # Aussie Broadband
        "SIG",  # Sigma Healthcare
        "IOZ",  # iShares Core S&P/ASX 200 ETF
        "INR",  # Ioneer
        "IMU",  # Imugene
        "MQG",  # Macquarie Group
        "PLS",  # Pilbara Minerals
        "XRO",  # Xero
        "TCL",  # Transurban Group
        "SHL"   # Sonic Healthcare
    ]
    
    # Financial parameters from ASX branch
    INIT_CAPITAL = 3000.0
    HOLDING_PERIOD = 30  # days
    HURDLE_RATE = 0.05  # 5% minimum return after costs
    STOP_LOSS = 0.15  # 15% stop loss threshold
    MAX_POSITION_SIZE = 3000.0  # $3,000 per position
    
    app = create_app()
    
    with app.app_context():
        # Check if default profile already exists
        existing = ConfigProfile.for_market('ASX').filter_by(
            name='Default Growth Portfolio'
        ).first()
        
        if existing:
            print("⚠️  Default ASX profile already exists:")
            print(f"   ID: {existing.id}")
            print(f"   Market: {existing.market}")
            print(f"   Name: {existing.name}")
            print(f"   Stocks: {len(existing.stocks)} tickers")
            print(f"   Hurdle Rate: {existing.hurdle_rate*100:.1f}%")
            print(f"   Holding Period: {existing.holding_period} days")
            print(f"   Stop Loss: {existing.stop_loss*100:.1f}%")
            print(f"   Max Position: ${existing.max_position_size:,.0f}")
            print("\n✅ No action needed - profile already initialized")
            return
        
        # Create new default profile
        profile = ConfigProfile(
            market='ASX',
            name='Default Growth Portfolio',
            stocks=DEFAULT_STOCKS,
            holding_period=HOLDING_PERIOD,
            hurdle_rate=HURDLE_RATE,
            max_position_size=MAX_POSITION_SIZE,
            stop_loss=STOP_LOSS
        )
        
        db.session.add(profile)
        db.session.commit()
        
        print("✅ Successfully created default ASX profile:")
        print(f"   Market: {profile.market}")
        print(f"   Name: {profile.name}")
        print(f"   Stocks: {len(profile.stocks)} tickers")
        print(f"   Portfolio:")
        for i, ticker in enumerate(profile.stocks, 1):
            print(f"      {i:2d}. {ticker}.AX")
        print(f"\n   Configuration:")
        print(f"      Holding Period: {profile.holding_period} days")
        print(f"      Hurdle Rate: {profile.hurdle_rate*100:.1f}% (minimum return after costs)")
        print(f"      Stop Loss: {profile.stop_loss*100:.1f}%")
        print(f"      Max Position Size: ${profile.max_position_size:,.0f}")
        print(f"\n   Cost Structure (from ASX branch):")
        print(f"      Brokerage: 0.12%")
        print(f"      Clearing Fee: 0.00225%")
        print(f"      Settlement Fee: $1.50")
        print(f"      Tax Rate: 25%")
        print(f"      Risk Buffer: 0.5% (slippage/volatility)")
        print(f"\n🎉 Default profile ready for signal generation!")


if __name__ == '__main__':
    try:
        init_asx_default_profile()
    except Exception as e:
        print(f"❌ Error initializing default profile: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
