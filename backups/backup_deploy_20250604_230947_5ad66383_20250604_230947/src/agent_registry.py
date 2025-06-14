# Agent Registry
class BaseAgent:
    def delegate_task(self, user_id, input_text, context):
        # Stub: real implementation would route to specialized agent
        return [{
            'task': input_text,
            'status': 'pending',
            'assigned_to': self.__class__.__name__
        }]

class ScheduleAgent(BaseAgent):
    pass

class ReminderAgent(BaseAgent):
    pass

class CallAgent(BaseAgent):
    pass

class GeneralAgent(BaseAgent):
    pass

def get_agent_for_intent(intent):
    if intent == 'schedule_appointment':
        return ScheduleAgent()
    elif intent == 'set_reminder':
        return ReminderAgent()
    elif intent == 'initiate_call':
        return CallAgent()
    else:
        return GeneralAgent()
