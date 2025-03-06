from strategies.strategy import Strategy
import pandas as pd
from loguru import logger


class ExponentialStrategy(Strategy):
    BUY_FRACTION = 0.5  # Fraction of cash to invest when buying

    def __init__(
        self,
        bank: int,
        init_date: str,
        end_date: str,
        save_data: bool = False,
        test_type: str = "forward",
    ):
        super().__init__(save_data, test_type)
        self.bank = bank
        self.init_date = init_date
        self.end_date = end_date
        self.load_data(init_date, end_date)
        self.dates = self.prices.index
        self.compute_performance()
        returns = self.save_returns(
            self.portfolio_value_per_asset, test_type, "data/exponential_returns.csv"
        )

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
            {
                ticker: [self.bank / num_assets] * num_dates
                for ticker in self.prices.columns
            },
            index=self.prices.index,
            dtype=float,
        )

        self.position = pd.DataFrame(
            {ticker: [0] * num_dates for ticker in self.prices.columns},
            index=self.prices.index,
            dtype=float,
        )

    def _simulate_trading(self):
        """Loop through decisions and prices to simulate trading."""
        for date, decisions_row in self.decisions.iterrows():
            for ticker, decision in decisions_row.items():
                self._handle_decision(date, ticker, decision)

    def _handle_decision(self, date, ticker, decision):
        """Update cash and position data based on trading decision."""
        price = self.prices.loc[date, ticker]
        date_idx = self.position.index.get_loc(date)
        ticker_idx = self.position.columns.get_loc(ticker)

        if decision == "buy" and date_idx > 0:
            self._buy_asset(date, ticker, price, date_idx, ticker_idx)
        elif decision == "sell" and self.position.iloc[date_idx - 1, ticker_idx] > 0:
            self._sell_asset(date_idx, ticker_idx, price)
        elif decision == "hold" and date_idx > 0:
            self._hold_asset(date_idx, ticker_idx)

    def _buy_asset(self, date, ticker, price, date_idx, ticker_idx):
        """Update cash and position data for buying asset."""
        amount_to_invest = self.cash.iloc[date_idx - 1, ticker_idx] * self.BUY_FRACTION
        self.cash.loc[date, ticker] = (
            self.cash.iloc[date_idx - 1, ticker_idx] - amount_to_invest
        )
        self.position.loc[date, ticker] = (
            self.position.iloc[date_idx - 1, ticker_idx] + amount_to_invest / price
        )

    def _sell_asset(self, date_idx, ticker_idx, price):
        """Update cash and position data for selling asset."""
        self.cash.iloc[date_idx, ticker_idx] = self.cash.iloc[
            date_idx - 1, ticker_idx
        ] + (self.position.iloc[date_idx - 1, ticker_idx] * price)
        self.position.iloc[date_idx, ticker_idx] = 0

    def _hold_asset(self, date_idx, ticker_idx):
        """Update cash and position data for holding asset."""
        self.position.iloc[date_idx, ticker_idx] = self.position.iloc[
            date_idx - 1, ticker_idx
        ]
        self.cash.iloc[date_idx, ticker_idx] = self.cash.iloc[date_idx - 1, ticker_idx]

    def _compute_portfolio_values(self):
        """Compute total value of the portfolio for each asset and total portfolio."""
        self.portfolio_value_per_asset = self.cash + self.position * self.prices
        self.portfolio_value_per_asset = self.portfolio_value_per_asset.ffill()
        self.portfolio_total = self.portfolio_value_per_asset.sum(axis=1)
        self.performance = self.portfolio_total.tolist()
