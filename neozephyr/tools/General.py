import random
import time
from typing import Any
from openai import (
    OpenAI,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    BadRequestError,
    PermissionDeniedError,
    InternalServerError,
    APIError,
)

def openai_request_with_retry(
    client: OpenAI,
    *,
    max_retries: int = 6,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    **kwargs: Any,
):
    """
    Execute client.chat.completions.parse() with automatic retries.

    Parameters
    ----------
    client : OpenAI
        OpenAI client.

    max_retries : int
        Maximum number of retries for transient errors.

    initial_delay : float
        Initial exponential backoff delay.

    max_delay : float
        Maximum backoff delay.

    **kwargs
        All keyword arguments are forwarded to
        client.chat.completions.parse().

    Returns
    -------
    ParsedChatCompletion
    """

    attempt = 0

    while True:
        try:
            return client.chat.completions.parse(**kwargs)

        # ---------- Permanent errors ----------

        except AuthenticationError as e:
            raise RuntimeError(
                "Authentication failed. Check your OpenAI API key."
            ) from e

        except PermissionDeniedError as e:
            raise RuntimeError(
                "Permission denied. Check your model access."
            ) from e

        except BadRequestError as e:
            raise RuntimeError(
                f"Invalid request: {e}"
            ) from e

        # ---------- Retryable errors ----------

        except (
            RateLimitError,
            APIConnectionError,
            APITimeoutError,
            InternalServerError,
            APIError,
        ) as e:

            attempt += 1

            if attempt > max_retries:
                raise RuntimeError(
                    f"OpenAI request failed after {max_retries} retries."
                ) from e

            # Exponential backoff with jitter
            delay = min(
                initial_delay * (2 ** (attempt - 1)),
                max_delay,
            )

            delay += random.uniform(0, delay * 0.25)

            print(
                f"[OpenAI] {type(e).__name__} "
                f"(attempt {attempt}/{max_retries}) "
                f"Retrying in {delay:.2f}s..."
            )

            time.sleep(delay)