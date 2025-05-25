from src.types import LLMModel
from src.types import LLMProvider


model_to_provider: dict[LLMModel, LLMProvider] = {
    "anthropic/claude-3.7-sonnet": LLMProvider.openrouter,
    "anthropic/claude-3.5-haiku": LLMProvider.openrouter,
}
