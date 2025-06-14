#!/usr/bin/env python3
"""
Alternative Eigencode Implementation for Karen AI
Provides code analysis and monitoring capabilities when official Eigencode is not available.
"""

import json
import os
import sys
import time
import ast
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KarenEigencode:
    """Alternative Eigencode implementation for Karen AI multi-agent system"""
    
    def __init__(self, config_file: str = "eigencode.config.json"):
        """Initialize with configuration"""
        self.config_file = config_file
        self.config = self._load_config()
        self.daemon_running = False
        self.analysis_results = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found")
            return self._default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "project": {"name": "karen-ai"},
            "language": "python",
            "style": {"line_length": 100},
            "analysis": {"depth": "comprehensive"},
            "daemons": {"interval": 300},
            "exclude": ["__pycache__", ".git", "node_modules"]
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content, filename=file_path)
            
            # Analyze the file
            analysis = {
                "file": file_path,
                "timestamp": datetime.now().isoformat(),
                "metrics": self._calculate_metrics(content, tree),
                "issues": self._find_issues(content, tree),
                "suggestions": self._generate_suggestions(content, tree),
                "agent_patterns": self._analyze_agent_patterns(content, file_path)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {"file": file_path, "error": str(e)}
    
    def _calculate_metrics(self, content: str, tree: ast.AST) -> Dict[str, Any]:
        """Calculate code metrics"""
        lines = content.split('\n')
        
        # Count different elements
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        imports = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)))
        
        # Calculate complexity (simplified)
        complexity = self._calculate_complexity(tree)
        
        return {
            "lines_of_code": len(lines),
            "blank_lines": sum(1 for line in lines if not line.strip()),
            "comment_lines": sum(1 for line in lines if line.strip().startswith('#')),
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "complexity": complexity,
            "docstring_coverage": self._calculate_docstring_coverage(tree)
        }
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity (simplified)"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
                
        return complexity
    
    def _calculate_docstring_coverage(self, tree: ast.AST) -> float:
        """Calculate docstring coverage percentage"""
        total_functions = 0
        documented_functions = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                total_functions += 1
                if (ast.get_docstring(node) is not None):
                    documented_functions += 1
        
        if total_functions == 0:
            return 100.0
        
        return (documented_functions / total_functions) * 100
    
    def _find_issues(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """Find potential issues in code"""
        issues = []
        lines = content.split('\n')
        
        # Check line length
        max_length = self.config.get("style", {}).get("line_length", 100)
        for i, line in enumerate(lines, 1):
            if len(line) > max_length:
                issues.append({
                    "type": "style",
                    "severity": "warning",
                    "line": i,
                    "message": f"Line too long ({len(line)} > {max_length})",
                    "suggestion": "Break long line into multiple lines"
                })
        
        # Check for missing docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if ast.get_docstring(node) is None:
                    issues.append({
                        "type": "documentation",
                        "severity": "info",
                        "line": node.lineno,
                        "message": f"Missing docstring for {node.name}",
                        "suggestion": "Add docstring to document purpose and parameters"
                    })
        
        # Check for TODO/FIXME comments
        for i, line in enumerate(lines, 1):
            if 'TODO' in line or 'FIXME' in line:
                issues.append({
                    "type": "maintenance",
                    "severity": "info",
                    "line": i,
                    "message": "TODO/FIXME comment found",
                    "suggestion": "Address pending task or remove comment"
                })
        
        return issues
    
    def _generate_suggestions(self, content: str, tree: ast.AST) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Check for agent patterns
        if "class" in content and "Agent" in content:
            suggestions.append("Consider implementing consistent agent interface patterns")
        
        if "def process_" in content or "def handle_" in content:
            suggestions.append("Consider adding error handling and logging to processing methods")
        
        if "redis" in content.lower() or "celery" in content.lower():
            suggestions.append("Ensure proper connection handling and graceful degradation")
        
        return suggestions
    
    def _analyze_agent_patterns(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze agent-specific patterns"""
        patterns = {
            "is_agent": False,
            "communication_patterns": [],
            "state_management": False,
            "error_handling": False
        }
        
        # Check if this is an agent file
        if "agent" in file_path.lower() or "Agent" in content:
            patterns["is_agent"] = True
        
        # Check for communication patterns
        if "send_message" in content or "receive_message" in content:
            patterns["communication_patterns"].append("message_handling")
        
        if "inbox" in content or "outbox" in content:
            patterns["communication_patterns"].append("inbox_outbox")
        
        # Check for state management
        if "state" in content.lower() and ("get_state" in content or "set_state" in content):
            patterns["state_management"] = True
        
        # Check for error handling
        if "try:" in content and "except" in content:
            patterns["error_handling"] = True
        
        return patterns
    
    def analyze_project(self) -> Dict[str, Any]:
        """Analyze entire project"""
        logger.info("Starting project analysis...")
        
        results = {
            "project": self.config.get("project", {}),
            "timestamp": datetime.now().isoformat(),
            "files": [],
            "summary": {},
            "agent_analysis": {}
        }
        
        # Get files to analyze
        src_dir = self.config.get("structure", {}).get("src_dir", "src/")
        python_files = list(Path(src_dir).rglob("*.py"))
        
        # Add agent files
        agent_files = self.config.get("agents", {}).get("monitor", [])
        for agent_file in agent_files:
            if Path(agent_file).exists():
                python_files.append(Path(agent_file))
        
        # Analyze each file
        total_metrics = {
            "total_files": 0,
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_issues": 0
        }
        
        for file_path in python_files:
            if self._should_exclude(str(file_path)):
                continue
                
            analysis = self.analyze_file(str(file_path))
            results["files"].append(analysis)
            
            # Aggregate metrics
            if "metrics" in analysis:
                metrics = analysis["metrics"]
                total_metrics["total_files"] += 1
                total_metrics["total_lines"] += metrics.get("lines_of_code", 0)
                total_metrics["total_functions"] += metrics.get("functions", 0)
                total_metrics["total_classes"] += metrics.get("classes", 0)
                total_metrics["total_issues"] += len(analysis.get("issues", []))
        
        results["summary"] = total_metrics
        results["agent_analysis"] = self._analyze_agent_system(results["files"])
        
        logger.info(f"Analysis complete: {total_metrics['total_files']} files analyzed")
        return results
    
    def _should_exclude(self, file_path: str) -> bool:
        """Check if file should be excluded"""
        exclude_patterns = self.config.get("exclude", [])
        for pattern in exclude_patterns:
            if pattern in file_path:
                return True
        return False
    
    def _analyze_agent_system(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze multi-agent system patterns"""
        agent_analysis = {
            "agent_files": 0,
            "communication_files": 0,
            "state_management_files": 0,
            "patterns": {
                "consistent_interfaces": True,
                "proper_error_handling": True,
                "communication_standards": True
            },
            "recommendations": []
        }
        
        for analysis in file_analyses:
            if "agent_patterns" in analysis:
                patterns = analysis["agent_patterns"]
                
                if patterns["is_agent"]:
                    agent_analysis["agent_files"] += 1
                
                if patterns["communication_patterns"]:
                    agent_analysis["communication_files"] += 1
                
                if patterns["state_management"]:
                    agent_analysis["state_management_files"] += 1
                
                if not patterns["error_handling"]:
                    agent_analysis["patterns"]["proper_error_handling"] = False
        
        # Generate recommendations
        if agent_analysis["agent_files"] > 0:
            agent_analysis["recommendations"].append(
                "Multi-agent system detected. Ensure consistent communication patterns."
            )
        
        if not agent_analysis["patterns"]["proper_error_handling"]:
            agent_analysis["recommendations"].append(
                "Some agents lack proper error handling. Consider adding try-catch blocks."
            )
        
        return agent_analysis
    
    def save_analysis(self, results: Dict[str, Any], output_file: str = "reports/eigencode_analysis.json"):
        """Save analysis results"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Analysis saved to {output_file}")
    
    def start_daemon(self):
        """Start monitoring daemon"""
        logger.info("Starting Eigencode daemon...")
        self.daemon_running = True
        
        def monitor_loop():
            while self.daemon_running:
                try:
                    results = self.analyze_project()
                    self.save_analysis(results)
                    
                    # Check for critical issues
                    self._check_critical_issues(results)
                    
                    # Wait for next analysis
                    time.sleep(self.config.get("daemons", {}).get("interval", 300))
                    
                except Exception as e:
                    logger.error(f"Daemon error: {e}")
                    time.sleep(60)  # Wait before retrying
        
        daemon_thread = threading.Thread(target=monitor_loop, daemon=True)
        daemon_thread.start()
        logger.info("Daemon started successfully")
    
    def stop_daemon(self):
        """Stop monitoring daemon"""
        self.daemon_running = False
        logger.info("Daemon stopped")
    
    def _check_critical_issues(self, results: Dict[str, Any]):
        """Check for critical issues and alert"""
        critical_issues = []
        
        for file_analysis in results.get("files", []):
            for issue in file_analysis.get("issues", []):
                if issue.get("severity") == "error":
                    critical_issues.append(issue)
        
        if critical_issues:
            logger.warning(f"Found {len(critical_issues)} critical issues")
    
    def generate_report(self, output_file: str = "reports/eigencode_report.md"):
        """Generate human-readable report"""
        results = self.analyze_project()
        
        report = f"""# Karen AI - Eigencode Analysis Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Project Summary
- **Project**: {results.get('project', {}).get('name', 'karen-ai')}
- **Files Analyzed**: {results.get('summary', {}).get('total_files', 0)}
- **Total Lines**: {results.get('summary', {}).get('total_lines', 0)}
- **Functions**: {results.get('summary', {}).get('total_functions', 0)}
- **Classes**: {results.get('summary', {}).get('total_classes', 0)}
- **Issues Found**: {results.get('summary', {}).get('total_issues', 0)}

## Agent System Analysis
- **Agent Files**: {results.get('agent_analysis', {}).get('agent_files', 0)}
- **Communication Files**: {results.get('agent_analysis', {}).get('communication_files', 0)}
- **State Management Files**: {results.get('agent_analysis', {}).get('state_management_files', 0)}

## Recommendations
"""
        
        recommendations = results.get('agent_analysis', {}).get('recommendations', [])
        for rec in recommendations:
            report += f"- {rec}\n"
        
        report += "\n## File Details\n"
        
        for file_analysis in results.get('files', []):
            if file_analysis.get('error'):
                continue
                
            file_path = file_analysis.get('file', 'Unknown')
            metrics = file_analysis.get('metrics', {})
            issues = file_analysis.get('issues', [])
            
            report += f"\n### {file_path}\n"
            report += f"- Lines: {metrics.get('lines_of_code', 0)}\n"
            report += f"- Functions: {metrics.get('functions', 0)}\n"
            report += f"- Classes: {metrics.get('classes', 0)}\n"
            report += f"- Complexity: {metrics.get('complexity', 0)}\n"
            report += f"- Docstring Coverage: {metrics.get('docstring_coverage', 0):.1f}%\n"
            
            if issues:
                report += f"- Issues: {len(issues)}\n"
                for issue in issues[:3]:  # Show first 3 issues
                    report += f"  - Line {issue.get('line', 0)}: {issue.get('message', '')}\n"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Report generated: {output_file}")
        return output_file

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Karen AI Eigencode Alternative")
    parser.add_argument('command', choices=['analyze', 'daemon', 'stop', 'status', 'report'],
                       help='Command to execute')
    parser.add_argument('--config', default='eigencode.config.json',
                       help='Configuration file path')
    parser.add_argument('--output', default='reports/eigencode_analysis.json',
                       help='Output file path')
    
    args = parser.parse_args()
    
    eigencode = KarenEigencode(args.config)
    
    if args.command == 'analyze':
        results = eigencode.analyze_project()
        eigencode.save_analysis(results, args.output)
        print(f"✓ Analysis complete. Results saved to {args.output}")
        
    elif args.command == 'daemon':
        eigencode.start_daemon()
        print("✓ Daemon started. Press Ctrl+C to stop.")
        try:
            while eigencode.daemon_running:
                time.sleep(1)
        except KeyboardInterrupt:
            eigencode.stop_daemon()
            
    elif args.command == 'report':
        report_file = eigencode.generate_report()
        print(f"✓ Report generated: {report_file}")
        
    elif args.command == 'status':
        print("📊 Karen AI Eigencode Status:")
        print(f"Configuration: {args.config}")
        print(f"Project: {eigencode.config.get('project', {}).get('name', 'karen-ai')}")
        print("✓ Alternative Eigencode implementation ready")

if __name__ == "__main__":
    main()