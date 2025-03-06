from strategies.exponential_strategy import ExponentialStrategy
from strategies.exponential_strategy_shorts import ExponentialStrategyShorts
from strategies.market_neutral import MarketNeutralStrategy
from strategies.buy_and_hold import BuyAndHoldStrategy
import pandas as pd
import os
from datetime import datetime
from plots.plots import plot_comparison_tickers
from plots.plots import plot_comparison_sectors

cash = 1000
end_date = datetime.today().strftime('%Y-%m-%d')
end_date = pd.Timestamp(end_date) - pd.Timedelta(days=2)
end_date = end_date.strftime('%Y-%m-%d')

market_data = pd.read_csv("data/markets/sp500.csv")

exp_strat_shorts = ExponentialStrategyShorts(cash, "2023-03-03", end_date, save_data=True, test_type="backtest")
exp_strat = ExponentialStrategy(cash, "2023-03-03", end_date, save_data=True, test_type="backtest")
market_neutral = MarketNeutralStrategy(cash, "2023-03-03", end_date, market_data, save_data=True, test_type="backtest")
buy_and_hold = BuyAndHoldStrategy(cash, "2023-03-03", end_date, save_data=True, test_type="backtest")

# %%
# Fix IndexingError by using a different approach to update test_type field
# For exp_strat
forward_data = exp_strat.portfolio_total[exp_strat.portfolio_total.index >= "2023-09-06"]
forward_data["test_type"] = "forward"
exp_strat.portfolio_total.update(forward_data)

# For exp_strat_shorts
forward_data = exp_strat_shorts.portfolio_total[exp_strat_shorts.portfolio_total.index >= "2023-09-06"]
forward_data["test_type"] = "forward"
exp_strat_shorts.portfolio_total.update(forward_data)

# For market_neutral
forward_data = market_neutral.portfolio_total[market_neutral.portfolio_total.index >= "2023-09-06"]
forward_data["test_type"] = "forward"
market_neutral.portfolio_total.update(forward_data)

# For buy_and_hold
forward_data = buy_and_hold.portfolio_total[buy_and_hold.portfolio_total.index >= "2023-09-06"]
forward_data["test_type"] = "forward"
buy_and_hold.portfolio_total.update(forward_data)


dates = market_neutral.portfolio_total.index
c_dict = {
    "Exponential": exp_strat.portfolio_value_per_asset.loc[dates],
    "Exponential Shorts": exp_strat_shorts.portfolio_value_per_asset.loc[dates],
    "Buy & Hold": buy_and_hold.portfolio_value_per_asset.loc[dates],
}
plot_comparison_tickers(
    c_dict,
    exp_strat.portfolio_total.loc[dates].index,
    market_data=market_data,
    output_file="plots/exponential_strategies/assets/fw_test_assets",
    fixed_strategy="Buy & Hold",
    backtest_init_date="2023-09-06",
)
plot_comparison_sectors(
    c_dict,
    exp_strat.portfolio_total.loc[dates].index,
    market_data=market_data,
    output_file="plots/exponential_strategies/sector/fw_test_sectors",
    fixed_strategy="Buy & Hold",
    backtest_init_date="2023-09-06",
)
c_dict = {
    "Market Neutral": market_neutral.portfolio_value_per_asset.loc[dates],
}
plot_comparison_tickers(
    c_dict,
    exp_strat.portfolio_total.loc[dates].index,
    market_data=market_data,
    output_file="plots/market_neutral/assets/fw_test_assets_market_neutral",
    fixed_strategy="Market Neutral",
    backtest_init_date="2023-09-06",
    cash=market_neutral.initial_cash,
)
# Apply sector map to initial cash
# apply sector map to initial cash
market_neutral_sector_map = market_data.set_index("symbol")["sector"]
market_neutral_sector_map = market_neutral_sector_map[market_neutral_sector_map.index.isin(market_neutral.initial_cash.index)]
cash = market_neutral.initial_cash.groupby(market_neutral_sector_map).sum()
# Agg all cash for all sectors
#cash = pd.Series(cash.sum(), index=["All"])

plot_comparison_sectors(
    c_dict,
    exp_strat.portfolio_total.loc[dates].index,
    market_data=market_data,
    output_file="plots/market_neutral/sector/fw_test_sectors_market_neutral",
    fixed_strategy="Market Neutral",
    backtest_init_date="2023-09-06",
    cash=cash,
)
