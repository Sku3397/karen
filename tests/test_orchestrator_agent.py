import unittest
from unittest.mock import patch, MagicMock
from src.orchestrator_agent import OrchestratorAgent

class TestOrchestratorAgent(unittest.TestCase):
    def test_handle_input(self):
        agent = OrchestratorAgent()
        user_id = 'user_123'
        input_text = 'Please schedule a meeting tomorrow.'
        result = agent.handle_input(user_id, input_text)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]['assigned_to'], 'ScheduleAgent')
    
    def test_get_status(self):
        agent = OrchestratorAgent()
        user_id = 'user_123'
        # Add some context first
        agent.context_manager.update_context(user_id, {'last_tasks': []})
        context = agent.get_status(user_id)
        self.assertIn('last_tasks', context)

if __name__ == '__main__':
    unittest.main()
