import os
import asyncio
import argparse
import logging
from dotenv import load_dotenv
from src.core.debugger import CodeDebugger
from src.core.llm_factory import LLMFactory
from datetime import datetime
import re
from configs.default_config import DEFAULT_CONFIG


# Load environment variables from .env file
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Debug Python code using an LLM.")
    parser.add_argument("--code_dir", type=str, default=DEFAULT_CONFIG["code_dir"], help="The directory where the Python project files are located.")
    parser.add_argument("--max_attempts", type=int, default=DEFAULT_CONFIG["max_attempts"], help="The maximum number of debugging attempts to make.")
    parser.add_argument("--files_to_debug", type=str, nargs="*", help="Specific Python files to debug (space-separated). If not provided, all .py files in the code_dir will be debugged.")
    parser.add_argument("--enable_internet_search", type=bool, default=DEFAULT_CONFIG["enable_internet_search"], help="Enable internet search during debugging, 'True' or 'False' (defaults to True)")
    parser.add_argument("--num_search_urls", type=int, default=DEFAULT_CONFIG["num_search_urls"], help="Number of URLs to fetch during web search (defaults to 5)")
    parser.add_argument("--internet_search_threshold", type=int, default=DEFAULT_CONFIG["internet_search_threshold"], help="Threshold for consecutive same error to trigger web search (defaults to 5)")
    parser.add_argument("--llm_type", type=str, default=DEFAULT_CONFIG["llm_type"], choices=["openai", "huggingface", "gemini"], help="The type of LLM to use. Choices: 'openai', 'huggingface', 'gemini'")
    parser.add_argument("--openai_model", type=str, default=DEFAULT_CONFIG["openai_model"], help="OpenAI model name (if using openai as llm)")
    parser.add_argument("--openai_base_url", type=str, default=DEFAULT_CONFIG["openai_base_url"], help="Base url for openai custom endpoint (if using openai as llm)")
    parser.add_argument("--huggingface_model", type=str, default=DEFAULT_CONFIG["huggingface_model"], help="HuggingFace model ID (if using huggingface as llm)")
    parser.add_argument("--huggingface_device", type=str, default=DEFAULT_CONFIG["huggingface_device"], help="Device to use for HuggingFace. 'auto','cpu' or 'cuda' ")
    parser.add_argument("--gemini_model", type=str, default=DEFAULT_CONFIG["gemini_model"], help="Gemini model name (if using gemini as llm)")

    args = parser.parse_args()

    # Extract the folder name from the given path
    project_folder_name = os.path.basename(args.code_dir)
    
    # Construct debug directory path
    debug_dir = os.path.join(args.code_dir, f"debug_{project_folder_name}")

    # Create the debug directory if it does not exist
    os.makedirs(debug_dir, exist_ok=True)
   
    # Construct the log file path within the project directory
    log_file_name = os.path.join(debug_dir, f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Configure Logging with the new log file path
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file_name),
                        logging.StreamHandler()
                    ])


    llm_config = {}
    if args.llm_type == "openai":
        llm_config = {"model_name": args.openai_model, "base_url": args.openai_base_url}
    elif args.llm_type == "huggingface":
        llm_config = {"model_id": args.huggingface_model, "device":args.huggingface_device}
    elif args.llm_type == "gemini":
         llm_config = {"model_name":args.gemini_model}

    try:
      llm_instance = LLMFactory.create_llm(args.llm_type, llm_config)
    except ValueError as e:
         logging.error(e)
         exit(1)

    debugger = CodeDebugger(
         code_dir=args.code_dir,
         max_attempts=args.max_attempts,
         files_to_debug=args.files_to_debug,
         enable_internet_search = args.enable_internet_search,
         num_search_urls = args.num_search_urls,
         internet_search_threshold = args.internet_search_threshold,
         llm = llm_instance
    )
    asyncio.run(debugger.debug())


if __name__ == "__main__":
    main()