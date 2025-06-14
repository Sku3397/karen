# Escalation Protocols for Emergencies
def handle_escalation(emergency):
    """
    Determine escalation path based on emergency severity, type, and past history.
    Returns an escalation action dict.
    """
    severity = emergency.get('severity', 'unknown')
    escalation_level = 'normal'
    actions = []

    if severity == 'critical':
        escalation_level = 'high'
        actions.append('notify_all_contacts')
        actions.append('notify_authorities')
    elif severity == 'warning':
        escalation_level = 'medium'
        actions.append('notify_primary_contact')
    else:
        actions.append('log_event')

    return {
        'level': escalation_level,
        'actions': actions
    }