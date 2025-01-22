from abc import ABC, abstractmethod
from typing import List, Dict

class LLMInterface(ABC):
    """Abstract base class for LLM interactions."""

    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]], system_prompt: str = None) -> str:
        """Abstract method to generate a response from the LLM."""
        pass