"""
Database connection management for jeera_trader.
Provides context manager for safe database connections.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

from jeera_trader.config import Config
from jeera_trader.logger import get_logger

logger = get_logger(__name__)


class DatabaseError(Exception):
    """Raised when database operations fail."""

    pass


@contextmanager
def get_connection(
    db_path: Optional[str] = None, row_factory: bool = True
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.

    Args:
        db_path: Path to database file. If None, uses Config.DATABASE_PATH
        row_factory: If True, use Row factory for dict-like access

    Yields:
        sqlite3.Connection: Database connection

    Raises:
        DatabaseError: If connection fails

    Example:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM futures_prices")
            rows = cursor.fetchall()
    """
    # Get database path from config if not provided
    if db_path is None:
        if not Config.is_loaded():
            Config.load_from_env()
        db_path = Config.DATABASE_PATH

    if not db_path:
        raise DatabaseError("Database path not configured")

    conn = None
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        # Use Row factory for dict-like access
        if row_factory:
            conn.row_factory = sqlite3.Row

        logger.debug(f"Connected to database: {db_path}")

        yield conn

    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        if conn:
            conn.rollback()
        raise DatabaseError(f"Database connection failed: {e}")

    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


@contextmanager
def get_cursor(
    db_path: Optional[str] = None, row_factory: bool = True
) -> Generator[sqlite3.Cursor, None, None]:
    """
    Context manager for database cursor with automatic commit.

    Args:
        db_path: Path to database file. If None, uses Config.DATABASE_PATH
        row_factory: If True, use Row factory for dict-like access

    Yields:
        sqlite3.Cursor: Database cursor

    Raises:
        DatabaseError: If connection fails

    Example:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM futures_prices WHERE date = ?", (date,))
            rows = cursor.fetchall()
    """
    with get_connection(db_path=db_path, row_factory=row_factory) as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database cursor error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")


def execute_query(
    query: str,
    params: Optional[tuple] = None,
    db_path: Optional[str] = None,
    fetch: str = "all",
) -> list:
    """
    Execute a SELECT query and return results.

    Args:
        query: SQL query string
        params: Query parameters (optional)
        db_path: Path to database file
        fetch: 'all', 'one', or 'none'

    Returns:
        List of rows (or single row if fetch='one', or empty list if fetch='none')

    Raises:
        DatabaseError: If query fails
    """
    with get_cursor(db_path=db_path) as cursor:
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch == "all":
                return cursor.fetchall()
            elif fetch == "one":
                result = cursor.fetchone()
                return result if result else None
            else:  # fetch == 'none'
                return []

        except sqlite3.Error as e:
            logger.error(f"Query execution error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise DatabaseError(f"Query failed: {e}")


def execute_insert(
    query: str,
    params: Optional[tuple] = None,
    db_path: Optional[str] = None,
) -> int:
    """
    Execute an INSERT query and return the last row ID.

    Args:
        query: SQL INSERT query string
        params: Query parameters (optional)
        db_path: Path to database file

    Returns:
        Last inserted row ID

    Raises:
        DatabaseError: If insert fails
    """
    with get_cursor(db_path=db_path) as cursor:
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            return cursor.lastrowid

        except sqlite3.Error as e:
            logger.error(f"Insert execution error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise DatabaseError(f"Insert failed: {e}")


def execute_many(
    query: str,
    params_list: list,
    db_path: Optional[str] = None,
) -> int:
    """
    Execute a query with multiple parameter sets (bulk insert/update).

    Args:
        query: SQL query string
        params_list: List of parameter tuples
        db_path: Path to database file

    Returns:
        Number of rows affected

    Raises:
        DatabaseError: If operation fails
    """
    if not params_list:
        logger.warning("execute_many called with empty params_list")
        return 0

    with get_cursor(db_path=db_path) as cursor:
        try:
            cursor.executemany(query, params_list)
            return cursor.rowcount

        except sqlite3.Error as e:
            logger.error(f"Bulk execution error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"First params: {params_list[0] if params_list else 'None'}")
            raise DatabaseError(f"Bulk operation failed: {e}")


def execute_update(
    query: str,
    params: Optional[tuple] = None,
    db_path: Optional[str] = None,
) -> int:
    """
    Execute an UPDATE or DELETE query and return the number of affected rows.

    Args:
        query: SQL UPDATE/DELETE query string
        params: Query parameters (optional)
        db_path: Path to database file

    Returns:
        Number of rows affected

    Raises:
        DatabaseError: If update fails
    """
    with get_cursor(db_path=db_path) as cursor:
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            return cursor.rowcount

        except sqlite3.Error as e:
            logger.error(f"Update execution error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise DatabaseError(f"Update failed: {e}")


def test_connection(db_path: Optional[str] = None) -> bool:
    """
    Test database connection.

    Args:
        db_path: Path to database file

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_connection(db_path=db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False
