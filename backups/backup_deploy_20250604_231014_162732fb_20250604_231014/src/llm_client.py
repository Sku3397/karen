import google.generativeai as genai
import logging
import os
from .config import GEMINI_API_KEY
import datetime # Added for dynamic date

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_FILE = os.path.join(os.path.dirname(__file__), 'llm_system_prompt.txt')

class LLMClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            logger.error("GEMINI_API_KEY not provided or found in environment.")
            raise ValueError("GEMINI_API_KEY is required for LLMClient")
        
        genai.configure(api_key=self.api_key)
        # For choosing a model, see https://ai.google.dev/gemini-api/docs/models/gemini
        # Using the latest available Flash model based on user request and recent documentation.
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        self._load_system_prompt() # Load system prompt on initialization
        logger.info(f"LLMClient initialized with Gemini model: gemini-2.5-flash-preview-05-20 and system prompt.")

    def _load_system_prompt(self):
        """Loads the system prompt from the predefined file."""
        try:
            with open(SYSTEM_PROMPT_FILE, 'r') as f:
                self.system_prompt_template = f.read()
            logger.info(f"Successfully loaded system prompt from {SYSTEM_PROMPT_FILE}")
        except FileNotFoundError:
            logger.error(f"System prompt file not found: {SYSTEM_PROMPT_FILE}. Using a default internal prompt.")
            self.system_prompt_template = "You are a helpful AI assistant." # Fallback
        except Exception as e:
            logger.error(f"Error loading system prompt from {SYSTEM_PROMPT_FILE}: {e}", exc_info=True)
            self.system_prompt_template = "You are a helpful AI assistant." # Fallback

    def get_system_prompt(self) -> str:
        """Returns the system prompt, with dynamic elements like date filled in."""
        self._load_system_prompt() # Reload the prompt each time it's requested
        current_date_str = datetime.date.today().strftime("%Y-%m-%d")
        return self.system_prompt_template.replace("{{current_date}}", current_date_str)

    def generate_text(self, user_prompt: str) -> str: # Renamed 'prompt' to 'user_prompt' for clarity
        """
        Generates text using the configured Gemini model, prepending the system prompt.

        Args:
            user_prompt: The user's input prompt for the LLM.

        Returns:
            The generated text as a string.
            Returns an error message string if generation fails.
        """
        if not self.api_key:
            logger.error("Cannot generate text: API key is not configured.")
            return "Error: LLM API key not configured."

        system_instructions_content = self.get_system_prompt()
        
        logger.debug(f"System Instructions: '{system_instructions_content[:200]}...'")
        logger.debug(f"User Prompt: '{user_prompt[:200]}...'")
        
        full_prompt = f"{system_instructions_content}\n\n{user_prompt}" # Combine prompts

        try:
            # Use the system_instruction parameter
            # The genai.GenerativeModel class is initialized in __init__
            # self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            # The generate_content method is called on this model instance.
            
            # Correct placement of system_instruction is within GenerationConfig
            # Ensure genai.types is available
            # import google.generativeai as genai # Already imported at the top of the file

            response = self.model.generate_content(
                contents=[full_prompt], # Pass combined prompt here
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7, # Example: set a temperature if needed
                    # top_p=... etc.
                )
            )
            
            if response and response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    generated_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                    logger.info(f"Successfully generated text. Length: {len(generated_text)}")
                    logger.debug(f"Generated text: '{generated_text[:200]}...'")
                    return generated_text
                else:
                    logger.error(f"No content or parts found in Gemini response candidate: {candidate}")
                    finish_reason = candidate.finish_reason if hasattr(candidate, 'finish_reason') else 'Unknown'
                    return f"Error: LLM response was empty or malformed. Finish Reason: {finish_reason}"
            else:
                logger.error(f"No candidates found in Gemini response: {response}")
                return "Error: LLM did not return any candidates."

        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}", exc_info=True)
            return f"Error: Exception during LLM text generation - {str(e)}"

if __name__ == '__main__':
    # This is for basic testing of the LLMClient
    # Ensure GEMINI_API_KEY is in your .env file or environment
    from dotenv import load_dotenv
    import sys
    # Assuming config.py is in the parent directory (src) 
    # and this script might be run from project root or src/
    # Adjust path if necessary for standalone execution
    if os.path.exists('.env'):
        load_dotenv()
        print("Loaded .env from current directory for testing.")
    elif os.path.exists('../.env'):
        load_dotenv(dotenv_path='../.env')
        print("Loaded .env from parent directory for testing.")
    else:
        print("Warning: .env file not found for testing LLMClient directly.")


    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set. Please set it in your .env file for this test.")
    else:
        logger.info(f"GEMINI_API_KEY found: {GEMINI_API_KEY[:5]}... (for testing)")
        try:
            client = LLMClient()
            # Test the system prompt loading
            logger.info(f"Current System Prompt for Test: {client.get_system_prompt()[:100]}...")
            
            test_user_prompt = "Summarize the following email content and suggest one primary action: \n\nSubject: Kitchen Sink Leaking\n\nHi, my kitchen sink is leaking badly under the cabinet. Water is everywhere. I need someone to come fix it ASAP. My address is 123 Main St. Thanks, John Doe."
            summary = client.generate_text(test_user_prompt)
            logger.info(f"Test Prompt: {test_user_prompt}")
            logger.info(f"Generated Summary/Action: {summary}")

            test_prompt_2 = "Create a concise task description for a handyman based on this: 'The client reports that their front door lock is jammed and they can't open it. They are located at 456 Oak Avenue and need it fixed today if possible.'"
            task_desc = client.generate_text(test_prompt_2)
            logger.info(f"Test Prompt 2: {test_prompt_2}")
            logger.info(f"Generated Task Description: {task_desc}")

        except Exception as e:
            logger.error(f"Error during LLMClient test: {e}", exc_info=True) 