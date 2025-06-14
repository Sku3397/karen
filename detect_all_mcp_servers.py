#!/usr/bin/env python3
"""
Detect all MCP servers running on the system
"""
import psutil
import socket
import json
import os
from pathlib import Path

def find_mcp_processes():
    """Find all processes that might be MCP servers"""
    mcp_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if any(keyword in cmdline.lower() for keyword in ['mcp', 'karen', 'agent', 'server']):
                mcp_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': cmdline
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return mcp_processes

def scan_ports():
    """Scan for services on common MCP ports"""
    common_ports = [3000, 8000, 8080, 5000, 9000]
    open_ports = []
    
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        except:
            pass
    
    return open_ports

def find_mcp_configs():
    """Find MCP configuration files"""
    config_locations = [
        Path.home() / ".cursor" / "mcp.json",
        Path.home() / ".config" / "cursor" / "mcp.json", 
        Path.home() / "AppData" / "Roaming" / "Cursor" / "User" / "mcp.json",
        Path.home() / "AppData" / "Local" / "Cursor" / "mcp.json",
        Path.cwd() / "mcp_config.json",
        Path.cwd() / "mcp.json"
    ]
    
    found_configs = []
    for config_path in config_locations:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                found_configs.append({
                    'path': str(config_path),
                    'config': config
                })
            except:
                found_configs.append({
                    'path': str(config_path),
                    'error': 'Could not parse JSON'
                })
    
    return found_configs

def main():
    print("🔍 SCANNING FOR ALL MCP SERVERS ON SYSTEM")
    print("=" * 50)
    
    # Find processes
    processes = find_mcp_processes()
    print(f"\n📋 POTENTIAL MCP PROCESSES ({len(processes)}):")
    for proc in processes:
        print(f"  PID {proc['pid']}: {proc['name']}")
        print(f"    Command: {proc['cmdline'][:100]}...")
    
    # Check ports
    ports = scan_ports()
    print(f"\n🌐 OPEN PORTS ({len(ports)}):")
    for port in ports:
        print(f"  localhost:{port} - LISTENING")
    
    # Find configs
    configs = find_mcp_configs()
    print(f"\n⚙️ MCP CONFIGURATIONS ({len(configs)}):")
    for config in configs:
        print(f"  📁 {config['path']}")
        if 'error' in config:
            print(f"    ❌ Error: {config['error']}")
        else:
            servers = config['config'].get('mcpServers', {})
            print(f"    🔧 Servers: {list(servers.keys())}")
    
    print("\n" + "=" * 50)
    print("🎯 ANALYSIS COMPLETE")

if __name__ == "__main__":
    main() 