DEFAULT_CONFIG = {
    "code_dir": None,  # Default directory to debug
    "max_attempts": 10,         # Maximum number of debugging attempts
    "files_to_debug": None,      # Specific files to debug (None for all .py files)
    "enable_internet_search": True,  # Enable/disable internet searching
    "num_search_urls": 5,        # Number of URLs to fetch during web search
    "internet_search_threshold": 5,  # Threshold for consecutive same errors before web search
    "llm_type": "openai",      # Default LLM type ("openai", "huggingface", "gemini")
    "openai_model": "meta-llama/Meta-Llama-3.1-405B-Instruct",  # Default OpenAI model name
    "openai_base_url": None,  # Base URL for custom OpenAI endpoint
    "huggingface_model": "meta-llama/Llama-3.2-3B-Instruct",  # Default Hugging Face model ID
    "huggingface_device": "auto",  # Device for Hugging Face (auto, cpu, cuda)
    "gemini_model": "gemini-1.5-flash",  # Default Gemini model name
}