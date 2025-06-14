# Event and mapping models
def event_to_dict(event):
    # Normalize event object to a dict for storage/comparison
    return {
        'id': event.get('id'),
        'summary': event.get('summary', event.get('subject', '')),
        'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date_time'),
        'end': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date_time'),
        'description': event.get('description', event.get('body', {}).get('content', '')),
    }

class EventMapping:
    def __init__(self, user_id, source, external_event_id, event_data):
        self.user_id = user_id
        self.source = source
        self.external_event_id = external_event_id
        self.event_data = event_data
