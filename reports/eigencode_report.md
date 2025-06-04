# Karen AI - Eigencode Analysis Report

Generated: 2025-06-04 10:41:08

## Project Summary
- **Project**: karen-ai
- **Files Analyzed**: 194
- **Total Lines**: 40517
- **Functions**: 1186
- **Classes**: 261
- **Issues Found**: 1918

## Agent System Analysis
- **Agent Files**: 67
- **Communication Files**: 18
- **State Management Files**: 0

## Recommendations
- Multi-agent system detected. Ensure consistent communication patterns.
- Some agents lack proper error handling. Consider adding try-catch blocks.

## File Details

### src/agent_communication.py
- Lines: 245
- Functions: 9
- Classes: 1
- Complexity: 31
- Docstring Coverage: 90.0%
- Issues: 32
  - Line 13: Line too long (102 > 100)
  - Line 27: Line too long (117 > 100)
  - Line 49: Line too long (114 > 100)

### src/agent_registry.py
- Lines: 32
- Functions: 2
- Classes: 5
- Complexity: 4
- Docstring Coverage: 0.0%
- Issues: 7
  - Line 2: Missing docstring for BaseAgent
  - Line 11: Missing docstring for ScheduleAgent
  - Line 14: Missing docstring for ReminderAgent

### src/ai_responder.py
- Lines: 84
- Functions: 1
- Classes: 0
- Complexity: 9
- Docstring Coverage: 100.0%
- Issues: 12
  - Line 19: Line too long (114 > 100)
  - Line 33: Line too long (105 > 100)
  - Line 36: Line too long (116 > 100)

### src/api.py
- Lines: 34
- Functions: 4
- Classes: 0
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 13: Missing docstring for create_task
  - Line 18: Missing docstring for assign_task
  - Line 25: Missing docstring for update_status

### src/billing_agent.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/business_hours_manager.py
- Lines: 651
- Functions: 23
- Classes: 5
- Complexity: 66
- Docstring Coverage: 96.4%
- Issues: 21
  - Line 140: Line too long (117 > 100)
  - Line 168: Line too long (110 > 100)
  - Line 184: Line too long (121 > 100)

### src/calendar_client.py
- Lines: 250
- Functions: 6
- Classes: 1
- Complexity: 34
- Docstring Coverage: 85.7%
- Issues: 21
  - Line 33: Line too long (102 > 100)
  - Line 35: Line too long (108 > 100)
  - Line 51: Line too long (108 > 100)

### src/celery_app.py
- Lines: 683
- Functions: 18
- Classes: 0
- Complexity: 39
- Docstring Coverage: 55.6%
- Issues: 95
  - Line 21: Line too long (102 > 100)
  - Line 24: Line too long (106 > 100)
  - Line 26: Line too long (103 > 100)

### src/celery_sms_schedule.py
- Lines: 91
- Functions: 0
- Classes: 0
- Complexity: 3
- Docstring Coverage: 100.0%

### src/celery_sms_tasks.py
- Lines: 424
- Functions: 10
- Classes: 0
- Complexity: 26
- Docstring Coverage: 100.0%

### src/check_gcp_speech_import.py
- Lines: 19
- Functions: 0
- Classes: 0
- Complexity: 3
- Docstring Coverage: 100.0%

### src/communication_agent.py
- Lines: 32
- Functions: 7
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 8
  - Line 6: Missing docstring for CommunicationAgent
  - Line 7: Missing docstring for __init__
  - Line 13: Missing docstring for send_email

### src/communication_router.py
- Lines: 703
- Functions: 21
- Classes: 5
- Complexity: 63
- Docstring Coverage: 96.2%
- Issues: 24
  - Line 113: Line too long (116 > 100)
  - Line 143: Line too long (123 > 100)
  - Line 213: Line too long (137 > 100)

### src/communicator_agent.py
- Lines: 180
- Functions: 9
- Classes: 4
- Complexity: 8
- Docstring Coverage: 53.8%
- Issues: 6
  - Line 170: Missing docstring for MockEmailClient
  - Line 174: Missing docstring for MockSMSClient
  - Line 178: Missing docstring for MockVoiceClient

### src/config.py
- Lines: 158
- Functions: 0
- Classes: 0
- Complexity: 13
- Docstring Coverage: 100.0%
- Issues: 19
  - Line 13: Line too long (101 > 100)
  - Line 27: Line too long (139 > 100)
  - Line 29: Line too long (131 > 100)

### src/conflict_resolver.py
- Lines: 9
- Functions: 1
- Classes: 0
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 3: Missing docstring for resolve_conflicts

### src/context_manager.py
- Lines: 17
- Functions: 3
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 2: Missing docstring for MultiAgentContextManager
  - Line 3: Missing docstring for __init__
  - Line 6: Missing docstring for get_context

### src/context_retrieval_engine.py
- Lines: 724
- Functions: 19
- Classes: 6
- Complexity: 70
- Docstring Coverage: 84.0%
- Issues: 17
  - Line 95: Line too long (105 > 100)
  - Line 322: Line too long (104 > 100)
  - Line 327: Line too long (108 > 100)

### src/customer_profile_builder.py
- Lines: 717
- Functions: 22
- Classes: 5
- Complexity: 106
- Docstring Coverage: 81.5%
- Issues: 17
  - Line 165: Line too long (104 > 100)
  - Line 307: Line too long (101 > 100)
  - Line 352: Line too long (106 > 100)

### src/database_backup.py
- Lines: 352
- Functions: 12
- Classes: 1
- Complexity: 59
- Docstring Coverage: 92.3%
- Issues: 9
  - Line 67: Line too long (101 > 100)
  - Line 116: Line too long (118 > 100)
  - Line 158: Line too long (115 > 100)

### src/datetime_utils.py
- Lines: 119
- Functions: 1
- Classes: 0
- Complexity: 27
- Docstring Coverage: 100.0%
- Issues: 17
  - Line 12: Line too long (103 > 100)
  - Line 24: Line too long (120 > 100)
  - Line 28: Line too long (101 > 100)

### src/dependencies.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/django_settings.py
- Lines: 98
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/elevenlabs_voice_handler.py
- Lines: 592
- Functions: 7
- Classes: 5
- Complexity: 44
- Docstring Coverage: 83.3%
- Issues: 9
  - Line 169: Line too long (116 > 100)
  - Line 172: Line too long (129 > 100)
  - Line 279: Line too long (108 > 100)

### src/email_client.py
- Lines: 677
- Functions: 14
- Classes: 1
- Complexity: 111
- Docstring Coverage: 60.0%
- Issues: 94
  - Line 28: Line too long (106 > 100)
  - Line 42: Line too long (107 > 100)
  - Line 60: Line too long (111 > 100)

### src/email_processing_agent.py
- Lines: 366
- Functions: 4
- Classes: 0
- Complexity: 62
- Docstring Coverage: 50.0%
- Issues: 67
  - Line 35: Line too long (102 > 100)
  - Line 77: Line too long (104 > 100)
  - Line 85: Line too long (103 > 100)

### src/emergency_response_agent.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/errors.py
- Lines: 20
- Functions: 1
- Classes: 4
- Complexity: 1
- Docstring Coverage: 80.0%
- Issues: 1
  - Line 5: Missing docstring for __init__

### src/expense_manager.py
- Lines: 23
- Functions: 2
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 8: Missing docstring for ExpenseManager
  - Line 9: Missing docstring for add_expense
  - Line 21: Missing docstring for list_expenses

### src/financial_reports.py
- Lines: 28
- Functions: 2
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 20: Line too long (109 > 100)
  - Line 7: Missing docstring for FinancialReports
  - Line 8: Missing docstring for __init__

### src/firebase_setup.py
- Lines: 191
- Functions: 8
- Classes: 1
- Complexity: 21
- Docstring Coverage: 88.9%
- Issues: 4
  - Line 50: Line too long (110 > 100)
  - Line 53: Line too long (115 > 100)
  - Line 139: Line too long (117 > 100)

### src/firestore_interface.py
- Lines: 32
- Functions: 7
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 11
  - Line 21: Line too long (129 > 100)
  - Line 24: Line too long (110 > 100)
  - Line 27: Line too long (116 > 100)

### src/firestore_models.py
- Lines: 51
- Functions: 5
- Classes: 0
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 6
  - Line 18: Line too long (132 > 100)
  - Line 18: Missing docstring for create_task
  - Line 33: Missing docstring for update_task_status

### src/firestore_repository.py
- Lines: 30
- Functions: 6
- Classes: 1
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 8
  - Line 24: Line too long (102 > 100)
  - Line 6: Missing docstring for FirestoreRepository
  - Line 7: Missing docstring for __init__

### src/google_calendar_service.py
- Lines: 65
- Functions: 6
- Classes: 1
- Complexity: 7
- Docstring Coverage: 0.0%
- Issues: 9
  - Line 42: Line too long (104 > 100)
  - Line 60: Line too long (114 > 100)
  - Line 6: Missing docstring for GoogleCalendarService

### src/handyman_response_engine.py
- Lines: 345
- Functions: 6
- Classes: 1
- Complexity: 30
- Docstring Coverage: 85.7%
- Issues: 33
  - Line 51: Line too long (116 > 100)
  - Line 52: Line too long (144 > 100)
  - Line 63: Line too long (130 > 100)

### src/handyman_sms_engine.py
- Lines: 357
- Functions: 9
- Classes: 1
- Complexity: 33
- Docstring Coverage: 90.0%
- Issues: 10
  - Line 98: Line too long (113 > 100)
  - Line 173: Line too long (110 > 100)
  - Line 181: Line too long (109 > 100)

### src/intelligent_memory_system.py
- Lines: 556
- Functions: 14
- Classes: 1
- Complexity: 27
- Docstring Coverage: 100.0%
- Issues: 15
  - Line 90: Line too long (103 > 100)
  - Line 99: Line too long (103 > 100)
  - Line 102: Line too long (108 > 100)

### src/intent_classifier.py
- Lines: 12
- Functions: 1
- Classes: 0
- Complexity: 4
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 2: Missing docstring for classify_intent
  - Line 3: TODO/FIXME comment found

### src/knowledge_base_agent.py
- Lines: 286
- Functions: 14
- Classes: 5
- Complexity: 26
- Docstring Coverage: 57.9%
- Issues: 9
  - Line 15: Line too long (131 > 100)
  - Line 14: Missing docstring for Procedure
  - Line 23: Missing docstring for FAQ

### src/language_utils.py
- Lines: 8
- Functions: 1
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 4: Missing docstring for generate_multilang_response

### src/llm_client.py
- Lines: 143
- Functions: 4
- Classes: 1
- Complexity: 16
- Docstring Coverage: 60.0%
- Issues: 12
  - Line 23: Line too long (114 > 100)
  - Line 32: Line too long (113 > 100)
  - Line 35: Line too long (102 > 100)

### src/logging_config.py
- Lines: 17
- Functions: 1
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 15: Missing docstring for get_logger

### src/main.py
- Lines: 412
- Functions: 5
- Classes: 0
- Complexity: 36
- Docstring Coverage: 80.0%
- Issues: 31
  - Line 33: Line too long (108 > 100)
  - Line 112: Line too long (112 > 100)
  - Line 122: Line too long (108 > 100)

### src/memory_analytics.py
- Lines: 1092
- Functions: 24
- Classes: 7
- Complexity: 113
- Docstring Coverage: 80.6%
- Issues: 61
  - Line 128: Line too long (116 > 100)
  - Line 145: Line too long (112 > 100)
  - Line 149: Line too long (104 > 100)

### src/memory_client.py
- Lines: 664
- Functions: 10
- Classes: 2
- Complexity: 49
- Docstring Coverage: 91.7%
- Issues: 11
  - Line 146: Line too long (117 > 100)
  - Line 230: Line too long (101 > 100)
  - Line 246: Line too long (102 > 100)

### src/memory_embeddings_manager.py
- Lines: 607
- Functions: 16
- Classes: 3
- Complexity: 49
- Docstring Coverage: 100.0%
- Issues: 2
  - Line 168: Line too long (106 > 100)
  - Line 209: Line too long (104 > 100)

### src/mock_email_client.py
- Lines: 140
- Functions: 6
- Classes: 1
- Complexity: 18
- Docstring Coverage: 28.6%
- Issues: 11
  - Line 30: Line too long (108 > 100)
  - Line 42: Line too long (143 > 100)
  - Line 43: Line too long (133 > 100)

### src/models.py
- Lines: 33
- Functions: 0
- Classes: 5
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 5
  - Line 5: Missing docstring for User
  - Line 10: Missing docstring for Procedure
  - Line 18: Missing docstring for FAQ

### src/monitoring.py
- Lines: 571
- Functions: 17
- Classes: 6
- Complexity: 41
- Docstring Coverage: 87.0%
- Issues: 11
  - Line 354: Line too long (102 > 100)
  - Line 360: Line too long (109 > 100)
  - Line 363: Line too long (118 > 100)

### src/oauth_token_manager.py
- Lines: 443
- Functions: 21
- Classes: 2
- Complexity: 48
- Docstring Coverage: 91.3%
- Issues: 7
  - Line 132: Line too long (102 > 100)
  - Line 157: Line too long (102 > 100)
  - Line 170: Line too long (103 > 100)

### src/orchestrator.py
- Lines: 784
- Functions: 20
- Classes: 6
- Complexity: 59
- Docstring Coverage: 96.2%
- Issues: 9
  - Line 194: Line too long (101 > 100)
  - Line 273: Line too long (103 > 100)
  - Line 499: Line too long (104 > 100)

### src/orchestrator_agent.py
- Lines: 279
- Functions: 11
- Classes: 2
- Complexity: 16
- Docstring Coverage: 92.3%
- Issues: 3
  - Line 2: Line too long (107 > 100)
  - Line 218: Line too long (109 > 100)
  - Line 17: Missing docstring for __init__

### src/phone_engineer_agent.py
- Lines: 878
- Functions: 8
- Classes: 1
- Complexity: 88
- Docstring Coverage: 100.0%
- Issues: 10
  - Line 65: Line too long (105 > 100)
  - Line 210: Line too long (105 > 100)
  - Line 314: Line too long (104 > 100)

### src/phone_integration.py
- Lines: 662
- Functions: 22
- Classes: 3
- Complexity: 36
- Docstring Coverage: 96.0%
- Issues: 17
  - Line 83: Line too long (107 > 100)
  - Line 109: Line too long (103 > 100)
  - Line 111: Line too long (109 > 100)

### src/quote_manager.py
- Lines: 23
- Functions: 2
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 8: Missing docstring for QuoteManager
  - Line 9: Missing docstring for create_quote
  - Line 21: Missing docstring for list_quotes

### src/reminder_service.py
- Lines: 25
- Functions: 4
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 5
  - Line 4: Missing docstring for ReminderService
  - Line 5: Missing docstring for __init__
  - Line 9: Missing docstring for schedule_reminder

### src/retry.py
- Lines: 28
- Functions: 3
- Classes: 0
- Complexity: 4
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 20: Line too long (101 > 100)
  - Line 8: Missing docstring for retry
  - Line 9: Missing docstring for decorator

### src/route_optimizer.py
- Lines: 7
- Functions: 1
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 2: Missing docstring for RouteOptimizer
  - Line 3: Missing docstring for optimize

### src/scheduler_agent.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/schemas_core.py
- Lines: 21
- Functions: 0
- Classes: 5
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 5
  - Line 5: Missing docstring for RepairKnowledgeQuery
  - Line 8: Missing docstring for ToolMaterialRecommendationRequest
  - Line 11: Missing docstring for CostEstimationRequest

### src/security_audit.py
- Lines: 498
- Functions: 16
- Classes: 2
- Complexity: 61
- Docstring Coverage: 83.3%
- Issues: 18
  - Line 65: Line too long (119 > 100)
  - Line 66: Line too long (128 > 100)
  - Line 67: Line too long (135 > 100)

### src/share_archaeological_findings.py
- Lines: 240
- Functions: 1
- Classes: 0
- Complexity: 5
- Docstring Coverage: 100.0%

### src/show_last_karen_email.py
- Lines: 112
- Functions: 1
- Classes: 0
- Complexity: 16
- Docstring Coverage: 0.0%
- Issues: 16
  - Line 34: Line too long (105 > 100)
  - Line 40: Line too long (103 > 100)
  - Line 43: Line too long (114 > 100)

### src/sms_appointment_integration.py
- Lines: 572
- Functions: 19
- Classes: 4
- Complexity: 41
- Docstring Coverage: 95.7%
- Issues: 5
  - Line 232: Line too long (105 > 100)
  - Line 315: Line too long (107 > 100)
  - Line 344: Line too long (123 > 100)

### src/sms_client.py
- Lines: 393
- Functions: 10
- Classes: 1
- Complexity: 44
- Docstring Coverage: 90.9%
- Issues: 16
  - Line 39: Line too long (110 > 100)
  - Line 78: Line too long (102 > 100)
  - Line 98: Line too long (105 > 100)

### src/sms_conversation_manager.py
- Lines: 699
- Functions: 25
- Classes: 5
- Complexity: 88
- Docstring Coverage: 93.3%
- Issues: 8
  - Line 217: Line too long (102 > 100)
  - Line 225: Line too long (108 > 100)
  - Line 527: Line too long (101 > 100)

### src/sms_engineer_agent.py
- Lines: 637
- Functions: 4
- Classes: 1
- Complexity: 56
- Docstring Coverage: 100.0%
- Issues: 2
  - Line 243: Line too long (115 > 100)
  - Line 246: Line too long (101 > 100)

### src/sms_integration.py
- Lines: 486
- Functions: 16
- Classes: 2
- Complexity: 25
- Docstring Coverage: 94.4%
- Issues: 11
  - Line 176: Line too long (103 > 100)
  - Line 231: Line too long (101 > 100)
  - Line 235: Line too long (107 > 100)

### src/sms_quick_replies.py
- Lines: 575
- Functions: 17
- Classes: 3
- Complexity: 54
- Docstring Coverage: 100.0%
- Issues: 21
  - Line 62: Line too long (175 > 100)
  - Line 69: Line too long (110 > 100)
  - Line 70: Line too long (135 > 100)

### src/sms_templates.py
- Lines: 607
- Functions: 22
- Classes: 2
- Complexity: 60
- Docstring Coverage: 100.0%
- Issues: 48
  - Line 49: Line too long (128 > 100)
  - Line 51: Line too long (111 > 100)
  - Line 55: Line too long (118 > 100)

### src/sms_template_system.py
- Lines: 352
- Functions: 17
- Classes: 1
- Complexity: 32
- Docstring Coverage: 88.9%
- Issues: 32
  - Line 19: Line too long (162 > 100)
  - Line 24: Line too long (153 > 100)
  - Line 29: Line too long (188 > 100)

### src/sms_webhook.py
- Lines: 35
- Functions: 0
- Classes: 0
- Complexity: 2
- Docstring Coverage: 100.0%

### src/start_test_monitoring.py
- Lines: 352
- Functions: 12
- Classes: 1
- Complexity: 28
- Docstring Coverage: 92.3%
- Issues: 4
  - Line 213: Line too long (103 > 100)
  - Line 278: Line too long (108 > 100)
  - Line 279: Line too long (110 > 100)

### src/stripe_client.py
- Lines: 29
- Functions: 3
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 7: Missing docstring for StripeClient
  - Line 8: Missing docstring for create_invoice
  - Line 22: Missing docstring for get_invoice

### src/task_management_agent.py
- Lines: 78
- Functions: 5
- Classes: 1
- Complexity: 6
- Docstring Coverage: 0.0%
- Issues: 7
  - Line 12: Line too long (110 > 100)
  - Line 8: Missing docstring for TaskManagementAgent
  - Line 9: Missing docstring for __init__

### src/task_manager.py
- Lines: 88
- Functions: 8
- Classes: 1
- Complexity: 12
- Docstring Coverage: 44.4%
- Issues: 10
  - Line 9: Line too long (101 > 100)
  - Line 11: Line too long (117 > 100)
  - Line 52: Line too long (133 > 100)

### src/task_manager_agent.py
- Lines: 379
- Functions: 10
- Classes: 5
- Complexity: 21
- Docstring Coverage: 66.7%
- Issues: 10
  - Line 310: Line too long (102 > 100)
  - Line 322: Line too long (203 > 100)
  - Line 331: Line too long (111 > 100)

### src/test_celery_task.py
- Lines: 20
- Functions: 0
- Classes: 0
- Complexity: 3
- Docstring Coverage: 100.0%

### src/test_engineer.py
- Lines: 633
- Functions: 27
- Classes: 1
- Complexity: 65
- Docstring Coverage: 96.4%
- Issues: 2
  - Line 303: Line too long (103 > 100)
  - Line 46: Missing docstring for __init__

### src/test_runner_simple.py
- Lines: 418
- Functions: 14
- Classes: 1
- Complexity: 29
- Docstring Coverage: 93.3%
- Issues: 3
  - Line 182: Line too long (101 > 100)
  - Line 399: Line too long (108 > 100)
  - Line 34: Missing docstring for __init__

### src/test_scheduler.py
- Lines: 489
- Functions: 11
- Classes: 1
- Complexity: 30
- Docstring Coverage: 91.7%
- Issues: 7
  - Line 148: Line too long (110 > 100)
  - Line 207: Line too long (121 > 100)
  - Line 388: Line too long (107 > 100)

### src/voice_call_analytics.py
- Lines: 786
- Functions: 40
- Classes: 2
- Complexity: 84
- Docstring Coverage: 97.6%
- Issues: 15
  - Line 290: Line too long (110 > 100)
  - Line 454: Line too long (102 > 100)
  - Line 481: Line too long (117 > 100)

### src/voice_call_tracker.py
- Lines: 689
- Functions: 24
- Classes: 5
- Complexity: 56
- Docstring Coverage: 93.1%
- Issues: 5
  - Line 406: Line too long (101 > 100)
  - Line 410: Line too long (103 > 100)
  - Line 612: Line too long (104 > 100)

### src/voice_client.py
- Lines: 602
- Functions: 13
- Classes: 1
- Complexity: 57
- Docstring Coverage: 100.0%
- Issues: 9
  - Line 24: Line too long (108 > 100)
  - Line 66: Line too long (110 > 100)
  - Line 84: Line too long (120 > 100)

### src/voice_emergency_handler.py
- Lines: 909
- Functions: 18
- Classes: 4
- Complexity: 68
- Docstring Coverage: 95.5%
- Issues: 13
  - Line 562: Line too long (105 > 100)
  - Line 571: Line too long (107 > 100)
  - Line 621: Line too long (104 > 100)

### src/voice_ivr_system.py
- Lines: 478
- Functions: 13
- Classes: 4
- Complexity: 28
- Docstring Coverage: 88.2%
- Issues: 14
  - Line 42: Line too long (105 > 100)
  - Line 78: Line too long (152 > 100)
  - Line 113: Line too long (158 > 100)

### src/voice_quality_assurance.py
- Lines: 1253
- Functions: 26
- Classes: 4
- Complexity: 101
- Docstring Coverage: 96.7%
- Issues: 19
  - Line 301: Line too long (103 > 100)
  - Line 312: Line too long (141 > 100)
  - Line 617: Line too long (107 > 100)

### src/voice_system_tester.py
- Lines: 849
- Functions: 4
- Classes: 2
- Complexity: 86
- Docstring Coverage: 66.7%
- Issues: 27
  - Line 74: Line too long (108 > 100)
  - Line 75: Line too long (109 > 100)
  - Line 76: Line too long (113 > 100)

### src/voice_transcription_handler.py
- Lines: 712
- Functions: 8
- Classes: 4
- Complexity: 68
- Docstring Coverage: 83.3%
- Issues: 26
  - Line 123: Line too long (114 > 100)
  - Line 124: Line too long (115 > 100)
  - Line 125: Line too long (104 > 100)

### src/voice_webhook_handler.py
- Lines: 810
- Functions: 13
- Classes: 1
- Complexity: 66
- Docstring Coverage: 92.9%
- Issues: 24
  - Line 25: Line too long (105 > 100)
  - Line 86: Line too long (102 > 100)
  - Line 106: Line too long (125 > 100)

### src/websocket_server.py
- Lines: 11
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/__init__.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/agents/base_agent.py
- Lines: 34
- Functions: 2
- Classes: 1
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 4: Missing docstring for BaseAgent
  - Line 5: Missing docstring for __init__
  - Line 11: Missing docstring for is_available

### src/agents/contact_manager.py
- Lines: 15
- Functions: 1
- Classes: 0
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 7: Missing docstring for get_emergency_contacts

### src/agents/emergency_response_agent.py
- Lines: 49
- Functions: 6
- Classes: 1
- Complexity: 4
- Docstring Coverage: 0.0%
- Issues: 8
  - Line 45: Line too long (107 > 100)
  - Line 11: Missing docstring for EmergencyResponseAgent
  - Line 12: Missing docstring for __init__

### src/agents/escalation_protocols.py
- Lines: 24
- Functions: 1
- Classes: 0
- Complexity: 3
- Docstring Coverage: 100.0%

### src/agents/handyman_agent.py
- Lines: 13
- Functions: 1
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 3: Missing docstring for HandymanAgent
  - Line 4: Missing docstring for __init__

### src/agents/reminders.py
- Lines: 18
- Functions: 1
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 7: Line too long (104 > 100)
  - Line 8: Line too long (108 > 100)
  - Line 7: Missing docstring for schedule_reminder

### src/agents/response_coordinator.py
- Lines: 10
- Functions: 1
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%
- Issues: 1
  - Line 9: TODO/FIXME comment found

### src/agents/scheduling_agent.py
- Lines: 42
- Functions: 3
- Classes: 1
- Complexity: 7
- Docstring Coverage: 0.0%
- Issues: 5
  - Line 32: Line too long (121 > 100)
  - Line 9: Missing docstring for SchedulingAgent
  - Line 10: Missing docstring for __init__

### src/analytics/customer_analytics.py
- Lines: 451
- Functions: 12
- Classes: 1
- Complexity: 16
- Docstring Coverage: 84.6%
- Issues: 27
  - Line 36: Line too long (103 > 100)
  - Line 49: Line too long (117 > 100)
  - Line 54: Line too long (110 > 100)

### src/analytics/operational_metrics.py
- Lines: 228
- Functions: 17
- Classes: 1
- Complexity: 27
- Docstring Coverage: 88.9%
- Issues: 5
  - Line 94: Line too long (103 > 100)
  - Line 104: Line too long (129 > 100)
  - Line 186: Line too long (103 > 100)

### src/analytics/revenue_intelligence.py
- Lines: 641
- Functions: 17
- Classes: 1
- Complexity: 29
- Docstring Coverage: 88.9%
- Issues: 59
  - Line 30: Line too long (101 > 100)
  - Line 35: Line too long (118 > 100)
  - Line 57: Line too long (132 > 100)

### src/analytics/__init__.py
- Lines: 4
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/api/appointments.py
- Lines: 38
- Functions: 5
- Classes: 0
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 6
  - Line 33: Line too long (111 > 100)
  - Line 10: Missing docstring for get_appointment_or_404
  - Line 17: Missing docstring for create_appointment

### src/api/routes.py
- Lines: 22
- Functions: 3
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 19: Line too long (103 > 100)
  - Line 9: Missing docstring for process_email
  - Line 14: Missing docstring for process_voice

### src/api/scheduling_routes.py
- Lines: 29
- Functions: 0
- Classes: 0
- Complexity: 4
- Docstring Coverage: 100.0%

### src/api/tasks.py
- Lines: 38
- Functions: 5
- Classes: 0
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 5
  - Line 10: Missing docstring for get_task_or_404
  - Line 17: Missing docstring for create_task
  - Line 25: Missing docstring for list_tasks

### src/api/users.py
- Lines: 32
- Functions: 4
- Classes: 0
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 12: Missing docstring for create_user
  - Line 19: Missing docstring for get_me
  - Line 23: Missing docstring for list_users

### src/auth/auth_helpers.py
- Lines: 7
- Functions: 2
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 1: Missing docstring for is_token_valid
  - Line 5: Missing docstring for get_current_user

### src/auth/jwt_handler.py
- Lines: 7
- Functions: 2
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 3: Missing docstring for generate_token
  - Line 6: Missing docstring for decode_token

### src/auth/jwt_service.py
- Lines: 27
- Functions: 3
- Classes: 1
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 4: Missing docstring for JWTService
  - Line 5: Missing docstring for __init__
  - Line 9: Missing docstring for encode_auth_token

### src/auth/middleware.py
- Lines: 23
- Functions: 3
- Classes: 0
- Complexity: 4
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 20: Line too long (105 > 100)
  - Line 11: Missing docstring for get_current_user
  - Line 17: Missing docstring for require_role

### src/auth/oauth.py
- Lines: 57
- Functions: 2
- Classes: 0
- Complexity: 4
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 22: Missing docstring for login_google
  - Line 26: Missing docstring for google_callback

### src/auth/oauth2.py
- Lines: 7
- Functions: 1
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 3: Missing docstring for OAuth2Server
  - Line 4: Missing docstring for __init__

### src/auth/oauth_service.py
- Lines: 14
- Functions: 2
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 13: Line too long (119 > 100)
  - Line 4: Missing docstring for OAuthService
  - Line 5: Missing docstring for __init__

### src/auth/rbac.py
- Lines: 27
- Functions: 3
- Classes: 0
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 14: Missing docstring for get_current_user
  - Line 20: Missing docstring for require_permission
  - Line 21: Missing docstring for decorator

### src/auth/role_based_access_control.py
- Lines: 10
- Functions: 2
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 1: Missing docstring for AccessControl
  - Line 2: Missing docstring for __init__
  - Line 9: Missing docstring for check_permission

### src/auth/security.py
- Lines: 29
- Functions: 2
- Classes: 0
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 13: Missing docstring for create_access_token
  - Line 21: Missing docstring for decode_access_token

### src/communication_agent/agent.py
- Lines: 873
- Functions: 5
- Classes: 1
- Complexity: 117
- Docstring Coverage: 16.7%
- Issues: 200
  - Line 17: Line too long (110 > 100)
  - Line 61: Line too long (104 > 100)
  - Line 62: Line too long (125 > 100)

### src/communication_agent/email_handler.py
- Lines: 26
- Functions: 2
- Classes: 1
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 5: Missing docstring for EmailHandler
  - Line 6: Missing docstring for __init__
  - Line 12: Missing docstring for send_email

### src/communication_agent/sms_handler.py
- Lines: 42
- Functions: 2
- Classes: 1
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 9: Missing docstring for SMSHandler
  - Line 10: Missing docstring for __init__
  - Line 14: Missing docstring for send_sms

### src/communication_agent/voice_transcription_handler.py
- Lines: 35
- Functions: 2
- Classes: 1
- Complexity: 5
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 16: Line too long (112 > 100)
  - Line 7: Missing docstring for VoiceTranscriptionHandler
  - Line 8: Missing docstring for __init__

### src/communication_agent/__init__.py
- Lines: 2
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/endpoints/appointments.py
- Lines: 67
- Functions: 0
- Classes: 2
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 13: Missing docstring for AppointmentCreate
  - Line 21: Missing docstring for AppointmentResponse

### src/endpoints/billing.py
- Lines: 61
- Functions: 0
- Classes: 2
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 13: Missing docstring for InvoiceCreate
  - Line 19: Missing docstring for InvoiceResponse

### src/endpoints/communications.py
- Lines: 197
- Functions: 0
- Classes: 5
- Complexity: 9
- Docstring Coverage: 0.0%
- Issues: 8
  - Line 74: Line too long (112 > 100)
  - Line 106: Line too long (112 > 100)
  - Line 121: Line too long (102 > 100)

### src/endpoints/inventory.py
- Lines: 62
- Functions: 0
- Classes: 2
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 13: Missing docstring for InventoryItemCreate
  - Line 20: Missing docstring for InventoryItemResponse

### src/endpoints/knowledge.py
- Lines: 267
- Functions: 0
- Classes: 8
- Complexity: 22
- Docstring Coverage: 0.0%
- Issues: 9
  - Line 266: Line too long (104 > 100)
  - Line 15: Missing docstring for ProcedureCreate
  - Line 22: Missing docstring for ProcedureUpdate

### src/endpoints/memory.py
- Lines: 140
- Functions: 0
- Classes: 0
- Complexity: 17
- Docstring Coverage: 100.0%
- Issues: 2
  - Line 10: Line too long (101 > 100)
  - Line 54: Line too long (105 > 100)

### src/endpoints/tasks.py
- Lines: 151
- Functions: 0
- Classes: 3
- Complexity: 11
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 18: Missing docstring for TaskCreate
  - Line 27: Missing docstring for TaskUpdate
  - Line 37: Missing docstring for TaskResponse

### src/endpoints/users.py
- Lines: 9
- Functions: 1
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 7: Missing docstring for create_user

### src/integrations/gmail_client.py
- Lines: 26
- Functions: 3
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 6: Missing docstring for GmailClient
  - Line 7: Missing docstring for __init__
  - Line 10: Missing docstring for send_email

### src/integrations/google_workspace.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%
- Issues: 1
  - Line 1: Line too long (139 > 100)

### src/integrations/paypal_gateway.py
- Lines: 31
- Functions: 1
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 28: Line too long (111 > 100)
  - Line 13: Missing docstring for PayPalGateway
  - Line 14: Missing docstring for charge

### src/integrations/sendgrid.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%
- Issues: 1
  - Line 1: Line too long (114 > 100)

### src/integrations/stripe.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%
- Issues: 1
  - Line 1: Line too long (108 > 100)

### src/integrations/stripe_gateway.py
- Lines: 22
- Functions: 1
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 9: Missing docstring for StripeGateway
  - Line 10: Missing docstring for charge

### src/integrations/transcription.py
- Lines: 17
- Functions: 2
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 4: Missing docstring for TranscriptionService
  - Line 5: Missing docstring for __init__
  - Line 8: Missing docstring for transcribe

### src/integrations/twilio.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%
- Issues: 1
  - Line 1: Line too long (108 > 100)

### src/integrations/twilio_client.py
- Lines: 35
- Functions: 4
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 5
  - Line 4: Missing docstring for TwilioClient
  - Line 5: Missing docstring for __init__
  - Line 9: Missing docstring for send_sms

### src/models/expense.py
- Lines: 19
- Functions: 3
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 5: Missing docstring for Expense
  - Line 6: Missing docstring for __init__
  - Line 14: Missing docstring for create

### src/models/invoice.py
- Lines: 22
- Functions: 3
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 5
  - Line 6: Line too long (103 > 100)
  - Line 5: Missing docstring for Invoice
  - Line 6: Missing docstring for __init__

### src/models/payment.py
- Lines: 20
- Functions: 3
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 5: Missing docstring for Payment
  - Line 6: Missing docstring for __init__
  - Line 15: Missing docstring for create

### src/nlu/basic_nlu.py
- Lines: 40
- Functions: 3
- Classes: 0
- Complexity: 6
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 19: Missing docstring for extract_intent
  - Line 27: Missing docstring for extract_entities
  - Line 35: Missing docstring for parse

### src/nlu/dialogflow_nlu.py
- Lines: 33
- Functions: 2
- Classes: 1
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 28: Line too long (107 > 100)
  - Line 10: Missing docstring for DialogflowNLU
  - Line 11: Missing docstring for __init__

### src/nlu/__init__.py
- Lines: 24
- Functions: 2
- Classes: 1
- Complexity: 7
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 12: Missing docstring for NLU
  - Line 13: Missing docstring for __init__
  - Line 20: Missing docstring for parse

### src/personality/core_personality.py
- Lines: 412
- Functions: 14
- Classes: 3
- Complexity: 48
- Docstring Coverage: 76.5%
- Issues: 23
  - Line 36: Line too long (116 > 100)
  - Line 84: Line too long (112 > 100)
  - Line 88: Line too long (101 > 100)

### src/personality/cultural_awareness.py
- Lines: 276
- Functions: 11
- Classes: 1
- Complexity: 23
- Docstring Coverage: 83.3%
- Issues: 14
  - Line 98: Line too long (107 > 100)
  - Line 99: Line too long (101 > 100)
  - Line 101: Line too long (118 > 100)

### src/personality/empathy_engine.py
- Lines: 198
- Functions: 7
- Classes: 1
- Complexity: 24
- Docstring Coverage: 75.0%
- Issues: 12
  - Line 41: Line too long (109 > 100)
  - Line 52: Line too long (112 > 100)
  - Line 53: Line too long (109 > 100)

### src/personality/humor_engine.py
- Lines: 222
- Functions: 10
- Classes: 1
- Complexity: 15
- Docstring Coverage: 81.8%
- Issues: 8
  - Line 32: Line too long (103 > 100)
  - Line 33: Line too long (103 > 100)
  - Line 41: Line too long (102 > 100)

### src/personality/phone_etiquette.py
- Lines: 151
- Functions: 9
- Classes: 1
- Complexity: 17
- Docstring Coverage: 80.0%
- Issues: 18
  - Line 14: Line too long (120 > 100)
  - Line 15: Line too long (123 > 100)
  - Line 17: Line too long (142 > 100)

### src/personality/regional_adaptation.py
- Lines: 212
- Functions: 9
- Classes: 1
- Complexity: 25
- Docstring Coverage: 80.0%
- Issues: 25
  - Line 25: Line too long (118 > 100)
  - Line 66: Line too long (108 > 100)
  - Line 67: Line too long (105 > 100)

### src/personality/response_enhancer.py
- Lines: 365
- Functions: 14
- Classes: 1
- Complexity: 51
- Docstring Coverage: 93.3%
- Issues: 17
  - Line 143: Line too long (120 > 100)
  - Line 151: Line too long (137 > 100)
  - Line 160: Line too long (106 > 100)

### src/personality/small_talk.py
- Lines: 230
- Functions: 10
- Classes: 1
- Complexity: 25
- Docstring Coverage: 81.8%
- Issues: 18
  - Line 14: Line too long (116 > 100)
  - Line 20: Line too long (115 > 100)
  - Line 21: Line too long (115 > 100)

### src/personality/voice_personality.py
- Lines: 175
- Functions: 10
- Classes: 1
- Complexity: 10
- Docstring Coverage: 81.8%
- Issues: 11
  - Line 41: Line too long (105 > 100)
  - Line 45: Line too long (103 > 100)
  - Line 49: Line too long (108 > 100)

### src/personality/__init__.py
- Lines: 22
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/routers/appointments.py
- Lines: 11
- Functions: 2
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 6: Missing docstring for schedule_appointment
  - Line 10: Missing docstring for list_appointments

### src/routers/billing.py
- Lines: 7
- Functions: 1
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 6: Missing docstring for charge

### src/routers/communications.py
- Lines: 7
- Functions: 1
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 6: Missing docstring for send_communication

### src/routers/inventory.py
- Lines: 7
- Functions: 1
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 6: Missing docstring for list_inventory_items

### src/routers/knowledge.py
- Lines: 7
- Functions: 1
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 6: Missing docstring for get_knowledge_item

### src/routers/tasks.py
- Lines: 11
- Functions: 2
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 6: Missing docstring for create_task
  - Line 10: Missing docstring for list_tasks

### src/routers/users.py
- Lines: 11
- Functions: 2
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 6: Missing docstring for create_user
  - Line 10: Missing docstring for read_user

### src/routes/knowledge_base.py
- Lines: 51
- Functions: 6
- Classes: 0
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 7
  - Line 4: Line too long (152 > 100)
  - Line 9: Missing docstring for get_agent
  - Line 15: Missing docstring for repair_knowledge

### src/scheduler/agent.py
- Lines: 106
- Functions: 10
- Classes: 4
- Complexity: 12
- Docstring Coverage: 21.4%
- Issues: 13
  - Line 17: Line too long (109 > 100)
  - Line 59: Line too long (116 > 100)
  - Line 8: Missing docstring for SchedulerAgent

### src/scheduler/google_calendar.py
- Lines: 66
- Functions: 4
- Classes: 1
- Complexity: 6
- Docstring Coverage: 0.0%
- Issues: 8
  - Line 8: Line too long (127 > 100)
  - Line 47: Line too long (143 > 100)
  - Line 63: Line too long (142 > 100)

### src/scheduler/models.py
- Lines: 18
- Functions: 2
- Classes: 1
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 2: Missing docstring for event_to_dict
  - Line 12: Missing docstring for EventMapping
  - Line 13: Missing docstring for __init__

### src/scheduler/outlook_calendar.py
- Lines: 62
- Functions: 4
- Classes: 1
- Complexity: 6
- Docstring Coverage: 0.0%
- Issues: 7
  - Line 43: Line too long (147 > 100)
  - Line 59: Line too long (138 > 100)
  - Line 4: Missing docstring for OutlookCalendarClient

### src/scheduler/utils.py
- Lines: 25
- Functions: 1
- Classes: 0
- Complexity: 9
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 9: Line too long (117 > 100)
  - Line 17: Line too long (109 > 100)
  - Line 22: Line too long (108 > 100)

### src/scheduler/webhooks.py
- Lines: 23
- Functions: 2
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 8: Missing docstring for google_webhook
  - Line 18: Missing docstring for outlook_webhook

### src/scheduler/__init__.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/schemas/appointment.py
- Lines: 21
- Functions: 0
- Classes: 4
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 4: Missing docstring for AppointmentBase
  - Line 10: Missing docstring for AppointmentCreate
  - Line 13: Missing docstring for AppointmentUpdate

### src/schemas/task.py
- Lines: 51
- Functions: 0
- Classes: 7
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 8
  - Line 19: Line too long (102 > 100)
  - Line 5: Missing docstring for TaskDetailsSchema
  - Line 11: Missing docstring for TaskBase

### src/schemas/user.py
- Lines: 20
- Functions: 0
- Classes: 4
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 4: Missing docstring for UserBase
  - Line 10: Missing docstring for UserCreate
  - Line 13: Missing docstring for UserUpdate

### src/schemas/__init__.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%

### src/security/audit_logging.py
- Lines: 10
- Functions: 2
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 4: Missing docstring for AuditLogger
  - Line 5: Missing docstring for __init__
  - Line 8: Missing docstring for log_action

### src/security/auth.py
- Lines: 30
- Functions: 1
- Classes: 0
- Complexity: 3
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 20: Missing docstring for get_current_user

### src/security/compliance_tools.py
- Lines: 9
- Functions: 2
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 3
  - Line 1: Missing docstring for ComplianceTool
  - Line 2: Missing docstring for __init__
  - Line 5: Missing docstring for run_compliance_checks

### src/security/encryption.py
- Lines: 12
- Functions: 3
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 3: Missing docstring for EncryptionService
  - Line 4: Missing docstring for __init__
  - Line 8: Missing docstring for encrypt_data

### src/security/encryption_utils.py
- Lines: 27
- Functions: 4
- Classes: 0
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 4
  - Line 4: Missing docstring for generate_key
  - Line 11: Missing docstring for load_key
  - Line 15: Missing docstring for encrypt_message

### src/security/kms.py
- Lines: 23
- Functions: 2
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 2
  - Line 13: Missing docstring for encrypt_symmetric
  - Line 19: Missing docstring for decrypt_symmetric

### src/security/secrets.py
- Lines: 13
- Functions: 1
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 9: Missing docstring for access_secret

### src/security/tls_config.py
- Lines: 7
- Functions: 1
- Classes: 0
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 1
  - Line 4: Missing docstring for create_tls_context

### src/utils/CacheImplementation.py
- Lines: 1
- Functions: 0
- Classes: 0
- Complexity: 1
- Docstring Coverage: 100.0%
- Issues: 1
  - Line 1: Line too long (295 > 100)

### src/validators/input_validators.py
- Lines: 47
- Functions: 4
- Classes: 3
- Complexity: 7
- Docstring Coverage: 0.0%
- Issues: 8
  - Line 43: Line too long (104 > 100)
  - Line 6: Missing docstring for EmailInput
  - Line 17: Missing docstring for VoiceInput

### src/agents/calendar/google_calendar.py
- Lines: 36
- Functions: 3
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 5
  - Line 17: Line too long (102 > 100)
  - Line 8: Missing docstring for GoogleCalendarClient
  - Line 9: Missing docstring for __init__

### src/agents/calendar/outlook_calendar.py
- Lines: 36
- Functions: 3
- Classes: 1
- Complexity: 2
- Docstring Coverage: 0.0%
- Issues: 5
  - Line 17: Line too long (102 > 100)
  - Line 5: Missing docstring for OutlookCalendarClient
  - Line 6: Missing docstring for __init__

### src/orchestrator_agent.py
- Lines: 279
- Functions: 11
- Classes: 2
- Complexity: 16
- Docstring Coverage: 92.3%
- Issues: 3
  - Line 2: Line too long (107 > 100)
  - Line 218: Line too long (109 > 100)
  - Line 17: Missing docstring for __init__

### src/communication_agent.py
- Lines: 32
- Functions: 7
- Classes: 1
- Complexity: 1
- Docstring Coverage: 0.0%
- Issues: 8
  - Line 6: Missing docstring for CommunicationAgent
  - Line 7: Missing docstring for __init__
  - Line 13: Missing docstring for send_email

### src/sms_engineer_agent.py
- Lines: 637
- Functions: 4
- Classes: 1
- Complexity: 56
- Docstring Coverage: 100.0%
- Issues: 2
  - Line 243: Line too long (115 > 100)
  - Line 246: Line too long (101 > 100)

### src/phone_engineer_agent.py
- Lines: 878
- Functions: 8
- Classes: 1
- Complexity: 88
- Docstring Coverage: 100.0%
- Issues: 10
  - Line 65: Line too long (105 > 100)
  - Line 210: Line too long (105 > 100)
  - Line 314: Line too long (104 > 100)

### src/memory_client.py
- Lines: 664
- Functions: 10
- Classes: 2
- Complexity: 49
- Docstring Coverage: 91.7%
- Issues: 11
  - Line 146: Line too long (117 > 100)
  - Line 230: Line too long (101 > 100)
  - Line 246: Line too long (102 > 100)
