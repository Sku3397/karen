import psutil
import os
import json
from datetime import datetime

class AgentHealthMonitor:
    def __init__(self):
        self.alerts = []
        
    def check_memory(self):
        """Monitor Node.js process memory usage"""
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            if 'node' in proc.info['name'].lower():
                memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                if memory_mb > 6000:  # Alert at 6GB
                    self.alert(f"High memory usage: {memory_mb:.0f}MB")
                    
    def alert(self, message):
        """Send alerts about memory issues"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'type': 'memory_warning'
        }
        self.alerts.append(alert)
        print(f"⚠️ ALERT: {message}")