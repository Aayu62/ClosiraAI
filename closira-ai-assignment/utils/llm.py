import logging
from typing import Any, Dict, Optional
from openai import OpenAI, APIError, APIConnectionError, RateLimitError


logger = logging.getLogger(__name__)


class LLMClient:
    """OpenRouter LLM client wrapper."""

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1", model: str = "deepseek/deepseek-chat"):
        try:
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=30.0
            )
        except TypeError as e:
            if 'proxies' in str(e):
                logger.warning(f"OpenAI client init warning: {e}, retrying with basic params")
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                raise
        self.model = model
        self.max_retries = 2

    def call(self, system_prompt: str, user_message: str, temperature: float = 0.3) -> Optional[str]:
        """
        Call LLM with system and user prompts.

        Args:
            system_prompt: System instruction
            user_message: User input
            temperature: Model temperature

        Returns:
            Response text or None on failure
        """
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=temperature
                )

                content = response.choices[0].message.content
                logger.debug(f"LLM response: {content[:100]}...")
                return content

            except RateLimitError:
                retry_count += 1
                if retry_count > self.max_retries:
                    logger.error("Rate limit exceeded after retries")
                    return None
                logger.warning(f"Rate limited, retrying... (attempt {retry_count})")

            except APIConnectionError as e:
                logger.error(f"Connection error: {str(e)}")
                return None

            except APIError as e:
                logger.error(f"API error: {str(e)}")
                return None

            except Exception as e:
                logger.error(f"Unexpected error in LLM call: {str(e)}")
                return None

        return None
