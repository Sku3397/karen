# Basic Intent Classifier Stub (to be replaced with NLP integration)
def classify_intent(text):
    # TODO: Integrate with NLP model or 3rd party API for production
    if 'schedule' in text.lower():
        return 'schedule_appointment'
    elif 'remind' in text.lower():
        return 'set_reminder'
    elif 'call' in text.lower():
        return 'initiate_call'
    else:
        return 'general_query'
