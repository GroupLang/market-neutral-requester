import openai
from loguru import logger

from market_router import config
from market_router.expections import CreateCompletionError


def create_completion(system_msg, user_msg):
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=config["max_tokens"],
        )
        response = completion.choices[0].message.content
        return response
    except Exception as e:
        logger.error(e)
        raise CreateCompletionError(e)
