import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.ticker import FuncFormatter
import pandas as pd

from plots.utils import (
    calculate_sharpe_ratio,
    calculate_all_tickers_sharpe_ratios,
    bootstrap_standard_error,
)


def get_stats(
    portfolios: dict,
    fixed_strategy: str,
    sector: str,
    cash: pd.Series = pd.Series(),
    ticker: str = None,
):
    """Get statistics for a given ticker."""
    if ticker:
        ticker_evolutions = {
            strategy: portfolios[strategy][ticker].tolist() for strategy in portfolios
        }
    else:
        ticker_evolutions = {
            strategy: portfolios[strategy].tolist() for strategy in portfolios
        }

    means_and_stds = {
        strategy: (np.mean(values), np.std(values))
        for strategy, values in ticker_evolutions.items()
    }

    if not cash.any():
        betas = {
            strategy: np.cov(values, ticker_evolutions[fixed_strategy])[0][1]
            / np.var(ticker_evolutions[fixed_strategy])
            for strategy, values in ticker_evolutions.items()
        }
    else:
        betas = None

    sharpe_ratios = {
        strategy: calculate_sharpe_ratio(values)
        for strategy, values in ticker_evolutions.items()
    }

    if not cash.any():
        portfolio_diffs = {
            strategy: [
                (x - y) / y for x, y in zip(values, ticker_evolutions[fixed_strategy])
            ]
            for strategy, values in ticker_evolutions.items()
        }
    else:
        if ticker:
            cash = cash[ticker]
        if not ticker:
            cash = cash[sector]

        portfolio_diffs = {
            strategy: [(x - cash) / cash for x in values]
            for strategy, values in ticker_evolutions.items()
        }

    return ticker_evolutions, means_and_stds, betas, sharpe_ratios, portfolio_diffs


def plot_comparison_tickers(
    portfolios: dict,
    dates: list,
    market_data: pd.DataFrame,
    output_file: str,
    fixed_strategy: str,
    backtest_init_date: str = None,
    cash: pd.Series = pd.Series(),
):
    """Plot comparison grids for portfolios across sectors."""

    for sector in market_data.sector.unique():
        relevant_tickers = market_data.loc[
            (market_data.sector == sector)
            & (market_data.symbol.isin(portfolios[fixed_strategy].columns))
        ].symbol.values.tolist()

        nrows, ncols = 5, 2
        fig, axes = plt.subplots(
            nrows, ncols, figsize=(14, 19), sharex=True, sharey=True
        )
        flat_axes = axes.flatten()

        for i, ticker in enumerate(relevant_tickers):
            (
                ticker_evolutions,
                means_and_stds,
                betas,
                sharpe_ratios,
                portfolio_diffs,
            ) = get_stats(portfolios, fixed_strategy, sector, cash, ticker)

            for j, strategy in enumerate(ticker_evolutions.keys()):
                if strategy == "Buy & Hold":
                    continue

                label = f"{strategy}\nmean: {means_and_stds[strategy][0]:.3f}, std: {means_and_stds[strategy][1]:.3f}"

                if betas:
                    label += f"\nbeta: {betas[strategy]:.2f}"
                label += f" sharpe: {sharpe_ratios[strategy]:.2f}"

                portfolio_diffs_bootstrap_se = bootstrap_standard_error(
                    portfolio_diffs[strategy]
                )
                upper_bound = (
                    np.array(portfolio_diffs[strategy]) + portfolio_diffs_bootstrap_se
                )
                lower_bound = (
                    np.array(portfolio_diffs[strategy]) - portfolio_diffs_bootstrap_se
                )

                flat_axes[i].plot(dates, portfolio_diffs[strategy], label=label)
                flat_axes[i].fill_between(
                    dates,
                    lower_bound,
                    upper_bound,
                    color="grey",
                    alpha=0.2,
                    label="Bootstrap Standard Error"
                    if j == len(ticker_evolutions) - 2 or cash.any()
                    else None,
                )
                flat_axes[i].axhline(y=0, color="black", linestyle="--", linewidth=1)
                flat_axes[i].set_title(f"{ticker}")

                if backtest_init_date:
                    flat_axes[i].axvline(x=backtest_init_date, color="grey", linestyle="-", linewidth=2, label="Backtest start")
                if i // ncols == nrows - 1:  # Check if it's in the last row
                    flat_axes[i].set_xlabel("Time Periods")
                ylabel = (
                    "Relative diff to Buy & Hold"
                    if not cash.any()
                    else "Relative diff to Cash"
                )
                flat_axes[i].set_ylabel(ylabel)
                flat_axes[i].legend(fontsize=6)
                flat_axes[i].yaxis.set_major_formatter(
                    FuncFormatter(lambda y, _: "{:.2%}".format(y))
                )

        sparse_dates = dates[:: int(len(dates) / 10)]
        for ax in flat_axes:
            ax.set_xticks(sparse_dates)
            ax.tick_params(axis="x", rotation=45)

        plt.tight_layout()
        plt.savefig(f"{output_file}_{sector}", dpi=400)


def plot_comparison_sectors(
    portfolios: dict,
    dates: list,
    market_data: pd.DataFrame,
    output_file: str,
    fixed_strategy: str,
    backtest_init_date: str = None,
    cash: pd.Series = pd.Series(),
):
    """Plot comparison grids for portfolios across sectors."""

    for sector in market_data.sector.unique():
        relevant_tickers = market_data.loc[
            (market_data.sector == sector)
            & (market_data.symbol.isin(portfolios[fixed_strategy].columns))
        ].symbol.values.tolist()

        fig, ax = plt.subplots(sharex=True, sharey=True)

        sector_portfolios = {}
        for portfolio in portfolios:
            sector_portfolios[portfolio] = portfolios[portfolio][relevant_tickers].sum(
                axis=1
            )

        (
            ticker_evolutions,
            means_and_stds,
            betas,
            sharpe_ratios,
            portfolio_diffs,
        ) = get_stats(
            sector_portfolios,
            fixed_strategy,
            sector,
            cash=cash if cash.any() else pd.Series(),
        )

        for j, strategy in enumerate(ticker_evolutions.keys()):
            if strategy == "Buy & Hold":
                continue

            label = f"{strategy}\nmean: {means_and_stds[strategy][0]:.3f}, std: {means_and_stds[strategy][1]:.3f}"

            if betas:
                label += f"\nbeta: {betas[strategy]:.2f}"
            label += f" sharpe: {sharpe_ratios[strategy]:.2f}"

            portfolio_diffs_bootstrap_se = bootstrap_standard_error(
                portfolio_diffs[strategy]
            )
            upper_bound = (
                np.array(portfolio_diffs[strategy]) + portfolio_diffs_bootstrap_se
            )
            lower_bound = (
                np.array(portfolio_diffs[strategy]) - portfolio_diffs_bootstrap_se
            )

            ax.plot(dates, portfolio_diffs[strategy], label=label)
            ax.fill_between(
                dates,
                lower_bound,
                upper_bound,
                color="grey",
                alpha=0.2,
                label="Bootstrap Standard Error"
                if j == len(ticker_evolutions) - 2 or cash.any()
                else None,
            )
            ax.axhline(y=0, color="black", linestyle="--", linewidth=1)

            ax.set_xlabel("Time Periods")
            ylabel = (
                "Relative diff to Buy & Hold"
                if not cash.any()
                else "Relative diff to Cash"
            )
            ax.set_ylabel(ylabel)
            ax.legend(fontsize=6)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: "{:.2%}".format(y)))
            if backtest_init_date:
                ax.axvline(x=backtest_init_date, color="grey", linestyle="-", linewidth=2, label="Backtest start")
        sparse_dates = dates[:: int(len(dates) / 10)]
        ax.set_xticks(sparse_dates)
        ax.tick_params(axis="x", rotation=45)
        # set title for the whole figure with sector name
        plt.suptitle(f"Comparison between strategies for {sector} sector")

        plt.tight_layout()
        plt.savefig(f"{output_file}_{sector}.png", dpi=400)


def plot_sharpe_ratios_histogram(portolios):
    sharpe_ratios = {}
    for strategy in portolios:
        portolios[strategy] = {
            ticker: portolios[strategy][ticker].tolist()
            for ticker in portolios[strategy].columns
        }
        sharpe_ratios[strategy] = calculate_all_tickers_sharpe_ratios(
            portolios[strategy]
        )

    # Calculate global min and max for the x-axis range
    all_sharpe_ratios = []
    for strategy in sharpe_ratios:
        all_sharpe_ratios += list(sharpe_ratios[strategy].values())
    global_min = min(all_sharpe_ratios)
    global_max = max(all_sharpe_ratios)

    n_rows = 1
    n_cols = len(sharpe_ratios)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5), sharex=True, sharey=True)
    plt.suptitle("Distribution of Sharpe Ratios Across Strategies")

    # Portfolio Sharpe Ratios
    for i, strategy in enumerate(sharpe_ratios):
        sns.histplot(
            sharpe_ratios[strategy].values(), ax=axes[i], palette="Blues", bins=10
        )
        axes[i].set_title(strategy)
        axes[i].set_xlim([global_min, global_max])
        axes[i].set_xlabel("Sharpe Ratio")
        axes[i].set_ylabel("Frequency")
        axes[i].legend().set_visible(False)

    plt.tight_layout()
    plt.subplots_adjust(top=0.85)  # Adjust suptitle to fit


def plot_sharpe_ratios_kde(portfolios):
    # Calculate sharpe ratios for each strategy
    sharpe_ratios = {}
    for strategy in portfolios:
        portfolios[strategy] = {
            ticker: portfolios[strategy][ticker].tolist()
            for ticker in portfolios[strategy].columns
        }
        sharpe_ratios[strategy] = calculate_all_tickers_sharpe_ratios(
            portfolios[strategy]
        )

    # Calculate global min and max for the x-axis range
    all_sharpe_ratios = []
    for strategy in sharpe_ratios:
        all_sharpe_ratios += list(sharpe_ratios[strategy].values())
    global_min = min(all_sharpe_ratios)
    global_max = max(all_sharpe_ratios)

    n_rows = 1
    n_cols = len(sharpe_ratios)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5), sharex=True, sharey=True)
    plt.suptitle("KDE distribution of Sharpe Ratios Across Strategies")

    # Portfolio Sharpe Ratios
    for i, strategy in enumerate(sharpe_ratios):
        sns.kdeplot(list(sharpe_ratios[strategy].values()), ax=axes[i], label=strategy)
        axes[i].set_xlim([global_min, global_max])
        axes[i].set_xlabel("Sharpe Ratio")
        axes[i].set_ylabel("Density")
        axes[i].legend(loc="upper right")

    plt.tight_layout()
    plt.subplots_adjust(top=0.85)  # Adjust suptitle to fit


def plot_sharpe_ratios_histogram_overlap(portfolios):
    # Calculate sharpe ratios for each strategy
    sharpe_ratios = {}
    for strategy in portfolios:
        portfolios[strategy] = {
            ticker: portfolios[strategy][ticker].tolist()
            for ticker in portfolios[strategy].columns
        }
        sharpe_ratios[strategy] = calculate_all_tickers_sharpe_ratios(
            portfolios[strategy]
        )

    # Calculate global min and max for the x-axis range
    all_sharpe_ratios = []
    for strategy in sharpe_ratios:
        all_sharpe_ratios += list(sharpe_ratios[strategy].values())
    global_min = min(all_sharpe_ratios)
    global_max = max(all_sharpe_ratios)

    fig, ax = plt.subplots(figsize=(10, 6))
    plt.suptitle("Distribution of Sharpe Ratios Across Strategies")

    # Define a palette dictionary for better control over colors
    palette_dict = {"Longs": "Blues", "Buy N Hold": "Greens", "Shorts": "Reds"}

    # Plot histograms for each strategy
    for strategy in sharpe_ratios:
        sns.histplot(
            list(sharpe_ratios[strategy].values()),
            ax=ax,
            palette=palette_dict.get(strategy, "Blues"),
            bins=10,
            label=strategy,
            alpha=0.5,
        )

    ax.set_xlim([global_min, global_max])
    ax.set_xlabel("Sharpe Ratio")
    ax.legend(loc="upper right")

    plt.tight_layout()
    plt.subplots_adjust(top=0.90)  # Adjust suptitle to fit
