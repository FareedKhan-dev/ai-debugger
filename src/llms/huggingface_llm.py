import os
from typing import List, Dict
import torch
from transformers import pipeline
from src.core.llm import LLMInterface
import logging

class HuggingFaceLLM(LLMInterface):
     """Class to handle interactions with HuggingFace Transformers."""
     def __init__(self, model_id:str, device:str = "auto"):
          """
           Initialise HuggingFaceLLM class.

           Args:
             model_id (str): Model id from huggingface.
             device (str): Device to use 'auto', 'cpu' or 'cuda'.
          """
          self.model_id = model_id
          self.device = device
          self.pipe = pipeline(
              "text-generation",
              model=self.model_id,
              torch_dtype=torch.bfloat16,
              device_map=self.device,
          )
          logging.info("HuggingFace Client Initiated")

     def generate_response(self, messages: List[Dict[str, str]], system_prompt:str = None) -> str:
           """Generate a response from HuggingFace Transformers."""
           if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
           outputs = self.pipe(
              messages
           )
           return outputs[0]["generated_text"][-1]['content']