import argparse
import sys
import os
from datetime import datetime, timedelta

from loguru import logger
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

from src import pipes
import pandas as pd

# Load environment variables
load_dotenv()

_TOP_N = 10

def _get_prices(tickers: list, date: str):
    try:
        logger.info(f"Getting prices for {len(tickers)} tickers on {date}")
        
        # Initialize Alpaca API client
        api_key = os.environ.get("ALPACA_API_KEY")
        api_secret = os.environ.get("ALPACA_SECRET_KEY")
        
        if not api_key or not api_secret:
            raise ValueError("Alpaca API credentials not found in environment variables")
            
        client = StockHistoricalDataClient(api_key, api_secret)
        
        # Convert date string to timestamps for Alpaca API
        start_date = pd.Timestamp(date)
        end_date = start_date + pd.Timedelta(days=1)
        
        # Get symbols from ticker objects
        symbols = [ticker.symbol for ticker in tickers]
        
        # Request stock bars for all symbols at once
        request_params = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date
        )
        
        # Get historical data and extract closing prices
        prices = {}
        try:
            bars = client.get_stock_bars(request_params)
            bars_dict = bars.data
            
            for ticker in tickers:
                symbol = ticker.symbol
                if symbol in bars_dict and bars_dict[symbol]:
                    # Get the first bar for the symbol (should be the only one if requesting a single day)
                    price = bars_dict[symbol][0].close
                    prices[symbol] = price
                else:
                    logger.warning(f"No price data found for {symbol} on {date}")
                    prices[symbol] = None
                    
        except Exception as api_err:
            logger.error(f"Alpaca API error: {str(api_err)}")
            # Fall back to individually querying each symbol
            for ticker in tickers:
                try:
                    single_request = StockBarsRequest(
                        symbol_or_symbols=ticker.symbol,
                        timeframe=TimeFrame.Day,
                        start=start_date,
                        end=end_date
                    )
                    bars = client.get_stock_bars(single_request)
                    bars_dict = bars.data
                    
                    if ticker.symbol in bars_dict and bars_dict[ticker.symbol]:
                        price = bars_dict[ticker.symbol][0].close
                        prices[ticker.symbol] = price
                    else:
                        prices[ticker.symbol] = None
                except Exception:
                    logger.warning(f"Could not get price for {ticker.symbol}")
                    prices[ticker.symbol] = None
        
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
