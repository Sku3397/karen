# Orchestrator implementation using Autogen
import asyncio
from autogen import Agent, Message, AgentManager
from typing import Dict, List, Optional, Any
from src.agents.base_agent import BaseAgent
import threading

class Orchestrator(Agent):
    def __init__(self):
        super().__init__(name="Orchestrator")
        self.agents: Dict[str, BaseAgent] = {}
        self.lock = threading.Lock()
        self.pending_tasks: List[dict] = []
        self.active_tasks: Dict[str, dict] = {}

    def register_agent(self, agent: BaseAgent):
        with self.lock:
            self.agents[agent.agent_id] = agent

    def unregister_agent(self, agent_id: str):
        with self.lock:
            if agent_id in self.agents:
                del self.agents[agent_id]

    async def assign_task(self, task: dict) -> Optional[str]:
        """
        Assigns a task to an available agent, handling conflicts and avoiding deadlocks.
        Returns the agent_id or None if no agent is available.
        """
        async with asyncio.Lock():
            available_agents = [a for a in self.agents.values() if a.is_available(task)]
            # Conflict resolution: prioritize by agent load, capabilities, etc.
            available_agents.sort(key=lambda a: a.current_load)
            for agent in available_agents:
                if await agent.accept_task(task):
                    self.active_tasks[task["task_id"]] = task
                    return agent.agent_id
            self.pending_tasks.append(task)
            return None

    async def handle_task_completion(self, agent_id: str, task_id: str):
        async with asyncio.Lock():
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            # Check for pending tasks and re-assign
            if self.pending_tasks:
                task = self.pending_tasks.pop(0)
                await self.assign_task(task)

    async def communicate(self, from_agent: str, to_agent: str, message: dict) -> Any:
        """
        Route message between agents, handling possible message conflicts.
        """
        async with asyncio.Lock():
            if to_agent in self.agents:
                return await self.agents[to_agent].receive_message(from_agent, message)
            return None

    async def run(self):
        """
        Main orchestrator event loop. Handles agent monitoring and task assignment.
        """
        while True:
            # Monitor agents for deadlocks or non-responsiveness
            await self.detect_and_resolve_deadlocks()
            await asyncio.sleep(1)

    async def detect_and_resolve_deadlocks(self):
        # Placeholder logic for deadlock detection and resolution
        # Could analyze dependencies between active tasks and agent states
        pass

# Example instantiation
# from src.agents.handyman_agent import HandymanAgent
# orchestrator = Orchestrator()
# handyman = HandymanAgent(agent_id="handyman-1")
# orchestrator.register_agent(handyman)
