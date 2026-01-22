"""
Time-based feature engineering for jeera futures.
Handles temporal patterns, seasonality, and crop cycle phases.
"""

import numpy as np
import pandas as pd

from jeera_trader.logger import get_logger
from jeera_trader.utils.constants import CROP_PHASE_MONTHS, CropPhase

logger = get_logger(__name__)


def extract_basic_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract basic time features from date.

    Args:
        df: DataFrame with 'date' column

    Returns:
        DataFrame with time features added
    """
    df = df.copy()

    # Ensure date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])

    # Extract basic features
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["day_of_week"] = df["date"].dt.dayofweek  # Monday=0, Sunday=6
    df["day_of_month"] = df["date"].dt.day
    df["week_of_year"] = df["date"].dt.isocalendar().week

    return df


def encode_cyclical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode cyclical time features using sine and cosine transformations.

    This preserves the cyclical nature of time (e.g., December is close to January).

    Args:
        df: DataFrame with time columns

    Returns:
        DataFrame with cyclical encodings added
    """
    df = df.copy()

    # Month (1-12)
    if "month" in df.columns:
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    # Quarter (1-4)
    if "quarter" in df.columns:
        df["quarter_sin"] = np.sin(2 * np.pi * df["quarter"] / 4)
        df["quarter_cos"] = np.cos(2 * np.pi * df["quarter"] / 4)

    # Day of week (0-6)
    if "day_of_week" in df.columns:
        df["day_of_week_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
        df["day_of_week_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

    return df


def get_crop_phase(month: int) -> str:
    """
    Determine jeera crop cycle phase based on month.

    Jeera crop cycle in India:
    - Sowing: Oct-Nov
    - Growing: Dec-Feb
    - Harvest: Mar-Apr
    - Post-harvest: May-Sep

    Args:
        month: Month number (1-12)

    Returns:
        Crop phase name
    """
    for phase, months in CROP_PHASE_MONTHS.items():
        if month in months:
            return phase.value

    # Default to post-harvest if not found
    return CropPhase.POST_HARVEST.value


def add_crop_cycle_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add jeera crop cycle phase features.

    Args:
        df: DataFrame with 'month' column

    Returns:
        DataFrame with crop phase features added
    """
    df = df.copy()

    if "month" not in df.columns:
        logger.warning("Month column not found, cannot add crop cycle features")
        return df

    # Add crop phase
    df["crop_phase"] = df["month"].apply(get_crop_phase)

    # One-hot encode crop phases
    for phase in CropPhase:
        phase_name = phase.value
        df[f"is_{phase_name}"] = (df["crop_phase"] == phase_name).astype(int)

    return df


def add_seasonal_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add seasonal indicator features.

    Args:
        df: DataFrame with 'month' column

    Returns:
        DataFrame with seasonal indicators added
    """
    df = df.copy()

    if "month" not in df.columns:
        logger.warning("Month column not found, cannot add seasonal indicators")
        return df

    # Define seasons (for India)
    df["is_winter"] = df["month"].isin([12, 1, 2]).astype(int)  # Dec, Jan, Feb
    df["is_summer"] = df["month"].isin([3, 4, 5]).astype(int)  # Mar, Apr, May
    df["is_monsoon"] = df["month"].isin([6, 7, 8, 9]).astype(int)  # Jun-Sep
    df["is_post_monsoon"] = df["month"].isin([10, 11]).astype(int)  # Oct, Nov

    # Quarter end effects (commodity traders often adjust positions)
    df["is_quarter_end"] = df["month"].isin([3, 6, 9, 12]).astype(int)

    # Year end effects
    df["is_year_end"] = (df["month"] == 12).astype(int)

    return df


def add_trading_day_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add trading day related features.

    Args:
        df: DataFrame with 'day_of_week' column

    Returns:
        DataFrame with trading day features added
    """
    df = df.copy()

    if "day_of_week" not in df.columns:
        logger.warning("day_of_week column not found, cannot add trading day features")
        return df

    # Monday effect (often higher volatility)
    df["is_monday"] = (df["day_of_week"] == 0).astype(int)

    # Friday effect (position squaring)
    df["is_friday"] = (df["day_of_week"] == 4).astype(int)

    # Mid-week
    df["is_mid_week"] = df["day_of_week"].isin([2, 3]).astype(int)

    return df


def add_calendar_effects(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add calendar-based effects.

    Args:
        df: DataFrame with date column

    Returns:
        DataFrame with calendar effects added
    """
    df = df.copy()

    if "day_of_month" not in df.columns:
        logger.warning("day_of_month column not found, cannot add calendar effects")
        return df

    # Start of month (often higher activity)
    df["is_month_start"] = (df["day_of_month"] <= 5).astype(int)

    # Mid month
    df["is_mid_month"] = df["day_of_month"].isin(range(12, 20)).astype(int)

    # End of month
    df["is_month_end"] = (df["day_of_month"] >= 25).astype(int)

    return df


def calculate_all_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all time-based features.

    Args:
        df: DataFrame with 'date' column

    Returns:
        DataFrame with all time features added
    """
    logger.info("Calculating time features")

    df = df.copy()

    # Ensure date column exists
    if "date" not in df.columns:
        raise ValueError("DataFrame must have 'date' column")

    # Extract basic features
    df = extract_basic_time_features(df)

    # Add cyclical encodings
    df = encode_cyclical_features(df)

    # Add crop cycle features
    df = add_crop_cycle_features(df)

    # Add seasonal indicators
    df = add_seasonal_indicators(df)

    # Add trading day features
    df = add_trading_day_features(df)

    # Add calendar effects
    df = add_calendar_effects(df)

    logger.info("Time features calculated")

    return df
