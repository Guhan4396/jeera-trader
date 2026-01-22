"""
Model training command handler.
"""

from datetime import datetime
from typing import Any

from jeera_trader.config import Config, ConfigError
from jeera_trader.database.repository import FeaturesRepository, ModelMetadataRepository
from jeera_trader.logger import get_logger, log_error, log_progress, log_section, log_success
from jeera_trader.models.evaluator import evaluate_model, print_metrics
from jeera_trader.models.random_forest import RandomForestModel

logger = get_logger(__name__)


def run_train(args: Any) -> int:
    """
    Run model training command.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        Config.load_from_env()

        model_type = args.model
        tune = args.tune if hasattr(args, 'tune') else False
        start_date = args.start_date if hasattr(args, 'start_date') and args.start_date else None
        end_date = args.end_date if hasattr(args, 'end_date') and args.end_date else None

        log_section("Model Training")

        # Load features from database
        log_progress("Loading features from database")
        features_repo = FeaturesRepository()

        if start_date and end_date:
            df = features_repo.to_dataframe(start_date, end_date, include_target=True)
        else:
            df = features_repo.to_dataframe(include_target=True)

        if df.empty:
            log_error("No features found in database. Please run feature engineering first.")
            return 1

        logger.info(f"Loaded {len(df)} feature records")

        # Remove rows with missing target values
        df = df.dropna(subset=['target_price_1d'])

        if df.empty:
            log_error("No valid training data after removing missing targets")
            return 1

        # Split features and target
        target_col = 'target_price_1d'
        exclude_cols = ['date', 'symbol', 'contract_month', 'crop_phase', 'target_price_1d', 'target_return_1d', 'id', 'created_at']
        feature_cols = [col for col in df.columns if col not in exclude_cols]

        X = df[feature_cols]
        y = df[target_col]

        # Time-based train/test split (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        logger.info(f"Training set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        logger.info(f"Features: {len(feature_cols)}")

        # Train models based on selection
        models_to_train = []
        if model_type in ['rf', 'all']:
            models_to_train.append('rf')
        if model_type in ['xgb', 'all']:
            models_to_train.append('xgb')

        trained_models = []

        for mt in models_to_train:
            if mt == 'rf':
                exit_code = train_random_forest(X_train, y_train, X_test, y_test, tune)
                if exit_code == 0:
                    trained_models.append('Random Forest')
            # XGBoost can be added later

        if trained_models:
            log_success(f"Training completed: {', '.join(trained_models)}")
            return 0
        else:
            log_error("No models were trained successfully")
            return 1

    except ConfigError as e:
        log_error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        log_error(f"Model training failed: {e}")
        logger.exception(e)
        return 1


def train_random_forest(X_train, y_train, X_test, y_test, tune: bool = False) -> int:
    """
    Train Random Forest model.

    Args:
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        tune: Whether to tune hyperparameters

    Returns:
        Exit code
    """
    try:
        log_progress("Training Random Forest model")

        # Create model
        model = RandomForestModel()

        # Train
        model.train(X_train, y_train, tune_hyperparameters=tune)

        # Evaluate
        log_progress("Evaluating model")

        # Train metrics
        y_train_pred = model.predict(X_train)
        train_metrics = evaluate_model(y_train.values, y_train_pred)
        print_metrics(train_metrics, "Training")

        # Test metrics
        y_test_pred = model.predict(X_test)
        test_metrics = evaluate_model(y_test.values, y_test_pred)
        print_metrics(test_metrics, "Test")

        # Save model
        log_progress("Saving model")
        model_path = model.save()

        # Get feature importance
        feature_importance = model.get_feature_importance()
        if feature_importance:
            top_features = dict(list(feature_importance.items())[:10])
            print("\nTop 10 Features:")
            for feat, importance in top_features.items():
                print(f"  {feat}: {importance:.4f}")

        # Save metadata to database
        log_progress("Saving model metadata")

        train_start = X_train.index.min() if hasattr(X_train.index, 'min') else 0
        train_end = X_train.index.max() if hasattr(X_train.index, 'max') else len(X_train)

        metadata_repo = ModelMetadataRepository()
        metadata_repo.insert(
            model_id=model.model_id,
            model_type="random_forest",
            version=1,
            train_start_date=str(train_start),
            train_end_date=str(train_end),
            n_features=len(model.feature_names),
            n_samples=len(X_train),
            rmse=test_metrics['rmse'],
            mae=test_metrics['mae'],
            r2=test_metrics['r2'],
            mape=test_metrics['mape'],
            direction_accuracy=test_metrics['direction_accuracy'],
            hyperparameters=str(model.model_params) if hasattr(model, 'model_params') else None,
            feature_importance=str(feature_importance) if feature_importance else None,
            file_path=model_path,
            is_active=True,
        )

        # Set as active model
        metadata_repo.set_active(model.model_id)

        log_success(f"Random Forest model trained and saved: {model.model_id}")

        return 0

    except Exception as e:
        log_error(f"Random Forest training failed: {e}")
        logger.exception(e)
        return 1
