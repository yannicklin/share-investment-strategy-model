"""
Trend Detection Module - Phase 7

Identifies market regime (UPTREND, DOWNTREND, RANGEBOUND) using technical indicators.
This enables adaptive thresholds for signal generation in different market conditions.

Author: AI Trading System (Phase 7)
Date: June 2, 2026
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def detect_trend(
    data: pd.DataFrame,
    ticker: str,
    lookback_days: int = 20,
    sma_period: int = 50,
    rsi_period: int = 14,
    adx_period: int = 14,
) -> Dict[str, Any]:
    """
    Detect market trend using multiple technical indicators.
    
    Args:
        data: OHLCV DataFrame with Close, High, Low columns (already sorted ascending by date)
        ticker: Stock ticker for logging
        lookback_days: Days to analyze for recent trend (default 20)
        sma_period: Moving average period (default 50)
        rsi_period: RSI period (default 14)
        adx_period: ADX period (default 14)
    
    Returns:
        Dict with keys:
        - trend: "UPTREND", "DOWNTREND", or "RANGEBOUND"
        - strength: Float 0.0-1.0 (confidence in trend)
        - rsi: Latest RSI value
        - adx: Latest ADX value
        - sma50: SMA50 value
        - current_close: Current closing price
        - timestamp: Data timestamp
    """
    
    if data is None or len(data) < max(sma_period, rsi_period, adx_period, lookback_days):
        logger.warning("[%s] Insufficient data (%d rows). Defaulting to RANGEBOUND.", ticker, len(data) if data is not None else 0)
        return {
            "trend": "RANGEBOUND",
            "strength": 0.0,
            "rsi": 50.0,
            "adx": 15.0,
            "sma50": None,
            "current_close": None,
            "timestamp": None,
        }
    
    try:
        # Calculate SMA50
        sma50 = data["Close"].rolling(window=sma_period).mean()
        
        # Calculate RSI
        rsi = _calculate_rsi(data["Close"], rsi_period)
        
        # Calculate ADX
        adx = _calculate_adx(data, adx_period)
        
        # Get latest values
        latest_close = data["Close"].iloc[-1]
        latest_sma50 = sma50.iloc[-1]
        latest_rsi = rsi.iloc[-1]
        latest_adx = adx.iloc[-1]
        
        # Get lookback data for trend confirmation
        lookback_rsi = rsi.tail(min(3, len(rsi)))  # Last 3 RSI values
        
        # Determine trend
        trend, strength = _determine_trend(
            close=latest_close,
            sma50=latest_sma50,
            rsi=latest_rsi,
            adx=latest_adx,
            lookback_rsi=lookback_rsi,
        )
        
        result = {
            "trend": trend,
            "strength": strength,
            "rsi": float(latest_rsi),
            "adx": float(latest_adx),
            "sma50": float(latest_sma50),
            "current_close": float(latest_close),
            "timestamp": str(data.index[-1]),
        }
        
        logger.debug(
            "[%s] Trend detection: %s (strength=%.2f, RSI=%.1f, ADX=%.1f, Close=%.2f, SMA50=%.2f)",
            ticker, trend, strength, latest_rsi, latest_adx, latest_close, latest_sma50
        )
        
        return result
        
    except Exception as e:
        logger.error("[%s] Error in trend detection: %s", ticker, e)
        return {
            "trend": "RANGEBOUND",
            "strength": 0.0,
            "rsi": 50.0,
            "adx": 15.0,
            "sma50": None,
            "current_close": None,
            "timestamp": None,
        }


def _calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _calculate_adx(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index (ADX)."""
    high = data["High"]
    low = data["Low"]
    close = data["Close"]
    
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    # Calculate Directional Movement
    up = high.diff()
    down = low.diff() * -1
    
    pos_dm = up.where((up > down) & (up > 0), 0)
    neg_dm = down.where((down > up) & (down > 0), 0)
    
    pos_di = 100 * (pos_dm.rolling(window=period).mean() / atr)
    neg_di = 100 * (neg_dm.rolling(window=period).mean() / atr)
    
    di_diff = abs(pos_di - neg_di)
    di_sum = pos_di + neg_di
    
    dx = 100 * (di_diff / di_sum)
    adx = dx.rolling(window=period).mean()
    
    return adx


def _determine_trend(
    close: float,
    sma50: float,
    rsi: float,
    adx: float,
    lookback_rsi: pd.Series,
) -> tuple:
    """
    Determine trend and strength using technical indicators.
    
    Returns:
        (trend: str, strength: float)
    """
    
    # Check for sufficient ADX strength (trend exists)
    if adx < 20:
        # Weak trend - rangebound market
        return "RANGEBOUND", 0.0
    
    # Check price vs SMA50 and RSI consistency
    above_sma = close > sma50
    rsi_confirms = False
    
    # Check if last 3 RSI values support direction
    if len(lookback_rsi) >= 3:
        recent_rsis = lookback_rsi.values[-3:]
        if all(r > 50 for r in recent_rsis if not np.isnan(r)):
            rsi_confirms = True
        elif all(r < 50 for r in recent_rsis if not np.isnan(r)):
            rsi_confirms = True
    else:
        # Not enough RSI history, just use latest
        rsi_confirms = (rsi > 50) if above_sma else (rsi < 50)
    
    # Determine trend based on price/SMA and RSI confirmation
    if above_sma and (rsi > 50 or rsi_confirms):
        # UPTREND: price above SMA50, RSI elevated, ADX > 20
        strength = min(1.0, (adx - 20) / 30.0)  # Normalize ADX 20-50 to 0-1
        return "UPTREND", strength
    
    elif not above_sma and (rsi < 50 or rsi_confirms):
        # DOWNTREND: price below SMA50, RSI depressed, ADX > 20
        strength = min(1.0, (adx - 20) / 30.0)  # Normalize ADX 20-50 to 0-1
        return "DOWNTREND", strength
    
    else:
        # Mixed signals = rangebound
        return "RANGEBOUND", 0.0
