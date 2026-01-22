"""
Model evaluation metrics for jeera price prediction.
"""

from typing import Dict

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from jeera_trader.logger import get_logger

logger = get_logger(__name__)


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Root Mean Squared Error."""
    return np.sqrt(mean_squared_error(y_true, y_pred))


def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Error."""
    return mean_absolute_error(y_true, y_pred)


def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R-squared score."""
    return r2_score(y_true, y_pred)


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Mean Absolute Percentage Error.

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        MAPE as percentage
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)

    # Avoid division by zero
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def calculate_direction_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate directional accuracy (percentage of correct direction predictions).

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        Direction accuracy as percentage
    """
    if len(y_true) <= 1:
        return 0.0

    # Get direction of change
    true_direction = np.diff(y_true) > 0
    pred_direction = np.diff(y_pred) > 0

    # Calculate accuracy
    accuracy = np.mean(true_direction == pred_direction) * 100

    return accuracy


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate all evaluation metrics.

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        Dictionary of metrics
    """
    metrics = {
        "rmse": calculate_rmse(y_true, y_pred),
        "mae": calculate_mae(y_true, y_pred),
        "r2": calculate_r2(y_true, y_pred),
        "mape": calculate_mape(y_true, y_pred),
        "direction_accuracy": calculate_direction_accuracy(y_true, y_pred),
    }

    return metrics


def print_metrics(metrics: Dict[str, float], dataset_name: str = "Test") -> None:
    """
    Print evaluation metrics in a formatted way.

    Args:
        metrics: Dictionary of metrics
        dataset_name: Name of dataset (e.g., "Test", "Validation")
    """
    print(f"\n{dataset_name} Metrics:")
    print("=" * 50)
    print(f"  RMSE:                {metrics['rmse']:.2f}")
    print(f"  MAE:                 {metrics['mae']:.2f}")
    print(f"  R²:                  {metrics['r2']:.4f}")
    print(f"  MAPE:                {metrics['mape']:.2f}%")
    print(f"  Direction Accuracy:  {metrics['direction_accuracy']:.2f}%")
    print("=" * 50)
