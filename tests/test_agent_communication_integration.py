"""
Agent Communication Integration Tests

Tests:
1. Inter-agent messaging
2. Task routing with skill-based system  
3. Load balancing under stress
4. Priority adjustment scenarios
5. Redis fallback to filesystem
"""

import pytest
import asyncio
import json
import tempfile
import shutil
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import redis
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from src.agent_communication import (
    AgentCommunicationSystem,
    TaskPriority,
    AgentSkill,
    Task,
    Agent,
    Message,
    MessageType
)

class TestAgentCommunicationIntegration:
    """Integration tests for agent communication system"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis connection"""
        mock_redis = Mock(spec=redis.Redis)
        mock_redis.ping.return_value = True
        mock_redis.pubsub.return_value = Mock()
        mock_redis.set.return_value = True
        mock_redis.get.return_value = None
        mock_redis.exists.return_value = False
        mock_redis.lpush.return_value = 1
        mock_redis.brpop.return_value = None
        return mock_redis
    
    @pytest.fixture
    def communication_system(self, temp_dir, mock_redis):
        """Create communication system for testing"""
        with patch('redis.Redis', return_value=mock_redis):
            system = AgentCommunicationSystem(
                redis_url="redis://localhost:6379",
                inbox_base_path=temp_dir
            )
            return system
    
    @pytest.fixture
    def test_agents(self):
        """Create test agents with different skills"""
        agents = [
            Agent(
                agent_id="orchestrator",
                name="Orchestrator Agent",
                skills=[AgentSkill.TASK_ORCHESTRATION, AgentSkill.COORDINATION],
                max_concurrent_tasks=10,
                performance_metrics={'avg_response_time': 0.5}
            ),
            Agent(
                agent_id="sms_engineer",
                name="SMS Engineer",
                skills=[AgentSkill.SMS_INTEGRATION, AgentSkill.API_INTEGRATION],
                max_concurrent_tasks=5,
                performance_metrics={'avg_response_time': 1.2}
            ),
            Agent(
                agent_id="memory_engineer", 
                name="Memory Engineer",
                skills=[AgentSkill.MEMORY_MANAGEMENT, AgentSkill.DATABASE_OPERATIONS],
                max_concurrent_tasks=3,
                performance_metrics={'avg_response_time': 0.8}
            ),
            Agent(
                agent_id="test_engineer",
                name="Test Engineer", 
                skills=[AgentSkill.TESTING_AUTOMATION, AgentSkill.CODE_ANALYSIS],
                max_concurrent_tasks=8,
                performance_metrics={'avg_response_time': 2.0}
            )
        ]
        return agents

    @pytest.mark.integration
    def test_inter_agent_messaging(self, communication_system, test_agents, temp_dir):
        """Test 1: Inter-agent messaging"""
        
        # Register agents
        for agent in test_agents:
            communication_system.register_agent(agent)
        
        # Create test message
        message = Message(
            message_id="test_msg_001",
            from_agent="orchestrator",
            to_agent="sms_engineer",
            message_type=MessageType.TASK_ASSIGNMENT,
            content={
                "task_id": "sms_task_001",
                "description": "Implement SMS template system",
                "priority": TaskPriority.HIGH.value,
                "deadline": (datetime.now() + timedelta(hours=24)).isoformat()
            },
            timestamp=datetime.now().isoformat()
        )
        
        # Send message
        success = communication_system.send_message(message)
        assert success, "Message sending should succeed"
        
        # Verify file-based delivery
        inbox_path = Path(temp_dir) / "sms_engineer" / f"orchestrator_to_sms_engineer_{message.timestamp.replace(':', '').replace('-', '').replace('.', '_')}.json"
        
        # Check if message file exists (might need to wait for async processing)
        time.sleep(0.1)
        assert inbox_path.exists() or any(
            f.name.startswith("orchestrator_to_sms_engineer") 
            for f in Path(temp_dir).glob("sms_engineer/*.json")
        ), "Message file should be created in inbox"
        
        # Test message retrieval
        messages = communication_system.get_messages("sms_engineer")
        assert len(messages) >= 1, "Should retrieve at least one message"
        
        # Verify message content
        retrieved_message = messages[0]
        assert retrieved_message.from_agent == "orchestrator"
        assert retrieved_message.to_agent == "sms_engineer"
        assert retrieved_message.message_type == MessageType.TASK_ASSIGNMENT
        assert retrieved_message.content["task_id"] == "sms_task_001"

    @pytest.mark.integration
    def test_skill_based_task_routing(self, communication_system, test_agents):
        """Test 2: Task routing with skill-based system"""
        
        # Register agents
        for agent in test_agents:
            communication_system.register_agent(agent)
        
        # Test cases for different skills
        test_cases = [
            {
                "task": Task(
                    task_id="sms_001",
                    title="SMS Integration Task",
                    description="Implement SMS webhook",
                    required_skills=[AgentSkill.SMS_INTEGRATION],
                    priority=TaskPriority.HIGH,
                    estimated_duration=timedelta(hours=4)
                ),
                "expected_agent": "sms_engineer"
            },
            {
                "task": Task(
                    task_id="memory_001", 
                    title="Memory System Task",
                    description="Optimize memory storage",
                    required_skills=[AgentSkill.MEMORY_MANAGEMENT],
                    priority=TaskPriority.MEDIUM,
                    estimated_duration=timedelta(hours=6)
                ),
                "expected_agent": "memory_engineer"
            },
            {
                "task": Task(
                    task_id="test_001",
                    title="Testing Task",
                    description="Create integration tests", 
                    required_skills=[AgentSkill.TESTING_AUTOMATION],
                    priority=TaskPriority.LOW,
                    estimated_duration=timedelta(hours=3)
                ),
                "expected_agent": "test_engineer"
            },
            {
                "task": Task(
                    task_id="orchestration_001",
                    title="Coordination Task",
                    description="Coordinate agent workflow",
                    required_skills=[AgentSkill.TASK_ORCHESTRATION],
                    priority=TaskPriority.CRITICAL,
                    estimated_duration=timedelta(hours=2)
                ),
                "expected_agent": "orchestrator"
            }
        ]
        
        # Test routing for each task
        for test_case in test_cases:
            task = test_case["task"]
            expected_agent = test_case["expected_agent"]
            
            best_agent = communication_system.find_best_agent_for_task(task)
            assert best_agent is not None, f"Should find agent for task {task.task_id}"
            assert best_agent.agent_id == expected_agent, f"Task {task.task_id} should route to {expected_agent}, got {best_agent.agent_id}"
        
        # Test multi-skill task routing
        multi_skill_task = Task(
            task_id="multi_001",
            title="Multi-skill Task", 
            description="Task requiring multiple skills",
            required_skills=[AgentSkill.API_INTEGRATION, AgentSkill.DATABASE_OPERATIONS],
            priority=TaskPriority.HIGH,
            estimated_duration=timedelta(hours=5)
        )
        
        # Should find agent with best skill match (sms_engineer has API_INTEGRATION)
        best_agent = communication_system.find_best_agent_for_task(multi_skill_task)
        assert best_agent is not None, "Should find agent for multi-skill task"
        
        # Test load balancing - simulate high load on preferred agent
        communication_system.agents["sms_engineer"].current_load = 5  # At max capacity
        overloaded_agent = communication_system.find_best_agent_for_task(multi_skill_task)
        assert overloaded_agent.agent_id != "sms_engineer" or overloaded_agent.current_load < 5, "Should consider load balancing"

    @pytest.mark.integration 
    @pytest.mark.performance
    def test_load_balancing_under_stress(self, communication_system, test_agents):
        """Test 3: Load balancing under stress"""
        
        # Register agents
        for agent in test_agents:
            communication_system.register_agent(agent)
        
        # Create stress test scenario
        stress_tasks = []
        for i in range(50):  # Create 50 tasks
            task = Task(
                task_id=f"stress_task_{i:03d}",
                title=f"Stress Test Task {i}",
                description=f"Load testing task number {i}",
                required_skills=[AgentSkill.API_INTEGRATION],  # Skill available to sms_engineer
                priority=TaskPriority.MEDIUM,
                estimated_duration=timedelta(minutes=30)
            )
            stress_tasks.append(task)
        
        # Distribute tasks and track assignments
        assignments = {}
        start_time = time.time()
        
        for task in stress_tasks:
            best_agent = communication_system.find_best_agent_for_task(task)
            if best_agent:
                # Simulate task assignment
                communication_system.assign_task_to_agent(task, best_agent.agent_id)
                
                if best_agent.agent_id not in assignments:
                    assignments[best_agent.agent_id] = 0
                assignments[best_agent.agent_id] += 1
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify load balancing performance
        assert processing_time < 5.0, f"Task assignment should complete quickly, took {processing_time:.2f}s"
        assert len(assignments) > 0, "Tasks should be assigned to agents"
        
        # Check that load is distributed (no single agent gets all tasks)
        max_tasks = max(assignments.values()) if assignments else 0
        total_tasks = sum(assignments.values()) if assignments else 0
        
        if total_tasks > 10:  # Only test distribution if we have sufficient tasks
            max_percentage = (max_tasks / total_tasks) * 100
            assert max_percentage < 80, f"Load should be distributed, one agent got {max_percentage:.1f}% of tasks"
        
        # Verify no agent exceeds capacity
        for agent_id, task_count in assignments.items():
            agent = communication_system.agents[agent_id]
            assert task_count <= agent.max_concurrent_tasks, f"Agent {agent_id} assigned {task_count} tasks, max is {agent.max_concurrent_tasks}"

    @pytest.mark.integration
    def test_priority_adjustment_scenarios(self, communication_system, test_agents):
        """Test 4: Priority adjustment scenarios"""
        
        # Register agents
        for agent in test_agents:
            communication_system.register_agent(agent)
        
        # Create tasks with different priorities
        tasks = [
            Task(
                task_id="low_priority_001",
                title="Low Priority Task",
                description="Non-urgent task",
                required_skills=[AgentSkill.TESTING_AUTOMATION],
                priority=TaskPriority.LOW,
                estimated_duration=timedelta(hours=2)
            ),
            Task(
                task_id="medium_priority_001", 
                title="Medium Priority Task",
                description="Standard priority task",
                required_skills=[AgentSkill.TESTING_AUTOMATION],
                priority=TaskPriority.MEDIUM,
                estimated_duration=timedelta(hours=3)
            ),
            Task(
                task_id="high_priority_001",
                title="High Priority Task", 
                description="Urgent task",
                required_skills=[AgentSkill.TESTING_AUTOMATION],
                priority=TaskPriority.HIGH,
                estimated_duration=timedelta(hours=1)
            ),
            Task(
                task_id="critical_priority_001",
                title="Critical Priority Task",
                description="Emergency task",
                required_skills=[AgentSkill.TESTING_AUTOMATION], 
                priority=TaskPriority.CRITICAL,
                estimated_duration=timedelta(minutes=30)
            )
        ]
        
        # Assign all tasks to test_engineer (has TESTING_AUTOMATION skill)
        agent_id = "test_engineer"
        for task in tasks:
            communication_system.assign_task_to_agent(task, agent_id)
        
        # Get task queue and verify priority ordering
        task_queue = communication_system.get_agent_task_queue(agent_id)
        assert len(task_queue) == 4, "All tasks should be in queue"
        
        # Verify tasks are ordered by priority (CRITICAL=1, HIGH=2, MEDIUM=3, LOW=4)
        priorities = [task.priority.value for task in task_queue]
        assert priorities == sorted(priorities), f"Tasks should be ordered by priority, got {priorities}"
        
        # Test dynamic priority adjustment
        original_priority = tasks[0].priority  # Low priority task
        communication_system.adjust_task_priority("low_priority_001", TaskPriority.CRITICAL)
        
        # Get updated queue
        updated_queue = communication_system.get_agent_task_queue(agent_id)
        
        # Find the adjusted task
        adjusted_task = next((t for t in updated_queue if t.task_id == "low_priority_001"), None)
        assert adjusted_task is not None, "Adjusted task should still be in queue"
        assert adjusted_task.priority == TaskPriority.CRITICAL, "Priority should be updated to CRITICAL"
        
        # Verify queue is reordered
        updated_priorities = [task.priority.value for task in updated_queue]
        assert updated_priorities == sorted(updated_priorities), "Queue should be reordered after priority adjustment"

    @pytest.mark.integration
    def test_redis_fallback_to_filesystem(self, temp_dir):
        """Test 5: Redis fallback to filesystem"""
        
        # Test 1: Redis connection failure
        with patch('redis.Redis') as mock_redis_class:
            # Simulate Redis connection failure
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.ConnectionError("Connection failed")
            mock_redis_class.return_value = mock_redis_instance
            
            # Initialize system - should fallback to filesystem
            system = AgentCommunicationSystem(
                redis_url="redis://localhost:6379",
                inbox_base_path=temp_dir,
                enable_fallback=True
            )
            
            # Verify fallback mode
            assert not system.redis_available, "Redis should be marked as unavailable"
            assert system.use_filesystem_fallback, "Should use filesystem fallback"
        
        # Test 2: Message handling in fallback mode
        agent = Agent(
            agent_id="test_agent",
            name="Test Agent",
            skills=[AgentSkill.API_INTEGRATION],
            max_concurrent_tasks=5
        )
        system.register_agent(agent)
        
        # Send message in fallback mode
        message = Message(
            message_id="fallback_test_001",
            from_agent="orchestrator",
            to_agent="test_agent",
            message_type=MessageType.TASK_ASSIGNMENT,
            content={"test": "fallback message"},
            timestamp=datetime.now().isoformat()
        )
        
        success = system.send_message(message)
        assert success, "Message should be sent successfully in fallback mode"
        
        # Verify file creation
        inbox_files = list(Path(temp_dir).glob("test_agent/*.json"))
        assert len(inbox_files) > 0, "Message file should be created in fallback mode"
        
        # Test 3: Task queue persistence in fallback mode
        task = Task(
            task_id="fallback_task_001",
            title="Fallback Test Task",
            description="Test task for fallback mode",
            required_skills=[AgentSkill.API_INTEGRATION],
            priority=TaskPriority.MEDIUM,
            estimated_duration=timedelta(hours=1)
        )
        
        system.assign_task_to_agent(task, "test_agent")
        
        # Verify task persistence
        task_queue = system.get_agent_task_queue("test_agent") 
        assert len(task_queue) > 0, "Task should be persisted in fallback mode"
        assert task_queue[0].task_id == "fallback_task_001", "Correct task should be retrieved"
        
        # Test 4: Recovery when Redis becomes available
        with patch.object(system, '_redis') as mock_redis:
            mock_redis.ping.return_value = True
            
            # Simulate Redis recovery
            system._check_redis_connection()
            
            # System should detect Redis is available again
            assert system.redis_available, "Redis should be marked as available after recovery"

    @pytest.mark.integration
    def test_message_persistence_and_recovery(self, communication_system, test_agents, temp_dir):
        """Test message persistence and recovery across system restarts"""
        
        # Register agents and send messages
        for agent in test_agents:
            communication_system.register_agent(agent)
        
        # Send several messages
        messages = []
        for i in range(3):
            message = Message(
                message_id=f"persist_test_{i:03d}",
                from_agent="orchestrator",
                to_agent="sms_engineer",
                message_type=MessageType.TASK_ASSIGNMENT,
                content={"test_id": i, "data": f"test message {i}"},
                timestamp=datetime.now().isoformat()
            )
            messages.append(message)
            communication_system.send_message(message)
        
        # Simulate system restart by creating new instance
        with patch('redis.Redis', return_value=communication_system._redis):
            new_system = AgentCommunicationSystem(
                redis_url="redis://localhost:6379",
                inbox_base_path=temp_dir
            )
            
            # Register agents in new system
            for agent in test_agents:
                new_system.register_agent(agent)
            
            # Retrieve messages - should recover persisted messages
            recovered_messages = new_system.get_messages("sms_engineer")
            
            assert len(recovered_messages) >= 3, f"Should recover at least 3 messages, got {len(recovered_messages)}"
            
            # Verify message content
            message_ids = [msg.message_id for msg in recovered_messages]
            for original_msg in messages:
                assert original_msg.message_id in message_ids, f"Message {original_msg.message_id} should be recovered"

    @pytest.mark.integration
    @pytest.mark.performance
    def test_concurrent_message_handling(self, communication_system, test_agents):
        """Test concurrent message handling and thread safety"""
        
        # Register agents
        for agent in test_agents:
            communication_system.register_agent(agent)
        
        # Test concurrent message sending
        def send_messages(agent_id, message_count, results):
            """Send messages from multiple threads"""
            thread_results = []
            for i in range(message_count):
                message = Message(
                    message_id=f"concurrent_{agent_id}_{i:03d}",
                    from_agent="orchestrator",
                    to_agent=agent_id,
                    message_type=MessageType.TASK_ASSIGNMENT,
                    content={"thread_test": True, "message_num": i},
                    timestamp=datetime.now().isoformat()
                )
                success = communication_system.send_message(message)
                thread_results.append(success)
            results.extend(thread_results)
        
        # Start multiple threads
        threads = []
        results = []
        message_count_per_thread = 10
        
        for agent in test_agents[:3]:  # Use first 3 agents
            thread = threading.Thread(
                target=send_messages,
                args=(agent.agent_id, message_count_per_thread, results)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all messages were sent successfully
        expected_total = len(threads) * message_count_per_thread
        assert len(results) == expected_total, f"Expected {expected_total} results, got {len(results)}"
        assert all(results), "All message sends should succeed"
        
        # Verify message delivery
        total_received = 0
        for agent in test_agents[:3]:
            messages = communication_system.get_messages(agent.agent_id)
            total_received += len(messages)
        
        assert total_received >= expected_total, f"Should receive at least {expected_total} messages, got {total_received}"

    @pytest.mark.integration
    def test_agent_health_monitoring(self, communication_system, test_agents):
        """Test agent health monitoring and status tracking"""
        
        # Register agents
        for agent in test_agents:
            communication_system.register_agent(agent)
        
        # Test health check
        health_status = communication_system.check_agent_health("sms_engineer")
        assert health_status is not None, "Should get health status for registered agent"
        assert "status" in health_status, "Health status should include status field"
        assert "last_heartbeat" in health_status, "Health status should include heartbeat field"
        
        # Test heartbeat update
        communication_system.update_agent_heartbeat("sms_engineer")
        
        updated_health = communication_system.check_agent_health("sms_engineer")
        assert updated_health["last_heartbeat"] != health_status["last_heartbeat"], "Heartbeat should be updated"
        
        # Test agent performance metrics
        performance = communication_system.get_agent_performance_metrics("sms_engineer")
        assert performance is not None, "Should get performance metrics"
        assert "avg_response_time" in performance, "Should include response time metric"
        
        # Test system-wide health
        system_health = communication_system.get_system_health()
        assert "total_agents" in system_health, "System health should include agent count"
        assert "active_agents" in system_health, "System health should include active agents"
        assert system_health["total_agents"] == len(test_agents), "Should report correct agent count"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])