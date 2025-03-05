import numpy as np
import scipy.stats as stats


def bootstrap_standard_error(data, num_samples=1000):
    """Bootstrap the standard error of the mean."""
    means = [
        np.mean(np.random.choice(data, len(data), replace=True))
        for _ in range(num_samples)
    ]
    return np.std(means)


def calculate_sharpe_ratio(portfolio_values, risk_free_rate_annual=0.05):
    """Calculate the Sharpe ratio of a portfolio."""

    risk_free_rate_daily = (1 + risk_free_rate_annual) ** (1/252) - 1
    
    daily_returns = [
        (portfolio_values[i] - portfolio_values[i - 1]) / portfolio_values[i - 1]
        for i in range(1, len(portfolio_values))
    ]
    
    expected_return = np.mean(daily_returns)
    portfolio_std_dev = np.std(daily_returns)
    
    sharpe_ratio = (expected_return - risk_free_rate_daily) / portfolio_std_dev
    return sharpe_ratio


def calculate_all_tickers_sharpe_ratios(ticker_values):
    """Calculate the Sharpe ratio for each ticker."""
    return {
        ticker: calculate_sharpe_ratio(values)
        for ticker, values in ticker_values.items()
    }


def add_market_cap_weights(assets_data, market_data):
    """Add market capitalization weights to assets data."""
    market_data = market_data.loc[market_data.symbol.isin(assets_data.ticker.unique())]
    market_data["weight"] = market_data["market_cap"] / market_data["market_cap"].sum()

    assets_data = (
        assets_data.merge(
            market_data.rename(columns={"symbol": "ticker"})[["ticker", "weight"]],
            on="ticker",
            how="left",
        )
        .sort_values(["date", "ticker"], ascending=True)
        .reset_index(drop=True)
    )
    return assets_data


def sharpe_t_stat(sharpe, n):
    """Compute the t-statistic for a Sharpe ratio."""
    return sharpe * np.sqrt(n - 1)


def holm_bonferroni_p_values(portfolios, alpha=0.05):
    """Compute the p-values for the Holm-Bonferroni test."""
    sharpe_ratios = {
        strategy: [calculate_sharpe_ratio(portfolio), len(portfolio)]
        for strategy, portfolio in portfolios.items()
    }
    t_stats = {
        strategy: [sharpe_t_stat(sharpe, len_portfolio), len_portfolio]
        for strategy, (sharpe, len_portfolio) in sharpe_ratios.items()
    }
    p_values = {
        strategy: (1 - stats.t.cdf(t_stat, len_portfolio - 1))
        for strategy, (t_stat, len_portfolio) in t_stats.items()
    }

    ranked_strategies = sorted(p_values, key=p_values.get)
    m = len(ranked_strategies)

    reject_null = {}
    for i, strategy in enumerate(ranked_strategies):
        threshold = alpha / (m - i)
        reject_null[strategy] = p_values[strategy] < threshold
    return p_values, reject_null
