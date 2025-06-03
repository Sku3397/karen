import logging
import os # Keep os for API_KEY check, though LLMClient handles its own key

# Import LLMClient
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

# Initialize LLMClient instance. 
# It will pick up API_KEY from config/environment itself.
# We can initialize it once at the module level.
llm_client_instance = None
try:
    llm_client_instance = LLMClient()
    logger.info("AIResponder: LLMClient initialized successfully.")
except ValueError as e:
    logger.error(f"AIResponder: Failed to initialize LLMClient: {e}. AI responses will not work.")
except Exception as e:
    logger.error(f"AIResponder: An unexpected error occurred during LLMClient initialization: {e}", exc_info=True)

def generate_response(subject: str, sender: str, body: str) -> str:
    """Generates a response to an email using the central LLMClient."""
    if not llm_client_instance:
        logger.error("Cannot generate AI response: LLMClient is not initialized.")
        return "Error: AI Responder (LLM Client) not configured or failed to initialize."

    # Construct the user-specific part of the prompt.
    # The system prompt is handled by LLMClient.
    user_query = (
        f"Email received from: {sender}\n"
        f"Subject: '{subject}'\n"
        f"Body:\n{body}\n\n"
        f"Based on the above email, please generate an appropriate reply according to your instructions."
    )

    logging.info(f"AIResponder: Generating response via LLMClient for email from {sender} with subject '{subject}'")
    # The LLMClient's generate_text will prepend the system prompt from llm_system_prompt.txt
    try:
        ai_text = llm_client_instance.generate_text(user_prompt=user_query)
        
        if ai_text and not ai_text.startswith("Error:"):
            logger.info(f"AIResponder: Successfully received response from LLMClient for email '{subject}'.")
            return ai_text.strip()
        else:
            # LLMClient already logs errors, ai_text will contain an error message from LLMClient
            logger.warning(f"AIResponder: LLMClient returned an error or empty response for email '{subject}'. Response: '{ai_text}'")
            return ai_text # Return the error message from LLMClient
            
    except Exception as e:
        logger.error(f"AIResponder: Error calling LLMClient for email '{subject}': {e}", exc_info=True)
        return f"Error: Could not generate AI response due to an internal error in AIResponder."

if __name__ == '__main__':
    # Example test (requires GEMINI_API_KEY to be set in .env for LLMClient)
    print("Testing AI Responder (with LLMClient)...")
    # Ensure .env is loaded for LLMClient if running this directly
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') 
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        print(f"Loaded .env from {dotenv_path}")
    else:
        print(f"Warning: .env file not found at {dotenv_path}. LLMClient might fail if API key not in environment.")

    # Basic logging for standalone test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    if not llm_client_instance:
        print("LLMClient instance in AIResponder is not available. Cannot run test.")
    else:
        print(f"System prompt that will be used by LLMClient (first 100 chars): {llm_client_instance.get_system_prompt()[:100]}...")
        test_subject = "Question about services"
        test_sender = "test@example.com"
        test_body = "Hi, I'd like to know if you offer plumbing services. Thanks!"
        print(f"Sending test prompt for: Subject='{test_subject}', Sender='{test_sender}', Body='{test_body}'")
        response = generate_response(test_subject, test_sender, test_body)
        print(f"\n--- Test AI Response ---\n{response}")

        test_subject_spam = "Update my bathroom"
        test_sender_spam = "potential_customer@example.com"
        test_body_spam = "I want to renovate my bathroom. I saw you specialize in that. Can you give me a quote? My address is 123 Main St."
        print(f"\nSending renovation query test prompt for: Subject='{test_subject_spam}', Sender='{test_sender_spam}', Body='{test_body_spam}'")
        response_spam = generate_response(test_subject_spam, test_sender_spam, test_body_spam)
        print(f"\n--- Test AI Renovation Response ---\n{response_spam}") 