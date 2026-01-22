"""
Weather data collector using Open-Meteo API (FREE).
Collects historical weather data for jeera growing regions (Gujarat and Rajasthan).
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from jeera_trader.collectors.base import BaseCollector, CollectorError
from jeera_trader.logger import get_logger
from jeera_trader.utils.constants import WEATHER_LOCATIONS, WEATHER_REQUEST_DELAY

logger = get_logger(__name__)


class WeatherCollector(BaseCollector):
    """
    Collector for weather data from Open-Meteo API (completely free).

    Open-Meteo provides:
    - Historical weather data from 1940 to present
    - No API key required
    - No rate limits for reasonable use
    - High quality data
    """

    def __init__(self):
        """Initialize weather collector."""
        super().__init__("Weather")

        # Open-Meteo Historical Weather API
        self.api_url = "https://archive-api.open-meteo.com/v1/archive"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JeeraTrader/1.0",
        })

    def collect(
        self, start_date: str, end_date: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Collect weather data for date range and all locations.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            **kwargs: Additional parameters

        Returns:
            List of weather records

        Raises:
            CollectorError: If collection fails
        """
        self.validate_date_range(start_date, end_date)

        all_records = []

        # Collect data for each location
        for location_name, location_info in WEATHER_LOCATIONS.items():
            try:
                self.logger.info(f"Collecting weather data for {location_name}")
                records = self._collect_location(
                    location_name,
                    location_info,
                    start_date,
                    end_date,
                )
                all_records.extend(records)
                self.rate_limit(WEATHER_REQUEST_DELAY)
            except Exception as e:
                self.logger.warning(
                    f"Failed to collect data for {location_name}: {e}"
                )
                # Continue with next location
                continue

        return all_records

    def _collect_location(
        self,
        location_name: str,
        location_info: Dict[str, Any],
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        Collect weather data for a specific location using Open-Meteo API.

        Args:
            location_name: Name of location
            location_info: Location configuration (lat, lon, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of weather records for this location

        Raises:
            CollectorError: If API request fails
        """
        lat = location_info["lat"]
        lon = location_info["lon"]

        # Open-Meteo API parameters
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": ",".join([
                "temperature_2m_mean",
                "temperature_2m_min",
                "temperature_2m_max",
                "precipitation_sum",
                "relative_humidity_2m_mean",
                "wind_speed_10m_max",
                "surface_pressure_mean",
            ]),
            "timezone": "Asia/Kolkata",
        }

        try:
            response = self.session.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Parse response
            records = self._parse_weather_response(location_name, data)

            return records

        except requests.RequestException as e:
            raise CollectorError(f"Failed to fetch weather data for {location_name}: {e}")
        except (KeyError, ValueError) as e:
            raise CollectorError(f"Failed to parse weather data for {location_name}: {e}")

    def _parse_weather_response(
        self, location: str, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Parse Open-Meteo API response.

        Args:
            location: Location name
            data: API response JSON

        Returns:
            List of weather records
        """
        records = []

        # Extract daily data
        if "daily" not in data:
            self.logger.warning(f"No daily data in response for {location}")
            return records

        daily = data["daily"]

        # Get arrays for each variable
        dates = daily.get("time", [])
        temp_mean = daily.get("temperature_2m_mean", [])
        temp_min = daily.get("temperature_2m_min", [])
        temp_max = daily.get("temperature_2m_max", [])
        precipitation = daily.get("precipitation_sum", [])
        humidity = daily.get("relative_humidity_2m_mean", [])
        wind_speed = daily.get("wind_speed_10m_max", [])
        pressure = daily.get("surface_pressure_mean", [])

        # Create records
        for i in range(len(dates)):
            try:
                record = {
                    "date": dates[i],
                    "location": location,
                    "temp_avg": round(temp_mean[i], 2) if i < len(temp_mean) and temp_mean[i] is not None else None,
                    "temp_min": round(temp_min[i], 2) if i < len(temp_min) and temp_min[i] is not None else None,
                    "temp_max": round(temp_max[i], 2) if i < len(temp_max) and temp_max[i] is not None else None,
                    "rainfall": round(precipitation[i], 2) if i < len(precipitation) and precipitation[i] is not None else 0.0,
                    "humidity": round(humidity[i], 2) if i < len(humidity) and humidity[i] is not None else None,
                    "wind_speed": round(wind_speed[i], 2) if i < len(wind_speed) and wind_speed[i] is not None else None,
                    "pressure": round(pressure[i], 2) if i < len(pressure) and pressure[i] is not None else None,
                }

                # Skip record if missing critical data
                if record["temp_avg"] is None:
                    self.logger.debug(f"Skipping {location} {dates[i]}: missing temperature data")
                    continue

                records.append(record)

            except Exception as e:
                self.logger.debug(f"Failed to parse record for {location} {dates[i]}: {e}")
                continue

        return records

    def validate_record(self, record: Dict[str, Any]) -> bool:
        """
        Validate a weather record.

        Args:
            record: Record to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["date", "location", "temp_avg"]

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

        # Validate location
        if record["location"] not in WEATHER_LOCATIONS:
            self.logger.debug(f"Invalid location: {record['location']}")
            return False

        # Validate temperature values (reasonable range for India: -10 to 60°C)
        try:
            temp_avg = float(record["temp_avg"])
            if not (-10 <= temp_avg <= 60):
                self.logger.debug(f"Temperature out of range: {temp_avg}")
                return False

            if "temp_min" in record and record["temp_min"] is not None:
                temp_min = float(record["temp_min"])
                if not (-10 <= temp_min <= 60):
                    self.logger.debug(f"Min temperature out of range: {temp_min}")
                    return False

            if "temp_max" in record and record["temp_max"] is not None:
                temp_max = float(record["temp_max"])
                if not (-10 <= temp_max <= 60):
                    self.logger.debug(f"Max temperature out of range: {temp_max}")
                    return False

                # Check temperature relationship
                if "temp_min" in record and record["temp_min"] is not None:
                    if temp_min > temp_max:
                        self.logger.debug(
                            f"Min temp ({temp_min}) > max temp ({temp_max})"
                        )
                        return False

        except (ValueError, TypeError) as e:
            self.logger.debug(f"Invalid temperature values: {e}")
            return False

        # Validate rainfall (must be non-negative)
        if "rainfall" in record and record["rainfall"] is not None:
            try:
                rainfall = float(record["rainfall"])
                if rainfall < 0:
                    self.logger.debug(f"Negative rainfall: {rainfall}")
                    return False
            except (ValueError, TypeError):
                self.logger.debug(f"Invalid rainfall: {record['rainfall']}")
                return False

        # Validate humidity (0-100%)
        if "humidity" in record and record["humidity"] is not None:
            try:
                humidity = float(record["humidity"])
                if not (0 <= humidity <= 100):
                    self.logger.debug(f"Humidity out of range: {humidity}")
                    return False
            except (ValueError, TypeError):
                self.logger.debug(f"Invalid humidity: {record['humidity']}")
                return False

        return True
