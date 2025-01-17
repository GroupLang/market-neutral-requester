import argparse
import sys
from datetime import datetime

from loguru import logger

from src import pipes
import pandas as pd
import yfinance as yf

_TOP_N = 10

def _get_prices(tickers: list, date: str):
    try:
        logger.info(f"Getting prices for {len(tickers)} tickers on {date}")
        prices = {}
        for ticker in tickers:
            ticker_obj = yf.Ticker(ticker.symbol)
            hist = ticker_obj.history(start=date, end=(pd.Timestamp(date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
            price = hist['Close'].iloc[0] if not hist.empty else None
            prices[ticker.symbol] = price
        return prices
    except Exception as e:
        logger.error(f"Error getting prices: {str(e)}")
        raise e

def sector_market_pipeline(market: str, date: str, sector: str, instance_id: str = None):
    try:
        logger.info("Started sector market pipeline")

        market = pipes.load_market(market)

        tickers = pipes.market_assets(market=market, sector=sector, top=_TOP_N)

        sector_news = pipes.sector_news_retrival(sector, date)

        decisions = pipes.get_model_predictions(sector_news, tickers, instance_id=instance_id)

        prices = _get_prices(tickers, date)
        
        for decision in decisions:
            decision["price"] = prices[decision["ticker"]]
            decision["test_type"] = "forward"
            decision["date"] = date


        logger.info("Finished sector market pipeline")

        return decisions

    except Exception as e:
        raise e


if __name__ == "__main__":
    try:
        market = "sp500"
        date = datetime.today().strftime("%Y-%m-%d")
        
        # Get unique sectors from SP500 data
        sectors = [
            "Information Technology",
            "Communication Services", 
            "Consumer Discretionary",
            "Consumer Staples",
            "Energy",
            "Financials",
            "Health Care",
            "Industrials",
            "Materials",
            "Real Estate",
            "Utilities"
        ]

        # Iterate through each sector
        for sector in sectors:
            logger.info(f"Processing sector: {sector}")
            sector_market_pipeline(market, date, sector)
            
    except Exception as e:
        logger.error(f"The pipeline raised the following error: {e}")
        sys.exit(1)
