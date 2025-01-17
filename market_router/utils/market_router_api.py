import os
import random

import requests
import requests.status_codes as status
from loguru import logger

from market_router import config

_LOGIN_VARIABLES = ["username", "password"]


def deposit(deposit_data: dict, api_key: str):
    try:
        headers = {"X-API-KEY": api_key}

        response = requests.post(
            f"{config['api_url']}/v1/payment/deposit",
            headers=headers,
            json=deposit_data,
        )
        response.raise_for_status()

        response_data = response.json()
        if response.status_code == status.codes.ok:
            logger.info(
                f"Please complete the payment process in the following link: {response_data['url']}"
            )
        return response_data

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e.response.text}")
        raise e
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def submit_instance(instance: dict, api_key: str) -> dict:
    headers = {"X-API-KEY": api_key}

    url = f"{config['api_url']}/v1/instances"

    try:
        response = requests.post(url, json=instance, headers=headers)
        response.raise_for_status()

        response_data = response.json()
        logger.info(f"Instance submitted successfully")
        return response_data

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e.response.text}")
        raise e
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def register_user(user_data: dict):
    try:
        response = requests.post(f"{config['api_url']}/v1/auth/register", json=user_data)
        response.raise_for_status()

        response_data = response.json()
        if response.status_code == status.codes.created:
            logger.info(f"User {user_data['username']} created successfully")

        return response_data

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e.response.text}")
        raise e
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def login_user(user_data: dict):
    try:
        login_data = {k: user_data[k] for k in _LOGIN_VARIABLES}

        response = requests.post(f"{config['api_url']}/v1/auth/login", data=login_data)
        response.raise_for_status()

        response_data = response.json()

        if response.status_code == status.codes.ok:
            logger.info(f"User {user_data['username']} logged in successfully")

        return response_data

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e.response.text}")
        raise e
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def create_api_key(login_info):
    try:
        headers = {"Authorization": f"Bearer {login_info['access_token']}"}

        response = requests.post(
            f"{config['api_url']}/v1/auth/create-api-key?name="
            f"neutral-portfolio_requester_{random.randint(1, 10000)}",
            headers=headers,
        )
        response.raise_for_status()

        response_data = response.json()
        if response.status_code == status.codes.created:
            logger.info("API key created successfully")

        return response_data

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e.response.text}")
        raise e
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def get_proposal(instance_id: str, api_key: str):
    headers = {"X-API-KEY": api_key}

    try:
        response = requests.get(
            f"{config['api_url']}/v1/proposals/by-instance/{instance_id}", headers=headers
        )
        response.raise_for_status()

        response_data = response.json()
        if response.status_code == status.codes.ok:
            logger.info(f"Proposal retrieved successfully")

        return response_data

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e.response.text}")
        raise e
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def get_predictions(baseline_prompt: str, api_key: str, instance_id: str):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"role": "user", "content": baseline_prompt}],
        "model": "gpt-4o-mini"
    }
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=data,
            headers=headers,
        )
        response.raise_for_status()
        response_data = response.json()
        if response.status_code == status.codes.ok:
            logger.info("Predictions retrieved successfully")

        return response_data

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e.response.text}")
        raise e
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def send_reward(gen_reward_data: dict, instance_id: str, api_key: str):
    headers = {"X-API-KEY": api_key}
    try:
        response = requests.put(
            f"{config['api_url']}/v1/instances/{instance_id}/report-reward",
            json=gen_reward_data,
            headers=headers,
        )
        response.raise_for_status()
        response_data = response.json()
        if response.status_code == status.codes.created:
            logger.info(f"Predictions retrieved successfully")

        return response_data

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e.response.text}")
        raise e
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e
