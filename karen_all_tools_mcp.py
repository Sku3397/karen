#!/usr/bin/env python3
"""
Karen All Tools MCP Server - Standalone Implementation
Combines all Karen tools in one server without external MCP dependency
"""

import os
import sys
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import subprocess
import redis
from pathlib import Path

# Configure logging to stderr so it doesn't interfere with MCP protocol
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

class KarenMCPServer:
    """Standalone MCP server implementation."""
    
    def __init__(self):
        self.server_name = "karen-all-tools"
        self.server_version = "1.0.0"
        self.protocol_version = "0.1.0"
        self.project_root = Path("/workspace")
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming JSON-RPC requests."""
        method = request.get("method")
        id = request.get("id")
        params = request.get("params", {})
        
        logger.info(f"Handling request: {method}")
        
        # Route to appropriate handler
        if method == "initialize":
            return self.handle_initialize(id, params)
        elif method == "initialized":
            return None  # No response needed
        elif method == "tools/list":
            return self.handle_list_tools(id)
        elif method == "tools/call":
            return await self.handle_call_tool(id, params)
        else:
            return self.error_response(id, -32601, f"Method not found: {method}")
    
    def handle_initialize(self, id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "protocolVersion": self.protocol_version,
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": self.server_name,
                    "version": self.server_version
                }
            }
        }
    
    def handle_list_tools(self, id: Any) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = [
            # System monitoring tools
            {
                "name": "karen_system_health",
                "description": "Get comprehensive Karen AI system health status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "karen_check_redis",
                "description": "Check Redis server connectivity and status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            # Project structure tools
            {
                "name": "karen_project_structure",
                "description": "Get hierarchical project structure",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "max_depth": {
                            "type": "integer",
                            "description": "Maximum depth to explore",
                            "default": 3
                        }
                    }
                }
            },
            # Git tools
            {
                "name": "karen_git_status",
                "description": "Get git repository status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            # Search tools
            {
                "name": "karen_search_files",
                "description": "Search for files by name pattern",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "File name pattern to search"
                        },
                        "directory": {
                            "type": "string",
                            "description": "Directory to search in",
                            "default": "."
                        }
                    },
                    "required": ["pattern"]
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "tools": tools
            }
        }
    
    async def handle_call_tool(self, id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"Calling tool: {tool_name}")
        
        try:
            if tool_name == "karen_system_health":
                result = await self.karen_system_health()
            elif tool_name == "karen_check_redis":
                result = await self.karen_check_redis()
            elif tool_name == "karen_project_structure":
                result = await self.karen_project_structure(arguments.get("max_depth", 3))
            elif tool_name == "karen_git_status":
                result = await self.karen_git_status()
            elif tool_name == "karen_search_files":
                result = await self.karen_search_files(
                    arguments.get("pattern"),
                    arguments.get("directory", ".")
                )
            else:
                return self.error_response(id, -32602, f"Unknown tool: {tool_name}")
            
            return {
                "jsonrpc": "2.0",
                "id": id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error in tool {tool_name}: {e}")
            return self.error_response(id, -32603, str(e))
    
    def error_response(self, id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            "jsonrpc": "2.0",
            "id": id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    # Tool implementations
    
    async def karen_system_health(self) -> str:
        """Get system health status."""
        health = {
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check Redis
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2)
            r.ping()
            health["components"]["redis"] = "✅ Connected"
        except:
            health["components"]["redis"] = "❌ Not connected"
        
        # Check Python
        health["components"]["python"] = f"✅ {sys.version.split()[0]}"
        
        # Check project
        health["components"]["project_root"] = f"✅ {self.project_root}"
        
        # Format output
        output = [
            "Karen AI System Health Report",
            "=" * 40,
            f"Timestamp: {health['timestamp']}",
            "",
            "Components:"
        ]
        
        for component, status in health["components"].items():
            output.append(f"  {component}: {status}")
        
        return "\n".join(output)
    
    async def karen_check_redis(self) -> str:
        """Check Redis connectivity."""
        output = ["Redis Status:", ""]
        
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2)
            r.ping()
            info = r.info()
            
            output.append("✅ Connected successfully")
            output.append(f"Version: {info.get('redis_version', 'unknown')}")
            output.append(f"Uptime: {info.get('uptime_in_seconds', 0)} seconds")
            output.append(f"Memory: {info.get('used_memory_human', 'unknown')}")
        except Exception as e:
            output.append("❌ Connection failed")
            output.append(f"Error: {str(e)}")
            output.append("")
            output.append("Troubleshooting:")
            output.append("1. Check if Redis is installed")
            output.append("2. Start Redis: redis-server")
            output.append("3. Or use Docker: docker run -d -p 6379:6379 redis")
        
        return "\n".join(output)
    
    async def karen_project_structure(self, max_depth: int = 3) -> str:
        """Get project structure."""
        output = [f"Project Structure (max depth: {max_depth}):", ""]
        
        def explore(path: Path, depth: int = 0, prefix: str = ""):
            if depth > max_depth:
                return
            
            try:
                items = sorted(path.iterdir())
                dirs = [i for i in items if i.is_dir() and not i.name.startswith('.')]
                files = [i for i in items if i.is_file() and not i.name.startswith('.')]
                
                # Show directories first
                for i, dir in enumerate(dirs[:10]):  # Limit to 10 items
                    is_last = (i == len(dirs) - 1) and len(files) == 0
                    output.append(f"{prefix}{'└── ' if is_last else '├── '}{dir.name}/")
                    if depth < max_depth:
                        explore(dir, depth + 1, prefix + ("    " if is_last else "│   "))
                
                # Show files
                for i, file in enumerate(files[:10]):  # Limit to 10 items
                    is_last = i == len(files) - 1
                    output.append(f"{prefix}{'└── ' if is_last else '├── '}{file.name}")
                
                if len(dirs) > 10 or len(files) > 10:
                    output.append(f"{prefix}└── ... more items")
                    
            except PermissionError:
                output.append(f"{prefix}└── [Permission Denied]")
        
        explore(self.project_root)
        return "\n".join(output)
    
    async def karen_git_status(self) -> str:
        """Get git status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return "❌ Not a git repository"
            
            # Get branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            output = ["Git Status:", ""]
            output.append(f"Branch: {branch_result.stdout.strip() or 'detached HEAD'}")
            output.append("")
            
            if result.stdout:
                output.append("Changes:")
                for line in result.stdout.strip().split('\n'):
                    output.append(f"  {line}")
            else:
                output.append("✅ Working tree clean")
            
            return "\n".join(output)
            
        except FileNotFoundError:
            return "❌ Git not installed"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def karen_search_files(self, pattern: str, directory: str = ".") -> str:
        """Search for files."""
        if not pattern:
            return "❌ No search pattern provided"
        
        search_dir = self.project_root / directory
        if not search_dir.exists():
            return f"❌ Directory not found: {directory}"
        
        output = [f"Searching for '{pattern}' in {directory}:", ""]
        
        matches = []
        try:
            for path in search_dir.rglob(pattern):
                if not any(part.startswith('.') for part in path.parts):
                    matches.append(str(path.relative_to(self.project_root)))
        except Exception as e:
            return f"❌ Search error: {str(e)}"
        
        if matches:
            output.append(f"Found {len(matches)} matches:")
            for match in matches[:20]:  # Limit to 20 results
                output.append(f"  {match}")
            if len(matches) > 20:
                output.append(f"  ... and {len(matches) - 20} more")
        else:
            output.append("No matches found")
        
        return "\n".join(output)


async def read_json_rpc():
    """Read a JSON-RPC message from stdin."""
    loop = asyncio.get_event_loop()
    line = await loop.run_in_executor(None, sys.stdin.readline)
    if not line:
        return None
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return None


async def write_json_rpc(message: Dict[str, Any]):
    """Write a JSON-RPC message to stdout."""
    if message is not None:
        print(json.dumps(message), flush=True)


async def main():
    """Main server loop."""
    logger.info("Karen All Tools MCP Server starting...")
    
    server = KarenMCPServer()
    
    while True:
        try:
            request = await read_json_rpc()
            if request is None:
                logger.info("No more input, shutting down")
                break
            
            response = await server.handle_request(request)
            if response:
                await write_json_rpc(response)
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            break
        except Exception as e:
            logger.error(f"Server error: {e}")
            # Continue running


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass