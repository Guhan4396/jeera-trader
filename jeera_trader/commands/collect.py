"""
Data collection command handler.
"""

from typing import Any

from jeera_trader.collectors.ncdex import NCDEXCollector
from jeera_trader.collectors.weather import WeatherCollector
from jeera_trader.config import Config, ConfigError
from jeera_trader.database.repository import (
    FuturesPricesRepository,
    WeatherDataRepository,
)
from jeera_trader.logger import (
    get_logger,
    log_error,
    log_progress,
    log_section,
    log_success,
    log_warning,
)

logger = get_logger(__name__)


def run_collect(args: Any) -> int:
    """
    Run data collection command.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        Config.load_from_env()

        source = args.source
        start_date = args.start_date
        end_date = args.end_date

        log_section(f"Data Collection: {source.upper()}")
        logger.info(f"Date range: {start_date} to {end_date}")

        if source == "ncdex" or source == "all":
            exit_code = collect_ncdex(start_date, end_date)
            if exit_code != 0 and source == "ncdex":
                return exit_code

        if source == "weather" or source == "all":
            exit_code = collect_weather(start_date, end_date)
            if exit_code != 0 and source == "weather":
                return exit_code

        log_success("Data collection completed")
        return 0

    except ConfigError as e:
        log_error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        log_error(f"Data collection failed: {e}")
        logger.exception(e)
        return 1


def collect_ncdex(start_date: str, end_date: str) -> int:
    """
    Collect NCDEX futures data.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        Exit code
    """
    try:
        log_progress("Collecting NCDEX futures data")

        # Initialize collector
        collector = NCDEXCollector()

        # Collect data with retry
        records = collector.collect_with_retry(start_date, end_date)

        if not records:
            log_warning("No NCDEX data collected")
            return 0

        log_progress(f"Saving {len(records)} NCDEX records to database")

        # Save to database
        repo = FuturesPricesRepository()
        saved_count = repo.bulk_insert(records)

        log_success(f"Saved {saved_count} NCDEX records")
        return 0

    except Exception as e:
        log_error(f"NCDEX collection failed: {e}")
        logger.exception(e)
        return 1


def collect_weather(start_date: str, end_date: str) -> int:
    """
    Collect weather data.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        Exit code
    """
    try:
        log_progress("Collecting weather data")

        # Initialize collector
        collector = WeatherCollector()

        # Collect data with retry
        records = collector.collect_with_retry(start_date, end_date)

        if not records:
            log_warning("No weather data collected")
            return 0

        log_progress(f"Saving {len(records)} weather records to database")

        # Save to database
        repo = WeatherDataRepository()
        saved_count = repo.bulk_insert(records)

        log_success(f"Saved {saved_count} weather records")
        return 0

    except Exception as e:
        log_error(f"Weather collection failed: {e}")
        logger.exception(e)
        return 1
