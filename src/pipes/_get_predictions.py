import json
import os

from loguru import logger

from market_router import utils
from src import baseline_system_prompt_tpl


def get_model_predictions(news: str, tickers: list, instance_id: str = None) -> list:
    if not instance_id:
        instance_id = os.getenv("INSTANCE_ID")

    api_key = os.getenv("MARKET_ROUTER_KEY")

    decisions = []

    for ticker in tickers:
        baseline_prompt = _format_baseline_prompt(news, ticker.name)

        predictions = utils.get_predictions(baseline_prompt, api_key, instance_id)

        decision = _get_decision(predictions)

        decisions.append({"ticker": ticker.symbol, "decision": decision})


    return decisions


def _format_baseline_prompt(news: str, ticker: str):
    return baseline_system_prompt_tpl.replace("{news}", news).replace("{name}", ticker)


def _get_decision(response: str) -> str:
    try:
        content = response["choices"][0]["message"]["content"].lower()
        action = content.split("action")[1]

        return "buy" if "buy" in action else "sell" if "sell" in action else "hold"

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"Error decoding response: {e}")
        return None
