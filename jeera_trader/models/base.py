"""
Base model class for jeera price prediction.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from jeera_trader.config import Config
from jeera_trader.logger import get_logger

logger = get_logger(__name__)


class BaseModel(ABC):
    """Abstract base class for prediction models."""

    def __init__(self, model_id: Optional[str] = None):
        """
        Initialize model.

        Args:
            model_id: Unique model identifier
        """
        self.model_id = model_id or self._generate_model_id()
        self.model = None
        self.feature_names = None
        self.is_trained = False

    def _generate_model_id(self) -> str:
        """Generate unique model ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.get_model_type()}_{timestamp}"

    @abstractmethod
    def get_model_type(self) -> str:
        """Get model type name."""
        pass

    @abstractmethod
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
    ) -> None:
        """
        Train the model.

        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
        """
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions.

        Args:
            X: Features

        Returns:
            Predictions array
        """
        pass

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance scores.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        return None

    def save(self, directory: Optional[str] = None) -> str:
        """
        Save model to disk.

        Args:
            directory: Directory to save model (default: from config)

        Returns:
            Path to saved model file
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        if directory is None:
            if not Config.is_loaded():
                Config.load_from_env()
            directory = Config.MODEL_DIR

        # Create directory if it doesn't exist
        Path(directory).mkdir(parents=True, exist_ok=True)

        # Save model
        file_path = Path(directory) / f"{self.model_id}.pkl"

        model_data = {
            "model": self.model,
            "model_id": self.model_id,
            "model_type": self.get_model_type(),
            "feature_names": self.feature_names,
            "is_trained": self.is_trained,
        }

        joblib.dump(model_data, file_path)

        logger.info(f"Model saved to: {file_path}")

        return str(file_path)

    @classmethod
    def load(cls, file_path: str) -> "BaseModel":
        """
        Load model from disk.

        Args:
            file_path: Path to model file

        Returns:
            Loaded model instance
        """
        model_data = joblib.load(file_path)

        # Create instance
        instance = cls(model_id=model_data["model_id"])
        instance.model = model_data["model"]
        instance.feature_names = model_data["feature_names"]
        instance.is_trained = model_data["is_trained"]

        logger.info(f"Model loaded from: {file_path}")

        return instance

    def prepare_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for prediction (ensure column order matches training).

        Args:
            X: Input features

        Returns:
            Prepared features
        """
        if self.feature_names is None:
            raise ValueError("Model has not been trained yet")

        # Ensure all required features are present
        missing_features = set(self.feature_names) - set(X.columns)
        if missing_features:
            raise ValueError(f"Missing required features: {missing_features}")

        # Select and order features
        X = X[self.feature_names].copy()

        return X
