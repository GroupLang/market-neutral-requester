from strategies.strategy import Strategy
import pandas as pd
from loguru import logger


class BuyAndHoldStrategy(Strategy):

    def __init__(self, bank: int, init_date: str, end_date: str, save_data: bool = False, test_type: str = "forward"):
        super().__init__(save_data, test_type)
        self.bank = bank
        self.init_date = init_date
        self.end_date = end_date
        self.load_data(init_date, end_date)
        self.dates = self.prices.index
        self.compute_performance()
        returns = self.save_returns(self.portfolio_value_per_asset, test_type, "buy_and_hold.csv")
        return returns

    def compute_performance(self):
        """Compute the performance of the strategy."""
        self._initialize_performance_data()
        self._simulate_trading()
        self._compute_portfolio_values()

    def _initialize_performance_data(self):
        """Initialize cash and position dataframes."""
        num_assets = len(self.prices.columns)
        num_dates = len(self.prices)

        self.cash = pd.DataFrame(
            {ticker: [self.bank / num_assets] * num_dates for ticker in self.prices.columns},
            index=self.prices.index,
            dtype=float
        )

        self.position = pd.DataFrame(
            {ticker: [0] * num_dates for ticker in self.prices.columns},
            index=self.prices.index,
            dtype=float
        )

    def _simulate_trading(self):
        """Simulate the buy and hold strategy."""
        # Buy the asset at the beginning of the time frame
        first_date = self.prices.index[0]
        for ticker in self.prices.columns:
            price = self.prices.loc[first_date, ticker]
            self._buy_asset(first_date, ticker, price, 0, self.prices.columns.get_loc(ticker))
        
        # Hold the asset for the rest of the time frame
        for date_idx, date in enumerate(self.prices.index[1:], 1):
            for ticker_idx, ticker in enumerate(self.prices.columns):
                self._hold_asset(date_idx, ticker_idx)

    def _buy_asset(self, date, ticker, price, date_idx, ticker_idx):
        """Update cash and position data for buying asset."""
        amount_to_invest = self.cash.iloc[date_idx, ticker_idx]
        self.cash.loc[date, ticker] = 0
        self.position.loc[date, ticker] = amount_to_invest / price

    def _hold_asset(self, date_idx, ticker_idx):
        """Update cash and position data for holding asset."""
        self.position.iloc[date_idx, ticker_idx] = self.position.iloc[date_idx - 1, ticker_idx]
        self.cash.iloc[date_idx, ticker_idx] = self.cash.iloc[date_idx - 1, ticker_idx]

    def _compute_portfolio_values(self):
        """Compute total value of the portfolio for each asset and total portfolio."""
        self.portfolio_value_per_asset = self.cash + self.position * self.prices
        self.portfolio_value_per_asset = self.portfolio_value_per_asset.ffill()
        self.portfolio_total = self.portfolio_value_per_asset.sum(axis=1)
        self.performance = self.portfolio_total.tolist()