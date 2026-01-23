"""Main module for the AI-Based Stock Investment System."""

import logging
from config import load_config
from buildmodel import ModelBuilder
from backtest import BacktestEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main execution flow."""
    logger.info("Starting AI-Based Stock Investment System (ASX Version)")

    # 1. Load configuration
    config = load_config()

    # 2. Initialize Model Builder
    builder = ModelBuilder(config)

    # 3. Initialize Backtest Engine
    engine = BacktestEngine(config, builder)

    # 4. Process each ticker
    for ticker in config.target_stock_codes:
        try:
            logger.info(f"Processing ticker: {ticker}")

            # Load or train model
            builder.load_or_build(ticker)

            # Run backtest
            results = engine.run(ticker)

            if "error" in results:
                logger.error(f"Error in backtest for {ticker}: {results['error']}")
                continue

            logger.info(f"Backtest complete for {ticker}")
            logger.info(f"ROI: {results['roi']:.2%}")
            logger.info(f"Win Rate: {results['win_rate']:.2%}")
            logger.info(f"Total Trades: {results['total_trades']}")

        except Exception as e:
            logger.exception(f"An error occurred while processing {ticker}: {e}")


if __name__ == "__main__":
    main()
