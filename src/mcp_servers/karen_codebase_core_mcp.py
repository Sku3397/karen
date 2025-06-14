"""
Karen Codebase Core MCP Server - Phase 1
Provides core codebase discovery and navigation capabilities.
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    CallToolRequest,
    ListToolsResult
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("karen_codebase_core_mcp")

class KarenCodebaseCoreServer:
    """MCP server for core Karen codebase navigation and discovery."""
    
    def __init__(self, workspace_root: str = "/workspace"):
        self.workspace_root = Path(workspace_root)
        self.server = Server("karen-codebase-core")
        self.setup_handlers()
        
    def setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="karen_get_project_structure",
                        description="Get the high-level project structure of Karen codebase",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "include_hidden": {
                                    "type": "boolean",
                                    "description": "Include hidden files/directories",
                                    "default": False
                                }
                            }
                        }
                    ),
                    Tool(
                        name="karen_list_agents",
                        description="List all agent implementations in the Karen system",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    ),
                    Tool(
                        name="karen_get_agent_details",
                        description="Get details about a specific agent including its responsibilities and implementation",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "agent_name": {
                                    "type": "string",
                                    "description": "Name of the agent (e.g., 'orchestrator', 'email', 'sms')"
                                }
                            },
                            "required": ["agent_name"]
                        }
                    ),
                    Tool(
                        name="karen_find_configuration",
                        description="Find and retrieve configuration files",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "config_type": {
                                    "type": "string",
                                    "description": "Type of configuration to find (e.g., 'celery', 'oauth', 'api', 'docker')"
                                }
                            }
                        }
                    ),
                    Tool(
                        name="karen_get_documentation",
                        description="Retrieve project documentation including CLAUDE.md and README files",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "doc_name": {
                                    "type": "string",
                                    "description": "Name of the documentation file (default: CLAUDE.md)"
                                }
                            }
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls."""
            try:
                tool_name = request.params.name
                arguments = request.params.arguments or {}
                
                if tool_name == "karen_get_project_structure":
                    result = await self.get_project_structure(
                        arguments.get("include_hidden", False)
                    )
                elif tool_name == "karen_list_agents":
                    result = await self.list_agents()
                elif tool_name == "karen_get_agent_details":
                    result = await self.get_agent_details(
                        arguments.get("agent_name")
                    )
                elif tool_name == "karen_find_configuration":
                    result = await self.find_configuration(
                        arguments.get("config_type")
                    )
                elif tool_name == "karen_get_documentation":
                    result = await self.get_documentation(
                        arguments.get("doc_name", "CLAUDE.md")
                    )
                else:
                    result = f"Unknown tool: {tool_name}"
                
                return CallToolResult(
                    content=[TextContent(text=json.dumps(result, indent=2))]
                )
                
            except Exception as e:
                logger.error(f"Error in tool execution: {e}", exc_info=True)
                return CallToolResult(
                    content=[TextContent(text=f"Error: {str(e)}")]
                )
    
    async def get_project_structure(self, include_hidden: bool = False) -> Dict[str, Any]:
        """Get the high-level project structure."""
        structure = {
            "root": str(self.workspace_root),
            "main_directories": [],
            "key_files": [],
            "agent_structure": {},
            "configuration_files": []
        }
        
        # Main directories
        main_dirs = ["src", "tests", "scripts", "autonomous-agents", "logs", "templates"]
        for dir_name in main_dirs:
            dir_path = self.workspace_root / dir_name
            if dir_path.exists():
                structure["main_directories"].append({
                    "name": dir_name,
                    "path": str(dir_path),
                    "exists": True
                })
        
        # Key files
        key_files = [
            "CLAUDE.md", "README.md", "docker-compose.yml", 
            "requirements.txt", ".env", ".env.example"
        ]
        for file_name in key_files:
            file_path = self.workspace_root / file_name
            if file_path.exists():
                structure["key_files"].append({
                    "name": file_name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size
                })
        
        # Agent directories
        agent_dirs = {
            "core_agents": self.workspace_root / "src",
            "autonomous_agents": self.workspace_root / "autonomous-agents" / "agents"
        }
        
        for category, base_path in agent_dirs.items():
            if base_path.exists():
                structure["agent_structure"][category] = []
                for item in base_path.iterdir():
                    if item.is_file() and item.name.endswith("_agent.py"):
                        structure["agent_structure"][category].append(item.name)
                    elif item.is_dir() and (base_path.parent / "agents").exists():
                        structure["agent_structure"][category].append(f"{item.name}/")
        
        return structure
    
    async def list_agents(self) -> Dict[str, Any]:
        """List all agent implementations."""
        agents = {
            "core_agents": [],
            "autonomous_agents": [],
            "agent_details": {}
        }
        
        # Core agents in src/
        src_path = self.workspace_root / "src"
        if src_path.exists():
            for file in src_path.glob("*_agent.py"):
                agent_name = file.stem
                agents["core_agents"].append(agent_name)
                
                # Get basic details
                agents["agent_details"][agent_name] = {
                    "type": "core",
                    "file": str(file),
                    "has_tests": (self.workspace_root / "tests" / f"test_{file.name}").exists()
                }
        
        # Autonomous agents
        autonomous_path = self.workspace_root / "autonomous-agents" / "agents"
        if autonomous_path.exists():
            for agent_dir in autonomous_path.iterdir():
                if agent_dir.is_dir():
                    agent_name = agent_dir.name
                    agents["autonomous_agents"].append(agent_name)
                    
                    main_file = agent_dir / f"{agent_name}_agent.py"
                    if not main_file.exists():
                        main_file = agent_dir / "agent.py"
                    
                    agents["agent_details"][agent_name] = {
                        "type": "autonomous",
                        "directory": str(agent_dir),
                        "main_file": str(main_file) if main_file.exists() else None,
                        "has_config": (agent_dir / "config.json").exists(),
                        "has_tests": (agent_dir / "tests").exists()
                    }
        
        return agents
    
    async def get_agent_details(self, agent_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific agent."""
        if not agent_name:
            return {"error": "agent_name is required"}
        
        # Normalize agent name
        if not agent_name.endswith("_agent"):
            agent_name = f"{agent_name}_agent"
        
        details = {
            "name": agent_name,
            "found": False,
            "type": None,
            "files": [],
            "imports": [],
            "classes": [],
            "responsibilities": []
        }
        
        # Check core agents
        core_file = self.workspace_root / "src" / f"{agent_name}.py"
        if core_file.exists():
            details["found"] = True
            details["type"] = "core"
            details["main_file"] = str(core_file)
            
            # Read file to extract details
            try:
                content = core_file.read_text()
                lines = content.split('\n')
                
                # Extract imports
                for line in lines:
                    if line.startswith('import ') or line.startswith('from '):
                        details["imports"].append(line.strip())
                
                # Extract classes
                for line in lines:
                    if line.startswith('class ') and 'Agent' in line:
                        class_name = line.split('(')[0].replace('class ', '').strip()
                        details["classes"].append(class_name)
                
                # Extract docstrings for responsibilities
                in_docstring = False
                for line in lines:
                    if '"""' in line:
                        in_docstring = not in_docstring
                        if in_docstring and len(details["responsibilities"]) == 0:
                            doc_line = line.split('"""')[1].strip()
                            if doc_line:
                                details["responsibilities"].append(doc_line)
                    elif in_docstring and line.strip():
                        details["responsibilities"].append(line.strip())
                
            except Exception as e:
                details["read_error"] = str(e)
        
        # Check autonomous agents
        agent_base = agent_name.replace('_agent', '')
        autonomous_dir = self.workspace_root / "autonomous-agents" / "agents" / agent_base
        if autonomous_dir.exists():
            details["found"] = True
            details["type"] = "autonomous"
            details["directory"] = str(autonomous_dir)
            
            # List all files in the agent directory
            for file in autonomous_dir.rglob("*.py"):
                details["files"].append(str(file.relative_to(autonomous_dir)))
            
            # Check for specific files
            special_files = ["config.json", "README.md", "requirements.txt"]
            for special in special_files:
                if (autonomous_dir / special).exists():
                    details["files"].append(special)
        
        return details
    
    async def find_configuration(self, config_type: Optional[str] = None) -> Dict[str, Any]:
        """Find configuration files based on type."""
        configs = {
            "environment": [],
            "python": [],
            "docker": [],
            "oauth": [],
            "celery": [],
            "api": [],
            "other": []
        }
        
        # Environment configs
        for env_file in self.workspace_root.glob(".env*"):
            configs["environment"].append({
                "file": env_file.name,
                "path": str(env_file),
                "size": env_file.stat().st_size
            })
        
        # Python configs
        python_configs = ["config.py", "settings.py", "django_settings.py"]
        for pc in python_configs:
            for config_file in self.workspace_root.rglob(pc):
                configs["python"].append({
                    "file": config_file.name,
                    "path": str(config_file),
                    "relative_path": str(config_file.relative_to(self.workspace_root))
                })
        
        # Docker configs
        docker_files = ["docker-compose.yml", "Dockerfile", "docker-compose.*.yml"]
        for pattern in docker_files:
            for docker_file in self.workspace_root.glob(pattern):
                configs["docker"].append({
                    "file": docker_file.name,
                    "path": str(docker_file)
                })
        
        # OAuth token files
        for token_file in self.workspace_root.glob("*token*.json"):
            configs["oauth"].append({
                "file": token_file.name,
                "path": str(token_file)
            })
        
        # Celery configs
        if (self.workspace_root / "src" / "celery_app.py").exists():
            configs["celery"].append({
                "file": "celery_app.py",
                "path": str(self.workspace_root / "src" / "celery_app.py")
            })
        
        # Filter by type if specified
        if config_type:
            if config_type in configs:
                return {config_type: configs[config_type]}
            else:
                # Search in all categories
                filtered = {}
                for category, items in configs.items():
                    filtered_items = [
                        item for item in items 
                        if config_type.lower() in item["file"].lower()
                    ]
                    if filtered_items:
                        filtered[category] = filtered_items
                return filtered
        
        return configs
    
    async def get_documentation(self, doc_name: str = "CLAUDE.md") -> Dict[str, Any]:
        """Retrieve project documentation."""
        docs = {
            "requested": doc_name,
            "found": False,
            "content": None,
            "other_docs": []
        }
        
        # Look for the requested document
        doc_path = self.workspace_root / doc_name
        if doc_path.exists():
            docs["found"] = True
            docs["path"] = str(doc_path)
            try:
                docs["content"] = doc_path.read_text()
                docs["size"] = len(docs["content"])
                docs["lines"] = docs["content"].count('\n') + 1
            except Exception as e:
                docs["error"] = f"Could not read file: {str(e)}"
        
        # Find other documentation files
        doc_patterns = ["*.md", "*.MD", "*.rst", "*.txt"]
        for pattern in doc_patterns:
            for doc_file in self.workspace_root.glob(pattern):
                if doc_file.name != doc_name:
                    docs["other_docs"].append({
                        "name": doc_file.name,
                        "path": str(doc_file),
                        "size": doc_file.stat().st_size
                    })
        
        # Also check docs/ directory if it exists
        docs_dir = self.workspace_root / "docs"
        if docs_dir.exists():
            for doc_file in docs_dir.rglob("*"):
                if doc_file.is_file():
                    docs["other_docs"].append({
                        "name": doc_file.name,
                        "path": str(doc_file),
                        "relative_path": str(doc_file.relative_to(self.workspace_root))
                    })
        
        return docs
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)

def main():
    """Main entry point."""
    server = KarenCodebaseCoreServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()