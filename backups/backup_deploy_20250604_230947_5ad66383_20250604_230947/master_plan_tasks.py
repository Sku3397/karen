"""
Master plan task generator for Karen AI development
"""
import json
import time
from datetime import datetime
from pathlib import Path

class MasterPlanTaskGenerator:
    def __init__(self):
        self.phases = {
            'phase_1': {
                'name': 'Core Communication',
                'duration_hours': 2,
                'features': {
                    'sms_two_way': {
                        'tasks': [
                            'implement_sms_conversation_threading',
                            'add_sms_template_system',
                            'create_sms_appointment_confirmations',
                            'implement_sms_quick_replies',
                            'add_sms_scheduling_integration'
                        ],
                        'agent': 'sms_engineer'
                    },
                    'phone_system': {
                        'tasks': [
                            'implement_twilio_voice_webhook',
                            'create_voice_answering_system',
                            'add_voicemail_transcription',
                            'implement_call_routing_logic',
                            'create_call_scheduling_system'
                        ],
                        'agent': 'phone_engineer'
                    }
                }
            },
            'phase_2': {
                'name': 'Intelligence & Memory',
                'duration_hours': 1,
                'features': {
                    'smart_memory': {
                        'tasks': [
                            'implement_conversation_embeddings',
                            'create_customer_preference_learning',
                            'add_cross_medium_context_linking',
                            'implement_important_dates_tracking',
                            'create_memory_search_system'
                        ],
                        'agent': 'memory_engineer'
                    },
                    'scheduling_intelligence': {
                        'tasks': [
                            'implement_multi_calendar_coordination',
                            'add_travel_time_calculation',
                            'create_buffer_time_management',
                            'implement_conflict_resolution',
                            'add_automatic_rescheduling'
                        ],
                        'agent': 'orchestrator'
                    }
                }
            },
            'phase_3': {
                'name': 'Business Operations',
                'duration_hours': 1,
                'features': {
                    'customer_management': {
                        'tasks': [
                            'create_customer_profile_system',
                            'implement_service_history_tracking',
                            'add_vip_customer_features',
                            'create_complaint_management_system',
                            'implement_customer_analytics'
                        ],
                        'agent': 'memory_engineer'
                    },
                    'financial_features': {
                        'tasks': [
                            'implement_invoice_generation',
                            'add_payment_processing_integration',
                            'create_quote_template_system',
                            'implement_expense_tracking',
                            'add_basic_bookkeeping_features'
                        ],
                        'agent': 'sms_engineer'
                    }
                }
            },
            'phase_4': {
                'name': 'Advanced Features',
                'duration_hours': 1,
                'features': {
                    'proactive_assistance': {
                        'tasks': [
                            'implement_daily_briefing_generation',
                            'add_weather_based_scheduling',
                            'create_maintenance_reminders',
                            'implement_seasonal_suggestions',
                            'add_special_date_reminders'
                        ],
                        'agent': 'orchestrator'
                    },
                    'multi_channel': {
                        'tasks': [
                            'create_unified_inbox_system',
                            'implement_smart_routing_logic',
                            'add_escalation_procedures',
                            'create_after_hours_handling',
                            'implement_vacation_mode'
                        ],
                        'agent': 'orchestrator'
                    }
                }
            },
            'phase_5': {
                'name': 'Human-Like Excellence',
                'duration_hours': 1,
                'features': {
                    'personality': {
                        'tasks': [
                            'implement_consistent_personality',
                            'add_phone_etiquette_system',
                            'create_empathy_responses',
                            'implement_small_talk_capability',
                            'add_cultural_awareness'
                        ],
                        'agent': 'archaeologist'
                    },
                    'advanced_integration': {
                        'tasks': [
                            'implement_crm_sync_system',
                            'add_calendar_app_integration',
                            'create_accounting_connectors',
                            'implement_marketing_automation',
                            'add_review_management'
                        ],
                        'agent': 'memory_engineer'
                    }
                }
            }
        }
        
        # Testing tasks run continuously
        self.continuous_tasks = {
            'test_engineer': [
                'test_email_system_health',
                'test_sms_functionality',
                'test_phone_system_integration',
                'test_memory_retrieval_accuracy',
                'test_scheduling_conflicts',
                'test_payment_processing',
                'test_customer_data_integrity',
                'run_integration_test_suite',
                'generate_quality_report',
                'test_system_performance'
            ]
        }
        
    def generate_phase_tasks(self, phase_num, current_time):
        """Generate all tasks for a specific phase"""
        phase_key = f'phase_{phase_num}'
        if phase_key not in self.phases:
            return []
            
        phase = self.phases[phase_key]
        tasks = []
        
        for feature_name, feature_data in phase['features'].items():
            for i, task_type in enumerate(feature_data['tasks']):
                task = {
                    'id': f"{phase_key}_{feature_name}_{task_type}_{current_time.timestamp()}",
                    'agent': feature_data['agent'],
                    'type': task_type,
                    'description': f"Phase {phase_num}: {task_type.replace('_', ' ').title()}",
                    'phase': phase_num,
                    'feature': feature_name,
                    'priority': 1 if 'critical' in task_type else 2,
                    'created': current_time.isoformat(),
                    'status': 'pending',
                    'estimated_duration': 600  # 10 minutes per task
                }
                tasks.append(task)
                
        return tasks
        
    def generate_test_tasks(self, current_time):
        """Generate continuous testing tasks"""
        tasks = []
        for task_type in self.continuous_tasks['test_engineer']:
            task = {
                'id': f"test_{task_type}_{current_time.timestamp()}",
                'agent': 'test_engineer',
                'type': task_type,
                'description': f"Continuous: {task_type.replace('_', ' ').title()}",
                'phase': 'continuous',
                'priority': 1 if 'email' in task_type else 2,
                'created': current_time.isoformat(),
                'status': 'pending'
            }
            tasks.append(task)
        return tasks
        
    def create_task_instruction(self, task):
        """Create detailed instruction for each task"""
        instructions = {
            'implement_sms_conversation_threading': '''
# Implement SMS Conversation Threading
Create a conversation management system in src/sms_conversation_manager.py:
- Track conversation threads by phone number
- Maintain conversation context
- Link related messages together
- Store conversation state
- Implement thread timeout handling
''',
            'implement_twilio_voice_webhook': '''
# Implement Twilio Voice Webhook Handler
Create src/voice_webhook_handler.py:
- FastAPI endpoint for Twilio webhooks
- Handle incoming calls with TwiML
- Route calls based on business hours
- Implement IVR menu system
- Log all call events
''',
            'implement_conversation_embeddings': '''
# Implement Conversation Embeddings
Enhance src/memory_client.py:
- Generate embeddings for all conversations
- Store in ChromaDB with metadata
- Implement semantic search
- Add relevance scoring
- Create context retrieval methods
''',
            # Add more task-specific instructions...
        }
        
        base_instruction = f'''
import sys
sys.path.append('.')
from claude_helpers import {task['agent']}_helper as helper

# Task: {task['type']}
# Phase: {task.get('phase', 'N/A')}
# Description: {task['description']}

helper.update_status('working', 20, {{'task': '{task['id']}', 'phase': {task.get('phase', 0)}}})

# Implementation for {task['type']}
{instructions.get(task['type'], f"# Implement {task['type']}")}

# Mark progress
helper.update_status('implementing', 60, {{'task': '{task['id']}', 'progress': 'coding'}})

# Create necessary files and implementation
# [Implementation code here]

# Update completion
helper.update_status('testing', 90, {{'task': '{task['id']}', 'status': 'validating'}})

# Final status
helper.update_status('completed', 100, {{'task': '{task['id']}', 'phase': {task.get('phase', 0)}, 'feature': '{task.get('feature', 'core')}''}})
print(f"Completed task: {task['id']}")
'''
        return base_instruction

    def save_master_plan(self):
        """Save the complete development plan"""
        plan = {
            'created': datetime.now().isoformat(),
            'total_phases': len(self.phases),
            'estimated_hours': 6,
            'phases': self.phases,
            'continuous_tasks': self.continuous_tasks,
            'total_features': sum(len(p['features']) for p in self.phases.values()),
            'total_tasks': sum(
                len(f['tasks']) 
                for p in self.phases.values() 
                for f in p['features'].values()
            )
        }
        
        with open('master_development_plan.json', 'w') as f:
            json.dump(plan, f, indent=2)
            
        return plan

# Generate and save the master plan
if __name__ == '__main__':
    generator = MasterPlanTaskGenerator()
    plan = generator.save_master_plan()
    print(f"Master plan created: {plan['total_tasks']} tasks across {plan['total_phases']} phases")

