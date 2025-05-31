import google.generativeai as genai
import logging
import os
from .config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            logger.error("GEMINI_API_KEY not provided or found in environment.")
            raise ValueError("GEMINI_API_KEY is required for LLMClient")
        
        genai.configure(api_key=self.api_key)
        # For choosing a model, see https://ai.google.dev/gemini-api/docs/models/gemini
        # Initially, let's use a general model. We can refine this later.
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest') 
        logger.info("LLMClient initialized with Gemini model.")

    def generate_text(self, prompt: str) -> str:
        """
        Generates text using the configured Gemini model.

        Args:
            prompt: The input prompt for the LLM.

        Returns:
            The generated text as a string.
            Returns an error message string if generation fails.
        """
        if not self.api_key:
            logger.error("Cannot generate text: API key is not configured.")
            return "Error: LLM API key not configured."

        logger.debug(f"Generating text with prompt: '{prompt[:100]}...'")
        try:
            response = self.model.generate_content(prompt)
            
            # Debug: Print the full response object to understand its structure
            # logger.debug(f"Full Gemini API response object: {response}")

            if response and response.candidates:
                # Assuming the first candidate is the one we want and it has content.
                # Accessing parts of the response needs to be robust.
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
            test_prompt = "Summarize the following email content and suggest one primary action: \n\nSubject: Kitchen Sink Leaking\n\nHi, my kitchen sink is leaking badly under the cabinet. Water is everywhere. I need someone to come fix it ASAP. My address is 123 Main St. Thanks, John Doe."
            summary = client.generate_text(test_prompt)
            logger.info(f"Test Prompt: {test_prompt}")
            logger.info(f"Generated Summary/Action: {summary}")

            test_prompt_2 = "Create a concise task description for a handyman based on this: 'The client reports that their front door lock is jammed and they can't open it. They are located at 456 Oak Avenue and need it fixed today if possible.'"
            task_desc = client.generate_text(test_prompt_2)
            logger.info(f"Test Prompt 2: {test_prompt_2}")
            logger.info(f"Generated Task Description: {task_desc}")

        except Exception as e:
            logger.error(f"Error during LLMClient test: {e}", exc_info=True) 