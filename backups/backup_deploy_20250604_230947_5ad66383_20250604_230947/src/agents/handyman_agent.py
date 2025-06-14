from src.agents.base_agent import BaseAgent
import asyncio
class HandymanAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, capabilities=["repair", "install", "maintenance"])

    async def execute_task(self, task: dict):
        # Simulate performing handyman task
        print(f"{self.agent_id} is performing task {task['task_id']}")
        await asyncio.sleep(task.get('duration', 2))
        self.current_load -= 1
        print(f"{self.agent_id} completed task {task['task_id']}")
        # In production: notify orchestrator of completion