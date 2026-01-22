"""
Main CLI entry point for jeera_trader.
"""

import argparse
import sys
from typing import List, Optional

from jeera_trader.config import Config, ConfigError
from jeera_trader.database import schema
from jeera_trader.logger import get_logger, log_error, log_section, log_success

logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="jeera-trader",
        description="Machine learning-based predictive system for jeera futures trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Database management commands
    db_parser = subparsers.add_parser("db", help="Database management")
    db_group = db_parser.add_mutually_exclusive_group(required=True)
    db_group.add_argument("--init", action="store_true", help="Initialize database")
    db_group.add_argument(
        "--stats", action="store_true", help="Show database statistics"
    )
    db_group.add_argument(
        "--drop", action="store_true", help="Drop all tables (use with caution!)"
    )

    # Data collection commands
    collect_parser = subparsers.add_parser("collect", help="Collect data from sources")
    collect_parser.add_argument(
        "--source",
        choices=["ncdex", "weather", "all"],
        required=True,
        help="Data source to collect from",
    )
    collect_parser.add_argument(
        "--start-date",
        required=True,
        help="Start date (YYYY-MM-DD)",
    )
    collect_parser.add_argument(
        "--end-date",
        required=True,
        help="End date (YYYY-MM-DD)",
    )

    # Feature engineering commands
    features_parser = subparsers.add_parser(
        "features", help="Generate features for ML"
    )
    features_parser.add_argument(
        "--start-date",
        required=True,
        help="Start date (YYYY-MM-DD)",
    )
    features_parser.add_argument(
        "--end-date",
        required=True,
        help="End date (YYYY-MM-DD)",
    )

    # Model training commands
    train_parser = subparsers.add_parser("train", help="Train ML models")
    train_parser.add_argument(
        "--model",
        choices=["rf", "xgb", "all"],
        default="all",
        help="Model type to train (rf=Random Forest, xgb=XGBoost)",
    )
    train_parser.add_argument(
        "--tune",
        action="store_true",
        help="Perform hyperparameter tuning",
    )
    train_parser.add_argument(
        "--start-date",
        help="Start date for training data (YYYY-MM-DD)",
    )
    train_parser.add_argument(
        "--end-date",
        help="End date for training data (YYYY-MM-DD)",
    )

    # Prediction commands
    predict_parser = subparsers.add_parser("predict", help="Make predictions")
    predict_parser.add_argument(
        "--model",
        help="Model ID to use (default: active model)",
    )
    predict_parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days ahead to predict",
    )
    predict_parser.add_argument(
        "--date",
        help="Date to predict from (default: latest data)",
    )

    # Trading signal commands
    signal_parser = subparsers.add_parser("signal", help="Generate trading signals")
    signal_parser.add_argument(
        "--model",
        help="Model ID to use (default: active model)",
    )
    signal_parser.add_argument(
        "--date",
        help="Date to generate signal for (default: today)",
    )

    # Backtesting commands
    backtest_parser = subparsers.add_parser("backtest", help="Backtest trading strategy")
    backtest_parser.add_argument(
        "--start-date",
        required=True,
        help="Start date for backtest (YYYY-MM-DD)",
    )
    backtest_parser.add_argument(
        "--end-date",
        required=True,
        help="End date for backtest (YYYY-MM-DD)",
    )
    backtest_parser.add_argument(
        "--model",
        required=True,
        help="Model ID to use for backtest",
    )
    backtest_parser.add_argument(
        "--initial-capital",
        type=float,
        default=100000,
        help="Initial capital in INR (default: 100000)",
    )

    # Daily update command
    update_parser = subparsers.add_parser("update", help="Run daily update routine")

    # Configuration command
    config_parser = subparsers.add_parser("config", help="Show configuration")

    return parser


def handle_db_command(args) -> int:
    """Handle database management commands."""
    try:
        Config.load_from_env()

        if args.init:
            log_section("Initializing Database")
            schema.create_tables(Config.DATABASE_PATH)
            log_success(f"Database initialized at: {Config.DATABASE_PATH}")
            return 0

        elif args.stats:
            log_section("Database Statistics")
            table_info = schema.get_table_info(Config.DATABASE_PATH)

            if not table_info:
                print("No tables found in database")
                return 0

            print(f"\nDatabase: {Config.DATABASE_PATH}\n")
            print(f"{'Table':<25} {'Row Count':>15}")
            print("-" * 42)

            total_rows = 0
            for table_name, count in sorted(table_info.items()):
                print(f"{table_name:<25} {count:>15,}")
                total_rows += count

            print("-" * 42)
            print(f"{'TOTAL':<25} {total_rows:>15,}\n")
            return 0

        elif args.drop:
            log_section("Dropping All Tables")
            response = input(
                "Are you sure you want to drop all tables? This cannot be undone. (yes/no): "
            )
            if response.lower() == "yes":
                schema.drop_tables(Config.DATABASE_PATH)
                log_success("All tables dropped")
                return 0
            else:
                print("Operation cancelled")
                return 1

    except ConfigError as e:
        log_error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        log_error(f"Database operation failed: {e}")
        logger.exception(e)
        return 1


def handle_config_command(args) -> int:
    """Handle configuration command."""
    try:
        Config.load_from_env()
        print(Config.get_summary())
        return 0
    except ConfigError as e:
        log_error(f"Configuration error: {e}")
        return 1


def handle_collect_command(args) -> int:
    """Handle data collection commands."""
    try:
        from jeera_trader.commands.collect import run_collect

        return run_collect(args)
    except ImportError:
        log_error("Data collection module not yet implemented")
        return 1
    except Exception as e:
        log_error(f"Data collection failed: {e}")
        logger.exception(e)
        return 1


def handle_features_command(args) -> int:
    """Handle feature engineering commands."""
    try:
        from jeera_trader.commands.features import run_features

        return run_features(args)
    except ImportError:
        log_error("Feature engineering module not yet implemented")
        return 1
    except Exception as e:
        log_error(f"Feature engineering failed: {e}")
        logger.exception(e)
        return 1


def handle_train_command(args) -> int:
    """Handle model training commands."""
    try:
        from jeera_trader.commands.train import run_train

        return run_train(args)
    except ImportError:
        log_error("Model training module not yet implemented")
        return 1
    except Exception as e:
        log_error(f"Model training failed: {e}")
        logger.exception(e)
        return 1


def handle_predict_command(args) -> int:
    """Handle prediction commands."""
    try:
        from jeera_trader.commands.predict import run_predict

        return run_predict(args)
    except ImportError:
        log_error("Prediction module not yet implemented")
        return 1
    except Exception as e:
        log_error(f"Prediction failed: {e}")
        logger.exception(e)
        return 1


def handle_signal_command(args) -> int:
    """Handle trading signal commands."""
    try:
        from jeera_trader.commands.signal import run_signal

        return run_signal(args)
    except ImportError:
        log_error("Trading signal module not yet implemented")
        return 1
    except Exception as e:
        log_error(f"Signal generation failed: {e}")
        logger.exception(e)
        return 1


def handle_backtest_command(args) -> int:
    """Handle backtesting commands."""
    try:
        from jeera_trader.commands.backtest import run_backtest

        return run_backtest(args)
    except ImportError:
        log_error("Backtesting module not yet implemented")
        return 1
    except Exception as e:
        log_error(f"Backtesting failed: {e}")
        logger.exception(e)
        return 1


def handle_update_command(args) -> int:
    """Handle daily update commands."""
    try:
        from jeera_trader.commands.update import run_update

        return run_update(args)
    except ImportError:
        log_error("Update module not yet implemented")
        return 1
    except Exception as e:
        log_error(f"Daily update failed: {e}")
        logger.exception(e)
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main CLI entry point.

    Args:
        argv: Command line arguments (for testing)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0

    # Dispatch to appropriate handler
    handlers = {
        "db": handle_db_command,
        "config": handle_config_command,
        "collect": handle_collect_command,
        "features": handle_features_command,
        "train": handle_train_command,
        "predict": handle_predict_command,
        "signal": handle_signal_command,
        "backtest": handle_backtest_command,
        "update": handle_update_command,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        log_error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
