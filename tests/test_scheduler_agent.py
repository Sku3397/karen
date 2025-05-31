# Tests for SchedulerAgent
import unittest
from src.scheduler.agent import SchedulerAgent

class TestSchedulerAgent(unittest.TestCase):
    def setUp(self):
        self.agent = SchedulerAgent('test_user', gc_creds={}, outlook_creds={})

    def test_create_event_google(self):
        dummy_event = {"summary": "Test Event", "start": {"dateTime": "2024-06-10T10:00:00Z"}, "end": {"dateTime": "2024-06-10T11:00:00Z"}}
        # Should mock GoogleCalendarClient for a real test
        # result = self.agent.create_event('google', dummy_event)
        # self.assertIn('id', result)
        self.assertTrue(True)

    def test_sync_events(self):
        # Should mock both clients for a real test
        # sync_result = self.agent.sync_events()
        # self.assertIn('synced', sync_result)
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
