"""
Trading signal generation for jeera futures.
"""

from typing import Dict, Optional

from jeera_trader.logger import get_logger
from jeera_trader.utils.constants import SIGNAL_THRESHOLDS, SignalType

logger = get_logger(__name__)


def generate_signal(
    current_price: float,
    predicted_price: float,
    confidence: Optional[float] = None,
) -> Dict:
    """
    Generate trading signal based on price prediction.

    Args:
        current_price: Current market price
        predicted_price: Predicted future price
        confidence: Prediction confidence (optional)

    Returns:
        Dictionary with signal information
    """
    # Calculate predicted return
    predicted_return = ((predicted_price - current_price) / current_price) * 100

    # Determine signal type based on thresholds
    signal_type = determine_signal_type(predicted_return)

    # Generate reasoning
    reasoning = generate_reasoning(signal_type, current_price, predicted_price, predicted_return)

    signal = {
        "signal_type": signal_type.value,
        "current_price": round(current_price, 2),
        "predicted_price": round(predicted_price, 2),
        "predicted_return": round(predicted_return, 2),
        "confidence": round(confidence, 2) if confidence else None,
        "reasoning": reasoning,
    }

    return signal


def determine_signal_type(predicted_return: float) -> SignalType:
    """
    Determine signal type based on predicted return.

    Args:
        predicted_return: Predicted return percentage

    Returns:
        SignalType enum
    """
    if predicted_return >= SIGNAL_THRESHOLDS[SignalType.STRONG_BUY]:
        return SignalType.STRONG_BUY
    elif predicted_return >= SIGNAL_THRESHOLDS[SignalType.BUY]:
        return SignalType.BUY
    elif predicted_return <= SIGNAL_THRESHOLDS[SignalType.STRONG_SELL]:
        return SignalType.STRONG_SELL
    elif predicted_return <= SIGNAL_THRESHOLDS[SignalType.SELL]:
        return SignalType.SELL
    else:
        return SignalType.HOLD


def generate_reasoning(
    signal_type: SignalType,
    current_price: float,
    predicted_price: float,
    predicted_return: float,
) -> str:
    """
    Generate human-readable reasoning for the signal.

    Args:
        signal_type: Signal type
        current_price: Current price
        predicted_price: Predicted price
        predicted_return: Predicted return percentage

    Returns:
        Reasoning string
    """
    direction = "increase" if predicted_return > 0 else "decrease"
    abs_return = abs(predicted_return)

    reasoning_map = {
        SignalType.STRONG_BUY: (
            f"Strong bullish signal. Model predicts {abs_return:.1f}% price {direction} "
            f"from ₹{current_price:,.0f} to ₹{predicted_price:,.0f}. "
            f"Consider aggressive long position."
        ),
        SignalType.BUY: (
            f"Bullish signal. Model predicts {abs_return:.1f}% price {direction} "
            f"from ₹{current_price:,.0f} to ₹{predicted_price:,.0f}. "
            f"Consider moderate long position."
        ),
        SignalType.HOLD: (
            f"Neutral signal. Model predicts {abs_return:.1f}% price change "
            f"from ₹{current_price:,.0f} to ₹{predicted_price:,.0f}. "
            f"Hold existing positions or stay on sidelines."
        ),
        SignalType.SELL: (
            f"Bearish signal. Model predicts {abs_return:.1f}% price {direction} "
            f"from ₹{current_price:,.0f} to ₹{predicted_price:,.0f}. "
            f"Consider moderate short position or exit longs."
        ),
        SignalType.STRONG_SELL: (
            f"Strong bearish signal. Model predicts {abs_return:.1f}% price {direction} "
            f"from ₹{current_price:,.0f} to ₹{predicted_price:,.0f}. "
            f"Consider aggressive short position or exit all longs."
        ),
    }

    return reasoning_map.get(signal_type, "No signal generated")


def format_signal_output(signal: Dict, risk_params: Optional[Dict] = None) -> str:
    """
    Format signal for display.

    Args:
        signal: Signal dictionary
        risk_params: Risk management parameters (optional)

    Returns:
        Formatted string
    """
    output = []

    output.append("\n" + "=" * 70)
    output.append("JEERA FUTURES TRADING SIGNAL")
    output.append("=" * 70)

    # Signal type with color/emphasis
    signal_type = signal["signal_type"]
    output.append(f"\nSignal: {signal_type}")

    # Prices
    output.append(f"\nCurrent Price:   ₹{signal['current_price']:,.2f}")
    output.append(f"Predicted Price: ₹{signal['predicted_price']:,.2f}")
    output.append(f"Expected Return: {signal['predicted_return']:+.2f}%")

    if signal.get("confidence"):
        output.append(f"Confidence:      {signal['confidence']:.1f}%")

    # Risk parameters
    if risk_params:
        output.append("\n" + "-" * 70)
        output.append("RISK MANAGEMENT")
        output.append("-" * 70)
        output.append(f"Stop Loss:       ₹{risk_params['stop_loss']:,.2f} ({risk_params['stop_loss_pct']:+.1f}%)")
        output.append(f"Take Profit:     ₹{risk_params['take_profit']:,.2f} ({risk_params['take_profit_pct']:+.1f}%)")
        output.append(f"Position Size:   ₹{risk_params['position_size']:,.0f}")

        if 'risk_reward_ratio' in risk_params:
            output.append(f"Risk/Reward:     1:{risk_params['risk_reward_ratio']:.2f}")

    # Reasoning
    output.append("\n" + "-" * 70)
    output.append("ANALYSIS")
    output.append("-" * 70)
    output.append(signal["reasoning"])

    output.append("\n" + "=" * 70)

    return "\n".join(output)
