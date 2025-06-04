#!/usr/bin/env python3
"""
Archaeologist Agent - Share Findings via AgentCommunication
==========================================================

This script demonstrates how the archaeologist agent shares its findings
with other agents in the Karen AI system using the AgentCommunication framework.

Run this script to broadcast archaeological discoveries to other agents.
"""

import sys
import os
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from agent_communication import AgentCommunication
except ImportError as e:
    print(f"Error importing AgentCommunication: {e}")
    print("Make sure Redis is available and the agent_communication module is accessible")
    sys.exit(1)

def main():
    """Share archaeological findings with other agents."""
    
    # Initialize agent communication
    comm = AgentCommunication('archaeologist')
    
    print("🏛️  Archaeologist Agent - Sharing Findings")
    print("=" * 50)
    
    # Update status to indicate sharing phase
    comm.update_status('sharing_findings', 90, {
        'phase': 'broadcasting_discoveries',
        'findings_count': 5,
        'timestamp': datetime.now().isoformat()
    })
    
    # 1. Share Email Processing Flow Discovery
    comm.share_knowledge('email_processing_flow', {
        'discovery_type': 'system_architecture',
        'component': 'email_processing_pipeline',
        'entry_point': 'src/celery_app.py:check_secretary_emails_task',
        'frequency': 'every_2_minutes',
        'flow_stages': [
            'celery_beat_scheduler',
            'communication_agent_initialization', 
            'gmail_api_fetch',
            'handyman_response_engine_classification',
            'llm_gemini_response_generation',
            'calendar_integration_check',
            'reply_sending',
            'label_processing'
        ],
        'critical_files': [
            'src/celery_app.py',
            'src/communication_agent/agent.py',
            'src/email_client.py',
            'src/handyman_response_engine.py',
            'src/llm_client.py'
        ],
        'dual_email_system': {
            'sending_account': 'karensecretaryai@gmail.com',
            'monitoring_account': 'hello@757handy.com',
            'token_files': ['gmail_token_karen.json', 'gmail_token_monitor.json']
        }
    })
    
    # 2. Share OAuth Architecture Discovery
    comm.share_knowledge('oauth_architecture', {
        'discovery_type': 'authentication_system',
        'pattern': 'oauth2_token_management',
        'auto_refresh_mechanism': True,
        'project_relative_paths': True,
        'error_recovery': 'comprehensive_with_admin_notification',
        'token_files': {
            'gmail_karen': 'gmail_token_karen.json',
            'gmail_monitor': 'gmail_token_monitor.json',
            'calendar': 'gmail_token_hello_calendar.json',
            'credentials': 'credentials.json'
        },
        'scopes_required': {
            'gmail': ['gmail.send', 'gmail.compose', 'gmail.readonly', 'gmail.modify'],
            'calendar': ['calendar.readonly', 'calendar.events']
        },
        'critical_methods': [
            '_load_and_refresh_credentials',
            '_save_credentials',
            '_load_client_config'
        ]
    })
    
    # 3. Share Coding Patterns Discovery
    comm.share_knowledge('coding_patterns', {
        'discovery_type': 'development_patterns',
        'error_handling_pattern': 'multi_level_with_admin_notification',
        'logging_pattern': 'structured_context_aware_debug_level',
        'async_integration': 'asyncio_to_thread_bridge',
        'configuration_management': 'early_env_loading_for_celery',
        'service_client_pattern': 'oauth_with_graceful_degradation',
        'email_processing_state': 'gmail_label_based_tracking',
        'admin_notification_triggers': [
            'oauth_refresh_failures',
            'api_quota_exceeded',
            'unexpected_exceptions',
            'email_processing_failures'
        ],
        'special_markers': {
            'logging': 'योग prefix for visibility',
            'debug': 'PRINT_DEBUG for critical checkpoints',
            'processed_emails': 'Karen_Processed label'
        }
    })
    
    # 4. Share Critical Dependencies Discovery
    comm.share_knowledge('system_dependencies', {
        'discovery_type': 'infrastructure_requirements',
        'external_services': {
            'redis': 'celery_message_broker_and_agent_communication',
            'gmail_api': 'email_operations_with_quotas',
            'calendar_api': 'appointment_scheduling',
            'gemini_api': 'ai_response_generation'
        },
        'database_files': {
            'celery_beat': 'celerybeat-schedule.sqlite3',
            'agent_status': 'in_memory_task_manager'
        },
        'monitoring_tasks': {
            'celery_logs': 'every_15_minutes',
            'redis_queues': 'every_10_minutes', 
            'gmail_quotas': 'every_12_hours'
        },
        'rate_limits': {
            'gmail_api': '250_quota_units_per_user_per_second',
            'email_check_frequency': 'every_2_minutes_safe_for_quotas'
        }
    })
    
    # 5. Share DO NOT MODIFY List
    comm.share_knowledge('critical_files_warning', {
        'discovery_type': 'system_safety',
        'danger_level': 'CRITICAL',
        'never_modify': [
            'gmail_token_*.json',
            'credentials.json',
            '.env',
            'src/celery_app.py',
            'src/email_client.py',
            'src/communication_agent/agent.py'
        ],
        'modify_with_extreme_caution': [
            'src/llm_system_prompt.txt',
            'src/config.py',
            'src/calendar_client.py',
            'src/task_manager_agent.py'
        ],
        'breaking_changes_impact': 'stops_customer_email_processing',
        'recovery_procedures': {
            'oauth_tokens': 'run_setup_scripts',
            'environment_vars': 'check_config_py_for_required_names',
            'celery_tasks': 'verify_redis_and_restart_processes'
        }
    })
    
    # Send notifications to specific agents
    agents_to_notify = ['sms_engineer', 'phone_engineer', 'memory_engineer', 'test_engineer']
    
    for agent in agents_to_notify:
        comm.send_message(agent, 'archaeological_report_available', {
            'report_type': 'complete_system_analysis',
            'findings_location': 'autonomous-agents/shared-knowledge/',
            'critical_discoveries': [
                'email_processing_flow_mapped',
                'oauth_architecture_documented', 
                'coding_patterns_identified',
                'do_not_modify_list_created',
                'templates_generated'
            ],
            'documentation_files': [
                'karen-architecture.md',
                'DO-NOT-MODIFY-LIST.md',
                'templates/new_agent_template.py',
                'templates/service_client_template.py',
                'templates/agent_communication_template.py'
            ],
            'next_steps': 'consult_shared_knowledge_before_making_changes',
            'safety_warning': 'karen_is_production_system_handling_real_customers'
        })
    
    # Send special message to orchestrator (if exists)
    comm.send_message('orchestrator', 'system_architecture_mapped', {
        'archaeologist_status': 'mission_complete',
        'system_understanding': 'comprehensive',
        'architecture_documentation': 'autonomous-agents/shared-knowledge/karen-architecture.md',
        'safety_documentation': 'autonomous-agents/shared-knowledge/DO-NOT-MODIFY-LIST.md', 
        'extension_templates': 'autonomous-agents/shared-knowledge/templates/',
        'key_insights': {
            'email_processing': 'celery_based_every_2_minutes',
            'dual_email_system': 'karen_sends_monitor_receives',
            'oauth_architecture': 'automatic_refresh_with_fallbacks',
            'agent_communication': 'redis_based_missing_implementation',
            'critical_constraint': 'production_system_serving_customers'
        },
        'recommendations': [
            'implement_agent_communication_from_template',
            'establish_change_review_process',
            'create_staging_environment_for_testing',
            'monitor_api_quotas_proactively'
        ]
    })
    
    # Final status update
    comm.update_status('completed', 100, {
        'phase': 'archaeological_mission_complete',
        'findings_shared': True,
        'documentation_created': True,
        'templates_generated': True,
        'agents_notified': len(agents_to_notify) + 1,  # +1 for orchestrator
        'completion_time': datetime.now().isoformat()
    })
    
    print("\n✅ Archaeological findings successfully shared with all agents!")
    print(f"📋 Notified {len(agents_to_notify) + 1} agents")
    print("📚 Documentation available in autonomous-agents/shared-knowledge/")
    print("⚠️  Critical safety information in DO-NOT-MODIFY-LIST.md")
    print("\n🏛️  Archaeologist mission complete. System architecture preserved for posterity.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Archaeological sharing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during archaeological sharing: {e}")
        import traceback
        traceback.print_exc()