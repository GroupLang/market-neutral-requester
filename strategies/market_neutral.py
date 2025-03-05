from strategies.strategy import Strategy
import pandas as pd
from loguru import logger

class MarketNeutralStrategy(Strategy):
    def __init__(self, bank: int, init_date: str, end_date: str, market_data: pd.DataFrame, save_data: bool = False, test_type: str = "forward"):
        super().__init__(save_data, test_type)
        self.bank = bank
        self.init_date = init_date
        self.end_date = end_date
        self.load_data(init_date, end_date)
        self.market_data = market_data.loc[market_data['symbol'].isin(self.prices.columns)]
        self.market_caps = market_data.set_index('symbol')['market_cap']
        self.total_market_cap = self.market_caps.sum()
        self.dates = self.prices.index
        self.compute_performance()
        returns = self.save_returns(self.portfolio_value_per_asset, test_type, "market_neutral_returns.csv")
        return returns

    def compute_performance(self):
        """Compute the performance of the strategy."""
        self._initialize_performance_data()
        self._simulate_trading()
        self._compute_portfolio_values()

    def _initialize_performance_data(self):
        """Initialize cash and position dataframes based on market cap weights."""
        num_dates = len(self.prices)
        
        self.cash = pd.DataFrame(
            {ticker: [self.bank * (self.market_caps[ticker] / self.total_market_cap)] * num_dates for ticker in self.prices.columns},
            index=self.prices.index,
            dtype=float
        )
        self.initial_cash = self.cash.iloc[0].copy()

        self.position = pd.DataFrame(
            {ticker: [0] * num_dates for ticker in self.prices.columns},
            index=self.prices.index,
            dtype=float
        )

    def _simulate_trading(self):
        """Loop through decisions and prices to simulate trading."""
        for date, decisions_row in self.decisions.iterrows():
            if date != self.prices.index[0]:
                prev_date = self.position.index[self.position.index.get_loc(date) - 1]
                position_value = self.position.loc[prev_date] * self.prices.loc[date]
                total_value_per_asset = position_value + self.cash.loc[prev_date]
                self.cash.loc[date] = total_value_per_asset

            longs = decisions_row[decisions_row == "buy"].index.tolist()
            shorts = decisions_row[decisions_row == "sell"].index.tolist()
            holds = decisions_row[decisions_row == "hold"].index.tolist()

            # Ensure market neutrality by rebalancing the longs and shorts if needed
            min_len = min(len(longs), len(shorts))
            longs = longs[:min_len]
            shorts = shorts[:min_len]

            for ticker in longs:
                self._handle_decision(date, ticker, "buy")
            for ticker in shorts:
                self._handle_decision(date, ticker, "sell")
            for ticker in holds:
                self._handle_decision(date, ticker, "hold")

    def _handle_decision(self, date, ticker, decision):
        """Update cash and position data based on trading decision."""
        price = self.prices.loc[date, ticker]
        available_cash = self.cash.loc[date, ticker]
        
        if decision == "buy":
            amount_to_invest = available_cash / 2  # Investing half of the available cash
            self.cash.loc[date, ticker] -= amount_to_invest
            self.position.loc[date, ticker] += amount_to_invest / price  # Buying stocks worth amount_to_invest
            
        elif decision == "sell":
            amount_to_sell = self.position.loc[date, ticker] / 2  # Selling half of the stocks
            self.cash.loc[date, ticker] += amount_to_sell * price  # Adding the selling amount to cash
            self.position.loc[date, ticker] -= amount_to_sell  # Updating the position after selling
            
        elif decision == "hold":
            # During hold, simply maintain the current cash and position levels.
            pass


    def _compute_portfolio_values(self):
        """Compute total value of the portfolio for each asset and total portfolio."""
        # Compute value from the positions (number of shares * their respective prices)
        position_value = self.position * self.prices
        # Adding cash to the position value to get the total value per asset
        total_value_per_asset = position_value + self.cash
        # Compute the total value of the entire portfolio by summing over assets
        self.portfolio_total = total_value_per_asset.sum(axis=1)
        # Save the individual asset values as an attribute
        self.portfolio_value_per_asset = total_value_per_asset
        # Save the performance (may or may not be necessary depending on the subsequent use case)
        self.performance = self.portfolio_total.tolist()
