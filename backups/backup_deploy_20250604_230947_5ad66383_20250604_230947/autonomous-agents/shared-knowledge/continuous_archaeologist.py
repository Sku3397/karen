#!/usr/bin/env python3
"""
Continuous Archaeologist - Autonomous code pattern analysis and documentation
Runs continuously to analyze Karen codebase and share findings with other agents
"""

import sys
import time
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContinuousArchaeologist:
    """Autonomous code analysis agent that runs continuously"""
    
    def __init__(self):
        self.agent_name = 'archaeologist'
        self.project_root = Path(__file__).parent.parent.parent
        self.comm_dir = self.project_root / 'autonomous-agents' / 'communication'
        self.src_dir = self.project_root / 'src'
        self.docs_dir = self.project_root / 'autonomous-agents' / 'shared-knowledge' / 'docs'
        self.templates_dir = self.project_root / 'autonomous-agents' / 'shared-knowledge' / 'templates'
        
        # Ensure directories exist
        self.ensure_directories()
        
        # Pattern analysis cache
        self.last_analysis = {}
        self.analysis_count = 0
        
        logger.info(f"ContinuousArchaeologist initialized for {self.agent_name}")
    
    def ensure_directories(self):
        """Create required directories"""
        self.comm_dir.mkdir(parents=True, exist_ok=True)
        (self.comm_dir / 'status').mkdir(exist_ok=True)
        (self.comm_dir / 'knowledge-base').mkdir(exist_ok=True)
        (self.comm_dir / 'inbox' / 'sms_engineer').mkdir(parents=True, exist_ok=True)
        (self.comm_dir / 'inbox' / 'phone_engineer').mkdir(parents=True, exist_ok=True)
        (self.comm_dir / 'inbox' / 'memory_engineer').mkdir(parents=True, exist_ok=True)
        (self.comm_dir / 'inbox' / 'test_engineer').mkdir(parents=True, exist_ok=True)
        (self.comm_dir / 'inbox' / 'orchestrator').mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def update_status(self, status: str, progress: int, details: Dict[str, Any] = None):
        """Update agent status"""
        try:
            status_data = {
                'agent': self.agent_name,
                'status': status,
                'progress': progress,
                'details': details or {},
                'timestamp': datetime.now().isoformat(),
                'analysis_count': self.analysis_count
            }
            
            status_file = self.comm_dir / 'status' / f'{self.agent_name}_status.json'
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            
            logger.info(f"Status updated: {status} ({progress}%) - {details}")
            
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
    
    def send_message(self, to_agent: str, message_type: str, content: Dict[str, Any]):
        """Send message to another agent"""
        try:
            message = {
                'from': self.agent_name,
                'to': to_agent,
                'type': message_type,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'analysis_cycle': self.analysis_count
            }
            
            inbox_path = self.comm_dir / 'inbox' / to_agent
            inbox_path.mkdir(parents=True, exist_ok=True)
            
            filename = f"{self.agent_name}_to_{to_agent}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
            message_file = inbox_path / filename
            
            with open(message_file, 'w') as f:
                json.dump(message, f, indent=2)
            
            logger.info(f"Message sent to {to_agent}: {message_type}")
            
        except Exception as e:
            logger.error(f"Failed to send message to {to_agent}: {e}")
    
    def share_knowledge(self, knowledge_type: str, content: Dict[str, Any]):
        """Share knowledge with all agents"""
        try:
            knowledge = {
                'contributor': self.agent_name,
                'type': knowledge_type,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'analysis_cycle': self.analysis_count
            }
            
            kb_dir = self.comm_dir / 'knowledge-base'
            filename = f"{knowledge_type}_{self.agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
            
            with open(kb_dir / filename, 'w') as f:
                json.dump(knowledge, f, indent=2)
            
            logger.info(f"Knowledge shared: {knowledge_type}")
            
        except Exception as e:
            logger.error(f"Failed to share knowledge: {e}")
    
    def scan_source_files(self) -> List[Path]:
        """Scan for Python source files"""
        src_files = []
        
        if not self.src_dir.exists():
            logger.warning(f"Source directory not found: {self.src_dir}")
            return src_files
        
        for file_path in self.src_dir.rglob('*.py'):
            if file_path.is_file() and 'test' not in str(file_path).lower():
                src_files.append(file_path)
        
        logger.info(f"Found {len(src_files)} Python source files")
        return src_files
    
    def analyze_file_patterns(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single file for patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            patterns = {
                'file_path': str(file_path),
                'size': len(content),
                'lines': len(content.splitlines()),
                'patterns_found': []
            }
            
            # Error handling patterns
            if re.search(r'try:\s*\n.*except', content, re.MULTILINE | re.DOTALL):
                patterns['patterns_found'].append('comprehensive_error_handling')
                if 'exc_info=True' in content:
                    patterns['patterns_found'].append('detailed_exception_logging')
                if 'admin_email' in content or 'send_admin' in content:
                    patterns['patterns_found'].append('admin_notification_on_error')
            
            # API Client patterns
            if re.search(r'class.*Client.*:', content):
                patterns['patterns_found'].append('api_client_class')
                if 'oauth' in content.lower() or 'credentials' in content.lower():
                    patterns['patterns_found'].append('oauth_authentication')
                if 'refresh' in content.lower() and 'token' in content.lower():
                    patterns['patterns_found'].append('token_refresh_mechanism')
            
            # Celery task patterns
            if '@celery_app.task' in content:
                patterns['patterns_found'].append('celery_task_definition')
                if 'bind=True' in content:
                    patterns['patterns_found'].append('celery_task_binding')
                if 'ignore_result=True' in content:
                    patterns['patterns_found'].append('celery_fire_and_forget')
            
            # Agent patterns
            if re.search(r'class.*Agent.*:', content):
                patterns['patterns_found'].append('agent_class')
                if 'update_status' in content:
                    patterns['patterns_found'].append('status_tracking')
                if 'send_message' in content:
                    patterns['patterns_found'].append('inter_agent_communication')
            
            # Async patterns
            if 'asyncio.run' in content:
                patterns['patterns_found'].append('async_sync_bridge')
            if 'await asyncio.to_thread' in content:
                patterns['patterns_found'].append('sync_in_async_context')
            
            # Google API patterns
            if 'from googleapiclient' in content:
                patterns['patterns_found'].append('google_api_integration')
            if 'gmail' in content.lower() and 'service' in content.lower():
                patterns['patterns_found'].append('gmail_api_usage')
            if 'calendar' in content.lower() and 'service' in content.lower():
                patterns['patterns_found'].append('calendar_api_usage')
            
            # Configuration patterns
            if 'os.getenv' in content:
                patterns['patterns_found'].append('environment_variable_usage')
            if 'load_dotenv' in content:
                patterns['patterns_found'].append('dotenv_configuration')
            
            # Logging patterns
            if 'logger = logging.getLogger' in content:
                patterns['patterns_found'].append('module_level_logging')
            if 'logger.error' in content and 'exc_info=True' in content:
                patterns['patterns_found'].append('comprehensive_error_logging')
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return {'file_path': str(file_path), 'error': str(e), 'patterns_found': []}
    
    def analyze_all_patterns(self, src_files: List[Path]) -> Dict[str, Any]:
        """Analyze all files and aggregate patterns"""
        self.update_status('analyzing', 20, {'phase': 'pattern_analysis', 'files_to_analyze': len(src_files)})
        
        all_patterns = {
            'analysis_timestamp': datetime.now().isoformat(),
            'files_analyzed': 0,
            'total_files': len(src_files),
            'pattern_summary': {},
            'file_details': [],
            'top_patterns': []
        }
        
        pattern_counts = {}
        
        for i, file_path in enumerate(src_files):
            file_patterns = self.analyze_file_patterns(file_path)
            all_patterns['file_details'].append(file_patterns)
            all_patterns['files_analyzed'] += 1
            
            # Count pattern occurrences
            for pattern in file_patterns.get('patterns_found', []):
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            # Update progress
            progress = 20 + int((i / len(src_files)) * 50)
            if i % 10 == 0:  # Update every 10 files
                self.update_status('analyzing', progress, {
                    'phase': 'pattern_analysis',
                    'files_processed': i + 1,
                    'total_files': len(src_files)
                })
        
        # Generate pattern summary
        all_patterns['pattern_summary'] = pattern_counts
        all_patterns['top_patterns'] = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return all_patterns
    
    def generate_documentation(self, patterns: Dict[str, Any]):
        """Generate comprehensive pattern documentation"""
        self.update_status('documenting', 75, {'phase': 'documentation_generation'})
        
        # Generate main pattern documentation
        doc_content = f"""# Karen AI Code Patterns Analysis
Generated: {patterns['analysis_timestamp']}
Analysis Cycle: {self.analysis_count}

## Summary
- **Files Analyzed**: {patterns['files_analyzed']}
- **Unique Patterns Found**: {len(patterns['pattern_summary'])}
- **Total Pattern Instances**: {sum(patterns['pattern_summary'].values())}

## Top Patterns by Frequency

"""
        
        for pattern, count in patterns['top_patterns']:
            doc_content += f"- **{pattern.replace('_', ' ').title()}**: {count} files\n"
        
        doc_content += "\n## Pattern Details\n\n"
        
        # Group files by pattern
        pattern_to_files = {}
        for file_detail in patterns['file_details']:
            file_path = file_detail['file_path']
            for pattern in file_detail.get('patterns_found', []):
                if pattern not in pattern_to_files:
                    pattern_to_files[pattern] = []
                pattern_to_files[pattern].append(file_path)
        
        for pattern, files in sorted(pattern_to_files.items()):
            doc_content += f"### {pattern.replace('_', ' ').title()}\n"
            doc_content += f"Found in {len(files)} files:\n"
            for file_path in files[:5]:  # Show first 5 files
                doc_content += f"- `{file_path}`\n"
            if len(files) > 5:
                doc_content += f"- ... and {len(files) - 5} more files\n"
            doc_content += "\n"
        
        # Save documentation
        doc_file = self.docs_dir / 'code_patterns_analysis.md'
        with open(doc_file, 'w') as f:
            f.write(doc_content)
        
        logger.info(f"Documentation generated: {doc_file}")
        
        # Generate JSON summary for agents
        summary_file = self.docs_dir / 'pattern_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(patterns, f, indent=2)
        
        return doc_content
    
    def create_templates(self, patterns: Dict[str, Any]):
        """Create or update templates based on discovered patterns"""
        self.update_status('templating', 85, {'phase': 'template_generation'})
        
        # Find best examples for each pattern type
        api_client_files = []
        celery_task_files = []
        agent_class_files = []
        
        for file_detail in patterns['file_details']:
            patterns_found = file_detail.get('patterns_found', [])
            file_path = file_detail['file_path']
            
            if 'api_client_class' in patterns_found and 'oauth_authentication' in patterns_found:
                api_client_files.append(file_path)
            
            if 'celery_task_definition' in patterns_found and 'celery_task_binding' in patterns_found:
                celery_task_files.append(file_path)
            
            if 'agent_class' in patterns_found and 'status_tracking' in patterns_found:
                agent_class_files.append(file_path)
        
        templates_created = []
        
        # Create enhanced API client template
        if api_client_files:
            try:
                # Use the first good example
                example_file = Path(api_client_files[0])
                if example_file.exists():
                    with open(example_file, 'r') as f:
                        content = f.read()
                    
                    # Create enhanced template
                    template_content = f"""# Enhanced API Client Template
# Generated from: {example_file}
# Analysis cycle: {self.analysis_count}

{content}

# TEMPLATE USAGE:
# 1. Replace class name with your service
# 2. Update API endpoints and methods
# 3. Modify OAuth scopes as needed
# 4. Add service-specific error handling
"""
                    
                    template_file = self.templates_dir / 'enhanced_api_client_template.py'
                    with open(template_file, 'w') as f:
                        f.write(template_content)
                    
                    templates_created.append('enhanced_api_client_template.py')
                    logger.info(f"Created enhanced API client template from {example_file}")
                    
            except Exception as e:
                logger.error(f"Error creating API client template: {e}")
        
        # Create enhanced Celery task template
        if celery_task_files:
            try:
                example_file = Path(celery_task_files[0])
                if example_file.exists():
                    with open(example_file, 'r') as f:
                        content = f.read()
                    
                    template_content = f"""# Enhanced Celery Task Template
# Generated from: {example_file}
# Analysis cycle: {self.analysis_count}

{content}

# TEMPLATE USAGE:
# 1. Replace task name and function
# 2. Update task logic for your use case
# 3. Modify status tracking details
# 4. Add task-specific error handling
"""
                    
                    template_file = self.templates_dir / 'enhanced_celery_task_template.py'
                    with open(template_file, 'w') as f:
                        f.write(template_content)
                    
                    templates_created.append('enhanced_celery_task_template.py')
                    logger.info(f"Created enhanced Celery task template from {example_file}")
                    
            except Exception as e:
                logger.error(f"Error creating Celery task template: {e}")
        
        return templates_created
    
    def share_findings(self, patterns: Dict[str, Any], templates_created: List[str]):
        """Share analysis findings with other agents"""
        self.update_status('sharing', 95, {'phase': 'knowledge_sharing'})
        
        # Share with SMS engineer
        self.send_message('sms_engineer', 'pattern_analysis_update', {
            'analysis_cycle': self.analysis_count,
            'relevant_patterns': {
                'api_client_patterns': patterns['pattern_summary'].get('api_client_class', 0),
                'oauth_patterns': patterns['pattern_summary'].get('oauth_authentication', 0),
                'celery_task_patterns': patterns['pattern_summary'].get('celery_task_definition', 0),
                'error_handling_patterns': patterns['pattern_summary'].get('comprehensive_error_handling', 0)
            },
            'templates_available': templates_created,
            'recommendation': 'Use enhanced templates for SMS service integration'
        })
        
        # Share with phone engineer
        self.send_message('phone_engineer', 'pattern_analysis_update', {
            'analysis_cycle': self.analysis_count,
            'relevant_patterns': {
                'google_api_patterns': patterns['pattern_summary'].get('google_api_integration', 0),
                'async_patterns': patterns['pattern_summary'].get('async_sync_bridge', 0),
                'agent_patterns': patterns['pattern_summary'].get('agent_class', 0)
            },
            'templates_available': templates_created,
            'recommendation': 'Focus on Google Cloud Speech API integration patterns'
        })
        
        # Share with memory engineer
        self.send_message('memory_engineer', 'pattern_analysis_update', {
            'analysis_cycle': self.analysis_count,
            'relevant_patterns': {
                'configuration_patterns': patterns['pattern_summary'].get('environment_variable_usage', 0),
                'logging_patterns': patterns['pattern_summary'].get('module_level_logging', 0),
                'agent_communication': patterns['pattern_summary'].get('inter_agent_communication', 0)
            },
            'templates_available': templates_created,
            'recommendation': 'Implement conversation history management using agent patterns'
        })
        
        # Share comprehensive report with orchestrator
        self.send_message('orchestrator', 'comprehensive_analysis_report', {
            'analysis_cycle': self.analysis_count,
            'summary': {
                'files_analyzed': patterns['files_analyzed'],
                'patterns_discovered': len(patterns['pattern_summary']),
                'templates_created': len(templates_created)
            },
            'top_patterns': patterns['top_patterns'][:5],
            'system_health': self.assess_system_health(patterns),
            'recommendations': self.generate_recommendations(patterns)
        })
        
        # Share knowledge base entry
        self.share_knowledge('continuous_analysis', {
            'cycle': self.analysis_count,
            'timestamp': patterns['analysis_timestamp'],
            'patterns_summary': patterns['pattern_summary'],
            'templates_created': templates_created,
            'files_analyzed': patterns['files_analyzed']
        })
    
    def assess_system_health(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall system health based on patterns"""
        health = {
            'error_handling_coverage': 'good' if patterns['pattern_summary'].get('comprehensive_error_handling', 0) > 10 else 'needs_improvement',
            'oauth_implementation': 'mature' if patterns['pattern_summary'].get('oauth_authentication', 0) > 3 else 'basic',
            'async_readiness': 'good' if patterns['pattern_summary'].get('async_sync_bridge', 0) > 5 else 'limited',
            'agent_coordination': 'implemented' if patterns['pattern_summary'].get('inter_agent_communication', 0) > 3 else 'needs_work'
        }
        return health
    
    def generate_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate system improvement recommendations"""
        recommendations = []
        
        if patterns['pattern_summary'].get('comprehensive_error_handling', 0) < patterns['files_analyzed'] * 0.5:
            recommendations.append("Increase error handling coverage across more files")
        
        if patterns['pattern_summary'].get('module_level_logging', 0) < patterns['files_analyzed'] * 0.7:
            recommendations.append("Add consistent logging to more modules")
        
        if patterns['pattern_summary'].get('agent_class', 0) < 5:
            recommendations.append("Implement more specialized agent classes")
        
        if patterns['pattern_summary'].get('celery_task_definition', 0) < 10:
            recommendations.append("Consider breaking down operations into more Celery tasks")
        
        return recommendations
    
    def run_analysis_cycle(self):
        """Run a single analysis cycle"""
        self.analysis_count += 1
        logger.info(f"Starting analysis cycle {self.analysis_count}")
        
        try:
            # 1. Scan for source files
            self.update_status('scanning', 10, {'phase': 'file_discovery', 'cycle': self.analysis_count})
            src_files = self.scan_source_files()
            
            if not src_files:
                logger.warning("No source files found to analyze")
                return
            
            # 2. Analyze patterns
            patterns = self.analyze_all_patterns(src_files)
            
            # 3. Generate documentation
            self.generate_documentation(patterns)
            
            # 4. Create/update templates
            templates_created = self.create_templates(patterns)
            
            # 5. Share findings
            self.share_findings(patterns, templates_created)
            
            # 6. Complete cycle
            self.update_status('completed', 100, {
                'phase': 'cycle_complete',
                'cycle': self.analysis_count,
                'files_analyzed': patterns['files_analyzed'],
                'patterns_found': len(patterns['pattern_summary']),
                'templates_created': len(templates_created)
            })
            
            logger.info(f"Analysis cycle {self.analysis_count} completed successfully")
            
        except Exception as e:
            logger.error(f"Error in analysis cycle {self.analysis_count}: {e}")
            self.update_status('error', 0, {
                'error': str(e),
                'cycle': self.analysis_count,
                'phase': 'analysis_cycle_failed'
            })
    
    def run_continuous(self, cycle_interval: int = 600):
        """Run continuous analysis loop"""
        logger.info(f"Starting continuous analysis with {cycle_interval}s intervals")
        
        try:
            while True:
                self.run_analysis_cycle()
                
                logger.info(f"Sleeping for {cycle_interval} seconds before next cycle")
                time.sleep(cycle_interval)
                
        except KeyboardInterrupt:
            logger.info("Continuous analysis stopped by user")
            self.update_status('stopped', 100, {
                'reason': 'user_interrupt',
                'total_cycles': self.analysis_count
            })
        except Exception as e:
            logger.error(f"Fatal error in continuous analysis: {e}")
            self.update_status('error', 0, {
                'error': str(e),
                'total_cycles': self.analysis_count,
                'phase': 'continuous_loop_failed'
            })


def main():
    """Main entry point"""
    archaeologist = ContinuousArchaeologist()
    
    # Run a single cycle first
    archaeologist.run_analysis_cycle()
    
    # Then run continuously (commented out for manual control)
    # archaeologist.run_continuous(cycle_interval=600)  # 10 minutes
    
    logger.info("Archaeologist analysis complete")


if __name__ == "__main__":
    main()