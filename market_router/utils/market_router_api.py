import os
import random
import time

import requests
import requests.status_codes as status
from loguru import logger
import openai

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
    from src.utils.ai_utils import create_completion
    
    try:
        # Use vertex AI from ai_utils.py
        # For vertex, we don't need a system message, so we'll pass an empty string
        system_msg = ""
        user_msg = baseline_prompt
        
        # Call the vertex AI completion function
        content = create_completion(system_msg, user_msg)
        
        # Format response to match expected structure similar to OpenAI's response
        formatted_response = {
            "id": instance_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "gemini-2.5-flash",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": -1,  # Vertex doesn't provide token counts in the same way
                "completion_tokens": -1,
                "total_tokens": -1
            }
        }
        
        logger.info("Predictions retrieved successfully using Google Vertex AI")
        return formatted_response

    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def get_predictions_gpt4(baseline_prompt: str, api_key: str, instance_id: str):
    """
    Get predictions using OpenAI's GPT-4 API instead of AWS Bedrock.
    
    This function maintains the same interface and return format as get_predictions
    but uses the OpenAI API client instead of Bedrock.
    
    Args:
        baseline_prompt (str): The prompt to send to the model
        api_key (str): API key for the market router API (not used for OpenAI calls)
        instance_id (str): Instance ID for tracking
        
    Returns:
        dict: Formatted response matching the structure of the original function
        
    Raises:
        Exception: If an error occurs during the API call
    """
    try:
        # Check if OpenAI API key is available
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Call the OpenAI API with GPT-4
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # Using GPT-4 Turbo for similar capabilities to Claude 3.5
            messages=[
                {"role": "user", "content": baseline_prompt}
            ],
            max_tokens=config.get("max_tokens", 16384),
            temperature=config.get("temperature", 0.7)
        )
        
        # Format response to match the expected structure from the original function
        formatted_response = {
            "id": instance_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "gpt-4o",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.choices[0].message.content
                    },
                    "finish_reason": response.choices[0].finish_reason
                }
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        logger.info("Predictions retrieved successfully using OpenAI GPT-4")
        return formatted_response

    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise e
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
