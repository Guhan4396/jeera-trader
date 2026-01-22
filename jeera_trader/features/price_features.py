"""
Price-based feature engineering for jeera futures.
Calculates technical indicators: Moving Averages, RSI, MACD, Bollinger Bands, etc.
"""

from typing import Dict, List

import numpy as np
import pandas as pd

from jeera_trader.logger import get_logger
from jeera_trader.utils.constants import (
    BOLLINGER_PERIOD,
    BOLLINGER_STD,
    MACD_FAST,
    MACD_SIGNAL,
    MACD_SLOW,
    MOVING_AVERAGE_PERIODS,
    RSI_PERIOD,
    VOLATILITY_WINDOW,
)

logger = get_logger(__name__)


def calculate_moving_averages(df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
    """
    Calculate Simple Moving Averages for multiple periods.

    Args:
        df: DataFrame with 'close' column
        periods: List of MA periods (default: from constants)

    Returns:
        DataFrame with MA columns added
    """
    if periods is None:
        periods = MOVING_AVERAGE_PERIODS

    df = df.copy()

    for period in periods:
        df[f"ma_{period}"] = df["close"].rolling(window=period, min_periods=1).mean()

    return df


def calculate_rsi(df: pd.DataFrame, period: int = RSI_PERIOD) -> pd.DataFrame:
    """
    Calculate Relative Strength Index (RSI).

    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss

    Args:
        df: DataFrame with 'close' column
        period: RSI period (default: 14)

    Returns:
        DataFrame with 'rsi_14' column added
    """
    df = df.copy()

    # Calculate price changes
    delta = df["close"].diff()

    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    df[f"rsi_{period}"] = rsi

    return df


def calculate_macd(
    df: pd.DataFrame,
    fast: int = MACD_FAST,
    slow: int = MACD_SLOW,
    signal: int = MACD_SIGNAL,
) -> pd.DataFrame:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    MACD Line = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD Line, signal)
    Histogram = MACD Line - Signal Line

    Args:
        df: DataFrame with 'close' column
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line period (default: 9)

    Returns:
        DataFrame with MACD columns added
    """
    df = df.copy()

    # Calculate EMAs
    ema_fast = df["close"].ewm(span=fast, adjust=False, min_periods=1).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False, min_periods=1).mean()

    # Calculate MACD line
    macd_line = ema_fast - ema_slow

    # Calculate signal line
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=1).mean()

    # Calculate histogram
    macd_hist = macd_line - signal_line

    df["macd"] = macd_line
    df["macd_signal"] = signal_line
    df["macd_hist"] = macd_hist

    return df


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = BOLLINGER_PERIOD,
    std_dev: float = BOLLINGER_STD,
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands.

    Middle Band = SMA(period)
    Upper Band = Middle Band + (std_dev * standard deviation)
    Lower Band = Middle Band - (std_dev * standard deviation)

    Args:
        df: DataFrame with 'close' column
        period: Moving average period (default: 20)
        std_dev: Number of standard deviations (default: 2)

    Returns:
        DataFrame with Bollinger Band columns added
    """
    df = df.copy()

    # Calculate middle band (SMA)
    middle = df["close"].rolling(window=period, min_periods=1).mean()

    # Calculate standard deviation
    std = df["close"].rolling(window=period, min_periods=1).std()

    # Calculate upper and lower bands
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)

    # Calculate bandwidth (useful indicator)
    bandwidth = (upper - lower) / middle

    df["bb_middle"] = middle
    df["bb_upper"] = upper
    df["bb_lower"] = lower
    df["bb_width"] = bandwidth

    return df


def calculate_volatility(df: pd.DataFrame, window: int = VOLATILITY_WINDOW) -> pd.DataFrame:
    """
    Calculate historical volatility (standard deviation of returns).

    Args:
        df: DataFrame with 'close' column
        window: Rolling window size (default: 20)

    Returns:
        DataFrame with 'volatility_20' column added
    """
    df = df.copy()

    # Calculate daily returns
    returns = df["close"].pct_change()

    # Calculate rolling standard deviation
    volatility = returns.rolling(window=window, min_periods=1).std()

    # Annualize volatility (assuming 252 trading days)
    volatility_annualized = volatility * np.sqrt(252)

    df[f"volatility_{window}"] = volatility_annualized

    return df


def calculate_momentum(df: pd.DataFrame, period: int = 10) -> pd.DataFrame:
    """
    Calculate price momentum.

    Momentum = Current Price - Price N periods ago

    Args:
        df: DataFrame with 'close' column
        period: Lookback period (default: 10)

    Returns:
        DataFrame with 'price_momentum' column added
    """
    df = df.copy()

    df["price_momentum"] = df["close"] - df["close"].shift(period)

    return df


def calculate_rate_of_change(df: pd.DataFrame, period: int = 10) -> pd.DataFrame:
    """
    Calculate Rate of Change (ROC).

    ROC = ((Current Price - Price N periods ago) / Price N periods ago) * 100

    Args:
        df: DataFrame with 'close' column
        period: Lookback period (default: 10)

    Returns:
        DataFrame with 'roc_10' column added
    """
    df = df.copy()

    roc = ((df["close"] - df["close"].shift(period)) / df["close"].shift(period)) * 100

    df[f"roc_{period}"] = roc

    return df


def calculate_all_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all price-based features.

    Args:
        df: DataFrame with OHLC columns

    Returns:
        DataFrame with all price features added
    """
    logger.info("Calculating price features")

    df = df.copy()

    # Ensure we have required columns
    required_cols = ["open", "high", "low", "close"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Calculate all features
    df = calculate_moving_averages(df)
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_bollinger_bands(df)
    df = calculate_volatility(df)
    df = calculate_momentum(df)
    df = calculate_rate_of_change(df)

    logger.info(f"Generated {len([c for c in df.columns if c not in required_cols + ['volume', 'open_interest']])} price features")

    return df


def validate_price_features(df: pd.DataFrame) -> Dict[str, int]:
    """
    Validate price features and return statistics.

    Args:
        df: DataFrame with price features

    Returns:
        Dictionary with validation statistics
    """
    stats = {
        "total_rows": len(df),
        "null_counts": {},
        "infinite_counts": {},
    }

    # Check for nulls and infinites
    for col in df.columns:
        if col not in ["date", "symbol", "contract_month"]:
            null_count = df[col].isnull().sum()
            inf_count = np.isinf(df[col].replace([np.inf, -np.inf], np.nan)).sum()

            if null_count > 0:
                stats["null_counts"][col] = null_count
            if inf_count > 0:
                stats["infinite_counts"][col] = inf_count

    return stats
