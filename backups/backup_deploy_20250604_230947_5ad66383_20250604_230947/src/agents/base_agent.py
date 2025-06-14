from autogen import Agent
from typing import Dict, Any

class BaseAgent(Agent):
    def __init__(self, agent_id: str, capabilities: list = None):
        super().__init__(name=agent_id)
        self.agent_id = agent_id
        self.capabilities = capabilities or []
        self.current_load = 0

    def is_available(self, task: dict) -> bool:
        # Simulate availability (placeholder logic)
        return self.current_load < 3  # e.g., max 3 concurrent tasks

    async def accept_task(self, task: dict) -> bool:
        # Accept the task if available
        if self.is_available(task):
            self.current_load += 1
            # Start task asynchronously
            asyncio.create_task(self.execute_task(task))
            return True
        return False

    async def execute_task(self, task: dict):
        # Simulated task execution (replace with real logic)
        import asyncio
        await asyncio.sleep(task.get('duration', 1))
        self.current_load -= 1
        # Notify orchestrator of completion (to be implemented)

    async def receive_message(self, from_agent: str, message: dict):
        # Handle inter-agent communication (override in subclass if needed)
        pass
