"""Generate sample NCDEX data for demonstration."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from jeera_trader.database.repository import FuturesPricesRepository
from jeera_trader.config import Config

# Load config
Config.load_from_env()

# Generate sample data
start_date = datetime(2024, 1, 1)
dates = pd.date_range(start_date, periods=250, freq='B')  # Business days

# Base price around 28000
base_price = 28000
price_changes = np.random.randn(len(dates)) * 200  # Random walk
prices = base_price + np.cumsum(price_changes)

# Generate OHLC data
data = []
for i, date in enumerate(dates):
    price = prices[i]
    daily_volatility = np.random.uniform(0.005, 0.02)

    # Generate OHLC
    open_price = price + np.random.uniform(-100, 100)
    high = max(open_price, price) + abs(np.random.uniform(0, 200))
    low = min(open_price, price) - abs(np.random.uniform(0, 200))
    close = price

    # Contract months (3 active contracts)
    for month_offset in [1, 2, 3]:
        contract_month = (date + timedelta(days=30*month_offset)).strftime('%b%y').upper()

        record = {
            'date': date.strftime('%Y-%m-%d'),
            'symbol': 'JEERA',
            'contract_month': contract_month,
            'expiry_date': (date + timedelta(days=30*month_offset)).strftime('%Y-%m-%d'),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': int(np.random.uniform(5000, 15000)),
            'open_interest': int(np.random.uniform(10000, 30000)),
            'value': close * np.random.uniform(5000, 15000),
        }
        data.append(record)

# Save to database
repo = FuturesPricesRepository()
repo.bulk_insert(data)

print(f"✓ Created {len(data)} sample NCDEX records")
print(f"  Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
print(f"  Price range: ₹{prices.min():.2f} to ₹{prices.max():.2f}")
