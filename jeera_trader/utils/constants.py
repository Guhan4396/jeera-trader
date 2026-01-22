"""
Constants used throughout the jeera_trader application.
"""

from enum import Enum


# Commodity information
JEERA_SYMBOL = "JEERA"
JEERA_FULL_NAME = "Cumin Seed"
JEERA_UNIT = "Quintal"  # 100 kg


# Contract months (NCDEX typically has contracts for these months)
CONTRACT_MONTHS = [
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
]


# Weather locations for jeera growing regions
WEATHER_LOCATIONS = {
    "Gujarat": {
        "city": "Ahmedabad",
        "lat": 23.0225,
        "lon": 72.5714,
        "importance": 0.6,  # Weight in aggregation
    },
    "Rajasthan": {
        "city": "Jodhpur",
        "lat": 26.2389,
        "lon": 73.0243,
        "importance": 0.4,
    },
}


# Crop cycle phases (approximate months)
class CropPhase(Enum):
    """Jeera crop cycle phases."""

    SOWING = "sowing"  # Oct-Nov
    GROWING = "growing"  # Dec-Feb
    HARVEST = "harvest"  # Mar-Apr
    POST_HARVEST = "post_harvest"  # May-Sep


CROP_PHASE_MONTHS = {
    CropPhase.SOWING: [10, 11],  # October, November
    CropPhase.GROWING: [12, 1, 2],  # December, January, February
    CropPhase.HARVEST: [3, 4],  # March, April
    CropPhase.POST_HARVEST: [5, 6, 7, 8, 9],  # May through September
}


# Feature names
class FeatureGroups:
    """Feature group identifiers."""

    PRICE = "price"
    TIME = "time"
    WEATHER = "weather"
    VOLUME = "volume"
    LAG = "lag"
    TARGET = "target"


# Technical indicator parameters
MOVING_AVERAGE_PERIODS = [5, 10, 20, 50]
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2
VOLATILITY_WINDOW = 20


# Weather feature parameters
RAINFALL_WINDOWS = [7, 30]  # days
TEMP_ANOMALY_WINDOW = 30  # days


# Volume feature parameters
VOLUME_MA_PERIOD = 20
OI_CHANGE_PERIOD = 5


# Lag periods for creating lag features
LAG_PERIODS = [1, 5, 10]


# Target prediction horizons
PREDICTION_HORIZONS = [1]  # days ahead (can be extended to [1, 5, 10])


# Model types
class ModelType(Enum):
    """Available model types."""

    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"


# Model hyperparameters
RANDOM_FOREST_PARAMS = {
    "n_estimators": [100, 200, 300],
    "max_depth": [10, 20, 30, None],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4],
}

XGBOOST_PARAMS = {
    "n_estimators": [100, 200, 300],
    "max_depth": [3, 5, 7, 9],
    "learning_rate": [0.01, 0.05, 0.1],
    "subsample": [0.8, 0.9, 1.0],
    "colsample_bytree": [0.8, 0.9, 1.0],
}


# Trading signal types
class SignalType(Enum):
    """Trading signal types."""

    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


# Signal thresholds (percentage price change)
SIGNAL_THRESHOLDS = {
    SignalType.STRONG_BUY: 3.0,  # >= 3% predicted increase
    SignalType.BUY: 1.5,  # >= 1.5% predicted increase
    SignalType.HOLD: -1.5,  # between -1.5% and 1.5%
    SignalType.SELL: -3.0,  # <= -3% predicted decrease
    SignalType.STRONG_SELL: -5.0,  # <= -5% predicted decrease
}


# Risk management
DEFAULT_COMMISSION_PCT = 0.1  # 0.1% per trade
DEFAULT_SLIPPAGE_PCT = 0.05  # 0.05% slippage


# Backtesting
INITIAL_CAPITAL = 100000  # Default initial capital in INR
RISK_FREE_RATE = 0.06  # 6% annual risk-free rate for Sharpe ratio


# Data collection
NCDEX_REQUEST_DELAY = 1  # seconds between requests to avoid rate limiting
WEATHER_REQUEST_DELAY = 1  # seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


# Database
DB_BATCH_SIZE = 1000  # Batch size for bulk inserts


# Date formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# Model versioning
MODEL_VERSION_FORMAT = "{model_type}_v{version}_{date}"  # e.g., random_forest_v1_2025-01-22


# Evaluation metrics
METRICS = [
    "rmse",
    "mae",
    "r2",
    "mape",
    "direction_accuracy",
]


# Time series cross-validation
CV_N_SPLITS = 5
CV_TEST_SIZE = 30  # days in test set for each split
