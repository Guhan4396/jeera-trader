"""
Database schema definitions for jeera_trader.
Creates SQLite tables for storing NCDEX data, weather data, features, and predictions.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from jeera_trader.logger import get_logger

logger = get_logger(__name__)


def create_tables(db_path: str) -> None:
    """
    Create all database tables.

    Args:
        db_path: Path to SQLite database file
    """
    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Futures prices table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS futures_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                contract_month TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER,
                open_interest INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, symbol, contract_month)
            )
        """
        )

        # Create indexes for futures_prices
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_futures_date
            ON futures_prices(date)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_futures_symbol
            ON futures_prices(symbol)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_futures_symbol_date
            ON futures_prices(symbol, date)
        """
        )

        # 2. Weather data table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS weather_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                location TEXT NOT NULL,
                temp_avg REAL,
                temp_min REAL,
                temp_max REAL,
                rainfall REAL DEFAULT 0.0,
                humidity REAL,
                wind_speed REAL,
                pressure REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, location)
            )
        """
        )

        # Create indexes for weather_data
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_weather_date
            ON weather_data(date)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_weather_location
            ON weather_data(location)
        """
        )

        # 3. Features table (wide table with all engineered features)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,

                -- Price features
                close REAL,
                open REAL,
                high REAL,
                low REAL,
                ma_5 REAL,
                ma_10 REAL,
                ma_20 REAL,
                ma_50 REAL,
                rsi_14 REAL,
                macd REAL,
                macd_signal REAL,
                macd_hist REAL,
                bb_upper REAL,
                bb_middle REAL,
                bb_lower REAL,
                bb_width REAL,
                volatility_20 REAL,
                price_momentum REAL,

                -- Time features
                year INTEGER,
                month INTEGER,
                quarter INTEGER,
                day_of_week INTEGER,
                day_of_month INTEGER,
                week_of_year INTEGER,
                month_sin REAL,
                month_cos REAL,
                quarter_sin REAL,
                quarter_cos REAL,
                crop_phase TEXT,

                -- Weather features
                temp_avg REAL,
                temp_min REAL,
                temp_max REAL,
                rainfall REAL,
                rainfall_7d REAL,
                rainfall_30d REAL,
                humidity REAL,
                temp_anomaly REAL,

                -- Volume features
                volume REAL,
                open_interest REAL,
                volume_ma_20 REAL,
                oi_change_5 REAL,
                volume_oi_ratio REAL,

                -- Lag features
                close_lag_1 REAL,
                close_lag_5 REAL,
                close_lag_10 REAL,
                volume_lag_1 REAL,
                volume_lag_5 REAL,

                -- Target variables
                target_price_1d REAL,
                target_return_1d REAL,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create index for features
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_features_date
            ON features(date)
        """
        )

        # 4. Predictions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_date TEXT NOT NULL,
                target_date TEXT NOT NULL,
                model_id TEXT NOT NULL,
                predicted_price REAL NOT NULL,
                predicted_return REAL,
                confidence REAL,
                actual_price REAL,
                actual_return REAL,
                error REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(prediction_date, target_date, model_id)
            )
        """
        )

        # Create indexes for predictions
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_predictions_date
            ON predictions(prediction_date)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_predictions_model
            ON predictions(model_id)
        """
        )

        # 5. Trading signals table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                current_price REAL NOT NULL,
                predicted_price REAL NOT NULL,
                predicted_return REAL NOT NULL,
                confidence REAL NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                position_size REAL,
                model_id TEXT NOT NULL,
                reasoning TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, model_id)
            )
        """
        )

        # Create index for trading_signals
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_signals_date
            ON trading_signals(date)
        """
        )

        # 6. Model metadata table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT NOT NULL UNIQUE,
                model_type TEXT NOT NULL,
                version INTEGER NOT NULL,
                train_start_date TEXT NOT NULL,
                train_end_date TEXT NOT NULL,
                n_features INTEGER NOT NULL,
                n_samples INTEGER NOT NULL,
                rmse REAL,
                mae REAL,
                r2 REAL,
                mape REAL,
                direction_accuracy REAL,
                hyperparameters TEXT,
                feature_importance TEXT,
                file_path TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes for model_metadata
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_model_type
            ON model_metadata(model_type)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_model_active
            ON model_metadata(is_active)
        """
        )

        # 7. Backtest results table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id TEXT NOT NULL UNIQUE,
                model_id TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                initial_capital REAL NOT NULL,
                final_capital REAL NOT NULL,
                total_return REAL NOT NULL,
                total_return_pct REAL NOT NULL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                max_drawdown_duration INTEGER,
                win_rate REAL,
                profit_factor REAL,
                n_trades INTEGER NOT NULL,
                n_winning_trades INTEGER,
                n_losing_trades INTEGER,
                avg_win REAL,
                avg_loss REAL,
                largest_win REAL,
                largest_loss REAL,
                commission_paid REAL,
                slippage_cost REAL,
                equity_curve TEXT,
                trade_log TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes for backtest_results
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_backtest_model
            ON backtest_results(model_id)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_backtest_date
            ON backtest_results(start_date, end_date)
        """
        )

        conn.commit()
        logger.info("Database tables created successfully")

    except sqlite3.Error as e:
        logger.error(f"Error creating database tables: {e}")
        raise
    finally:
        conn.close()


def drop_tables(db_path: str) -> None:
    """
    Drop all database tables. Use with caution!

    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        tables = [
            "futures_prices",
            "weather_data",
            "features",
            "predictions",
            "trading_signals",
            "model_metadata",
            "backtest_results",
        ]

        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            logger.info(f"Dropped table: {table}")

        conn.commit()
        logger.info("All tables dropped successfully")

    except sqlite3.Error as e:
        logger.error(f"Error dropping tables: {e}")
        raise
    finally:
        conn.close()


def get_table_info(db_path: str) -> dict:
    """
    Get information about all tables in the database.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Dictionary with table names as keys and row counts as values
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get all table names
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = cursor.fetchall()

        table_info = {}
        for (table_name,) in tables:
            # Get row count for each table
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            table_info[table_name] = count

        return table_info

    except sqlite3.Error as e:
        logger.error(f"Error getting table info: {e}")
        raise
    finally:
        conn.close()
