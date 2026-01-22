"""
Base collector class with retry logic and error handling.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from jeera_trader.logger import get_logger, log_error, log_progress, log_warning
from jeera_trader.utils.constants import MAX_RETRIES, RETRY_DELAY

logger = get_logger(__name__)


class CollectorError(Exception):
    """Raised when data collection fails."""

    pass


class BaseCollector(ABC):
    """Base class for data collectors."""

    def __init__(self, name: str):
        """
        Initialize collector.

        Args:
            name: Collector name for logging
        """
        self.name = name
        self.logger = get_logger(f"jeera_trader.collectors.{name}")

    @abstractmethod
    def collect(
        self, start_date: str, end_date: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Collect data for the specified date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            **kwargs: Additional collector-specific parameters

        Returns:
            List of data records

        Raises:
            CollectorError: If collection fails
        """
        pass

    @abstractmethod
    def validate_record(self, record: Dict[str, Any]) -> bool:
        """
        Validate a single data record.

        Args:
            record: Data record to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def collect_with_retry(
        self,
        start_date: str,
        end_date: str,
        max_retries: int = MAX_RETRIES,
        retry_delay: int = RETRY_DELAY,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Collect data with automatic retry on failure.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries (seconds)
            **kwargs: Additional collector-specific parameters

        Returns:
            List of data records

        Raises:
            CollectorError: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                log_progress(
                    f"[{self.name}] Collecting data from {start_date} to {end_date}"
                )
                records = self.collect(start_date, end_date, **kwargs)

                # Validate records
                valid_records = []
                invalid_count = 0

                for record in records:
                    if self.validate_record(record):
                        valid_records.append(record)
                    else:
                        invalid_count += 1
                        self.logger.debug(f"Invalid record: {record}")

                if invalid_count > 0:
                    log_warning(
                        f"[{self.name}] Skipped {invalid_count} invalid records"
                    )

                self.logger.info(
                    f"[{self.name}] Successfully collected {len(valid_records)} records"
                )
                return valid_records

            except Exception as e:
                if attempt < max_retries - 1:
                    log_warning(
                        f"[{self.name}] Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)
                else:
                    log_error(
                        f"[{self.name}] All {max_retries} attempts failed: {e}"
                    )
                    raise CollectorError(
                        f"Data collection failed after {max_retries} attempts: {e}"
                    )

        raise CollectorError("Data collection failed")

    def parse_date(self, date_str: str, format: str = "%Y-%m-%d") -> datetime:
        """
        Parse date string to datetime object.

        Args:
            date_str: Date string
            format: Date format (default: YYYY-MM-DD)

        Returns:
            datetime object

        Raises:
            CollectorError: If date parsing fails
        """
        try:
            return datetime.strptime(date_str, format)
        except ValueError as e:
            raise CollectorError(f"Invalid date format: {date_str}. Expected: {format}")

    def format_date(self, date_obj: datetime, format: str = "%Y-%m-%d") -> str:
        """
        Format datetime object to string.

        Args:
            date_obj: datetime object
            format: Date format (default: YYYY-MM-DD)

        Returns:
            Formatted date string
        """
        return date_obj.strftime(format)

    def validate_date_range(self, start_date: str, end_date: str) -> None:
        """
        Validate that start_date is before end_date.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Raises:
            CollectorError: If date range is invalid
        """
        start = self.parse_date(start_date)
        end = self.parse_date(end_date)

        if start > end:
            raise CollectorError(
                f"Invalid date range: start_date ({start_date}) is after end_date ({end_date})"
            )

        # Check if dates are not too far in the future
        now = datetime.now()
        if start > now:
            raise CollectorError(
                f"Start date ({start_date}) is in the future"
            )

    def split_date_range(
        self, start_date: str, end_date: str, chunk_days: int = 30
    ) -> List[tuple]:
        """
        Split date range into smaller chunks for batch processing.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            chunk_days: Number of days per chunk

        Returns:
            List of (start, end) date tuples
        """
        from datetime import timedelta

        start = self.parse_date(start_date)
        end = self.parse_date(end_date)

        chunks = []
        current = start

        while current <= end:
            chunk_end = min(current + timedelta(days=chunk_days - 1), end)
            chunks.append(
                (self.format_date(current), self.format_date(chunk_end))
            )
            current = chunk_end + timedelta(days=1)

        return chunks

    def rate_limit(self, delay_seconds: float = 1.0) -> None:
        """
        Apply rate limiting between requests.

        Args:
            delay_seconds: Delay in seconds
        """
        time.sleep(delay_seconds)
