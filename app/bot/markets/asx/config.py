"""
ASX (Australian Securities Exchange) Market Configuration

Market-specific constants for Australian stock market trading.
"""

# Market Identity
MARKET_CODE = 'ASX'
MARKET_NAME = 'Australian Securities Exchange'
COUNTRY_CODE = 'AU'

# Trading Parameters
TICKER_SUFFIX = '.AX'  # Yahoo Finance suffix for ASX stocks
CURRENCY = 'AUD'
TIMEZONE = 'Australia/Sydney'

# Trading Hours (AEST/AEDT)
TRADING_HOURS_START = '10:00'
TRADING_HOURS_END = '16:00'
PRE_MARKET_START = '09:00'
AFTER_HOURS_END = '17:00'

# Signal Generation
SIGNAL_TIME = '08:00'  # Daily signal generation time (AEST)
SIGNAL_CRON = '0 22 * * 0-4'  # 08:00 AEST = 22:00 UTC (previous day)
BACKUP_SIGNAL_CRON = '0 0 * * 1-5'  # 10:00 AEST = 00:00 UTC (backup trigger)

# Market-Specific Validation
MIN_PRICE = 0.001  # Minimum stock price (AUD)
MAX_PRICE = 100000.0  # Maximum stock price (AUD)
MIN_VOLUME = 10000  # Minimum daily volume
MAX_STOCKS_PER_PROFILE = 50  # Maximum stocks in one profile

# Default Trading Strategy
DEFAULT_HOLDING_PERIOD = 30  # days
DEFAULT_HURDLE_RATE = 0.05  # 5% minimum return after fees
DEFAULT_MAX_POSITION = 10000.0  # AUD
DEFAULT_STOP_LOSS = 0.10  # 10% stop loss

# Data Sources
DATA_SOURCE = 'Yahoo Finance'
DATA_INTERVAL = '1d'  # Daily data
LOOKBACK_PERIOD = 730  # 2 years of historical data for training

# Holidays (ASX closed - simplified list, expand as needed)
PUBLIC_HOLIDAYS = [
    '2026-01-01',  # New Year's Day
    '2026-01-26',  # Australia Day
    '2026-04-10',  # Good Friday
    '2026-04-13',  # Easter Monday
    '2026-04-25',  # ANZAC Day
    '2026-12-25',  # Christmas Day
    '2026-12-28',  # Boxing Day (observed)
]
