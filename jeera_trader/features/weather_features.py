"""
Weather-based feature engineering for jeera futures.
Aggregates and transforms weather data for ML features.
"""

import pandas as pd

from jeera_trader.logger import get_logger
from jeera_trader.utils.constants import RAINFALL_WINDOWS, TEMP_ANOMALY_WINDOW, WEATHER_LOCATIONS

logger = get_logger(__name__)


def aggregate_weather_by_location(weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate weather data across locations using weighted average.

    Args:
        weather_df: DataFrame with weather data for multiple locations

    Returns:
        DataFrame with aggregated weather by date
    """
    if weather_df.empty:
        return pd.DataFrame()

    # Group by date and aggregate using weights from WEATHER_LOCATIONS
    aggregated = []

    for date in weather_df["date"].unique():
        date_data = weather_df[weather_df["date"] == date]

        record = {"date": date}

        # Weighted average for each weather variable
        for var in ["temp_avg", "temp_min", "temp_max", "rainfall", "humidity"]:
            if var in date_data.columns:
                weighted_sum = 0
                total_weight = 0

                for _, row in date_data.iterrows():
                    location = row["location"]
                    if location in WEATHER_LOCATIONS and row[var] is not None:
                        weight = WEATHER_LOCATIONS[location]["importance"]
                        weighted_sum += row[var] * weight
                        total_weight += weight

                record[var] = weighted_sum / total_weight if total_weight > 0 else None

        aggregated.append(record)

    return pd.DataFrame(aggregated)


def calculate_rolling_rainfall(df: pd.DataFrame, windows: list = None) -> pd.DataFrame:
    """
    Calculate rolling rainfall sums.

    Args:
        df: DataFrame with 'rainfall' column
        windows: List of window sizes (default: from constants)

    Returns:
        DataFrame with rolling rainfall columns added
    """
    if windows is None:
        windows = RAINFALL_WINDOWS

    df = df.copy()

    for window in windows:
        df[f"rainfall_{window}d"] = (
            df["rainfall"].rolling(window=window, min_periods=1).sum()
        )

    return df


def calculate_temperature_anomaly(df: pd.DataFrame, window: int = TEMP_ANOMALY_WINDOW) -> pd.DataFrame:
    """
    Calculate temperature anomaly (deviation from rolling average).

    Args:
        df: DataFrame with 'temp_avg' column
        window: Rolling window size (default: 30 days)

    Returns:
        DataFrame with temperature anomaly column added
    """
    df = df.copy()

    rolling_mean = df["temp_avg"].rolling(window=window, min_periods=1).mean()
    df["temp_anomaly"] = df["temp_avg"] - rolling_mean

    return df


def calculate_all_weather_features(weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all weather-based features.

    Args:
        weather_df: Raw weather data

    Returns:
        DataFrame with weather features
    """
    logger.info("Calculating weather features")

    if weather_df.empty:
        logger.warning("No weather data provided")
        return pd.DataFrame()

    # Aggregate across locations
    df = aggregate_weather_by_location(weather_df)

    if df.empty:
        return df

    # Calculate rolling rainfall
    df = calculate_rolling_rainfall(df)

    # Calculate temperature anomaly
    df = calculate_temperature_anomaly(df)

    logger.info("Weather features calculated")

    return df
