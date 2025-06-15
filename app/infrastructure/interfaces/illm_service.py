from abc import ABC, abstractmethod

class ILLMService(ABC):
    """
    Interface para serviços de LLM.
    """
    @abstractmethod
    def get_llm(self):
        pass
