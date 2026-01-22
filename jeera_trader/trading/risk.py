"""
Risk management for jeera futures trading.
"""

from typing import Dict

from jeera_trader.config import Config
from jeera_trader.logger import get_logger

logger = get_logger(__name__)


def calculate_stop_loss(
    current_price: float,
    signal_type: str,
    stop_loss_pct: float = None,
) -> float:
    """
    Calculate stop loss price.

    Args:
        current_price: Current market price
        signal_type: Signal type (BUY, SELL, etc.)
        stop_loss_pct: Stop loss percentage (default: from config)

    Returns:
        Stop loss price
    """
    if stop_loss_pct is None:
        if not Config.is_loaded():
            Config.load_from_env()
        stop_loss_pct = Config.DEFAULT_STOP_LOSS_PCT

    # For long positions (BUY signals), stop loss is below current price
    # For short positions (SELL signals), stop loss is above current price
    if "BUY" in signal_type:
        stop_loss = current_price * (1 - stop_loss_pct / 100)
    elif "SELL" in signal_type:
        stop_loss = current_price * (1 + stop_loss_pct / 100)
    else:  # HOLD
        stop_loss = current_price * (1 - stop_loss_pct / 100)

    return stop_loss


def calculate_take_profit(
    current_price: float,
    signal_type: str,
    take_profit_pct: float = None,
) -> float:
    """
    Calculate take profit price.

    Args:
        current_price: Current market price
        signal_type: Signal type (BUY, SELL, etc.)
        take_profit_pct: Take profit percentage (default: from config)

    Returns:
        Take profit price
    """
    if take_profit_pct is None:
        if not Config.is_loaded():
            Config.load_from_env()
        take_profit_pct = Config.DEFAULT_TAKE_PROFIT_PCT

    # For long positions (BUY signals), take profit is above current price
    # For short positions (SELL signals), take profit is below current price
    if "BUY" in signal_type:
        take_profit = current_price * (1 + take_profit_pct / 100)
    elif "SELL" in signal_type:
        take_profit = current_price * (1 - take_profit_pct / 100)
    else:  # HOLD
        take_profit = current_price * (1 + take_profit_pct / 100)

    return take_profit


def calculate_position_size(
    capital: float = None,
    risk_per_trade_pct: float = 2.0,
    current_price: float = None,
    stop_loss: float = None,
) -> float:
    """
    Calculate position size based on risk management.

    Args:
        capital: Available capital (default: from config)
        risk_per_trade_pct: Risk per trade as percentage of capital
        current_price: Current market price
        stop_loss: Stop loss price

    Returns:
        Position size in currency
    """
    if capital is None:
        if not Config.is_loaded():
            Config.load_from_env()
        capital = Config.DEFAULT_POSITION_SIZE

    # Simple position sizing: use configured position size
    # More sophisticated: calculate based on risk per trade
    if current_price and stop_loss:
        # Risk amount
        risk_amount = capital * (risk_per_trade_pct / 100)

        # Price risk per unit
        price_risk = abs(current_price - stop_loss)

        if price_risk > 0:
            # Position size = Risk Amount / Price Risk
            position_size = risk_amount / price_risk
            # But cap at available capital
            position_size = min(position_size * current_price, capital)
        else:
            position_size = capital
    else:
        position_size = capital

    return position_size


def calculate_risk_reward_ratio(
    current_price: float,
    stop_loss: float,
    take_profit: float,
) -> float:
    """
    Calculate risk/reward ratio.

    Args:
        current_price: Current market price
        stop_loss: Stop loss price
        take_profit: Take profit price

    Returns:
        Risk/reward ratio
    """
    risk = abs(current_price - stop_loss)
    reward = abs(take_profit - current_price)

    if risk == 0:
        return 0.0

    return reward / risk


def generate_risk_parameters(
    signal: Dict,
    stop_loss_pct: float = None,
    take_profit_pct: float = None,
    capital: float = None,
) -> Dict:
    """
    Generate complete risk management parameters for a signal.

    Args:
        signal: Trading signal dictionary
        stop_loss_pct: Stop loss percentage (optional)
        take_profit_pct: Take profit percentage (optional)
        capital: Available capital (optional)

    Returns:
        Dictionary with risk parameters
    """
    current_price = signal["current_price"]
    signal_type = signal["signal_type"]

    # Calculate stop loss and take profit
    stop_loss = calculate_stop_loss(current_price, signal_type, stop_loss_pct)
    take_profit = calculate_take_profit(current_price, signal_type, take_profit_pct)

    # Calculate position size
    position_size = calculate_position_size(capital, 2.0, current_price, stop_loss)

    # Calculate risk/reward ratio
    risk_reward = calculate_risk_reward_ratio(current_price, stop_loss, take_profit)

    # Calculate percentages
    stop_loss_pct_calc = ((stop_loss - current_price) / current_price) * 100
    take_profit_pct_calc = ((take_profit - current_price) / current_price) * 100

    risk_params = {
        "stop_loss": round(stop_loss, 2),
        "take_profit": round(take_profit, 2),
        "position_size": round(position_size, 2),
        "stop_loss_pct": round(stop_loss_pct_calc, 2),
        "take_profit_pct": round(take_profit_pct_calc, 2),
        "risk_reward_ratio": round(risk_reward, 2),
    }

    return risk_params
