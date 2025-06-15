from langchain_openai import ChatOpenAI
from app.infrastructure.config.config import settings

class OpenAIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_NAME,
            temperature=settings.OPENAI_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY,
        )
