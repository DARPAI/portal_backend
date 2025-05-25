from src.llm_clients import OpenAIClient
from src.settings import settings
from src.types import LLMProvider


provider_to_client: dict[LLMProvider, OpenAIClient] = {
    LLMProvider.openrouter: OpenAIClient(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY),
}
