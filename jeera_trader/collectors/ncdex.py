"""
NCDEX data collector for jeera futures prices.
Downloads and parses Bhavcopy CSV files from NCDEX official website.
"""

import io
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from jeera_trader.collectors.base import BaseCollector, CollectorError
from jeera_trader.config import Config
from jeera_trader.utils.constants import (
    CONTRACT_MONTHS,
    JEERA_SYMBOL,
    NCDEX_REQUEST_DELAY,
)


class NCDEXCollector(BaseCollector):
    """
    Collector for NCDEX jeera futures data.
    Downloads daily Bhavcopy CSV files from NCDEX official website.
    """

    def __init__(self):
        """Initialize NCDEX collector."""
        super().__init__("NCDEX")

        if not Config.is_loaded():
            Config.load_from_env()

        self.base_url = Config.NCDEX_BASE_URL
        # Bhavcopy URL pattern: https://www.ncdex.com/downloads/bhavcopy/ncdex/bhavcopy_DDMMYYYY.csv
        self.bhavcopy_url_template = f"{self.base_url}/downloads/bhavcopy/ncdex/bhavcopy_{{date}}.csv"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/csv,application/csv,text/plain,*/*",
        })

    def collect(
        self, start_date: str, end_date: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Collect NCDEX futures data for date range by downloading Bhavcopy CSVs.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            **kwargs: Additional parameters

        Returns:
            List of futures price records

        Raises:
            CollectorError: If collection fails
        """
        self.validate_date_range(start_date, end_date)

        all_records = []

        # Generate dates in the range
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = start

        while current <= end:
            # Skip weekends
            if current.weekday() >= 5:
                current += timedelta(days=1)
                continue

            date_str = current.strftime("%Y-%m-%d")

            try:
                # Try to collect data for this date
                daily_records = self._collect_daily_data(current)
                if daily_records:
                    all_records.extend(daily_records)
                    self.logger.info(f"Collected {len(daily_records)} records for {date_str}")

                # Rate limiting
                self.rate_limit(NCDEX_REQUEST_DELAY)

            except Exception as e:
                self.logger.debug(f"No data for {date_str}: {e}")
                # It's normal to have no data for holidays

            current += timedelta(days=1)

        return all_records

    def _collect_daily_data(self, date: datetime) -> List[Dict[str, Any]]:
        """
        Download and parse Bhavcopy CSV for a specific date.

        Args:
            date: Date to collect

        Returns:
            List of jeera futures records for this date

        Raises:
            CollectorError: If download or parsing fails
        """
        # Format date for URL (DDMMYYYY)
        date_str = date.strftime("%d%m%Y")
        url = self.bhavcopy_url_template.format(date=date_str)

        try:
            # Download CSV file
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Parse CSV content
            csv_content = response.text

            # Try to read as CSV
            try:
                df = pd.read_csv(io.StringIO(csv_content))
            except Exception as e:
                self.logger.debug(f"Failed to parse CSV for {date_str}: {e}")
                raise CollectorError(f"Invalid CSV format: {e}")

            # Filter for JEERA symbol
            # Column names may vary, so we need to be flexible
            # Common column names: Symbol, Commodity, TradingSymbol, etc.
            symbol_col = None
            for col in df.columns:
                if col.upper() in ['SYMBOL', 'COMMODITY', 'TRADINGSYMBOL', 'INSTRUMENT']:
                    symbol_col = col
                    break

            if symbol_col is None:
                self.logger.debug(f"No symbol column found in CSV. Columns: {df.columns.tolist()}")
                raise CollectorError("Symbol column not found in Bhavcopy")

            # Filter for JEERA
            jeera_df = df[df[symbol_col].str.upper().str.contains('JEERA|CUMIN', na=False)]

            if jeera_df.empty:
                self.logger.debug(f"No JEERA data found in Bhavcopy for {date_str}")
                return []

            # Extract records
            records = self._parse_bhavcopy_dataframe(jeera_df, date)

            return records

        except requests.RequestException as e:
            # File not found or network error - likely holiday
            self.logger.debug(f"Bhavcopy not available for {date_str}: {e}")
            return []

    def _parse_bhavcopy_dataframe(
        self, df: pd.DataFrame, date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Parse Bhavcopy DataFrame to extract jeera futures records.

        Args:
            df: Filtered DataFrame containing jeera records
            date: Trading date

        Returns:
            List of parsed records
        """
        records = []
        date_str = date.strftime("%Y-%m-%d")

        # Map common column names (Bhavcopy format may vary)
        column_mappings = {
            'open': ['Open', 'OpenPrice', 'Open_Price', 'OPEN'],
            'high': ['High', 'HighPrice', 'High_Price', 'HIGH'],
            'low': ['Low', 'LowPrice', 'Low_Price', 'LOW'],
            'close': ['Close', 'ClosePrice', 'Close_Price', 'CLOSE', 'Settle_Price', 'SettlePrice'],
            'volume': ['Volume', 'TradedQty', 'Traded_Qty', 'VOLUME', 'No_Of_Contracts'],
            'oi': ['Open_Interest', 'OpenInterest', 'OI', 'OPEN_INTEREST'],
            'expiry': ['Expiry', 'ExpiryDate', 'Expiry_Date', 'EXPIRY'],
        }

        def find_column(df, possible_names):
            """Find the first matching column name."""
            for name in possible_names:
                if name in df.columns:
                    return name
            return None

        # Find actual column names
        open_col = find_column(df, column_mappings['open'])
        high_col = find_column(df, column_mappings['high'])
        low_col = find_column(df, column_mappings['low'])
        close_col = find_column(df, column_mappings['close'])
        volume_col = find_column(df, column_mappings['volume'])
        oi_col = find_column(df, column_mappings['oi'])
        expiry_col = find_column(df, column_mappings['expiry'])

        # Check if we have minimum required columns
        if not all([close_col]):  # At least close price is required
            self.logger.warning(f"Missing price columns in Bhavcopy. Columns: {df.columns.tolist()}")
            return records

        for idx, row in df.iterrows():
            try:
                # Extract contract month from expiry date
                contract_month = None
                if expiry_col and pd.notna(row[expiry_col]):
                    try:
                        # Parse expiry date (format may vary: DD-MMM-YYYY, YYYY-MM-DD, etc.)
                        expiry_str = str(row[expiry_col])
                        expiry_date = self._parse_expiry_date(expiry_str)
                        contract_month = expiry_date.strftime("%b").upper()
                    except Exception:
                        pass

                # If contract month not found from expiry, try to infer from symbol
                if not contract_month:
                    # Try to extract from symbol (e.g., JEERA JAN25, JEERAJAN25)
                    for col in df.columns:
                        if col.upper() in ['SYMBOL', 'TRADINGSYMBOL', 'INSTRUMENT']:
                            symbol_str = str(row[col]).upper()
                            for month in CONTRACT_MONTHS:
                                if month in symbol_str:
                                    contract_month = month
                                    break
                            break

                # Default to current month + 1 if still not found
                if not contract_month:
                    next_month = date + timedelta(days=30)
                    contract_month = next_month.strftime("%b").upper()

                # Extract prices with fallbacks
                close = float(row[close_col]) if close_col and pd.notna(row[close_col]) else None
                if close is None:
                    continue  # Skip if no close price

                open_price = float(row[open_col]) if open_col and pd.notna(row[open_col]) else close
                high = float(row[high_col]) if high_col and pd.notna(row[high_col]) else close
                low = float(row[low_col]) if low_col and pd.notna(row[low_col]) else close

                # Ensure price relationships are valid
                high = max(high, open_price, close)
                low = min(low, open_price, close)

                # Extract volume and OI
                volume = None
                if volume_col and pd.notna(row[volume_col]):
                    try:
                        volume = int(float(row[volume_col]))
                    except (ValueError, TypeError):
                        volume = None

                open_interest = None
                if oi_col and pd.notna(row[oi_col]):
                    try:
                        open_interest = int(float(row[oi_col]))
                    except (ValueError, TypeError):
                        open_interest = None

                record = {
                    "date": date_str,
                    "symbol": JEERA_SYMBOL,
                    "contract_month": contract_month,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close, 2),
                    "volume": volume,
                    "open_interest": open_interest,
                }

                records.append(record)

            except Exception as e:
                self.logger.debug(f"Failed to parse row: {e}")
                continue

        return records

    def _parse_expiry_date(self, expiry_str: str) -> datetime:
        """
        Parse expiry date from various formats.

        Args:
            expiry_str: Expiry date string

        Returns:
            Parsed datetime object
        """
        expiry_str = expiry_str.strip()

        # Try various date formats
        formats = [
            "%d-%b-%Y",      # 20-JAN-2025
            "%d-%b-%y",      # 20-JAN-25
            "%d/%m/%Y",      # 20/01/2025
            "%Y-%m-%d",      # 2025-01-20
            "%d-%m-%Y",      # 20-01-2025
            "%d%b%Y",        # 20JAN2025
            "%d%b%y",        # 20JAN25
        ]

        for fmt in formats:
            try:
                return datetime.strptime(expiry_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse expiry date: {expiry_str}")

    def validate_record(self, record: Dict[str, Any]) -> bool:
        """
        Validate a futures price record.

        Args:
            record: Record to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "date",
            "symbol",
            "contract_month",
            "open",
            "high",
            "low",
            "close",
        ]

        # Check required fields
        for field in required_fields:
            if field not in record:
                self.logger.debug(f"Missing field: {field}")
                return False

        # Validate date format
        try:
            datetime.strptime(record["date"], "%Y-%m-%d")
        except ValueError:
            self.logger.debug(f"Invalid date format: {record['date']}")
            return False

        # Validate symbol
        if record["symbol"] != JEERA_SYMBOL:
            self.logger.debug(f"Invalid symbol: {record['symbol']}")
            return False

        # Validate contract month
        if record["contract_month"] not in CONTRACT_MONTHS:
            self.logger.debug(f"Invalid contract month: {record['contract_month']}")
            return False

        # Validate price relationships: low <= open, close <= high
        try:
            low = float(record["low"])
            high = float(record["high"])
            open_price = float(record["open"])
            close = float(record["close"])

            if not (low <= open_price <= high):
                self.logger.debug(
                    f"Invalid price: open ({open_price}) not between low ({low}) and high ({high})"
                )
                return False

            if not (low <= close <= high):
                self.logger.debug(
                    f"Invalid price: close ({close}) not between low ({low}) and high ({high})"
                )
                return False

            # Check for reasonable price values (between 1000 and 100000)
            if not (1000 <= low <= 100000 and 1000 <= high <= 100000):
                self.logger.debug(f"Price out of reasonable range: {low}-{high}")
                return False

        except (ValueError, TypeError) as e:
            self.logger.debug(f"Invalid price values: {e}")
            return False

        # Validate volume and OI (optional fields, but must be non-negative if present)
        if "volume" in record and record["volume"] is not None:
            try:
                if int(record["volume"]) < 0:
                    self.logger.debug(f"Negative volume: {record['volume']}")
                    return False
            except (ValueError, TypeError):
                self.logger.debug(f"Invalid volume: {record['volume']}")
                return False

        if "open_interest" in record and record["open_interest"] is not None:
            try:
                if int(record["open_interest"]) < 0:
                    self.logger.debug(f"Negative open interest: {record['open_interest']}")
                    return False
            except (ValueError, TypeError):
                self.logger.debug(f"Invalid open interest: {record['open_interest']}")
                return False

        return True
