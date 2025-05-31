# Webhook handlers for calendar change notifications
from flask import Blueprint, request
from .agent import SchedulerAgent

webhooks_bp = Blueprint('webhooks', __name__)

@webhooks_bp.route('/webhook/google', methods=['POST'])
def google_webhook():
    # Handle incoming Google Calendar push notification
    # Extract user_id, re-sync events
    user_id = request.headers.get('X-User-ID')
    # Fetch credentials in production system
    agent = SchedulerAgent(user_id, gc_creds={}, outlook_creds={})
    agent.sync_events()
    return '', 204

@webhooks_bp.route('/webhook/outlook', methods=['POST'])
def outlook_webhook():
    user_id = request.headers.get('X-User-ID')
    agent = SchedulerAgent(user_id, gc_creds={}, outlook_creds={})
    agent.sync_events()
    return '', 204
