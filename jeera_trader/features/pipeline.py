"""
Feature engineering pipeline.
Orchestrates all feature extraction and creates final feature set for ML.
"""

import numpy as np
import pandas as pd

from jeera_trader.database.repository import (
    FeaturesRepository,
    FuturesPricesRepository,
    WeatherDataRepository,
)
from jeera_trader.features.price_features import calculate_all_price_features
from jeera_trader.features.time_features import calculate_all_time_features
from jeera_trader.features.volume_features import calculate_all_volume_features
from jeera_trader.features.weather_features import calculate_all_weather_features
from jeera_trader.logger import get_logger, log_progress, log_warning
from jeera_trader.utils.constants import LAG_PERIODS, PREDICTION_HORIZONS

logger = get_logger(__name__)


def create_lag_features(df: pd.DataFrame, columns: list, periods: list = None) -> pd.DataFrame:
    """
    Create lag features for specified columns.

    Args:
        df: DataFrame
        columns: List of column names to create lags for
        periods: List of lag periods (default: from constants)

    Returns:
        DataFrame with lag features added
    """
    if periods is None:
        periods = LAG_PERIODS

    df = df.copy()

    for col in columns:
        if col not in df.columns:
            continue

        for period in periods:
            df[f"{col}_lag_{period}"] = df[col].shift(period)

    return df


def create_target_variables(df: pd.DataFrame, horizons: list = None) -> pd.DataFrame:
    """
    Create target variables for prediction.

    Args:
        df: DataFrame with 'close' column
        horizons: List of prediction horizons in days (default: from constants)

    Returns:
        DataFrame with target variables added
    """
    if horizons is None:
        horizons = PREDICTION_HORIZONS

    df = df.copy()

    for horizon in horizons:
        # Future price
        df[f"target_price_{horizon}d"] = df["close"].shift(-horizon)

        # Future return
        df[f"target_return_{horizon}d"] = (
            (df[f"target_price_{horizon}d"] - df["close"]) / df["close"] * 100
        )

    return df


def merge_weather_data(price_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge weather features with price data.

    Args:
        price_df: DataFrame with price data
        weather_df: DataFrame with weather features

    Returns:
        Merged DataFrame
    """
    if weather_df.empty:
        log_warning("No weather data to merge")
        return price_df

    # Ensure both have date as datetime
    price_df["date"] = pd.to_datetime(price_df["date"])
    weather_df["date"] = pd.to_datetime(weather_df["date"])

    # Merge on date
    merged = pd.merge(price_df, weather_df, on="date", how="left")

    return merged


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in feature DataFrame.

    Strategy:
    - Forward fill for most features (carries last known value forward)
    - Fill remaining nulls with 0

    Args:
        df: DataFrame with features

    Returns:
        DataFrame with missing values handled
    """
    df = df.copy()

    # Columns to exclude from filling
    exclude_cols = ["date", "symbol", "contract_month", "crop_phase"]

    # Get numeric columns
    numeric_cols = df.select_dtypes(include=["number"]).columns
    fill_cols = [col for col in numeric_cols if col not in exclude_cols]

    # Forward fill
    df[fill_cols] = df[fill_cols].fillna(method="ffill")

    # Fill remaining with 0
    df[fill_cols] = df[fill_cols].fillna(0)

    return df


def run_feature_pipeline(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Run complete feature engineering pipeline.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        DataFrame with all features
    """
    logger.info(f"Running feature pipeline for {start_date} to {end_date}")

    # 1. Load futures price data
    log_progress("Loading futures price data")
    futures_repo = FuturesPricesRepository()
    price_df = futures_repo.to_dataframe(start_date, end_date)

    if price_df.empty:
        log_warning("No futures price data found")
        return pd.DataFrame()

    # Get most liquid contract (highest volume) for each date
    price_df = (
        price_df.sort_values(["date", "volume"], ascending=[True, False])
        .groupby("date")
        .first()
        .reset_index()
    )

    logger.info(f"Loaded {len(price_df)} price records")

    # 2. Calculate price features
    log_progress("Calculating price features")
    price_df = calculate_all_price_features(price_df)

    # 3. Calculate time features
    log_progress("Calculating time features")
    price_df = calculate_all_time_features(price_df)

    # 4. Calculate volume features
    log_progress("Calculating volume features")
    price_df = calculate_all_volume_features(price_df)

    # 5. Load and merge weather data
    log_progress("Loading and merging weather data")
    weather_repo = WeatherDataRepository()
    weather_df = weather_repo.to_dataframe(start_date, end_date)

    if not weather_df.empty:
        weather_features = calculate_all_weather_features(weather_df)
        price_df = merge_weather_data(price_df, weather_features)
    else:
        log_warning("No weather data found, skipping weather features")

    # 6. Create lag features
    log_progress("Creating lag features")
    lag_columns = ["close", "volume"]
    price_df = create_lag_features(price_df, lag_columns)

    # 7. Create target variables
    log_progress("Creating target variables")
    price_df = create_target_variables(price_df)

    # 8. Handle missing values
    log_progress("Handling missing values")
    price_df = handle_missing_values(price_df)

    logger.info(f"Feature pipeline complete: {len(price_df)} rows, {len(price_df.columns)} columns")

    return price_df


def save_features_to_db(features_df: pd.DataFrame) -> int:
    """
    Save features to database.

    Args:
        features_df: DataFrame with features

    Returns:
        Number of records saved
    """
    if features_df.empty:
        logger.warning("No features to save")
        return 0

    log_progress("Saving features to database")

    # Keep only columns that exist in the schema
    schema_columns = [
        'date', 'close', 'open', 'high', 'low',
        'ma_5', 'ma_10', 'ma_20', 'ma_50',
        'rsi_14', 'macd', 'macd_signal', 'macd_hist',
        'bb_upper', 'bb_middle', 'bb_lower', 'bb_width',
        'volatility_20', 'price_momentum',
        'year', 'month', 'quarter', 'day_of_week', 'day_of_month', 'week_of_year',
        'month_sin', 'month_cos', 'quarter_sin', 'quarter_cos', 'crop_phase',
        'temp_avg', 'temp_min', 'temp_max', 'rainfall',
        'rainfall_7d', 'rainfall_30d', 'humidity', 'temp_anomaly',
        'volume', 'open_interest', 'volume_ma_20', 'oi_change_5', 'volume_oi_ratio',
        'close_lag_1', 'close_lag_5', 'close_lag_10',
        'volume_lag_1', 'volume_lag_5',
        'target_price_1d', 'target_return_1d'
    ]

    # Filter dataframe to only include schema columns
    available_columns = [col for col in schema_columns if col in features_df.columns]
    features_df = features_df[available_columns].copy()

    # Convert date to string if it's a Timestamp
    if 'date' in features_df.columns:
        features_df['date'] = features_df['date'].astype(str)

    # Convert any NaN/inf to None for SQL compatibility
    features_df = features_df.replace([np.inf, -np.inf], np.nan)

    repo = FeaturesRepository()
    saved_count = repo.bulk_insert_from_dataframe(features_df)

    logger.info(f"Saved {saved_count} feature records to database")

    return saved_count
