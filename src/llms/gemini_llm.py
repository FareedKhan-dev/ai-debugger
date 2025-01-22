import os
from typing import List, Dict
import google.generativeai as genai
from src.core.llm import LLMInterface
import logging

class GeminiLLM(LLMInterface):
      """Class to handle interactions with Google Gemini API."""
      def __init__(self, model_name:str="gemini-1.5-flash", api_key:str=None): # Update the init method
          """
           Initialise GeminiLLM class.

           Args:
             model_name (str): Model name to use from gemini.
             api_key (str): api key to connect with gemini
          """
          if not api_key:
               api_key = os.environ["GEMINI_API_KEY"]

          genai.configure(api_key=api_key)
          self.model = genai.GenerativeModel(model_name)
          logging.info("Gemini Client Initiated")

      def generate_response(self, messages: List[Dict[str, str]], system_prompt: str=None) -> str:
        """Generate a response from the Gemini API."""
        prompt = ""
        if system_prompt:
              prompt += system_prompt
        for message in messages:
              prompt += message['content']
        response = self.model.generate_content(prompt)
        return response.text