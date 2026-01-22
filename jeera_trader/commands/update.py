"""
Daily update automation command handler.
Runs complete data collection, feature generation, and signal generation workflow.
"""

from datetime import datetime, timedelta
from typing import Any

from jeera_trader.commands.collect import collect_ncdex, collect_weather
from jeera_trader.commands.signal import run_signal
from jeera_trader.config import Config, ConfigError
from jeera_trader.features.pipeline import run_feature_pipeline, save_features_to_db
from jeera_trader.logger import get_logger, log_error, log_section, log_success

logger = get_logger(__name__)


def run_update(args: Any) -> int:
    """
    Run daily update routine.

    This command:
    1. Collects latest NCDEX data
    2. Collects latest weather data
    3. Generates features
    4. Generates trading signal

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        Config.load_from_env()

        log_section("Daily Update Routine")

        # Determine date range (collect data for last 7 days to ensure we have latest)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        logger.info(f"Update period: {start_date} to {end_date}")

        # Step 1: Collect NCDEX data
        logger.info("Step 1: Collecting NCDEX data")
        try:
            collect_ncdex(start_date, end_date)
        except Exception as e:
            logger.warning(f"NCDEX collection partially failed: {e}")
            # Continue anyway - we might have some data

        # Step 2: Collect weather data
        logger.info("Step 2: Collecting weather data")
        try:
            collect_weather(start_date, end_date)
        except Exception as e:
            logger.warning(f"Weather collection partially failed: {e}")
            # Continue anyway

        # Step 3: Generate features
        logger.info("Step 3: Generating features")
        try:
            features_df = run_feature_pipeline(start_date, end_date)
            if not features_df.empty:
                save_features_to_db(features_df)
            else:
                logger.warning("No features generated")
        except Exception as e:
            logger.error(f"Feature generation failed: {e}")
            return 1

        # Step 4: Generate trading signal
        logger.info("Step 4: Generating trading signal")
        try:
            # Create a dummy args object for signal command
            class SignalArgs:
                model = None
                date = None

            signal_args = SignalArgs()
            exit_code = run_signal(signal_args)

            if exit_code != 0:
                logger.warning("Signal generation had issues")

        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            # Don't fail the whole update for this
            logger.info("Continuing despite signal generation failure")

        log_success("Daily update completed")

        return 0

    except ConfigError as e:
        log_error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        log_error(f"Daily update failed: {e}")
        logger.exception(e)
        return 1
