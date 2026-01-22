"""
Feature engineering command handler.
"""

from typing import Any

from jeera_trader.config import Config, ConfigError
from jeera_trader.features.pipeline import run_feature_pipeline, save_features_to_db
from jeera_trader.logger import get_logger, log_error, log_section, log_success

logger = get_logger(__name__)


def run_features(args: Any) -> int:
    """
    Run feature engineering command.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        Config.load_from_env()

        start_date = args.start_date
        end_date = args.end_date

        log_section(f"Feature Engineering: {start_date} to {end_date}")

        # Run feature pipeline
        features_df = run_feature_pipeline(start_date, end_date)

        if features_df.empty:
            log_error("No features generated. Please collect data first.")
            return 1

        # Save to database
        saved_count = save_features_to_db(features_df)

        log_success(f"Feature engineering completed: {saved_count} records saved")

        # Show feature summary
        print(f"\nFeature Summary:")
        print(f"  Total Records: {len(features_df)}")
        print(f"  Total Features: {len(features_df.columns)}")
        print(f"  Date Range: {features_df['date'].min()} to {features_df['date'].max()}")

        return 0

    except ConfigError as e:
        log_error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        log_error(f"Feature engineering failed: {e}")
        logger.exception(e)
        return 1
