#!/usr/bin/env python3
"""
Agent Communication Monitor for Email Processing
Monitors inter-agent communication during email processing pipeline
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.agent_communication import AgentCommunication

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_communication_monitor.log')
    ]
)
logger = logging.getLogger(__name__)

class AgentCommunicationMonitor:
    """Real-time monitor for inter-agent communication during email processing"""
    
    def __init__(self, monitor_duration_minutes: int = 10):
        self.monitor_duration = monitor_duration_minutes
        self.comm = AgentCommunication('monitor')
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=monitor_duration_minutes)
        
        # Communication tracking
        self.messages_log = []
        self.agent_status_log = []
        self.knowledge_updates = []
        self.task_assignments = []
        
        # File system paths for monitoring
        self.comm_dir = Path(PROJECT_ROOT) / 'autonomous-agents' / 'communication'
        self.inbox_dir = self.comm_dir / 'inbox'
        self.status_dir = self.comm_dir / 'status'
        self.knowledge_dir = self.comm_dir / 'knowledge-base'
        
        # Monitoring flags
        self.monitoring_active = False
        self.monitoring_thread = None
        
        logger.info(f"Agent Communication Monitor initialized for {monitor_duration_minutes} minutes")
    
    def start_monitoring(self):
        """Start real-time monitoring of agent communication"""
        print("\n🔍 Starting Agent Communication Monitor")
        print("=" * 60)
        print(f"📅 Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ Duration: {self.monitor_duration} minutes")
        print(f"🏁 End Time: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.monitoring_active = True
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Start Redis message listener in main thread
        try:
            self._start_redis_listener()
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
            self.stop_monitoring()
    
    def _monitoring_loop(self):
        """Main monitoring loop for file-based communication"""
        last_check = {}
        
        while self.monitoring_active and datetime.now() < self.end_time:
            try:
                # Monitor inbox messages
                self._check_inbox_messages(last_check)
                
                # Monitor agent status updates
                self._check_agent_status()
                
                # Monitor knowledge base updates
                self._check_knowledge_updates(last_check)
                
                # Print periodic summary
                current_time = datetime.now()
                if (current_time - self.start_time).seconds % 30 == 0:
                    self._print_monitoring_summary()
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(5)
    
    def _start_redis_listener(self):
        """Listen for Redis pub/sub messages"""
        try:
            # Subscribe to agent communication channels
            channels = [
                'agent_communication',
                'email_processing',
                'task_assignment',
                'agent_status',
                'emergency_alerts'
            ]
            
            print(f"\n📡 Listening for Redis messages on channels: {channels}")
            
            def message_callback(message):
                self._handle_redis_message(message)
            
            self.comm.listen_for_messages(message_callback, channels)
            
        except Exception as e:
            logger.error(f"Error starting Redis listener: {e}", exc_info=True)
            print(f"⚠️  Redis listener failed: {e}")
    
    def _handle_redis_message(self, message):
        """Handle incoming Redis pub/sub messages"""
        try:
            timestamp = datetime.now()
            
            # Parse message data
            if isinstance(message.get('data'), bytes):
                data = json.loads(message['data'].decode('utf-8'))
            else:
                data = message.get('data', {})
            
            channel = message.get('channel', 'unknown')
            
            # Log the message
            message_log = {
                'timestamp': timestamp.isoformat(),
                'channel': channel,
                'type': 'redis_pubsub',
                'data': data
            }
            
            self.messages_log.append(message_log)
            
            # Print real-time message
            self._print_real_time_message(message_log)
            
        except Exception as e:
            logger.error(f"Error handling Redis message: {e}", exc_info=True)
    
    def _check_inbox_messages(self, last_check):
        """Check for new inbox messages"""
        try:
            if not self.inbox_dir.exists():
                return
            
            for agent_dir in self.inbox_dir.iterdir():
                if not agent_dir.is_dir():
                    continue
                
                agent_name = agent_dir.name
                
                # Get modification time for tracking new files
                if agent_name not in last_check:
                    last_check[agent_name] = {}
                
                for message_file in agent_dir.glob('*.json'):
                    file_key = str(message_file)
                    file_mtime = message_file.stat().st_mtime
                    
                    # Check if this is a new or updated file
                    if file_key not in last_check[agent_name] or file_mtime > last_check[agent_name][file_key]:
                        last_check[agent_name][file_key] = file_mtime
                        self._process_inbox_message(agent_name, message_file)
        
        except Exception as e:
            logger.error(f"Error checking inbox messages: {e}", exc_info=True)
    
    def _process_inbox_message(self, agent_name, message_file):
        """Process a new inbox message"""
        try:
            with open(message_file, 'r') as f:
                message_data = json.load(f)
            
            timestamp = datetime.now()
            
            message_log = {
                'timestamp': timestamp.isoformat(),
                'agent': agent_name,
                'file': message_file.name,
                'type': 'inbox_message',
                'from': message_data.get('from', 'unknown'),
                'to': message_data.get('to', agent_name),
                'message_type': message_data.get('type', 'unknown'),
                'content_preview': str(message_data.get('content', {}))[:100]
            }
            
            self.messages_log.append(message_log)
            self._print_real_time_message(message_log)
            
        except Exception as e:
            logger.error(f"Error processing inbox message {message_file}: {e}", exc_info=True)
    
    def _check_agent_status(self):
        """Check agent status updates"""
        try:
            if not self.status_dir.exists():
                return
            
            for status_file in self.status_dir.glob('*.json'):
                try:
                    with open(status_file, 'r') as f:
                        status_data = json.load(f)
                    
                    # Only log recent status updates
                    last_update = status_data.get('last_updated', '')
                    if last_update:
                        update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                        if update_time > self.start_time:
                            status_log = {
                                'timestamp': datetime.now().isoformat(),
                                'agent': status_file.stem,
                                'type': 'status_update',
                                'status': status_data.get('status', 'unknown'),
                                'progress': status_data.get('progress', 0),
                                'details': status_data.get('details', {})
                            }
                            
                            # Avoid duplicate status logs
                            if not any(log.get('agent') == status_log['agent'] and 
                                     log.get('status') == status_log['status'] 
                                     for log in self.agent_status_log[-5:]):
                                self.agent_status_log.append(status_log)
                                self._print_real_time_message(status_log)
                
                except Exception as e:
                    logger.warning(f"Error reading status file {status_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error checking agent status: {e}", exc_info=True)
    
    def _check_knowledge_updates(self, last_check):
        """Check for knowledge base updates"""
        try:
            if not self.knowledge_dir.exists():
                return
            
            if 'knowledge' not in last_check:
                last_check['knowledge'] = {}
            
            for knowledge_file in self.knowledge_dir.glob('*.json'):
                file_key = str(knowledge_file)
                file_mtime = knowledge_file.stat().st_mtime
                
                if file_key not in last_check['knowledge'] or file_mtime > last_check['knowledge'][file_key]:
                    last_check['knowledge'][file_key] = file_mtime
                    self._process_knowledge_update(knowledge_file)
        
        except Exception as e:
            logger.error(f"Error checking knowledge updates: {e}", exc_info=True)
    
    def _process_knowledge_update(self, knowledge_file):
        """Process a knowledge base update"""
        try:
            with open(knowledge_file, 'r') as f:
                knowledge_data = json.load(f)
            
            knowledge_log = {
                'timestamp': datetime.now().isoformat(),
                'type': 'knowledge_update',
                'file': knowledge_file.name,
                'knowledge_type': knowledge_data.get('type', 'unknown'),
                'source_agent': knowledge_data.get('source_agent', 'unknown'),
                'content_preview': str(knowledge_data.get('content', {}))[:100]
            }
            
            self.knowledge_updates.append(knowledge_log)
            self._print_real_time_message(knowledge_log)
            
        except Exception as e:
            logger.error(f"Error processing knowledge update {knowledge_file}: {e}", exc_info=True)
    
    def _print_real_time_message(self, message_log):
        """Print real-time message updates"""
        timestamp = message_log.get('timestamp', '')
        time_str = timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp[:8]
        
        msg_type = message_log.get('type', 'unknown')
        
        if msg_type == 'inbox_message':
            print(f"📬 {time_str} | {message_log['from']} → {message_log['to']} | {message_log['message_type']}")
            print(f"   File: {message_log['file']}")
            if message_log.get('content_preview'):
                print(f"   Preview: {message_log['content_preview']}")
        
        elif msg_type == 'status_update':
            status_emoji = {'running': '🟢', 'completed': '✅', 'failed': '❌', 'waiting': '🟡'}.get(
                message_log.get('status', '').lower(), '📊'
            )
            print(f"{status_emoji} {time_str} | {message_log['agent']} | {message_log['status']} ({message_log['progress']}%)")
        
        elif msg_type == 'knowledge_update':
            print(f"🧠 {time_str} | Knowledge Update | {message_log['source_agent']} | {message_log['knowledge_type']}")
            print(f"   File: {message_log['file']}")
        
        elif msg_type == 'redis_pubsub':
            print(f"📡 {time_str} | Redis | {message_log['channel']} | {message_log['data']}")
        
        print()  # Add spacing
    
    def _print_monitoring_summary(self):
        """Print periodic monitoring summary"""
        current_time = datetime.now()
        elapsed = current_time - self.start_time
        remaining = self.end_time - current_time
        
        print(f"\n📊 MONITORING SUMMARY - {current_time.strftime('%H:%M:%S')}")
        print(f"⏱️  Elapsed: {elapsed.seconds//60}m {elapsed.seconds%60}s | Remaining: {remaining.seconds//60}m {remaining.seconds%60}s")
        print(f"📬 Messages: {len(self.messages_log)} | 📊 Status Updates: {len(self.agent_status_log)} | 🧠 Knowledge: {len(self.knowledge_updates)}")
        print("-" * 40)
    
    def stop_monitoring(self):
        """Stop monitoring and generate final report"""
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        self._generate_final_report()
    
    def _generate_final_report(self):
        """Generate comprehensive monitoring report"""
        print("\n" + "=" * 80)
        print("📊 AGENT COMMUNICATION MONITORING REPORT")
        print("=" * 80)
        
        total_time = datetime.now() - self.start_time
        
        print(f"📅 Monitoring Period: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total Duration: {total_time.seconds//60} minutes {total_time.seconds%60} seconds")
        
        # Message Summary
        print(f"\n📬 MESSAGE SUMMARY")
        print(f"   Total Messages: {len(self.messages_log)}")
        print(f"   Status Updates: {len(self.agent_status_log)}")
        print(f"   Knowledge Updates: {len(self.knowledge_updates)}")
        
        # Agent Activity
        agent_activity = {}
        for msg in self.messages_log:
            if msg.get('type') == 'inbox_message':
                agent = msg.get('to', 'unknown')
                agent_activity[agent] = agent_activity.get(agent, 0) + 1
        
        if agent_activity:
            print(f"\n🤖 AGENT ACTIVITY")
            for agent, count in sorted(agent_activity.items(), key=lambda x: x[1], reverse=True):
                print(f"   {agent}: {count} messages")
        
        # Message Types
        message_types = {}
        for msg in self.messages_log:
            msg_type = msg.get('message_type', msg.get('type', 'unknown'))
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        if message_types:
            print(f"\n📋 MESSAGE TYPES")
            for msg_type, count in sorted(message_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   {msg_type}: {count}")
        
        # Recent Activity (last 10 messages)
        if self.messages_log:
            print(f"\n📝 RECENT ACTIVITY (Last 10 messages)")
            for msg in self.messages_log[-10:]:
                timestamp = msg.get('timestamp', '')
                time_str = timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp
                
                if msg.get('type') == 'inbox_message':
                    print(f"   {time_str} | {msg['from']} → {msg['to']} | {msg['message_type']}")
                else:
                    print(f"   {time_str} | {msg.get('type', 'unknown')} | {str(msg)[:60]}...")
        
        # Save detailed report
        self._save_detailed_report()
        
        print(f"\n✅ Monitoring completed. Detailed report saved to 'agent_communication_report.json'")
    
    def _save_detailed_report(self):
        """Save detailed monitoring report to file"""
        report = {
            'monitoring_period': {
                'start': self.start_time.isoformat(),
                'end': datetime.now().isoformat(),
                'duration_minutes': self.monitor_duration
            },
            'summary': {
                'total_messages': len(self.messages_log),
                'status_updates': len(self.agent_status_log),
                'knowledge_updates': len(self.knowledge_updates)
            },
            'messages': self.messages_log,
            'status_updates': self.agent_status_log,
            'knowledge_updates': self.knowledge_updates
        }
        
        with open('agent_communication_report.json', 'w') as f:
            json.dump(report, f, indent=2)

def main():
    """Main monitoring function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor agent communication during email processing")
    parser.add_argument('--duration', '-d', type=int, default=10, 
                       help='Monitoring duration in minutes (default: 10)')
    parser.add_argument('--channels', '-c', nargs='+', 
                       default=['agent_communication', 'email_processing', 'task_assignment'],
                       help='Redis channels to monitor')
    
    args = parser.parse_args()
    
    print("🔍 Karen AI Agent Communication Monitor")
    print("=" * 50)
    print(f"📡 Monitoring agent communication for {args.duration} minutes")
    print(f"📻 Redis channels: {args.channels}")
    print("\n💡 Usage tips:")
    print("   • Run email tests in another terminal while this monitors")
    print("   • Press Ctrl+C to stop monitoring early")
    print("   • Detailed report will be saved as 'agent_communication_report.json'")
    
    try:
        monitor = AgentCommunicationMonitor(args.duration)
        monitor.start_monitoring()
        
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring interrupted by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}", exc_info=True)
        print(f"❌ Monitoring failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())