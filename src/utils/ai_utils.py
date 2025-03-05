import boto3
from loguru import logger
import os
import json
import openai

from market_router import config
from market_router.expections import CreateCompletionError


def create_completion(system_msg, user_msg):
    try:
        # Initialize the Bedrock Runtime client
        bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.environ.get("AWS_REGION"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
        
        # Prepare the request for Claude in Bedrock format
        # Claude in Bedrock doesn't use system messages the same way
        # Instead, we'll prepend the system message to the user message
        combined_message = f"{system_msg}\n\n{user_msg}"
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": config["max_tokens"],
            "temperature": config.get("temperature", 0.7),
            "messages": [
                {"role": "user", "content": combined_message}
            ]
        }
        
        # Call the Bedrock Invoke API with Claude 3.5 Sonnet
        response = bedrock_runtime.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response.get("body").read())
        return response_body["content"][0]["text"]
    
    except Exception as e:
        logger.error(e)
        raise CreateCompletionError(e)
        
def create_completion_gpt4(system_msg, user_msg):
    """
    Create a completion using OpenAI's GPT-4 API instead of AWS Bedrock.
    
    This function maintains the same interface as create_completion but uses
    the OpenAI API client instead of Bedrock.
    
    Args:
        system_msg (str): The system message to guide the model's behavior
        user_msg (str): The user prompt/query to be completed
        
    Returns:
        str: The generated text from GPT-4
        
    Raises:
        CreateCompletionError: If an error occurs during the API call
    """
    try:
        # Check if API key is available
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Prepare the messages in OpenAI format
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
        
        # Call the OpenAI API with GPT-4
        response = client.chat.completions.create(
            model="gpt-4o",  # Using GPT-4 Turbo for similar capabilities to Claude 3.5
            messages=messages,
            max_tokens=config["max_tokens"],
            temperature=config.get("temperature", 0.7)
        )
        
        # Return the completion text
        return response.choices[0].message.content
    
    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise CreateCompletionError(e)
    except Exception as e:
        logger.error(f"Error in GPT-4 completion: {e}")
        raise CreateCompletionError(e)
