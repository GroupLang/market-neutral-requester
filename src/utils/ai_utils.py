import boto3
from loguru import logger
import os
import json

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
