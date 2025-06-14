#!/usr/bin/env python3
"""
Check Archaeologist Agent Status
================================

This script checks the current status of the archaeologist agent and reports
on its analysis completion state.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from agent_communication import AgentCommunication
except ImportError as e:
    print(f"Error importing AgentCommunication: {e}")
    print("Make sure Redis is available and the agent_communication module is accessible")
    sys.exit(1)

def check_archaeologist_status():
    """Check the archaeologist agent's current status."""
    
    # Initialize communication
    comm = AgentCommunication('status_checker')
    
    print("🔍 Checking Archaeologist Agent Status")
    print("=" * 60)
    
    # Check Redis status
    try:
        redis_status = comm.redis_client.get('agent_status_archaeologist')
        if redis_status:
            status_data = json.loads(redis_status)
            print("\n📡 Redis Status (Real-time):")
            print(f"   Status: {status_data.get('status', 'unknown')}")
            print(f"   Progress: {status_data.get('progress', 0)}%")
            print(f"   Details: {json.dumps(status_data.get('details', {}), indent=4)}")
            print(f"   Last Update: {status_data.get('timestamp', 'unknown')}")
        else:
            print("\n⚠️  No real-time status found in Redis for archaeologist agent")
    except Exception as e:
        print(f"\n❌ Error checking Redis status: {e}")
    
    # Check filesystem status
    status_file = Path(__file__).parent / 'autonomous-agents' / 'communication' / 'status' / 'archaeologist_status.json'
    if status_file.exists():
        with open(status_file, 'r') as f:
            fs_status = json.load(f)
        print("\n📂 Filesystem Status (Persistent):")
        print(f"   Status: {fs_status.get('status', 'unknown')}")
        print(f"   Progress: {fs_status.get('progress', 0)}%")
        print(f"   Details: {json.dumps(fs_status.get('details', {}), indent=4)}")
        print(f"   Last Update: {fs_status.get('timestamp', 'unknown')}")
    else:
        print("\n⚠️  No filesystem status file found for archaeologist agent")
    
    # Check for shared knowledge files
    kb_dir = Path(__file__).parent / 'autonomous-agents' / 'communication' / 'knowledge-base'
    archaeologist_files = list(kb_dir.glob('*_archaeologist_*.json')) if kb_dir.exists() else []
    
    print(f"\n📚 Knowledge Base Contributions: {len(archaeologist_files)} files found")
    if archaeologist_files:
        for file in sorted(archaeologist_files)[-5:]:  # Show last 5
            print(f"   - {file.name}")
    
    # Check shared-knowledge directory for analysis files
    shared_knowledge_dir = Path(__file__).parent / 'autonomous-agents' / 'shared-knowledge'
    if shared_knowledge_dir.exists():
        print("\n📄 Shared Knowledge Directory Contents:")
        files = list(shared_knowledge_dir.glob('*.md'))
        for file in files:
            print(f"   - {file.name}")
            # Check if these are the archaeologist's work
            if file.name in ['karen-architecture.md', 'karen-implementation-patterns.md', 'DO-NOT-MODIFY-LIST.md']:
                print(f"     ✅ Archaeologist analysis file confirmed")
    
    # Analyze completion status
    print("\n🎯 Analysis Completion Assessment:")
    
    completion_indicators = {
        'karen-architecture.md': shared_knowledge_dir / 'karen-architecture.md' if shared_knowledge_dir.exists() else None,
        'karen-implementation-patterns.md': shared_knowledge_dir / 'karen-implementation-patterns.md' if shared_knowledge_dir.exists() else None,
        'DO-NOT-MODIFY-LIST.md': shared_knowledge_dir / 'DO-NOT-MODIFY-LIST.md' if shared_knowledge_dir.exists() else None,
        'templates_directory': shared_knowledge_dir / 'templates' if shared_knowledge_dir.exists() else None
    }
    
    completed_items = []
    for item, path in completion_indicators.items():
        if path and path.exists():
            completed_items.append(item)
            print(f"   ✅ {item} - FOUND")
        else:
            print(f"   ❌ {item} - NOT FOUND")
    
    completion_percentage = (len(completed_items) / len(completion_indicators)) * 100
    
    print(f"\n📊 Overall Completion: {completion_percentage:.0f}%")
    
    if completion_percentage == 100:
        print("\n✅ VERDICT: Archaeologist analysis appears COMPLETE!")
        print("   All expected deliverables are present in shared-knowledge directory.")
        
        # Check if findings were shared
        if archaeologist_files:
            print("\n📡 Knowledge sharing status: COMPLETED")
            print(f"   {len(archaeologist_files)} knowledge items shared via AgentCommunication")
        else:
            print("\n⚠️  Knowledge sharing status: No files found in knowledge-base")
            print("   The archaeologist may not have run share_archaeological_findings.py")
    else:
        print("\n⚠️  VERDICT: Archaeologist analysis appears INCOMPLETE!")
        print("   Some expected deliverables are missing.")
        print("\n   Next steps:")
        print("   1. Check if archaeologist task is still running")
        print("   2. Review Celery logs for any errors")
        print("   3. Consider restarting the archaeologist task")

if __name__ == '__main__':
    try:
        check_archaeologist_status()
    except KeyboardInterrupt:
        print("\n\n🛑 Status check interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during status check: {e}")
        import traceback
        traceback.print_exc()