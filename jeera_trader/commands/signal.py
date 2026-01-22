"""
Trading signal generation command handler.
"""

from datetime import datetime
from typing import Any

from jeera_trader.config import Config, ConfigError
from jeera_trader.database.repository import (
    FeaturesRepository,
    FuturesPricesRepository,
    ModelMetadataRepository,
    TradingSignalsRepository,
)
from jeera_trader.logger import get_logger, log_error, log_progress, log_section, log_success
from jeera_trader.models.random_forest import RandomForestModel
from jeera_trader.trading.risk import generate_risk_parameters
from jeera_trader.trading.signals import format_signal_output, generate_signal

logger = get_logger(__name__)


def run_signal(args: Any) -> int:
    """
    Run trading signal generation command.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        Config.load_from_env()

        model_id = args.model if hasattr(args, 'model') and args.model else None
        signal_date = args.date if hasattr(args, 'date') and args.date else None

        log_section("Trading Signal Generation")

        # Get model
        log_progress("Loading model")
        model, model_metadata = load_model(model_id)

        if model is None:
            log_error("No trained model found. Please train a model first.")
            return 1

        logger.info(f"Using model: {model_metadata['model_id']}")

        # Get latest features
        log_progress("Loading latest market data")

        features_repo = FeaturesRepository()
        if signal_date:
            # Get features for specific date
            features = features_repo.get_by_date_range(signal_date, signal_date)
            if not features:
                log_error(f"No features found for date: {signal_date}")
                return 1
            latest_features = features[0]
        else:
            # Get most recent features
            features = features_repo.get_latest(limit=1)
            if not features:
                log_error("No features found in database")
                return 1
            latest_features = features[0]

        feature_date = latest_features['date']
        logger.info(f"Generating signal for date: {feature_date}")

        # Get current price
        current_price = latest_features.get('close')
        if not current_price:
            log_error("No current price available")
            return 1

        # Prepare features for prediction
        import pandas as pd
        features_df = pd.DataFrame([latest_features])

        # Remove non-feature columns
        exclude_cols = ['id', 'date', 'created_at', 'target_price_1d', 'target_return_1d']
        feature_cols = [col for col in features_df.columns if col not in exclude_cols]
        X = features_df[feature_cols]

        # Make prediction
        log_progress("Generating prediction")
        predicted_price = model.predict(X)[0]

        logger.info(f"Current price: ₹{current_price:,.2f}")
        logger.info(f"Predicted price: ₹{predicted_price:,.2f}")

        # Generate signal
        log_progress("Generating trading signal")
        signal = generate_signal(
            current_price=current_price,
            predicted_price=predicted_price,
            confidence=None,  # Can add confidence calculation later
        )

        # Calculate risk parameters
        risk_params = generate_risk_parameters(signal)

        # Save signal to database
        log_progress("Saving signal to database")
        signals_repo = TradingSignalsRepository()
        signals_repo.insert(
            date=str(feature_date),
            signal_type=signal['signal_type'],
            current_price=signal['current_price'],
            predicted_price=signal['predicted_price'],
            predicted_return=signal['predicted_return'],
            confidence=signal.get('confidence'),
            model_id=model_metadata['model_id'],
            stop_loss=risk_params['stop_loss'],
            take_profit=risk_params['take_profit'],
            position_size=risk_params['position_size'],
            reasoning=signal['reasoning'],
        )

        # Display signal
        output = format_signal_output(signal, risk_params)
        print(output)

        log_success("Trading signal generated successfully")

        return 0

    except ConfigError as e:
        log_error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        log_error(f"Signal generation failed: {e}")
        logger.exception(e)
        return 1


def load_model(model_id: str = None):
    """
    Load model from database.

    Args:
        model_id: Specific model ID (optional, uses active model if None)

    Returns:
        Tuple of (model, metadata) or (None, None) if not found
    """
    metadata_repo = ModelMetadataRepository()

    if model_id:
        # Load specific model
        metadata = metadata_repo.get_by_id(model_id)
    else:
        # Load active model
        metadata = metadata_repo.get_active()

    if not metadata:
        return None, None

    # Load model from file
    model_file = metadata['file_path']

    try:
        model = RandomForestModel.load(model_file)
        return model, metadata
    except Exception as e:
        logger.error(f"Failed to load model from {model_file}: {e}")
        return None, None
