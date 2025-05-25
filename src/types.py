from enum import StrEnum
from typing import Literal


class Environment(StrEnum):
    debug = "debug"
    deployed = "deployed"


class LLMProvider(StrEnum):
    openrouter = "OpenRouter"


LLMModel = Literal[
    "anthropic/claude-3.7-sonnet",
    "anthropic/claude-3.5-haiku",
]
