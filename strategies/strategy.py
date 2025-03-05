# %%
import os
import pandas as pd
import requests
from abc import ABC, abstractmethod
from loguru import logger
import numpy as np
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


API_KEY = os.getenv("API_KEY")
HEADERS = {
    "x-api-key": API_KEY,
    "content-type": "application/json",
    "accept": "application/json",
}
DATA_PATH = os.path.join(os.getcwd(), "data")
DECISIONS_FILE = "gpt_raw_decisions_o1.csv"

class Strategy(ABC):
    def __init__(self, save_data: bool = False, test_type: str = "forward"):
        self.data = None
        self.save_data = save_data
        self.test_type = test_type

    def load_data(self, init_date: str, end_date: str):
        if os.path.exists(DATA_PATH):
            data = pd.read_csv(os.path.join(DATA_PATH, DECISIONS_FILE)).drop_duplicates(
                subset=["date", "ticker"], keep="last"
            )
            data = data.loc[(data["date"] >= init_date) & (data["date"] <= end_date)]
            self.prices = data.pivot(index="date", columns="ticker", values="price")
            self.decisions = data.pivot(
                index="date", columns="ticker", values="decision"
            )

            dates_wo_data = [
                date.strftime("%Y-%m-%d")
                for date in pd.date_range(init_date, end_date)
                if date.strftime("%Y-%m-%d") not in self.prices.index
                # exclude weekends
                and date.weekday() < 5
            ]
        else:
            logger.error("No data found. Please upload data first.")
            raise FileNotFoundError

        cal = calendar()
        holidays = cal.holidays(start=init_date, end=end_date).strftime("%Y-%m-%d").to_list()
        dates_wo_data = [
            date
            for date in dates_wo_data
            if date not in holidays
        ]
        
        self.prices = self.prices.ffill()
        self.decisions = self.decisions.loc[self.prices.index]
        
        return self.prices, self.decisions

    def _process_data(self, signals, test_type, old_data):
        dates, decisions, assets = zip(
            *[
                (signal["date"], trade["decision"], trade["asset"])
                for signal in signals
                for decision in signal["decisions"]
                for trade in decision["trades"]
            ]
        )
        
        # Initialize Alpaca API client
        api_key = os.environ.get("ALPACA_API_KEY")
        api_secret = os.environ.get("ALPACA_SECRET_KEY")
        
        if not api_key or not api_secret:
            raise ValueError("Alpaca API credentials not found in environment variables")
            
        client = StockHistoricalDataClient(api_key, api_secret)
        
        prices = []
        for date, ticker in zip(dates, assets):
            try:
                # Convert date string to timestamps for Alpaca API
                start_date = pd.Timestamp(date)
                end_date = start_date + pd.Timedelta(days=1)
                
                # Create request parameters
                request_params = StockBarsRequest(
                    symbol_or_symbols=ticker,
                    timeframe=TimeFrame.Day,
                    start=start_date,
                    end=end_date
                )
                
                # Get data from Alpaca
                bars = client.get_stock_bars(request_params)
                
                if ticker in bars.data and bars.data[ticker]:
                    # Get the first price for the symbol (should be the only one if requesting a single day)
                    # Using open price to match yfinance behavior
                    price = bars.data[ticker][0].open
                    prices.append(price)
                else:
                    logger.warning(f"No price data found for {ticker} on {date}")
                    prices.append(np.nan)
                    
            except Exception as e:
                logger.warning(f"Could not download data for {ticker} on {date}: {str(e)}")
                prices.append(np.nan)

        data = pd.DataFrame(
            {"date": dates, "ticker": assets, "decision": decisions, "price": prices}
        ).drop_duplicates(subset=["date", "ticker"], keep="last")

        if self.save_data:
            data = pd.concat([old_data, data.assign(test_type=test_type)])
            self._save_csv(data, test_type)

        prices = data.pivot(index="date", columns="ticker", values="price")
        decisions = data.pivot(index="date", columns="ticker", values="decision")
        return prices, decisions

    def _save_csv(self, data: pd.DataFrame, test_type: str):
        data = data.assign(test_type=test_type)
        data.to_csv(os.path.join(DATA_PATH, DECISIONS_FILE), index=False)

    def save_returns(self, portfolio_values_per_asset, test_type, output_file):
        portfolio_returns = portfolio_values_per_asset.pct_change().iloc[1:]
        portfolio_returns = portfolio_returns.assign(test_type=test_type)
        portfolio_returns.to_csv(os.path.join(DATA_PATH, output_file))
        return portfolio_returns

    @abstractmethod
    def compute_performance(self):
        pass
