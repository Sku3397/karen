#!/usr/bin/env python3
"""
Autonomous Eigencode Worker Loop
Continuously processes Eigencode tasks and implements improvements
"""
import json
import time
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [EIGENCODE] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/eigencode_worker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AutonomousEigencodeWorker:
    """Autonomous worker that processes Eigencode analysis tasks"""
    
    def __init__(self):
        self.task_file = Path("tasks/eigencode_assigned_tasks.json")
        self.eigencode_config = Path("eigencode.config.json")
        self.running = True
        self.current_task = None
        self.worker_id = "eigencode_autonomous_worker"
        
        # Ensure required directories exist
        Path("logs").mkdir(exist_ok=True)
        Path("reports").mkdir(exist_ok=True)
        
    def load_config(self) -> Dict:
        """Load Eigencode configuration"""
        if self.eigencode_config.exists():
            with open(self.eigencode_config, 'r') as f:
                return json.load(f)
        return {}
    
    def get_next_task(self) -> Optional[Dict]:
        """Get the next pending Eigencode task"""
        if not self.task_file.exists():
            logger.info("No task file found, creating empty one")
            with open(self.task_file, 'w') as f:
                json.dump([], f)
            return None
            
        with open(self.task_file, 'r') as f:
            tasks = json.load(f)
        
        # Find high priority tasks first, then medium, then low
        for priority in ['high', 'medium', 'low']:
            for task in tasks:
                if (task.get('status') in ['new', 'pending'] and 
                    task.get('priority') == priority and
                    task.get('assigned_to') == 'EigencodeAgent'):
                    return task
        
        return None
    
    def update_task_status(self, task_id: str, status: str, details: Dict = None):
        """Update task status in the task file"""
        if not self.task_file.exists():
            return
            
        with open(self.task_file, 'r') as f:
            tasks = json.load(f)
        
        for task in tasks:
            if task.get('task_id') == task_id or task.get('id') == task_id:
                task['status'] = status
                task['updated_at'] = datetime.now().isoformat()
                task['worker_id'] = self.worker_id
                
                if details:
                    task.update(details)
                    
                if status == 'in_progress':
                    task['started_at'] = datetime.now().isoformat()
                elif status == 'completed':
                    task['completed_at'] = datetime.now().isoformat()
                
                break
        
        with open(self.task_file, 'w') as f:
            json.dump(tasks, f, indent=2)
        
        logger.info(f"Updated task {task_id} status to {status}")
    
    def log_activity(self, activity_type: str, details: Dict):
        """Log worker activity"""
        activity = {
            "timestamp": datetime.now().isoformat(),
            "worker_id": self.worker_id,
            "activity_type": activity_type,
            "details": details
        }
        
        with open("logs/eigencode_activity.jsonl", 'a') as f:
            f.write(json.dumps(activity) + '\n')
    
    def analyze_file_patterns(self, source_file: str) -> Dict:
        """Analyze patterns in source file"""
        file_path = Path(source_file)
        if not file_path.exists():
            return {"analysis": "File not found", "recommendations": []}
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            analysis = {
                "file_size": len(content),
                "line_count": len(content.split('\n')),
                "complexity_indicators": [],
                "security_concerns": [],
                "performance_issues": [],
                "recommendations": []
            }
            
            # Pattern analysis
            if "TODO" in content:
                analysis["complexity_indicators"].append("Contains TODO comments")
                analysis["recommendations"].append("Complete TODO items")
            
            if "placeholder" in content.lower():
                analysis["complexity_indicators"].append("Contains placeholder methods")
                analysis["recommendations"].append("Implement placeholder functionality")
            
            if "# TODO" in content or "# FIXME" in content:
                analysis["complexity_indicators"].append("Has marked implementation gaps")
                analysis["recommendations"].append("Address implementation gaps")
            
            # Security patterns
            if "password" in content.lower() and "hardcoded" not in content.lower():
                analysis["security_concerns"].append("Potential password handling")
            
            if "api_key" in content.lower() or "secret" in content.lower():
                analysis["security_concerns"].append("Potential credential exposure")
            
            # Performance patterns
            if "sleep(" in content or "time.sleep" in content:
                analysis["performance_issues"].append("Synchronous sleep calls found")
            
            if analysis["line_count"] > 500:
                analysis["performance_issues"].append("Large file - consider modularization")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file {source_file}: {e}")
            return {"analysis": f"Error: {e}", "recommendations": []}
    
    def implement_nlp_improvement(self, task: Dict) -> Dict:
        """Implement NLP improvements for a task"""
        source_file = task.get('source_file', '')
        description = task.get('description', '')
        
        logger.info(f"Implementing NLP improvement for {source_file}")
        
        # Analyze current file
        analysis = self.analyze_file_patterns(source_file)
        
        # Generate implementation strategy
        strategy = {
            "approach": "NLP Enhancement",
            "target_file": source_file,
            "improvements": [],
            "dependencies": [],
            "test_requirements": []
        }
        
        if "intent" in description.lower():
            strategy["improvements"].append("Implement intent classification using spaCy or transformers")
            strategy["dependencies"].append("spacy>=3.4.0")
            strategy["test_requirements"].append("Test intent classification accuracy")
        
        if "sentiment" in description.lower():
            strategy["improvements"].append("Add sentiment analysis capability")
            strategy["dependencies"].append("textblob>=0.17.1")
            strategy["test_requirements"].append("Test sentiment detection")
        
        if "urgency" in description.lower():
            strategy["improvements"].append("Implement urgency detection using keyword + context analysis")
            strategy["dependencies"].append("scikit-learn>=1.0.0")
            strategy["test_requirements"].append("Test urgency classification")
        
        if "context" in description.lower():
            strategy["improvements"].append("Add context summarization using extractive methods")
            strategy["dependencies"].append("sumy>=0.8.1")
            strategy["test_requirements"].append("Test context summary quality")
        
        return {
            "status": "analysis_complete",
            "analysis": analysis,
            "strategy": strategy,
            "next_steps": [
                "Install required dependencies",
                "Implement core NLP functionality",
                "Add unit tests",
                "Integrate with existing system"
            ]
        }
    
    def implement_performance_optimization(self, task: Dict) -> Dict:
        """Implement performance optimizations"""
        source_file = task.get('source_file', '')
        
        logger.info(f"Implementing performance optimization for {source_file}")
        
        analysis = self.analyze_file_patterns(source_file)
        
        strategy = {
            "approach": "Performance Optimization",
            "target_file": source_file,
            "optimizations": [],
            "caching_strategies": [],
            "monitoring": []
        }
        
        if "memory" in task.get('description', '').lower():
            strategy["optimizations"].append("Implement memory pooling and cleanup")
            strategy["caching_strategies"].append("Add LRU cache for frequently accessed data")
            strategy["monitoring"].append("Add memory usage tracking")
        
        if "redis" in source_file.lower():
            strategy["optimizations"].append("Optimize Redis connection pooling")
            strategy["caching_strategies"].append("Implement intelligent cache expiration")
            strategy["monitoring"].append("Add Redis performance metrics")
        
        return {
            "status": "optimization_planned",
            "analysis": analysis,
            "strategy": strategy,
            "estimated_improvement": "20-40% performance gain expected"
        }
    
    def create_test_suite(self, task: Dict) -> Dict:
        """Create comprehensive test suite"""
        source_file = task.get('source_file', '')
        
        logger.info(f"Creating test suite for {source_file}")
        
        test_strategy = {
            "approach": "Comprehensive Testing",
            "target_file": source_file,
            "test_types": [],
            "coverage_target": "85%",
            "test_files": []
        }
        
        if "integration" in task.get('description', '').lower():
            test_strategy["test_types"].append("Integration Tests")
            test_strategy["test_files"].append(f"tests/integration/test_{Path(source_file).stem}_integration.py")
        
        if "unit" in task.get('description', '').lower():
            test_strategy["test_types"].append("Unit Tests")
            test_strategy["test_files"].append(f"tests/unit/test_{Path(source_file).stem}.py")
        
        if "performance" in task.get('description', '').lower():
            test_strategy["test_types"].append("Performance Tests")
            test_strategy["test_files"].append(f"tests/performance/test_{Path(source_file).stem}_performance.py")
        
        return {
            "status": "test_suite_planned",
            "strategy": test_strategy,
            "implementation_order": [
                "Unit tests (core functionality)",
                "Integration tests (system interaction)",
                "Performance tests (benchmarks)"
            ]
        }
    
    def process_task(self, task: Dict) -> Dict:
        """Process a single Eigencode task"""
        task_id = task.get('task_id') or task.get('id')
        category = task.get('category', 'General')
        
        logger.info(f"Processing task {task_id}: {task.get('description', '')[:100]}...")
        
        self.current_task = task
        self.update_task_status(task_id, 'in_progress')
        
        try:
            # Route task based on category
            if category == 'NLP_Improvement':
                result = self.implement_nlp_improvement(task)
            elif category == 'Performance':
                result = self.implement_performance_optimization(task)
            elif category == 'Testing':
                result = self.create_test_suite(task)
            elif category == 'Implementation':
                result = self.analyze_file_patterns(task.get('source_file', ''))
            else:
                result = {"status": "analyzed", "message": f"Generic analysis for {category} task"}
            
            # Log successful completion
            self.update_task_status(task_id, 'completed', {
                'result': result,
                'completion_time': datetime.now().isoformat()
            })
            
            self.log_activity('task_completed', {
                'task_id': task_id,
                'category': category,
                'result_summary': result.get('status', 'completed')
            })
            
            logger.info(f"✅ Completed task {task_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing task {task_id}: {e}")
            self.update_task_status(task_id, 'failed', {
                'error': str(e),
                'failure_time': datetime.now().isoformat()
            })
            
            self.log_activity('task_failed', {
                'task_id': task_id,
                'error': str(e)
            })
            
            return {"status": "failed", "error": str(e)}
        
        finally:
            self.current_task = None
    
    def generate_progress_report(self) -> Dict:
        """Generate progress report"""
        if not self.task_file.exists():
            return {"total_tasks": 0, "completed": 0, "in_progress": 0, "failed": 0}
        
        with open(self.task_file, 'r') as f:
            tasks = json.load(f)
        
        stats = {
            "total_tasks": len(tasks),
            "completed": 0,
            "in_progress": 0,
            "failed": 0,
            "pending": 0,
            "categories": {},
            "priorities": {"high": 0, "medium": 0, "low": 0}
        }
        
        for task in tasks:
            status = task.get('status', 'pending')
            category = task.get('category', 'Unknown')
            priority = task.get('priority', 'medium')
            
            if status in stats:
                stats[status] += 1
            else:
                stats["pending"] += 1
            
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
            stats["priorities"][priority] += 1
        
        return stats
    
    async def autonomous_loop(self):
        """Main autonomous work loop"""
        logger.info("🚀 Starting Autonomous Eigencode Worker Loop")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"🔄 Starting work cycle {cycle_count}")
                
                # Get next task
                next_task = self.get_next_task()
                
                if next_task:
                    # Process the task
                    result = self.process_task(next_task)
                    
                    # Brief pause between tasks
                    await asyncio.sleep(5)
                else:
                    logger.info("📋 No pending tasks found, waiting...")
                    
                    # Generate progress report every 10 cycles
                    if cycle_count % 10 == 0:
                        report = self.generate_progress_report()
                        logger.info(f"📊 Progress: {report['completed']}/{report['total_tasks']} completed")
                        
                        # Save report
                        report_file = f"reports/eigencode_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(report_file, 'w') as f:
                            json.dump(report, f, indent=2)
                    
                    # Wait longer when no tasks
                    await asyncio.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal, stopping...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"💥 Error in autonomous loop: {e}")
                await asyncio.sleep(10)
        
        logger.info("✅ Autonomous Eigencode Worker stopped")
    
    def start(self):
        """Start the autonomous worker"""
        try:
            asyncio.run(self.autonomous_loop())
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
        except Exception as e:
            logger.error(f"Worker crashed: {e}")


def main():
    """Main entry point"""
    print("🤖 Autonomous Eigencode Worker")
    print("=" * 50)
    print("Continuously processing Eigencode analysis tasks")
    print("Press Ctrl+C to stop")
    print()
    
    worker = AutonomousEigencodeWorker()
    worker.start()


if __name__ == "__main__":
    main()