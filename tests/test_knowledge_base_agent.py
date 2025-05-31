import pytest
from src.knowledge_base_agent import KnowledgeBaseAgent
from src.models import Procedure, FAQ, ClientHistory, Pricing
from unittest.mock import patch

def test_procedure_crud():
    agent = KnowledgeBaseAgent(user_role='admin')
    proc = Procedure(id='p1', name='Fix Sink', description='Fix leaking sink', estimated_time_minutes=60, required_tools=['wrench'], price=120.0)
    agent.add_procedure(proc)
    result = agent.get_procedure('p1')
    assert result is not None
    assert result.name == 'Fix Sink'

    # Update
    agent.update_procedure('p1', {'description': 'Fix leaking kitchen sink'})
    updated = agent.get_procedure('p1')
    assert updated.description == 'Fix leaking kitchen sink'

def test_faq_learning():
    agent = KnowledgeBaseAgent(user_role='admin')
    interaction = {'question': 'How long does a sink repair take?', 'timestamp': '2024-06-01T12:00:00Z', 'charge': 0}
    agent.learn_from_interaction('c1', interaction)
    faqs = agent.list_faqs()
    assert any(faq.question == 'How long does a sink repair take?' for faq in faqs)
