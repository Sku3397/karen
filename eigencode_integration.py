#!/usr/bin/env python3
"""
Eigencode-Karen Bridge
Connects Eigencode's analysis capabilities with our multi-agent system
"""
import subprocess
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
import redis
from datetime import datetime

class EigencodeKarenBridge:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
        self.eigencode_available = self._check_eigencode()
        
    def _check_eigencode(self) -> bool:
        """Check if eigencode is available"""
        try:
            result = subprocess.run(['eigencode', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            print("⚠️  Eigencode not found. Using fallback methods.")
            return False
    
    def analyze_agent_code(self, agent_name: str, file_path: str) -> Dict:
        """Analyze code produced by an agent"""
        if not self.eigencode_available:
            return self._fallback_analysis(file_path)
            
        result = subprocess.run([
            'eigencode', 'analyze',
            '--file', file_path,
            '--context', f'agent:{agent_name}',
            '--json'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            analysis = json.loads(result.stdout)
            
            # Store analysis in Redis for other agents
            self.redis_client.setex(
                f"code_analysis:{agent_name}:{Path(file_path).stem}",
                3600,  # 1 hour expiry
                json.dumps(analysis)
            )
            
            return analysis
        
        return {}
    
    def _fallback_analysis(self, file_path: str) -> Dict:
        """Fallback analysis using AST and basic checks"""
        import ast
        import autopep8
        
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Basic analysis
        analysis = {
            'lines': len(code.splitlines()),
            'functions': [],
            'classes': [],
            'imports': [],
            'issues': []
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['functions'].append(node.name)
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append(node.name)
                elif isinstance(node, ast.Import):
                    analysis['imports'].extend([alias.name for alias in node.names])
                    
            # Check style with autopep8
            fixed_code = autopep8.fix_code(code)
            if fixed_code != code:
                analysis['issues'].append({
                    'type': 'style',
                    'message': 'Code style can be improved'
                })
                
        except SyntaxError as e:
            analysis['issues'].append({
                'type': 'syntax',
                'message': str(e)
            })
            
        return analysis
    
    def create_enhanced_daemon(self, daemon_spec: Dict) -> str:
        """Create an enhanced daemon using eigencode or fallback"""
        if self.eigencode_available:
            # Use eigencode to generate optimized daemon
            result = subprocess.run([
                'eigencode', 'generate',
                '--type', 'daemon',
                '--spec', json.dumps(daemon_spec)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout
        
        # Fallback daemon template
        return self._generate_daemon_fallback(daemon_spec)
    
    def _generate_daemon_fallback(self, spec: Dict) -> str:
        """Generate daemon code without eigencode"""
        template = f'''#!/usr/bin/env python3
"""
{spec.get('name', 'Unknown')} Daemon
{spec.get('description', 'Auto-generated daemon')}
"""
import time
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting {spec.get('name', 'daemon')}...")
    
    while True:
        try:
            # Main daemon logic
            {spec.get('logic', 'pass')}
            
            # Log activity
            logger.info(f"[{{datetime.now()}}] Daemon cycle complete")
            
        except Exception as e:
            logger.error(f"Daemon error: {{e}}")
            
        time.sleep({spec.get('interval', 300)})

if __name__ == "__main__":
    main()
'''
        return template
    
    async def monitor_agent_consistency(self):
        """Monitor all agents for code consistency"""
        agents = ['sms_engineer', 'phone_engineer', 'memory_engineer', 
                  'test_engineer', 'archaeologist', 'analytics_engineer']
        
        while True:
            consistency_report = {
                'timestamp': datetime.now().isoformat(),
                'agents': {}
            }
            
            for agent in agents:
                # Check recent code from agent
                # Assuming agents scripts are in PROJECT_ROOT/agents/<agent_name>/scripts/
                # This path might need adjustment based on actual project structure
                agent_script_dir = Path("agents") / agent / "scripts" 
                if agent_script_dir.exists() and agent_script_dir.is_dir():
                    agent_files = list(agent_script_dir.glob("*.py"))
                    
                    if agent_files:
                        latest_file = max(agent_files, key=lambda f: f.stat().st_mtime)
                        analysis = self.analyze_agent_code(agent, str(latest_file))
                        
                        consistency_report['agents'][agent] = {
                            'latest_file': str(latest_file),
                            'issues': analysis.get('issues', []),
                            'quality_score': self._calculate_quality_score(analysis)
                        }
                else:
                    consistency_report['agents'][agent] = {
                        'latest_file': None,
                        'issues': [{'type': 'error', 'message': f'Script directory not found: {agent_script_dir}'}],
                        'quality_score': 0
                    }

            # Store report
            # Ensure logs directory is within the project structure defined by start_session.py
            # e.g., PROJECT_ROOT/autonomous-agents/logs/consistency_reports
            report_dir = Path("autonomous-agents") / "logs" / "consistency_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / f"report_{int(time.time())}.json"
            report_path.write_text(json.dumps(consistency_report, indent=2))
            
            await asyncio.sleep(600)  # Check every 10 minutes
    
    def _calculate_quality_score(self, analysis: Dict) -> float:
        """Calculate code quality score from analysis"""
        score = 100.0
        
        # Deduct points for issues
        for issue in analysis.get('issues', []):
            if issue['type'] == 'syntax':
                score -= 50
            elif issue['type'] == 'style':
                score -= 5
            else:
                score -= 10
                
        return max(0, score)

# Daemon specifications
DAEMON_SPECS = {
    'code_quality': {
        'name': 'CodeQualityDaemon',
        'description': 'Monitors and ensures code quality across all agents',
        'interval': 300,
        'logic': '''
            # Analyze recent code changes
            # This logic assumes it's running from a daemon script placed in
            # autonomous-agents/daemons/ and needs to access PROJECT_ROOT/agents/
            from pathlib import Path
            import logging
            logger = logging.getLogger(__name__)

            # Determine project root based on daemon location
            # (autonomous-agents/daemons/script_name.py -> project_root)
            project_root = Path(__file__).resolve().parent.parent.parent 
            agents_base_dir = project_root / "agents"

            recent_files = []
            if agents_base_dir.exists():
                for agent_dir in agents_base_dir.iterdir():
                    if agent_dir.is_dir():
                        scripts_dir = agent_dir / "scripts"
                        if scripts_dir.exists():
                            scripts = list(scripts_dir.glob("*.py"))
                            # Get files modified in the last hour for example
                            # This requires more sophisticated logic than just [-5:]
                            # For simplicity, we'll stick to a placeholder for now.
                            # A more robust way would be to check timestamps or use a queue.
                            recent_files.extend(scripts[-2:]) # Example: last 2 scripts per agent
            
            # Run quality checks
            # This part would typically invoke the EigencodeKarenBridge.analyze_agent_code
            # However, this daemon doesn't have direct access to the bridge instance.
            # It would need to communicate via Redis, an API, or instantiate its own bridge.
            # For now, placeholder:
            if not recent_files:
                logger.info("No recent agent scripts found to analyze.")
            for file in recent_files:
                logger.info(f"CodeQualityDaemon: Analyzing {file.relative_to(project_root)}")
                # Actual analysis call would be needed here
                # e.g., bridge = EigencodeKarenBridge(); bridge.analyze_agent_code("agent_name", str(file))
                # This requires passing agent_name and handling EigencodeKarenBridge instantiation.
'''
    },
    'performance_monitor': {
        'name': 'PerformanceMonitorDaemon',
        'description': 'Monitors system performance and agent efficiency',
        'interval': 600,
        'logic': '''
            import psutil
            import redis
            import json
            from pathlib import Path
            from datetime import datetime
            import logging
            logger = logging.getLogger(__name__)

            # Determine project root and logs directory
            project_root = Path(__file__).resolve().parent.parent.parent
            perf_log_dir = project_root / "autonomous-agents" / "logs" / "performance"
            perf_log_dir.mkdir(parents=True, exist_ok=True)
            metrics_file = perf_log_dir / "metrics.json"

            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Redis metrics
            try:
                r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True) # Use db=1 as in bridge
                redis_info = r.info()
                redis_connected_clients = redis_info.get('connected_clients', 0)
                redis_memory_human = redis_info.get('used_memory_human', 'unknown')
            except redis.exceptions.ConnectionError:
                logger.warning("PerformanceMonitorDaemon: Could not connect to Redis.")
                redis_connected_clients = 'N/A'
                redis_memory_human = 'N/A'

            metrics = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'redis_connected_clients': redis_connected_clients,
                'redis_memory_human': redis_memory_human
            }
            logger.info(f"Performance Metrics: {metrics}")
            
            # Store metrics
            if metrics_file.exists():
                try:
                    data = json.loads(metrics_file.read_text())
                    if not isinstance(data, list): # Ensure it's a list
                        data = []
                except json.JSONDecodeError:
                    data = []
            else:
                data = []
                
            data.append({
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics
            })
            
            # Keep only last 1000 entries
            data = data[-1000:]
            metrics_file.write_text(json.dumps(data, indent=2))
'''
    }
}

if __name__ == "__main__":
    bridge = EigencodeKarenBridge()
    
    # Create enhanced daemons
    # This main block assumes it's run from PROJECT_ROOT.
    # The daemon scripts will be created in PROJECT_ROOT/daemons/
    # If this script itself is moved, these paths might need adjustment.
    daemons_output_dir = Path("daemons") 
    daemons_output_dir.mkdir(exist_ok=True, parents=True)

    for daemon_name, spec in DAEMON_SPECS.items():
        daemon_code = bridge.create_enhanced_daemon(spec)
        daemon_path = daemons_output_dir / f"{spec['name'].lower().replace('daemon', '')}_daemon.py"
        daemon_path.write_text(daemon_code)
        print(f"✅ Created daemon: {daemon_path}")
    
    # Start consistency monitoring (optional, can be run as a separate service)
    print("Starting consistency monitoring (run this separately if needed)...")
    # To run this, you'd typically have a separate script:
    # import asyncio
    # from eigencode_integration import EigencodeKarenBridge
    # bridge = EigencodeKarenBridge()
    # asyncio.run(bridge.monitor_agent_consistency())
    print("--> To run consistency monitor: create a script with the above lines and execute it.")
    # For now, let's just demonstrate a single analysis if eigencode is available
    if bridge.eigencode_available:
        print("\nTesting Eigencode analysis (example):")
        # Create a dummy file to analyze
        dummy_agent_dir = Path("agents/dummy_agent/scripts")
        dummy_agent_dir.mkdir(parents=True, exist_ok=True)
        dummy_file_path = dummy_agent_dir / "dummy_code.py"
        dummy_file_path.write_text("def hello():\n    print('world')\n\nclass MyClass:\n    pass\n")
        
        print(f"Analyzing dummy file: {dummy_file_path}")
        analysis_result = bridge.analyze_agent_code("dummy_agent", str(dummy_file_path))
        if analysis_result:
            print("Analysis successful. Results stored in Redis.")
            print(json.dumps(analysis_result, indent=2))
        else:
            print("Analysis failed or Eigencode returned no output.")
        # dummy_file_path.unlink() # Clean up
    else:
        print("\nEigencode not available, skipping direct analysis test.") 