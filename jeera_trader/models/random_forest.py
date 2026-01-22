"""
Random Forest model for jeera price prediction.
"""

from typing import Dict, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV

from jeera_trader.logger import get_logger
from jeera_trader.models.base import BaseModel
from jeera_trader.utils.constants import RANDOM_FOREST_PARAMS

logger = get_logger(__name__)


class RandomForestModel(BaseModel):
    """Random Forest regression model."""

    def __init__(self, model_id: Optional[str] = None, **kwargs):
        """
        Initialize Random Forest model.

        Args:
            model_id: Unique model identifier
            **kwargs: Additional parameters for RandomForestRegressor
        """
        super().__init__(model_id)
        self.model_params = kwargs
        self.best_params = None

    def get_model_type(self) -> str:
        """Get model type name."""
        return "random_forest"

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        tune_hyperparameters: bool = False,
    ) -> None:
        """
        Train Random Forest model.

        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
            tune_hyperparameters: Whether to perform hyperparameter tuning
        """
        logger.info("Training Random Forest model")

        # Store feature names
        self.feature_names = list(X_train.columns)

        if tune_hyperparameters:
            logger.info("Performing hyperparameter tuning")
            self._tune_hyperparameters(X_train, y_train)
        else:
            # Use default or provided parameters
            if not self.model_params:
                self.model_params = {
                    "n_estimators": 200,
                    "max_depth": 20,
                    "min_samples_split": 5,
                    "min_samples_leaf": 2,
                    "random_state": 42,
                    "n_jobs": -1,
                }

        # Create and train model
        self.model = RandomForestRegressor(**self.model_params)
        self.model.fit(X_train, y_train)

        self.is_trained = True

        logger.info(f"Random Forest trained with {len(self.feature_names)} features")

    def _tune_hyperparameters(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """
        Tune hyperparameters using Grid Search.

        Args:
            X_train: Training features
            y_train: Training targets
        """
        rf = RandomForestRegressor(random_state=42, n_jobs=-1)

        grid_search = GridSearchCV(
            rf,
            param_grid=RANDOM_FOREST_PARAMS,
            cv=3,
            scoring="neg_mean_squared_error",
            n_jobs=-1,
            verbose=1,
        )

        grid_search.fit(X_train, y_train)

        self.best_params = grid_search.best_params_
        self.model_params = grid_search.best_params_
        self.model_params["random_state"] = 42
        self.model_params["n_jobs"] = -1

        logger.info(f"Best parameters: {self.best_params}")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions.

        Args:
            X: Features

        Returns:
            Predictions array
        """
        if not self.is_trained:
            raise ValueError("Model has not been trained yet")

        X = self.prepare_features(X)

        predictions = self.model.predict(X)

        return predictions

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance scores.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_trained or self.feature_names is None:
            return None

        importance = self.model.feature_importances_

        # Create dictionary of feature importances
        feature_importance = dict(zip(self.feature_names, importance))

        # Sort by importance
        feature_importance = dict(
            sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        )

        return feature_importance
