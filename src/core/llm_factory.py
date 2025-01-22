from typing import Dict, Any
from src.core.llm import LLMInterface
from src.llms.openai_llm import OpenAILLM
from src.llms.huggingface_llm import HuggingFaceLLM
from src.llms.gemini_llm import GeminiLLM

class LLMFactory:
     """Factory class to create instances of the appropriate LLM."""
     @staticmethod
     def create_llm(llm_type:str, config:Dict[str,Any]=None) -> LLMInterface:
         """
         Create instances of the appropriate LLM.

         Args:
          llm_type (str): LLM to use
          config (dict): Configuration of the LLM.
         Returns:
          LLMInterface: Instance of the LLM.
         """
         if llm_type == "openai":
             if not config:
                  raise ValueError("Model name is required for openai.")
             return OpenAILLM(**config)
         elif llm_type == "huggingface":
             if not config:
                 raise ValueError("Model id is required for huggingface.")
             return HuggingFaceLLM(**config)
         elif llm_type == "gemini":
             return GeminiLLM(**config)
         else:
           raise ValueError("Invalid LLM Type.")