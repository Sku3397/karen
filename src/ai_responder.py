import google.generativeai as genai
import os
import logging

# Configure the Gemini client with the API key from environment variables
API_KEY = os.getenv('GEMINI_API_KEY')
if not API_KEY:
    logging.warning("GEMINI_API_KEY not found in environment variables. AI Responder will not function.")
    # You could raise an error here, or allow the module to load but fail on generate_response
else:
    try:
        genai.configure(api_key=API_KEY)
    except Exception as e:
        logging.error(f"Failed to configure Gemini API: {e}")

# For now, using gemini-1.5-flash, which is good for fast, high-volume tasks
# Ensure this model is available and appropriate for your use case.
MODEL_NAME = "gemini-1.5-flash-latest" # Using the latest flash model

def generate_response(subject: str, sender: str, body: str) -> str:
    """Generates a response to an email using the Gemini API."""
    if not API_KEY:
        logging.error("Cannot generate AI response: GEMINI_API_KEY is not configured.")
        return "Error: AI Responder not configured."

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        # Construct a more nuanced prompt
        prompt = (
            f"You are an AI Secretary Assistant for a handyman business called 'AI Handyman Secretary Assistant'. "
            f"Your name is not specified, you are just the assistant. "
            f"You are communicating with: {sender}. "
            f"The email subject is: '{subject}'. "
            f"The email body is: \n\n---\n{body}\n---\n\n"
            f"Please analyze the email and provide a concise, professional, and helpful reply. "
            f"If it's a simple query you can answer (e.g., asking about services, simple questions), try to answer it. "
            f"If it's a request for work or a quote, acknowledge the request and inform them that their message has been received and will be reviewed by the appropriate person. "
            f"If the email seems like spam, an advertisement, or automated notification not requiring a human reply, respond with a polite but brief declination or state that no action is needed. "
            f"If you are unsure how to respond, state that the email has been received and will be passed on for review. "
            f"Keep your replies relatively short and to the point. Do not ask to be contacted by phone unless explicitly necessary for the request."
        )

        logging.info(f"Sending prompt to Gemini ({MODEL_NAME}) for email from {sender} with subject '{subject}'")
        # logging.debug(f"Full prompt for Gemini: {prompt}") # Can be very verbose
        
        response = model.generate_content(prompt)
        
        if response.parts:
            ai_text = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
            logging.info(f"Successfully received response from Gemini for email '{subject}'.")
            # logging.debug(f"Gemini raw response text: {ai_text}")
            return ai_text.strip()
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
            logging.error(f"Gemini content generation blocked. Reason: {response.prompt_feedback.block_reason}")
            if response.prompt_feedback.safety_ratings:
                for rating in response.prompt_feedback.safety_ratings:
                    logging.error(f"  Safety Rating: Category {rating.category}, Probability {rating.probability}")
            return "Error: Content generation was blocked by the AI."
        else:
            logging.warning(f"Gemini response was empty or did not contain text parts for email '{subject}'. Response: {response}")
            return "AI response could not be generated at this time."

    except Exception as e:
        logging.error(f"Error during Gemini API call for email '{subject}': {e}", exc_info=True)
        return f"Error: Could not generate AI response due to an internal error."

if __name__ == '__main__':
    # Example test (requires GEMINI_API_KEY to be set in .env)
    print("Testing AI Responder...")
    # Ensure .env is loaded if running this directly and .env is in project root
    from dotenv import load_dotenv
    # Assumes this script is in src/, so .env is one level up
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') 
    load_dotenv(dotenv_path=dotenv_path)
    
    # Re-check API_KEY after attempting to load .env for standalone test
    API_KEY = os.getenv('GEMINI_API_KEY')
    if not API_KEY:
        print("GEMINI_API_KEY not set. Cannot run test.")
    else:
        genai.configure(api_key=API_KEY) # Re-configure if it failed initially
        test_subject = "Question about services"
        test_sender = "test@example.com"
        test_body = "Hi, I'd like to know if you offer plumbing services. Thanks!"
        print(f"Sending test prompt for: Subject='{test_subject}', Sender='{test_sender}', Body='{test_body}'")
        response = generate_response(test_subject, test_sender, test_body)
        print(f"\n--- Test AI Response ---\n{response}")

        test_subject_spam = "Amazing Deals! Click Now!"
        test_sender_spam = "spammer@example.com"
        test_body_spam = "You have won a million dollars! Click here!"
        print(f"\nSending spam test prompt for: Subject='{test_subject_spam}', Sender='{test_sender_spam}', Body='{test_body_spam}'")
        response_spam = generate_response(test_subject_spam, test_sender_spam, test_body_spam)
        print(f"\n--- Test AI Spam Response ---\n{response_spam}") 