"""
Streamlit web interface for Jeera Trader.
Interactive dashboard for data collection, model training, and trading signals.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jeera_trader.config import Config
from jeera_trader.commands.collect import collect_ncdex, collect_weather
from jeera_trader.commands.features import run_features
from jeera_trader.commands.train import run_train
from jeera_trader.commands.signal import run_signal
from jeera_trader.database.repository import (
    FuturesPricesRepository,
    WeatherDataRepository,
    FeaturesRepository,
    TradingSignalsRepository,
    ModelMetadataRepository,
)
from jeera_trader.database.connection import get_connection

# Page config
st.set_page_config(
    page_title="Jeera Trader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize config
try:
    Config.load_from_env()
except Exception as e:
    st.error(f"Configuration error: {e}")


def get_database_stats():
    """Get statistics from database."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Futures prices count
        cursor.execute("SELECT COUNT(*) FROM futures_prices")
        futures_count = cursor.fetchone()[0]

        # Weather data count
        cursor.execute("SELECT COUNT(*) FROM weather_data")
        weather_count = cursor.fetchone()[0]

        # Features count
        cursor.execute("SELECT COUNT(*) FROM features")
        features_count = cursor.fetchone()[0]

        # Signals count
        cursor.execute("SELECT COUNT(*) FROM trading_signals")
        signals_count = cursor.fetchone()[0]

        # Latest data dates
        cursor.execute("SELECT MAX(date) FROM futures_prices")
        latest_futures = cursor.fetchone()[0] or "No data"

        cursor.execute("SELECT MAX(date) FROM weather_data")
        latest_weather = cursor.fetchone()[0] or "No data"

        return {
            "futures_count": futures_count,
            "weather_count": weather_count,
            "features_count": features_count,
            "signals_count": signals_count,
            "latest_futures": latest_futures,
            "latest_weather": latest_weather,
        }


def show_dashboard():
    """Show main dashboard."""
    st.markdown('<h1 class="main-header">📈 Jeera Trader Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("**ML-Based Predictive Trading System for NCDEX Jeera Futures**")

    st.markdown("---")

    # Get database stats
    stats = get_database_stats()

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Futures Records", f"{stats['futures_count']:,}")
        st.caption(f"Latest: {stats['latest_futures']}")

    with col2:
        st.metric("Weather Records", f"{stats['weather_count']:,}")
        st.caption(f"Latest: {stats['latest_weather']}")

    with col3:
        st.metric("Features Generated", f"{stats['features_count']:,}")

    with col4:
        st.metric("Trading Signals", f"{stats['signals_count']:,}")

    st.markdown("---")

    # Latest signals
    st.subheader("📊 Latest Trading Signals")

    try:
        repo = TradingSignalsRepository()
        signals_df = repo.to_dataframe()

        if not signals_df.empty:
            signals_df = signals_df.sort_values('signal_date', ascending=False).head(5)

            for _, signal in signals_df.iterrows():
                signal_type = signal['signal_type']

                # Color based on signal type
                if 'BUY' in signal_type:
                    color = "#28a745"
                    emoji = "🟢"
                elif 'SELL' in signal_type:
                    color = "#dc3545"
                    emoji = "🔴"
                else:
                    color = "#6c757d"
                    emoji = "⚪"

                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                            padding: 1rem; border-radius: 10px; margin: 0.5rem 0;
                            border-left: 4px solid {color};">
                    <strong>{emoji} {signal_type}</strong> | {signal['signal_date']}<br>
                    Current: ₹{signal['current_price']:,.2f} |
                    Predicted: ₹{signal['predicted_price']:,.2f} |
                    Confidence: {signal['confidence']:.1%}<br>
                    <small>{signal['reasoning']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No trading signals yet. Generate your first signal from the 'Trading Signals' page!")

    except Exception as e:
        st.warning(f"Could not load signals: {e}")

    # Quick start guide
    st.markdown("---")
    st.subheader("🚀 Quick Start")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **First Time Setup:**
        1. Go to **Data Collection** → Collect data (2024)
        2. Go to **Model Training** → Train Random Forest
        3. Go to **Trading Signals** → Generate signal
        """)

    with col2:
        st.markdown("""
        **Daily Workflow:**
        1. Collect today's data
        2. Generate features automatically
        3. Get trading signal with risk levels
        """)


def show_data_collection():
    """Show data collection page."""
    st.markdown('<h1 class="main-header">🔄 Data Collection</h1>', unsafe_allow_html=True)

    st.markdown("""
    Collect historical data from **FREE** sources:
    - **NCDEX Bhavcopy** (Official CSV files)
    - **Open-Meteo API** (Weather data)
    """)

    st.markdown("---")

    # Date range selection
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime(2024, 1, 1),
            max_value=datetime.now(),
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            max_value=datetime.now(),
        )

    # Collection buttons
    st.subheader("Collect Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📈 Collect NCDEX Data", use_container_width=True):
            with st.spinner("Collecting NCDEX data..."):
                try:
                    collect_ncdex(
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d")
                    )
                    st.success("✓ NCDEX data collected successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        if st.button("🌤️ Collect Weather Data", use_container_width=True):
            with st.spinner("Collecting weather data..."):
                try:
                    collect_weather(
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d")
                    )
                    st.success("✓ Weather data collected successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col3:
        if st.button("🔄 Collect All Data", type="primary", use_container_width=True):
            with st.spinner("Collecting all data... This may take a few minutes."):
                try:
                    # Collect NCDEX
                    st.info("Collecting NCDEX data...")
                    collect_ncdex(
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d")
                    )

                    # Collect weather
                    st.info("Collecting weather data...")
                    collect_weather(
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d")
                    )

                    st.success("✓ All data collected successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

    # Show collected data stats
    st.markdown("---")
    st.subheader("📊 Collected Data")

    stats = get_database_stats()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 Futures Data</h3>
            <h2>{stats['futures_count']:,}</h2>
            <p>Latest: {stats['latest_futures']}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🌤️ Weather Data</h3>
            <h2>{stats['weather_count']:,}</h2>
            <p>Latest: {stats['latest_weather']}</p>
        </div>
        """, unsafe_allow_html=True)


def show_model_training():
    """Show model training page."""
    st.markdown('<h1 class="main-header">🤖 Model Training</h1>', unsafe_allow_html=True)

    st.markdown("Train machine learning models to predict jeera futures prices.")

    st.markdown("---")

    # Training options
    col1, col2 = st.columns([2, 1])

    with col1:
        model_type = st.selectbox(
            "Select Model",
            ["Random Forest", "XGBoost (Coming Soon)", "All Models"],
            disabled=True,  # Only RF is implemented
        )

        tune_hyperparameters = st.checkbox("Enable Hyperparameter Tuning", value=False)

        st.info("""
        **Note:** Hyperparameter tuning will take longer but may improve accuracy.
        Recommended for initial training only.
        """)

    with col2:
        st.markdown("""
        ### Training Info
        - **Data Split:** 80/20 (time-based)
        - **Algorithm:** Random Forest
        - **Features:** 50+ engineered features
        - **Target:** Next-day price
        """)

    # Train button
    if st.button("🚀 Train Model", type="primary", use_container_width=True):
        with st.spinner("Training model... This may take a few minutes."):
            try:
                # Create args object
                class TrainArgs:
                    model = "rf"
                    tune = tune_hyperparameters

                # Train model
                from jeera_trader.commands.train import run_train
                exit_code = run_train(TrainArgs())

                if exit_code == 0:
                    st.success("✓ Model trained successfully!")

                    # Show metrics
                    repo = ModelMetadataRepository()
                    metadata_df = repo.to_dataframe()

                    if not metadata_df.empty:
                        latest = metadata_df.iloc[-1]

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("RMSE", f"{latest['rmse']:.2f}")

                        with col2:
                            st.metric("MAE", f"{latest['mae']:.2f}")

                        with col3:
                            st.metric("R² Score", f"{latest['r2']:.3f}")

                        with col4:
                            st.metric("Direction Accuracy", f"{latest['direction_accuracy']:.1%}")

                        st.markdown("---")
                        st.info(f"Model saved as: **{latest['model_name']}**")
                else:
                    st.error("Model training failed. Check logs for details.")

            except Exception as e:
                st.error(f"Error: {e}")

    # Show training history
    st.markdown("---")
    st.subheader("📊 Training History")

    try:
        repo = ModelMetadataRepository()
        history_df = repo.to_dataframe()

        if not history_df.empty:
            st.dataframe(
                history_df[['model_name', 'trained_at', 'rmse', 'mae', 'r2', 'direction_accuracy']],
                use_container_width=True,
            )
        else:
            st.info("No training history yet. Train your first model!")

    except Exception as e:
        st.warning(f"Could not load training history: {e}")


def show_trading_signals():
    """Show trading signals page."""
    st.markdown('<h1 class="main-header">🎯 Trading Signals</h1>', unsafe_allow_html=True)

    st.markdown("Generate actionable trading signals with risk management.")

    st.markdown("---")

    # Generate signal button
    if st.button("🎯 Generate Trading Signal", type="primary", use_container_width=True):
        with st.spinner("Generating trading signal..."):
            try:
                # Create args object
                class SignalArgs:
                    model = None
                    date = None

                # Generate signal
                exit_code = run_signal(SignalArgs())

                if exit_code == 0:
                    st.success("✓ Trading signal generated successfully!")
                else:
                    st.error("Signal generation failed. Check logs for details.")

            except Exception as e:
                st.error(f"Error: {e}")

    # Show latest signal
    st.markdown("---")
    st.subheader("📊 Latest Signal")

    try:
        repo = TradingSignalsRepository()
        signals_df = repo.to_dataframe()

        if not signals_df.empty:
            latest = signals_df.iloc[-1]

            # Signal type
            signal_type = latest['signal_type']

            # Color based on signal type
            if 'STRONG_BUY' in signal_type:
                color = "#155724"
                bg_color = "#d4edda"
            elif 'BUY' in signal_type:
                color = "#28a745"
                bg_color = "#d4edda"
            elif 'HOLD' in signal_type:
                color = "#6c757d"
                bg_color = "#e2e3e5"
            elif 'SELL' in signal_type:
                color = "#dc3545"
                bg_color = "#f8d7da"
            elif 'STRONG_SELL' in signal_type:
                color = "#721c24"
                bg_color = "#f8d7da"

            # Display signal
            st.markdown(f"""
            <div style="background: {bg_color}; border-left: 4px solid {color};
                        padding: 2rem; border-radius: 10px; margin: 1rem 0;">
                <h2 style="color: {color}; margin: 0;">Signal: {signal_type}</h2>
                <p style="margin-top: 0.5rem;"><strong>{latest['signal_date']}</strong></p>
            </div>
            """, unsafe_allow_html=True)

            # Prices
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Current Price", f"₹{latest['current_price']:,.2f}")

            with col2:
                st.metric(
                    "Predicted Price",
                    f"₹{latest['predicted_price']:,.2f}",
                    f"{latest['expected_return']:.2%}"
                )

            with col3:
                st.metric("Confidence", f"{latest['confidence']:.1%}")

            # Risk management
            st.markdown("---")
            st.subheader("🛡️ Risk Management")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Stop Loss", f"₹{latest['stop_loss']:,.2f}")

            with col2:
                st.metric("Take Profit", f"₹{latest['take_profit']:,.2f}")

            with col3:
                st.metric("Position Size", f"₹{latest['position_size']:,.0f}")

            # Reasoning
            st.markdown("---")
            st.subheader("📝 Analysis")
            st.info(latest['reasoning'])

        else:
            st.info("No trading signals yet. Generate your first signal!")

    except Exception as e:
        st.warning(f"Could not load signals: {e}")


# Sidebar
with st.sidebar:
    st.markdown('<h2 style="color: #667eea;">📈 Jeera Trader</h2>', unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["Dashboard", "Data Collection", "Model Training", "Trading Signals"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown("""
    ### About
    ML-based predictive system for jeera futures trading on NCDEX.

    **Features:**
    - 🔄 Free data collection
    - ⚙️ 50+ engineered features
    - 🤖 Random Forest ML
    - 🎯 Automated signals
    - 🛡️ Risk management
    """)

    st.markdown("---")

    # System status
    st.markdown("### System Status")
    stats = get_database_stats()

    if stats['futures_count'] > 0:
        st.success("✓ Data collected")
    else:
        st.warning("⚠ No data")

    if stats['features_count'] > 0:
        st.success("✓ Features generated")
    else:
        st.warning("⚠ No features")

    # Check for trained model
    try:
        repo = ModelMetadataRepository()
        models_df = repo.to_dataframe()
        if not models_df.empty:
            st.success("✓ Model trained")
        else:
            st.warning("⚠ No model")
    except:
        st.warning("⚠ No model")

# Main content
if page == "Dashboard":
    show_dashboard()
elif page == "Data Collection":
    show_data_collection()
elif page == "Model Training":
    show_model_training()
elif page == "Trading Signals":
    show_trading_signals()
