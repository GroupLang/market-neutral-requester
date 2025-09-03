import vertexai
from vertexai.preview.generative_models import GenerativeModel, GenerationConfig


from loguru import logger
import os
import openai

from market_router import config
from market_router.expections import CreateCompletionError
from dotenv import load_dotenv

load_dotenv()


def create_completion(system_msg, user_msg):
    """
    Create a completion using Google Vertex AI with Text Generation model.
    
    Args:
        system_msg (str): The system message to guide the model's behavior
        user_msg (str): The user prompt/query to be completed
        
    Returns:
        str: The generated text from Vertex AI
        
    Raises:
        CreateCompletionError: If an error occurs during the API call
    """
    try:
        # Initialize Vertex AI with project and location
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "grouplang-450317")
        location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
        
        vertexai.init(project=project_id, location=location)
        
        model = GenerativeModel("gemini-2.5-flash")
        
        # Combine system and user messages
        combined_message = f"{system_msg}\n\n{user_msg}"
        
        response = model.generate_content(combined_message)
        
        # Return the generated text
        return response.text
    
    except Exception as e:
        logger.error(f"Vertex AI error: {e}")
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
