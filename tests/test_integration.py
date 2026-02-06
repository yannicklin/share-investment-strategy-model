#!/usr/bin/env python3
"""
ASX AI Trading System - Integration Tests

Purpose: Verify trading constraints and ledger components are properly integrated
         without running full backtest.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import sys
import pandas as pd
from datetime import datetime

print("=" * 70)
print("ASX AI Trading System - Integration Test Suite")
print("=" * 70)

# Test 1: Import core utilities
print("\n[1/6] Testing core utilities import...")
try:
    from core.utils import (
        format_date_with_weekday,
        get_asx_trading_days,
        calculate_trading_days_ahead,
        validate_buy_capacity,
    )
    print("✅ All utility functions imported successfully")
except ImportError as e:
    print(f"❌ Failed to import utilities: {e}")
    sys.exit(1)

# Test 2: Date formatting
print("\n[2/6] Testing date formatting...")
try:
    test_date = pd.Timestamp("2026-02-06")
    formatted = format_date_with_weekday(test_date)
    assert formatted == "2026-02-06(THU)", f"Expected '2026-02-06(THU)', got '{formatted}'"
    print(f"✅ Date formatting works: {formatted}")
except Exception as e:
    print(f"❌ Date formatting failed: {e}")
    sys.exit(1)

# Test 3: ASX trading days calendar
print("\n[3/6] Testing ASX trading days fetching...")
try:
    start = pd.Timestamp("2026-01-01")
    end = pd.Timestamp("2026-01-31")
    trading_days = get_asx_trading_days(start, end)
    
    # Verify weekends are excluded
    weekends = [d for d in trading_days if d.dayofweek >= 5]
    assert len(weekends) == 0, f"Found {len(weekends)} weekend days in trading calendar"
    
    print(f"✅ ASX calendar works: {len(trading_days)} trading days in Jan 2026")
    print(f"   (Expected ~22 trading days, excludes weekends + holidays)")
except Exception as e:
    print(f"❌ ASX calendar failed: {e}")
    sys.exit(1)

# Test 4: Trading days ahead calculation
print("\n[4/6] Testing trading days ahead calculation...")
try:
    start_date = pd.Timestamp("2026-02-03")  # Monday
    trading_days_year = get_asx_trading_days(
        pd.Timestamp("2026-01-01"), pd.Timestamp("2026-12-31")
    )
    
    # Calculate 5 trading days ahead
    target_date = calculate_trading_days_ahead(start_date, 5, trading_days_year)
    
    if target_date:
        days_diff = (target_date - start_date).days
        print(f"✅ Trading days calculation works:")
        print(f"   Start: {format_date_with_weekday(start_date)}")
        print(f"   5 trading days later: {format_date_with_weekday(target_date)}")
        print(f"   Calendar days span: {days_diff} days")
    else:
        print("❌ Failed to calculate trading days ahead")
        sys.exit(1)
except Exception as e:
    print(f"❌ Trading days calculation failed: {e}")
    sys.exit(1)

# Test 5: Portfolio validation
print("\n[5/6] Testing portfolio validation...")
try:
    # Test sufficient cash
    result1 = validate_buy_capacity(10000, {"ABB.AX": 15.25, "SIG.AX": 55.0})
    assert result1["can_trade"] == True, "Should be able to trade with sufficient cash"
    assert "ABB.AX" in result1["affordable_tickers"], "ABB.AX should be affordable"
    
    # Test insufficient cash
    result2 = validate_buy_capacity(50, {"ABB.AX": 55.0})
    assert result2["can_trade"] == False, "Should not be able to trade with insufficient cash"
    assert len(result2["affordable_tickers"]) == 0, "No tickers should be affordable"
    
    print("✅ Portfolio validation works:")
    print(f"   $10,000 cash: Can afford {len(result1['affordable_tickers'])} tickers")
    print(f"   $50 cash: {result2['reason']}")
except Exception as e:
    print(f"❌ Portfolio validation failed: {e}")
    sys.exit(1)

# Test 6: Transaction ledger
print("\n[6/6] Testing transaction ledger...")
try:
    from core.transaction_ledger import TransactionLedger
    
    ledger = TransactionLedger()
    
    # Add test entry
    ledger.add_entry(
        date=pd.Timestamp("2026-02-06"),
        ticker="TEST.AX",
        action="BUY",
        quantity=100,
        price=15.25,
        commission=9.95,
        cash_before=10000,
        cash_after=8464.55,
        positions_before={},
        positions_after={"TEST.AX": 100},
        strategy="test_strategy",
        notes="Integration test",
    )
    
    # Verify entry
    last_entry = ledger.get_last_entry()
    assert last_entry is not None, "Ledger entry should exist"
    assert last_entry["ticker"] == "TEST.AX", "Ticker mismatch"
    assert last_entry["date"] == "2026-02-06(THU)", "Date formatting not applied"
    
    # Test save (will create data/ledgers/ if needed)
    filepath = ledger.save_to_file(filename="integration_test.csv")
    
    import os
    assert os.path.exists(filepath), f"Ledger file not created at {filepath}"
    
    print("✅ Transaction ledger works:")
    print(f"   Entry recorded: {last_entry['action']} {last_entry['quantity']} units @ ${last_entry['price']}")
    print(f"   Saved to: {filepath}")
    
    # Cleanup test file
    os.remove(filepath)
    print(f"   Cleaned up test file")
    
except Exception as e:
    print(f"❌ Transaction ledger failed: {e}")
    sys.exit(1)

# Final summary
print("\n" + "=" * 70)
print("✅ ALL INTEGRATION TESTS PASSED")
print("=" * 70)
print("\nImplementation Status:")
print("  ✅ Date formatting (YYYY-MM-DD(DAY))")
print("  ✅ ASX market calendar (pandas_market_calendars)")
print("  ✅ Trading days calculation")
print("  ✅ Portfolio validation")
print("  ✅ Transaction ledger (memory-optimized)")
print("\nReady for GitHub Codespace testing!")
print("=" * 70)
