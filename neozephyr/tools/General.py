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
from pydantic import ValidationError

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
        
        except ValidationError:
            debug_kwargs = kwargs.copy()
            debug_kwargs.pop("response_format", None)

            raw = client.chat.completions.create(**debug_kwargs)

            print("=" * 80)
            print(raw.choices[0].message.content)
            print("=" * 80)

            raise

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


def toolforce(*, attempts: int = 5, tool_name: str = "", **kwargs):
    """
    Calls openai_request_with_retry until the expected tool is called.

    Retries up to `attempts` times. After each failed attempt, appends a
    reminder to the conversation instructing the model to call the required
    tool.
    """

    base_messages = list(kwargs["messages"])

    for attempt in range(attempts):
        messages = base_messages.copy()

        if attempt > 0:
            reminder = (
                f"NOTE: YOU HAVE TO CALL THE TOOL '{tool_name}'."
                if tool_name
                else "NOTE: YOU HAVE TO CALL AT LEAST ONE TOOL."
            )

            messages.append(
                {
                    "role": "developer",
                    "content": reminder,
                }
            )
        kwargs["messages"] = messages

        response = openai_request_with_retry(
            **kwargs,
        )

        reply = response.choices[0].message

        if reply.tool_calls:
            if not tool_name:
                return response

            for call in reply.tool_calls:
                if call.function.name == tool_name:
                    return response

        print(
            f"[ToolForce] Attempt {attempt + 1}/{attempts}: "
            f"Expected tool '{tool_name or 'any'}' was not called."
        )

    raise RuntimeError(
        f"Your model couldn't call the required tool "
        f"'{tool_name or 'any'}' after {attempts} attempts. "
        "Please choose a model with better tool-calling support."
    )