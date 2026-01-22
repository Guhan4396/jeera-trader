# Jeera Trader

A machine learning-based predictive system for jeera (cumin) futures trading on NCDEX.

## Overview

Jeera Trader is a CLI-based trading system that:
- Collects historical NCDEX futures data and weather data
- Engineers features using technical indicators and domain knowledge
- Trains Random Forest and XGBoost models for price prediction
- Generates actionable trading signals with risk management
- Provides backtesting capabilities to validate strategies

This is a learning prototype focused on demonstrating ML applications in commodity trading.

## Features

- **Data Collection**: Download NCDEX Bhavcopy CSV files (official, free) and fetch weather data from Open-Meteo API (free)
- **Feature Engineering**: 50+ features including technical indicators, seasonal patterns, and weather metrics
- **ML Models**: Random Forest and XGBoost with hyperparameter tuning
- **Trading Signals**: Generate BUY/SELL/HOLD signals with confidence scores
- **Risk Management**: Automatic stop-loss and take-profit calculations
- **Backtesting**: Validate strategies on historical data with comprehensive metrics
- **Daily Automation**: Scheduled updates for continuous operation
- **100% Free Data Sources**: No API keys or subscriptions required!

## Project Structure

```
jeera_trader/
├── jeera_trader/           # Main package
│   ├── collectors/         # Data collection modules
│   ├── features/           # Feature engineering
│   ├── models/             # ML models
│   ├── trading/            # Signal generation & risk management
│   ├── backtesting/        # Strategy validation
│   ├── commands/           # CLI command handlers
│   ├── database/           # Data persistence layer
│   ├── utils/              # Utilities and constants
│   ├── config.py           # Configuration management
│   ├── logger.py           # Logging setup
│   └── main.py             # CLI entry point
├── data/                   # Data storage (gitignored)
├── logs/                   # Log files (gitignored)
├── notebooks/              # Analysis notebooks
├── setup.py                # Package setup
├── requirements.txt        # Dependencies
└── .env                    # Configuration (gitignored)
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection (for downloading data from NCDEX and Open-Meteo)
- **No API keys required!** Both data sources are completely free

### Setup

1. Clone or download the project:
```bash
cd /Users/guhansenthilsubramanian/Desktop/jeera_trader
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install package in development mode:
```bash
pip install -e .
```

4. Configure environment variables (optional - defaults work fine):
```bash
cp .env.example .env
# Edit .env if you want to customize paths or parameters
```

5. Initialize database:
```bash
jeera-trader db --init
```

## Configuration

Edit `.env` file with your settings (all settings are optional with sensible defaults):

```bash
# Database path
DATABASE_PATH=/path/to/data/jeera_trader.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=/path/to/logs/jeera_trader.log

# Data Sources (both FREE, no API keys needed!)
NCDEX_BASE_URL=https://www.ncdex.com  # Downloads Bhavcopy CSVs
# Weather: Uses Open-Meteo API automatically

# Trading parameters
DEFAULT_STOP_LOSS_PCT=2.0
DEFAULT_TAKE_PROFIT_PCT=5.0
DEFAULT_POSITION_SIZE=100000
```

## Usage

### Database Management

```bash
# Initialize database
jeera-trader db --init

# Show statistics
jeera-trader db --stats

# Drop all tables (caution!)
jeera-trader db --drop
```

### Data Collection

```bash
# Collect NCDEX data
jeera-trader collect --source ncdex --start-date 2024-01-01 --end-date 2025-12-31

# Collect weather data
jeera-trader collect --source weather --start-date 2024-01-01 --end-date 2025-12-31

# Collect all data
jeera-trader collect --source all --start-date 2024-01-01 --end-date 2025-12-31
```

### Feature Engineering

```bash
# Generate features for date range
jeera-trader features --start-date 2024-01-01 --end-date 2025-12-31
```

### Model Training

```bash
# Train Random Forest
jeera-trader train --model rf

# Train XGBoost
jeera-trader train --model xgb

# Train all models
jeera-trader train --model all

# Train with hyperparameter tuning
jeera-trader train --model all --tune
```

### Trading Signals

```bash
# Generate today's trading signal
jeera-trader signal

# Generate signal for specific date
jeera-trader signal --date 2025-01-15

# Use specific model
jeera-trader signal --model random_forest_v1
```

### Predictions

```bash
# Make prediction with active model
jeera-trader predict --days 1

# Use specific model
jeera-trader predict --model random_forest_v1 --days 1
```

### Backtesting

```bash
# Backtest strategy
jeera-trader backtest --start-date 2024-06-01 --end-date 2025-12-31 --model random_forest_v1

# With custom initial capital
jeera-trader backtest --start-date 2024-06-01 --end-date 2025-12-31 --model random_forest_v1 --initial-capital 500000
```

### Daily Automation

```bash
# Run daily update (collect data, generate features, predict, signal)
jeera-trader update
```

### Configuration

```bash
# Show current configuration
jeera-trader config
```

## Workflow

### Initial Setup Workflow

1. **Install and configure**:
   ```bash
   pip install -e .
   cp .env.example .env
   # Edit .env with your API key
   jeera-trader db --init
   ```

2. **Collect historical data** (1-2 years recommended):
   ```bash
   jeera-trader collect --source all --start-date 2024-01-01 --end-date 2025-12-31
   ```

3. **Generate features**:
   ```bash
   jeera-trader features --start-date 2024-01-01 --end-date 2025-12-31
   ```

4. **Train models**:
   ```bash
   jeera-trader train --model all
   ```

5. **Generate trading signal**:
   ```bash
   jeera-trader signal
   ```

6. **Backtest strategy**:
   ```bash
   jeera-trader backtest --start-date 2024-06-01 --end-date 2025-12-31 --model random_forest_v1
   ```

### Daily Workflow

Set up cron job for daily automation:

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 7 PM (after market close)
0 19 * * 1-5 cd /path/to/jeera_trader && ./venv/bin/jeera-trader update >> logs/cron.log 2>&1
```

Or run manually:
```bash
jeera-trader update
```

## Features Engineering

The system generates 50+ features:

### Price Features
- Moving averages (5, 10, 20, 50 days)
- RSI (14-day)
- MACD and signal line
- Bollinger Bands
- Volatility (20-day)
- Price momentum

### Time Features
- Cyclical encoding (month, quarter)
- Day of week, day of month
- Week of year
- Crop cycle phases (sowing, growing, harvest, post-harvest)

### Weather Features
- Temperature (avg, min, max)
- Rainfall (current, 7-day, 30-day rolling)
- Humidity
- Temperature anomalies

### Volume Features
- Volume moving average
- Open interest changes
- Volume/OI ratio

### Lag Features
- Previous prices (1, 5, 10 days ago)
- Previous volume

## Models

### Random Forest
- Ensemble of decision trees
- Good for capturing non-linear relationships
- Provides feature importance
- Resistant to overfitting

### XGBoost
- Gradient boosting implementation
- Often better predictive performance
- Fast training with early stopping
- Handles missing values

Both models use time-based cross-validation and hyperparameter tuning.

## Trading Signals

Signal types and thresholds:

- **STRONG_BUY**: Predicted increase >= 3%
- **BUY**: Predicted increase >= 1.5%
- **HOLD**: Predicted change between -1.5% and 1.5%
- **SELL**: Predicted decrease <= -3%
- **STRONG_SELL**: Predicted decrease <= -5%

Each signal includes:
- Confidence score
- Current and predicted prices
- Stop-loss level (default: 2%)
- Take-profit level (default: 5%)
- Suggested position size
- Human-readable reasoning

## Backtesting Metrics

The backtesting engine calculates:

- **Returns**: Total return and percentage return
- **Risk**: Sharpe ratio, maximum drawdown, drawdown duration
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Trade Statistics**: Average win/loss, largest win/loss
- **Costs**: Commissions and slippage

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black jeera_trader/

# Lint code
flake8 jeera_trader/

# Type checking
mypy jeera_trader/
```

## Data Sources

### NCDEX Futures Data (FREE)
- **Source**: Official NCDEX Bhavcopy CSV files
- **URL**: https://www.ncdex.com/markets/bhavcopy
- **Data**: Daily OHLC prices, volume, open interest for jeera futures
- **Cost**: Completely free (official public data)
- **Reliability**: High (official source, structured CSV format)

### Weather Data (FREE)
- **Source**: Open-Meteo Historical Weather API
- **URL**: https://open-meteo.com
- **Data**: Daily temperature, rainfall, humidity for Gujarat & Rajasthan
- **Historical Range**: 1940 to present
- **Cost**: Completely free (no API key required)
- **Reliability**: High (research-grade weather data)

## Limitations

- NCDEX Bhavcopy files may not be available for recent dates immediately
- Weather data depends on Open-Meteo API availability
- Models require periodic retraining (monthly recommended)
- No real-time intraday data
- No automated order execution

## Future Enhancements

- [ ] More data sources (Agmarknet, export data, news sentiment)
- [ ] LSTM and ensemble models
- [ ] Web dashboard (Flask/Streamlit)
- [ ] Broker integration for automated trading
- [ ] Multi-commodity support (turmeric, coriander, etc.)
- [ ] Email/Telegram alerts
- [ ] Real-time data streaming

## License

MIT License

## Disclaimer

This software is for educational and research purposes only. Trading commodities involves substantial risk of loss. The predictions and signals generated by this system should not be considered as financial advice. Always conduct your own research and consult with a qualified financial advisor before making trading decisions.

## Support

For issues and questions, please create an issue on GitHub or contact the maintainer.

## Acknowledgments

- NCDEX for providing futures data
- OpenWeatherMap for weather API
- Scikit-learn and XGBoost teams for ML libraries
