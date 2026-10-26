"""llm.py - the one place this project talks to the local AI model, with safety limits."""

import os

import httpx
import ollama
from pydantic import BaseModel, ValidationError

MODEL = os.environ.get("INCIDENT_MODEL", "llama3.2")
TIMEOUT = int(os.environ.get("INCIDENT_TIMEOUT", "180"))  # seconds per answer
CONTEXT = 8192  # tokens the model can hold at once (prompt + answer)


class AIError(Exception):
    """The model was too slow, unreachable, or gave an answer we can't use."""


def ask(prompt: str, shape: type[BaseModel]) -> BaseModel:
    """Ask the model to fill in `shape`; one retry if the answer is broken."""
    client = ollama.Client(timeout=TIMEOUT)  # reads OLLAMA_HOST if set (used in Docker)
    for attempt in range(2):
        try:
            response = client.chat(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                format=shape.model_json_schema(),
                options={"temperature": 0 if attempt == 0 else 0.5, "num_ctx": CONTEXT, "num_predict": 2000},
            )
        except httpx.TimeoutException:
            raise AIError(f"{MODEL} took longer than {TIMEOUT} seconds") from None
        except (ConnectionError, httpx.ConnectError, ollama.ResponseError) as e:
            raise AIError(f"can't reach the model ({e}); is Ollama running?") from None
        if response.done_reason == "length":  # cut off mid-answer: try again
            continue
        try:
            return shape.model_validate_json(response.message.content)
        except ValidationError:
            continue
    raise AIError(f"{MODEL} couldn't give a usable answer, even on a second try")
