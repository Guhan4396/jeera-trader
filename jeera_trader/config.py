"""
Configuration management for jeera_trader.
Loads settings from environment variables using python-dotenv.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class Config:
    """Global configuration manager."""

    # Database
    DATABASE_PATH: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None

    # NCDEX
    NCDEX_BASE_URL: str = "https://www.ncdex.com"

    # Model storage
    MODEL_DIR: Optional[str] = None

    # Trading parameters
    DEFAULT_STOP_LOSS_PCT: float = 2.0
    DEFAULT_TAKE_PROFIT_PCT: float = 5.0
    DEFAULT_POSITION_SIZE: float = 100000.0

    @classmethod
    def load_from_env(cls, env_path: Optional[str] = None) -> None:
        """
        Load configuration from .env file.

        Args:
            env_path: Path to .env file. If None, searches in standard locations.

        Raises:
            ConfigError: If required configuration is missing or invalid.
        """
        # Try to find .env file
        if env_path:
            env_file = Path(env_path)
            if not env_file.exists():
                raise ConfigError(f".env file not found at: {env_path}")
        else:
            # Search in standard locations
            possible_paths = [
                Path.cwd() / ".env",
                Path.home() / "Desktop" / "jeera_trader" / ".env",
            ]
            env_file = None
            for path in possible_paths:
                if path.exists():
                    env_file = path
                    break

            if env_file is None:
                raise ConfigError(
                    "No .env file found. Please create one based on .env.example"
                )

        # Load environment variables
        load_dotenv(env_file)

        # Database
        cls.DATABASE_PATH = os.getenv("DATABASE_PATH")
        if not cls.DATABASE_PATH:
            raise ConfigError("DATABASE_PATH not set in .env")

        # Create data directory if it doesn't exist
        db_path = Path(cls.DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Logging
        cls.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        cls.LOG_FILE = os.getenv("LOG_FILE")

        # Create logs directory if LOG_FILE is specified
        if cls.LOG_FILE:
            log_path = Path(cls.LOG_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)

        # NCDEX
        cls.NCDEX_BASE_URL = os.getenv("NCDEX_BASE_URL", "https://www.ncdex.com")

        # Model storage
        cls.MODEL_DIR = os.getenv("MODEL_DIR")
        if cls.MODEL_DIR:
            model_dir = Path(cls.MODEL_DIR)
            model_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Default to data/models relative to project root
            project_root = Path(__file__).parent.parent
            cls.MODEL_DIR = str(project_root / "data" / "models")
            Path(cls.MODEL_DIR).mkdir(parents=True, exist_ok=True)

        # Trading parameters
        try:
            cls.DEFAULT_STOP_LOSS_PCT = float(
                os.getenv("DEFAULT_STOP_LOSS_PCT", "2.0")
            )
            cls.DEFAULT_TAKE_PROFIT_PCT = float(
                os.getenv("DEFAULT_TAKE_PROFIT_PCT", "5.0")
            )
            cls.DEFAULT_POSITION_SIZE = float(
                os.getenv("DEFAULT_POSITION_SIZE", "100000.0")
            )
        except ValueError as e:
            raise ConfigError(f"Invalid trading parameter value: {e}")

        # Validate trading parameters
        if cls.DEFAULT_STOP_LOSS_PCT <= 0 or cls.DEFAULT_STOP_LOSS_PCT > 100:
            raise ConfigError(
                f"DEFAULT_STOP_LOSS_PCT must be between 0 and 100, got: {cls.DEFAULT_STOP_LOSS_PCT}"
            )
        if cls.DEFAULT_TAKE_PROFIT_PCT <= 0 or cls.DEFAULT_TAKE_PROFIT_PCT > 100:
            raise ConfigError(
                f"DEFAULT_TAKE_PROFIT_PCT must be between 0 and 100, got: {cls.DEFAULT_TAKE_PROFIT_PCT}"
            )
        if cls.DEFAULT_POSITION_SIZE <= 0:
            raise ConfigError(
                f"DEFAULT_POSITION_SIZE must be positive, got: {cls.DEFAULT_POSITION_SIZE}"
            )

    @classmethod
    def is_loaded(cls) -> bool:
        """Check if configuration has been loaded."""
        return cls.DATABASE_PATH is not None

    @classmethod
    def get_summary(cls) -> str:
        """Get a summary of current configuration."""
        if not cls.is_loaded():
            return "Configuration not loaded"

        return f"""
Configuration Summary:
---------------------
Database: {cls.DATABASE_PATH}
Log Level: {cls.LOG_LEVEL}
Log File: {cls.LOG_FILE or 'Not set'}
Model Directory: {cls.MODEL_DIR}

Data Sources:
  NCDEX: {cls.NCDEX_BASE_URL} (Bhavcopy CSV - FREE)
  Weather: Open-Meteo API (FREE)

Trading Parameters:
  Stop Loss: {cls.DEFAULT_STOP_LOSS_PCT}%
  Take Profit: {cls.DEFAULT_TAKE_PROFIT_PCT}%
  Position Size: ₹{cls.DEFAULT_POSITION_SIZE:,.0f}
        """.strip()


# Auto-load configuration on import (if .env exists)
try:
    Config.load_from_env()
except ConfigError:
    # Don't fail on import, but configuration must be loaded before use
    pass
