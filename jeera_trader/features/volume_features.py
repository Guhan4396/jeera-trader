"""
Volume and Open Interest feature engineering for jeera futures.
"""

import pandas as pd

from jeera_trader.logger import get_logger
from jeera_trader.utils.constants import OI_CHANGE_PERIOD, VOLUME_MA_PERIOD

logger = get_logger(__name__)


def calculate_volume_ma(df: pd.DataFrame, period: int = VOLUME_MA_PERIOD) -> pd.DataFrame:
    """
    Calculate volume moving average.

    Args:
        df: DataFrame with 'volume' column
        period: MA period (default: 20)

    Returns:
        DataFrame with volume MA column added
    """
    df = df.copy()

    if "volume" in df.columns:
        df[f"volume_ma_{period}"] = (
            df["volume"].rolling(window=period, min_periods=1).mean()
        )

    return df


def calculate_oi_change(df: pd.DataFrame, period: int = OI_CHANGE_PERIOD) -> pd.DataFrame:
    """
    Calculate open interest change over period.

    Args:
        df: DataFrame with 'open_interest' column
        period: Lookback period (default: 5)

    Returns:
        DataFrame with OI change column added
    """
    df = df.copy()

    if "open_interest" in df.columns:
        df[f"oi_change_{period}"] = df["open_interest"] - df["open_interest"].shift(period)

    return df


def calculate_volume_oi_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate volume to open interest ratio.

    High ratio indicates active trading relative to outstanding positions.

    Args:
        df: DataFrame with 'volume' and 'open_interest' columns

    Returns:
        DataFrame with volume/OI ratio column added
    """
    df = df.copy()

    if "volume" in df.columns and "open_interest" in df.columns:
        df["volume_oi_ratio"] = df["volume"] / df["open_interest"].replace(0, 1)

    return df


def calculate_all_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all volume and OI features.

    Args:
        df: DataFrame with volume and OI columns

    Returns:
        DataFrame with volume features added
    """
    logger.info("Calculating volume features")

    df = df.copy()

    df = calculate_volume_ma(df)
    df = calculate_oi_change(df)
    df = calculate_volume_oi_ratio(df)

    logger.info("Volume features calculated")

    return df
