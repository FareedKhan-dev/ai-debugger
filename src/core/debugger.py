import os
import re
import time
import asyncio
import subprocess
from typing import List, Dict, Optional, Any
import logging
from src.core.llm import LLMInterface
from src.prompts.system_prompts import SYSTEM_PROMPT
from src.prompts.query_prompts import QUERY_SYSTEM_PROMPT
from src.internet.search import internet_search
from scrapling import Fetcher
from src.core.utils import get_diff

class CodeDebugger:
    """
    A class to handle debugging of Python code using an LLM and web searches.
    """

    def __init__(self, code_dir: str, max_attempts: int, files_to_debug: Optional[List[str]],
                 enable_internet_search: bool, num_search_urls: int, internet_search_threshold: int,
                 llm:LLMInterface):
        """
        Initialize the debugger with file locations and parameters.

        Args:
            code_dir (str): The directory where the Python project files are located.
            max_attempts (int): The maximum number of debugging attempts to make.
            files_to_debug (list): A list of file names that we want to debug.
            enable_internet_search (bool): Enable/Disable web search functionality (Defaults to True)
            num_search_urls (int): Number of URLs to fetch during web search (Defaults to 5)
            internet_search_threshold (int): Threshold for consecutive same error to trigger web search (Defaults to 5)
            llm (LLMInterface): Instance of the LLM.
        """
        self.code_dir = code_dir
        self.max_attempts = max_attempts
        self.files_to_debug = files_to_debug
        self.enable_internet_search = enable_internet_search
        self.num_search_urls = num_search_urls
        self.internet_search_threshold = internet_search_threshold
        self.llm = llm
        self.attempt_count = 0
        self.constant_error_count = 0
        self.last_error_signature = ""
        if not self.files_to_debug:
            logging.info("No files passed. Loading all files")
            self.files_to_debug = self._get_all_python_files() # Load all python files from the directory if not passed.

    def _get_all_python_files(self)->List[str]:
        """
        Get all the python files from the given directory.
        """
        python_files = [f for f in os.listdir(self.code_dir) if f.endswith(".py")]
        return python_files
        

    def _run_subprocess_and_capture_output(self, code_filename: str) -> str:
        """
         Executes a Python file using subprocess, captures its output, and any errors.

         Args:
             code_filename (str): The name of the Python file to execute.

         Returns:
             str: The standard output if successful, or standard error if it fails.
        """
        try:
            result = subprocess.run(
                ["python", os.path.join(self.code_dir, code_filename)],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return e.stderr.strip()

    def _generate_directory_tree(self, start_path: str, indent: str = "") -> str:
        """
        Recursively generates a directory tree structure as a string.

        Args:
            start_path (str): The root directory path for the tree.
            indent (str): The indentation string for each level of recursion.

        Returns:
            str: A formatted string representing the directory tree structure.
        """
        tree_structure = ""
        try:
            items = os.listdir(start_path)
        except PermissionError:
            return f"{indent}[Permission Denied]\n"

        for index, item in enumerate(items):
            item_path = os.path.join(start_path, item)
            is_last_item = index == len(items) - 1
            prefix = "└── " if is_last_item else "├── "
            tree_structure += f"{indent}{prefix}{item}\n"

            if os.path.isdir(item_path):
                new_indent = indent + ("    " if is_last_item else "│   ")
                tree_structure += self._generate_directory_tree(item_path, new_indent)

        return tree_structure

    def _construct_prompt_for_llm(self, internet_content: str = "") -> str:
        """
        Creates a prompt string for the language model with file structure, code, and errors.

        Args:
            internet_content (str, optional): Additional content from web searches. Defaults to "".

        Returns:
            str: A formatted prompt string to be used with the language model.
        """
        directory_tree = self._generate_directory_tree(self.code_dir)

        file_structure_prompt = f"""
        The file structure of the project is as follows:
        {directory_tree}
        """

        all_code = ""
        for code_filename in self.files_to_debug:
            with open(os.path.join(self.code_dir, code_filename), "r") as file:
                all_code += "# " + code_filename + "\n"
                code = file.read()
                all_code += code + "\n"
                all_code += "_________________\n\n"

        all_errors = ""
        for code_filename in self.files_to_debug:
            error_message = self._run_subprocess_and_capture_output(code_filename=code_filename)
            if "Traceback" in error_message:
                all_errors += f"# {code_filename}\n{error_message}\n_________________\n\n"
            else:
                all_errors += f"# {code_filename} has no error.\n_________________\n\n"

        if internet_content:
            final_prompt_with_error = f"""
            ### INTERNET INFO
            {internet_content}

            _______________________________________________________

            {file_structure_prompt}
            {all_code}
            error:
            {all_errors}
            """
        else:
            final_prompt_with_error = f"""
            {file_structure_prompt}
            {all_code}
            error:
            {all_errors}
            """
        return final_prompt_with_error

    def _extract_code_from_llm_response(self, llm_response: str) -> Dict[str, str]:
        """
        Extracts code from the language model's response.

        Args:
            llm_response(str): The raw text response from the language model.

        Returns:
            dict: A dictionary with filenames as keys and code as values.
        """
        pattern = r"#\s(\S+)\n```python\n(.*?)\n```"
        matches = re.findall(pattern, llm_response, re.DOTALL)
        return {filename: code.strip() for filename, code in matches}

    def _update_code_files(self, code_changes: Dict[str, str]) -> None:
        """
        Updates code files with the corrected code provided by the language model.

        Args:
            code_changes (dict): A dictionary of filename and code pairs.
        """
        for filename, code in code_changes.items():
            with open(os.path.join(self.code_dir, filename), "w") as file:
                file.write(code)

    def _check_for_errors(self) -> bool:
        """
        Checks if there are any errors left in the code files.

        Returns:
            bool: True if there is any error, otherwise False.
        """
        for code_filename in self.files_to_debug:
            error_message = self._run_subprocess_and_capture_output(code_filename=code_filename)
            if "Traceback" in error_message:
                return True  # Error found
        return False

    def _generate_search_query_for_google(self) -> str:
        """
        Generates a search query based on the code and error messages.

        Returns:
           str: A single-line Google search query.
        """
        
        full_prompt_error = self._construct_prompt_for_llm()
        llm_response = self.llm.generate_response(messages = [{"role": "user", "content": full_prompt_error}], system_prompt = QUERY_SYSTEM_PROMPT)
        search_query = re.search(r'search_query: "(.*?)"', llm_response).group(1)
        return search_query

    async def _fetch_internet_content(self, search_query: str, num_urls: int = 5) -> str:
        """
        Fetches content from the internet based on a search query.

        Args:
            search_query (str): The Google search query.
            num_urls (int): Number of URLs to fetch (default 5).

        Returns:
            str: Combined text content from the fetched pages.
        """
        if not self.enable_internet_search:
             return ""

        urls = await internet_search(search_query)
        if not urls:
            return ""

        fetcher = Fetcher(auto_match=False)
        combined_content = ""
        for url in urls[:num_urls]:
            try:
                page = fetcher.get(url, stealthy_headers=True)
                content = page.get_all_text(ignore_tags=("script", "style"))
                combined_content += f"### CONTENT FROM: {url}\n{content}\n\n"
            except Exception as e:
                logging.error(f"Error fetching {url}: {e}")
        return combined_content

    async def debug(self):
        """
        Main method to orchestrate the code debugging process using an LLM.
        """
        guide_prompt = "I have code3.py that is giving me an error. Can you fix it?"

        error_exists = True
        while error_exists and self.attempt_count < self.max_attempts:
            self.attempt_count += 1
            logging.info(f"Attempt {self.attempt_count}...")

            current_error_signature = ""
            for code_filename in self.files_to_debug:
                error_message = self._run_subprocess_and_capture_output(code_filename=code_filename)
                if "Traceback" in error_message:
                  current_error_signature+=error_message

            if current_error_signature == self.last_error_signature and current_error_signature!="":
                self.constant_error_count += 1
            else:
                self.constant_error_count = 0
                self.last_error_signature = current_error_signature

            if self.enable_internet_search and self.constant_error_count >= self.internet_search_threshold:
                logging.info(f"Same error detected for {self.internet_search_threshold} attempts, fetching internet information...")
                search_query = self._generate_search_query_for_google()
                logging.info(f"Generated Query {search_query}")
                internet_content = await self._fetch_internet_content(search_query, num_urls = self.num_search_urls)
                full_prompt_with_error = self._construct_prompt_for_llm(internet_content)
                self.constant_error_count = 0  # Reset the count since we used the web info.

            else:
                full_prompt_with_error = self._construct_prompt_for_llm()

            llm_response = self.llm.generate_response(messages = [{"role": "user", "content": full_prompt_with_error + guide_prompt}], system_prompt = SYSTEM_PROMPT)
            code_changes = self._extract_code_from_llm_response(llm_response)
            
            # Get the current code before updating
            code_before_change = {}
            for filename in code_changes:
                with open(os.path.join(self.code_dir, filename), "r") as file:
                    code_before_change[filename] = file.read()


            self._update_code_files(code_changes)

             # Create a change summary to show the difference
            change_summary = ""
            for filename, new_code in code_changes.items():
                 if filename in code_before_change:
                      old_code = code_before_change[filename]
                      if old_code.strip() != new_code.strip():
                           change_summary += f"\nFile: {filename}\n"
                           diff = get_diff(old_code.splitlines(), new_code.splitlines())
                           change_summary += "".join(diff)

                
            if change_summary: # Logging only when some change have been made.
                 logging.info(f"AI Made these changes:\n{change_summary}")
            else:
                 logging.info("No changes has been made on this attempt.")
                

            error_exists = self._check_for_errors()
            if error_exists:
                logging.info("Error still exists. Trying again after a pause...")
                time.sleep(2)
            else:
                logging.info("All errors fixed.")

        if self.attempt_count >= self.max_attempts:
            logging.info("Maximum attempt reached without fixing all errors.")