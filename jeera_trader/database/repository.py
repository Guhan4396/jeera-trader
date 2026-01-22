"""
Data repository layer for jeera_trader.
Provides CRUD operations for all database tables.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from jeera_trader.database.connection import (
    execute_insert,
    execute_many,
    execute_query,
    execute_update,
)
from jeera_trader.logger import get_logger
from jeera_trader.utils.constants import DB_BATCH_SIZE

logger = get_logger(__name__)


class FuturesPricesRepository:
    """Repository for futures_prices table."""

    @staticmethod
    def insert(
        date: str,
        symbol: str,
        contract_month: str,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: Optional[int] = None,
        open_interest: Optional[int] = None,
    ) -> int:
        """Insert a single futures price record."""
        query = """
            INSERT OR REPLACE INTO futures_prices
            (date, symbol, contract_month, open, high, low, close, volume, open_interest)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            date,
            symbol,
            contract_month,
            open_price,
            high,
            low,
            close,
            volume,
            open_interest,
        )
        return execute_insert(query, params)

    @staticmethod
    def bulk_insert(records: List[Dict[str, Any]]) -> int:
        """Bulk insert futures price records."""
        if not records:
            return 0

        query = """
            INSERT OR REPLACE INTO futures_prices
            (date, symbol, contract_month, open, high, low, close, volume, open_interest)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params_list = [
            (
                r["date"],
                r["symbol"],
                r["contract_month"],
                r["open"],
                r["high"],
                r["low"],
                r["close"],
                r.get("volume"),
                r.get("open_interest"),
            )
            for r in records
        ]

        return execute_many(query, params_list)

    @staticmethod
    def get_by_date_range(
        start_date: str,
        end_date: str,
        symbol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get futures prices for a date range."""
        query = """
            SELECT * FROM futures_prices
            WHERE date >= ? AND date <= ?
        """
        params = [start_date, end_date]

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        query += " ORDER BY date, symbol, contract_month"

        rows = execute_query(query, tuple(params))
        return [dict(row) for row in rows] if rows else []

    @staticmethod
    def get_latest(symbol: str, limit: int = 1) -> List[Dict[str, Any]]:
        """Get the most recent futures price records."""
        query = """
            SELECT * FROM futures_prices
            WHERE symbol = ?
            ORDER BY date DESC, contract_month DESC
            LIMIT ?
        """
        rows = execute_query(query, (symbol, limit))
        return [dict(row) for row in rows] if rows else []

    @staticmethod
    def to_dataframe(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> pd.DataFrame:
        """Convert futures prices to pandas DataFrame."""
        query = "SELECT * FROM futures_prices WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        query += " ORDER BY date, symbol, contract_month"

        rows = execute_query(query, tuple(params) if params else None)
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([dict(row) for row in rows])
        df["date"] = pd.to_datetime(df["date"])
        return df


class WeatherDataRepository:
    """Repository for weather_data table."""

    @staticmethod
    def insert(
        date: str,
        location: str,
        temp_avg: Optional[float] = None,
        temp_min: Optional[float] = None,
        temp_max: Optional[float] = None,
        rainfall: float = 0.0,
        humidity: Optional[float] = None,
        wind_speed: Optional[float] = None,
        pressure: Optional[float] = None,
    ) -> int:
        """Insert a single weather data record."""
        query = """
            INSERT OR REPLACE INTO weather_data
            (date, location, temp_avg, temp_min, temp_max, rainfall, humidity, wind_speed, pressure)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            date,
            location,
            temp_avg,
            temp_min,
            temp_max,
            rainfall,
            humidity,
            wind_speed,
            pressure,
        )
        return execute_insert(query, params)

    @staticmethod
    def bulk_insert(records: List[Dict[str, Any]]) -> int:
        """Bulk insert weather data records."""
        if not records:
            return 0

        query = """
            INSERT OR REPLACE INTO weather_data
            (date, location, temp_avg, temp_min, temp_max, rainfall, humidity, wind_speed, pressure)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params_list = [
            (
                r["date"],
                r["location"],
                r.get("temp_avg"),
                r.get("temp_min"),
                r.get("temp_max"),
                r.get("rainfall", 0.0),
                r.get("humidity"),
                r.get("wind_speed"),
                r.get("pressure"),
            )
            for r in records
        ]

        return execute_many(query, params_list)

    @staticmethod
    def get_by_date_range(
        start_date: str,
        end_date: str,
        location: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get weather data for a date range."""
        query = """
            SELECT * FROM weather_data
            WHERE date >= ? AND date <= ?
        """
        params = [start_date, end_date]

        if location:
            query += " AND location = ?"
            params.append(location)

        query += " ORDER BY date, location"

        rows = execute_query(query, tuple(params))
        return [dict(row) for row in rows] if rows else []

    @staticmethod
    def to_dataframe(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        location: Optional[str] = None,
    ) -> pd.DataFrame:
        """Convert weather data to pandas DataFrame."""
        query = "SELECT * FROM weather_data WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if location:
            query += " AND location = ?"
            params.append(location)

        query += " ORDER BY date, location"

        rows = execute_query(query, tuple(params) if params else None)
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([dict(row) for row in rows])
        df["date"] = pd.to_datetime(df["date"])
        return df


class FeaturesRepository:
    """Repository for features table."""

    @staticmethod
    def insert_from_dict(features_dict: Dict[str, Any]) -> int:
        """Insert features from a dictionary."""
        # Build dynamic INSERT query based on available keys
        columns = list(features_dict.keys())
        placeholders = ",".join(["?" for _ in columns])
        query = f"""
            INSERT OR REPLACE INTO features ({','.join(columns)})
            VALUES ({placeholders})
        """
        params = tuple(features_dict[col] for col in columns)
        return execute_insert(query, params)

    @staticmethod
    def bulk_insert_from_dataframe(df: pd.DataFrame) -> int:
        """Bulk insert features from DataFrame."""
        if df.empty:
            return 0

        # Convert DataFrame to list of dicts
        records = df.to_dict("records")

        # Get column names from first record
        columns = list(records[0].keys())
        placeholders = ",".join(["?" for _ in columns])

        query = f"""
            INSERT OR REPLACE INTO features ({','.join(columns)})
            VALUES ({placeholders})
        """

        params_list = [tuple(r[col] for col in columns) for r in records]

        return execute_many(query, params_list)

    @staticmethod
    def get_by_date_range(
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """Get features for a date range."""
        query = """
            SELECT * FROM features
            WHERE date >= ? AND date <= ?
            ORDER BY date
        """
        rows = execute_query(query, (start_date, end_date))
        return [dict(row) for row in rows] if rows else []

    @staticmethod
    def to_dataframe(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_target: bool = True,
    ) -> pd.DataFrame:
        """Convert features to pandas DataFrame."""
        query = "SELECT * FROM features WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date"

        rows = execute_query(query, tuple(params) if params else None)
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([dict(row) for row in rows])
        df["date"] = pd.to_datetime(df["date"])

        # Optionally exclude target columns
        if not include_target:
            target_cols = [col for col in df.columns if col.startswith("target_")]
            df = df.drop(columns=target_cols, errors="ignore")

        return df

    @staticmethod
    def get_latest(limit: int = 1) -> List[Dict[str, Any]]:
        """Get the most recent feature records."""
        query = """
            SELECT * FROM features
            ORDER BY date DESC
            LIMIT ?
        """
        rows = execute_query(query, (limit,))
        return [dict(row) for row in rows] if rows else []


class PredictionsRepository:
    """Repository for predictions table."""

    @staticmethod
    def insert(
        prediction_date: str,
        target_date: str,
        model_id: str,
        predicted_price: float,
        predicted_return: Optional[float] = None,
        confidence: Optional[float] = None,
    ) -> int:
        """Insert a prediction record."""
        query = """
            INSERT OR REPLACE INTO predictions
            (prediction_date, target_date, model_id, predicted_price, predicted_return, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            prediction_date,
            target_date,
            model_id,
            predicted_price,
            predicted_return,
            confidence,
        )
        return execute_insert(query, params)

    @staticmethod
    def update_actual(
        prediction_date: str,
        target_date: str,
        model_id: str,
        actual_price: float,
        actual_return: Optional[float] = None,
    ) -> int:
        """Update prediction with actual values."""
        query = """
            UPDATE predictions
            SET actual_price = ?,
                actual_return = ?,
                error = predicted_price - ?
            WHERE prediction_date = ? AND target_date = ? AND model_id = ?
        """
        params = (
            actual_price,
            actual_return,
            actual_price,
            prediction_date,
            target_date,
            model_id,
        )
        return execute_update(query, params)

    @staticmethod
    def get_by_model(
        model_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get predictions for a specific model."""
        query = "SELECT * FROM predictions WHERE model_id = ?"
        params = [model_id]

        if start_date:
            query += " AND prediction_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND prediction_date <= ?"
            params.append(end_date)

        query += " ORDER BY prediction_date"

        rows = execute_query(query, tuple(params))
        return [dict(row) for row in rows] if rows else []


class TradingSignalsRepository:
    """Repository for trading_signals table."""

    @staticmethod
    def insert(
        date: str,
        signal_type: str,
        current_price: float,
        predicted_price: float,
        predicted_return: float,
        confidence: float,
        model_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        position_size: Optional[float] = None,
        reasoning: Optional[str] = None,
    ) -> int:
        """Insert a trading signal."""
        query = """
            INSERT OR REPLACE INTO trading_signals
            (date, signal_type, current_price, predicted_price, predicted_return,
             confidence, stop_loss, take_profit, position_size, model_id, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            date,
            signal_type,
            current_price,
            predicted_price,
            predicted_return,
            confidence,
            stop_loss,
            take_profit,
            position_size,
            model_id,
            reasoning,
        )
        return execute_insert(query, params)

    @staticmethod
    def get_by_date_range(
        start_date: str,
        end_date: str,
        model_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get trading signals for a date range."""
        query = """
            SELECT * FROM trading_signals
            WHERE date >= ? AND date <= ?
        """
        params = [start_date, end_date]

        if model_id:
            query += " AND model_id = ?"
            params.append(model_id)

        query += " ORDER BY date"

        rows = execute_query(query, tuple(params))
        return [dict(row) for row in rows] if rows else []

    @staticmethod
    def get_latest(model_id: Optional[str] = None, limit: int = 1) -> List[Dict[str, Any]]:
        """Get the most recent trading signals."""
        query = "SELECT * FROM trading_signals"
        params = []

        if model_id:
            query += " WHERE model_id = ?"
            params.append(model_id)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        rows = execute_query(query, tuple(params))
        return [dict(row) for row in rows] if rows else []


class ModelMetadataRepository:
    """Repository for model_metadata table."""

    @staticmethod
    def insert(
        model_id: str,
        model_type: str,
        version: int,
        train_start_date: str,
        train_end_date: str,
        n_features: int,
        n_samples: int,
        file_path: str,
        rmse: Optional[float] = None,
        mae: Optional[float] = None,
        r2: Optional[float] = None,
        mape: Optional[float] = None,
        direction_accuracy: Optional[float] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        feature_importance: Optional[Dict[str, float]] = None,
        is_active: bool = False,
    ) -> int:
        """Insert model metadata."""
        query = """
            INSERT OR REPLACE INTO model_metadata
            (model_id, model_type, version, train_start_date, train_end_date,
             n_features, n_samples, rmse, mae, r2, mape, direction_accuracy,
             hyperparameters, feature_importance, file_path, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            model_id,
            model_type,
            version,
            train_start_date,
            train_end_date,
            n_features,
            n_samples,
            rmse,
            mae,
            r2,
            mape,
            direction_accuracy,
            json.dumps(hyperparameters) if hyperparameters else None,
            json.dumps(feature_importance) if feature_importance else None,
            file_path,
            is_active,
        )
        return execute_insert(query, params)

    @staticmethod
    def set_active(model_id: str) -> int:
        """Set a model as active and deactivate others of the same type."""
        # Get model type
        model_row = execute_query(
            "SELECT model_type FROM model_metadata WHERE model_id = ?",
            (model_id,),
            fetch="one",
        )
        if not model_row:
            logger.error(f"Model not found: {model_id}")
            return 0

        model_type = model_row["model_type"]

        # Deactivate all models of the same type
        execute_update(
            "UPDATE model_metadata SET is_active = 0 WHERE model_type = ?",
            (model_type,),
        )

        # Activate the specified model
        return execute_update(
            "UPDATE model_metadata SET is_active = 1 WHERE model_id = ?",
            (model_id,),
        )

    @staticmethod
    def get_active(model_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the active model (optionally filtered by type)."""
        query = "SELECT * FROM model_metadata WHERE is_active = 1"
        params = []

        if model_type:
            query += " AND model_type = ?"
            params.append(model_type)

        query += " ORDER BY created_at DESC LIMIT 1"

        row = execute_query(query, tuple(params) if params else None, fetch="one")
        return dict(row) if row else None

    @staticmethod
    def get_by_id(model_id: str) -> Optional[Dict[str, Any]]:
        """Get model metadata by ID."""
        row = execute_query(
            "SELECT * FROM model_metadata WHERE model_id = ?",
            (model_id,),
            fetch="one",
        )
        return dict(row) if row else None

    @staticmethod
    def get_all(model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all models (optionally filtered by type)."""
        query = "SELECT * FROM model_metadata"
        params = []

        if model_type:
            query += " WHERE model_type = ?"
            params.append(model_type)

        query += " ORDER BY created_at DESC"

        rows = execute_query(query, tuple(params) if params else None)
        return [dict(row) for row in rows] if rows else []


class BacktestResultsRepository:
    """Repository for backtest_results table."""

    @staticmethod
    def insert(
        backtest_id: str,
        model_id: str,
        start_date: str,
        end_date: str,
        initial_capital: float,
        final_capital: float,
        total_return: float,
        total_return_pct: float,
        n_trades: int,
        sharpe_ratio: Optional[float] = None,
        max_drawdown: Optional[float] = None,
        max_drawdown_duration: Optional[int] = None,
        win_rate: Optional[float] = None,
        profit_factor: Optional[float] = None,
        n_winning_trades: Optional[int] = None,
        n_losing_trades: Optional[int] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None,
        largest_win: Optional[float] = None,
        largest_loss: Optional[float] = None,
        commission_paid: Optional[float] = None,
        slippage_cost: Optional[float] = None,
        equity_curve: Optional[List] = None,
        trade_log: Optional[List] = None,
    ) -> int:
        """Insert backtest results."""
        query = """
            INSERT OR REPLACE INTO backtest_results
            (backtest_id, model_id, start_date, end_date, initial_capital,
             final_capital, total_return, total_return_pct, sharpe_ratio,
             max_drawdown, max_drawdown_duration, win_rate, profit_factor,
             n_trades, n_winning_trades, n_losing_trades, avg_win, avg_loss,
             largest_win, largest_loss, commission_paid, slippage_cost,
             equity_curve, trade_log)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            backtest_id,
            model_id,
            start_date,
            end_date,
            initial_capital,
            final_capital,
            total_return,
            total_return_pct,
            sharpe_ratio,
            max_drawdown,
            max_drawdown_duration,
            win_rate,
            profit_factor,
            n_trades,
            n_winning_trades,
            n_losing_trades,
            avg_win,
            avg_loss,
            largest_win,
            largest_loss,
            commission_paid,
            slippage_cost,
            json.dumps(equity_curve) if equity_curve else None,
            json.dumps(trade_log) if trade_log else None,
        )
        return execute_insert(query, params)

    @staticmethod
    def get_by_model(model_id: str) -> List[Dict[str, Any]]:
        """Get all backtest results for a model."""
        rows = execute_query(
            "SELECT * FROM backtest_results WHERE model_id = ? ORDER BY created_at DESC",
            (model_id,),
        )
        return [dict(row) for row in rows] if rows else []

    @staticmethod
    def get_by_id(backtest_id: str) -> Optional[Dict[str, Any]]:
        """Get backtest results by ID."""
        row = execute_query(
            "SELECT * FROM backtest_results WHERE backtest_id = ?",
            (backtest_id,),
            fetch="one",
        )
        return dict(row) if row else None
