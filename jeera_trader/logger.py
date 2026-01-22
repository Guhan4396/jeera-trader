"""
Logging configuration for jeera_trader.
Sets up file and console handlers with appropriate formatting.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from jeera_trader.config import Config


# Color codes for console output
class LogColors:
    RESET = "\033[0m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output."""

    COLORS = {
        logging.DEBUG: LogColors.GRAY,
        logging.INFO: LogColors.BLUE,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.RED,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, LogColors.RESET)
        record.levelname = f"{color}{record.levelname}{LogColors.RESET}"
        return super().format(record)


def setup_logger(
    name: str = "jeera_trader",
    log_file: Optional[str] = None,
    log_level: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Set up logger with file and console handlers.

    Args:
        name: Logger name
        log_file: Path to log file. If None, uses Config.LOG_FILE
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, uses Config.LOG_LEVEL
        console: Whether to add console handler

    Returns:
        Configured logger instance
    """
    # Get configuration
    if not Config.is_loaded():
        Config.load_from_env()

    if log_file is None:
        log_file = Config.LOG_FILE

    if log_level is None:
        log_level = Config.LOG_LEVEL

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_formatter = ColoredFormatter(
            "%(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str = "jeera_trader") -> logging.Logger:
    """
    Get or create logger with the given name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # If logger has no handlers, set it up
    if not logger.handlers:
        return setup_logger(name)

    return logger


# Create default logger instance
logger = setup_logger()


# Convenience functions
def log_section(title: str, logger_instance: Optional[logging.Logger] = None) -> None:
    """Log a section header."""
    log = logger_instance or logger
    log.info("=" * 70)
    log.info(f"  {title}")
    log.info("=" * 70)


def log_subsection(
    title: str, logger_instance: Optional[logging.Logger] = None
) -> None:
    """Log a subsection header."""
    log = logger_instance or logger
    log.info("-" * 70)
    log.info(f"  {title}")
    log.info("-" * 70)


def log_success(message: str, logger_instance: Optional[logging.Logger] = None) -> None:
    """Log a success message."""
    log = logger_instance or logger
    log.info(f"{LogColors.GREEN}✓{LogColors.RESET} {message}")


def log_error(message: str, logger_instance: Optional[logging.Logger] = None) -> None:
    """Log an error message."""
    log = logger_instance or logger
    log.error(f"{LogColors.RED}✗{LogColors.RESET} {message}")


def log_warning(
    message: str, logger_instance: Optional[logging.Logger] = None
) -> None:
    """Log a warning message."""
    log = logger_instance or logger
    log.warning(f"{LogColors.YELLOW}⚠{LogColors.RESET} {message}")


def log_progress(
    message: str, logger_instance: Optional[logging.Logger] = None
) -> None:
    """Log a progress message."""
    log = logger_instance or logger
    log.info(f"{LogColors.BLUE}→{LogColors.RESET} {message}")
