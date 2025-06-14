# Utility functions for event sync and conflict resolution
def resolve_conflicts(gc_events, outlook_events):
    # Simple conflict resolution: match by summary and time
    matched, conflicts = [], []
    new_events = {'google_to_outlook': [], 'outlook_to_google': [], 'mappings': []}
    seen = set()
    for gce in gc_events:
        for oe in outlook_events:
            if (gce['summary'] == oe.get('subject') and gce['start'].get('dateTime') == oe['start'].get('dateTime')):
                matched.append((gce, oe))
                seen.add(gce['id'])
                seen.add(oe['id'])
    # Events present in Google but not in Outlook
    for gce in gc_events:
        if gce['id'] not in seen:
            new_events['google_to_outlook'].append(gce)
            new_events['mappings'].append({'source': 'google', 'ext_event_id': gce['id'], 'event_data': gce})
    # Events present in Outlook but not in Google
    for oe in outlook_events:
        if oe['id'] not in seen:
            new_events['outlook_to_google'].append(oe)
            new_events['mappings'].append({'source': 'outlook', 'ext_event_id': oe['id'], 'event_data': oe})
    # (Placeholder) Add logic for conflict detection
    return new_events, conflicts
