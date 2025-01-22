import os
from typing import List, Dict
from openai import OpenAI
from src.core.llm import LLMInterface
import logging

class OpenAILLM(LLMInterface):
     """Class to handle interactions with the OpenAI API."""
     def __init__(self, model_name:str=None, api_key:str=None, base_url:str=None):
           """
           Initialise OpenAILLM class.

           Args:
             model_name (str): Model name to use from openai.
             api_key (str): api key to connect with openai
             base_url (str): Base url for llm endpoint.
           """
           if not api_key:
                api_key = os.environ["LLM_PROVIDER_API_KEY"]
           if base_url:
                self.client = OpenAI(base_url=base_url, api_key = api_key)
           else:
                self.client = OpenAI(api_key=api_key)
           self.model_name = model_name
           logging.info("OpenAI Client Initiated")
     def generate_response(self, messages: List[Dict[str, str]], system_prompt: str=None) -> str:
        """Generate a response from the OpenAI API."""
        if system_prompt:
             messages = [{"role": "system", "content": system_prompt}] + messages
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )
        return completion.choices[0].message.content