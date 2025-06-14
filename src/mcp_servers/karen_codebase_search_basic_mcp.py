"""
Karen Codebase Search Basic MCP Server - Phase 2A
Provides basic code search capabilities for the Karen codebase.
"""

import os
import re
import json
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import fnmatch

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
logger = logging.getLogger("karen_codebase_search_basic_mcp")

class KarenCodebaseSearchBasicServer:
    """MCP server for basic Karen codebase search capabilities."""
    
    def __init__(self, workspace_root: str = "/workspace"):
        self.workspace_root = Path(workspace_root)
        self.server = Server("karen-codebase-search-basic")
        self.setup_handlers()
        
        # Common exclude patterns
        self.exclude_patterns = {
            'node_modules', '__pycache__', '.git', '.venv', 'venv',
            '*.pyc', '*.pyo', '*.log', '*.sqlite3', '.DS_Store'
        }
        
    def setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="karen_search_files",
                        description="Search for files by name pattern in Karen codebase",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "pattern": {
                                    "type": "string",
                                    "description": "File name pattern to search (e.g., '*_agent.py', 'test_*.py')"
                                },
                                "directory": {
                                    "type": "string",
                                    "description": "Directory to search in (relative to workspace root)",
                                    "default": "."
                                },
                                "recursive": {
                                    "type": "boolean",
                                    "description": "Search recursively in subdirectories",
                                    "default": True
                                }
                            },
                            "required": ["pattern"]
                        }
                    ),
                    Tool(
                        name="karen_search_code",
                        description="Search for code patterns or text in Karen codebase files",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "pattern": {
                                    "type": "string",
                                    "description": "Text or regex pattern to search for"
                                },
                                "file_pattern": {
                                    "type": "string",
                                    "description": "File pattern to search in (e.g., '*.py')",
                                    "default": "*"
                                },
                                "directory": {
                                    "type": "string",
                                    "description": "Directory to search in",
                                    "default": "."
                                },
                                "regex": {
                                    "type": "boolean",
                                    "description": "Treat pattern as regex",
                                    "default": False
                                },
                                "case_sensitive": {
                                    "type": "boolean",
                                    "description": "Case sensitive search",
                                    "default": True
                                }
                            },
                            "required": ["pattern"]
                        }
                    ),
                    Tool(
                        name="karen_find_imports",
                        description="Find all imports of a specific module or from a package",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "module_name": {
                                    "type": "string",
                                    "description": "Module or package name to find imports of"
                                },
                                "import_type": {
                                    "type": "string",
                                    "enum": ["all", "from", "import"],
                                    "description": "Type of import to find",
                                    "default": "all"
                                }
                            },
                            "required": ["module_name"]
                        }
                    ),
                    Tool(
                        name="karen_find_functions",
                        description="Find function definitions by name pattern",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "function_pattern": {
                                    "type": "string",
                                    "description": "Function name pattern (can use * wildcard)"
                                },
                                "async_only": {
                                    "type": "boolean",
                                    "description": "Only find async functions",
                                    "default": False
                                },
                                "include_methods": {
                                    "type": "boolean",
                                    "description": "Include class methods",
                                    "default": True
                                }
                            },
                            "required": ["function_pattern"]
                        }
                    ),
                    Tool(
                        name="karen_find_classes",
                        description="Find class definitions by name pattern",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "class_pattern": {
                                    "type": "string",
                                    "description": "Class name pattern (can use * wildcard)"
                                },
                                "base_class": {
                                    "type": "string",
                                    "description": "Filter by base class name"
                                }
                            },
                            "required": ["class_pattern"]
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
                
                if tool_name == "karen_search_files":
                    result = await self.search_files(
                        arguments.get("pattern"),
                        arguments.get("directory", "."),
                        arguments.get("recursive", True)
                    )
                elif tool_name == "karen_search_code":
                    result = await self.search_code(
                        arguments.get("pattern"),
                        arguments.get("file_pattern", "*"),
                        arguments.get("directory", "."),
                        arguments.get("regex", False),
                        arguments.get("case_sensitive", True)
                    )
                elif tool_name == "karen_find_imports":
                    result = await self.find_imports(
                        arguments.get("module_name"),
                        arguments.get("import_type", "all")
                    )
                elif tool_name == "karen_find_functions":
                    result = await self.find_functions(
                        arguments.get("function_pattern"),
                        arguments.get("async_only", False),
                        arguments.get("include_methods", True)
                    )
                elif tool_name == "karen_find_classes":
                    result = await self.find_classes(
                        arguments.get("class_pattern"),
                        arguments.get("base_class")
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
    
    def should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded from search."""
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if '*' in pattern:
                if fnmatch.fnmatch(path.name, pattern):
                    return True
            else:
                if pattern in path_str:
                    return True
        return False
    
    async def search_files(self, pattern: str, directory: str = ".", recursive: bool = True) -> Dict[str, Any]:
        """Search for files by name pattern."""
        if not pattern:
            return {"error": "pattern is required"}
        
        search_path = self.workspace_root / directory
        if not search_path.exists():
            return {"error": f"Directory not found: {directory}"}
        
        results = {
            "pattern": pattern,
            "directory": directory,
            "matches": [],
            "total_found": 0
        }
        
        try:
            if recursive:
                for file_path in search_path.rglob(pattern):
                    if file_path.is_file() and not self.should_exclude(file_path):
                        results["matches"].append({
                            "path": str(file_path),
                            "relative_path": str(file_path.relative_to(self.workspace_root)),
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
            else:
                for file_path in search_path.glob(pattern):
                    if file_path.is_file() and not self.should_exclude(file_path):
                        results["matches"].append({
                            "path": str(file_path),
                            "relative_path": str(file_path.relative_to(self.workspace_root)),
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
            
            results["total_found"] = len(results["matches"])
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    async def search_code(self, pattern: str, file_pattern: str = "*", 
                         directory: str = ".", regex: bool = False, 
                         case_sensitive: bool = True) -> Dict[str, Any]:
        """Search for code patterns in files."""
        if not pattern:
            return {"error": "pattern is required"}
        
        search_path = self.workspace_root / directory
        if not search_path.exists():
            return {"error": f"Directory not found: {directory}"}
        
        results = {
            "pattern": pattern,
            "file_pattern": file_pattern,
            "matches": [],
            "total_matches": 0,
            "files_searched": 0
        }
        
        # Compile regex if needed
        if regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                compiled_pattern = re.compile(pattern, flags)
            except re.error as e:
                return {"error": f"Invalid regex pattern: {str(e)}"}
        else:
            if not case_sensitive:
                pattern = pattern.lower()
        
        # Search files
        for file_path in search_path.rglob(file_pattern):
            if file_path.is_file() and not self.should_exclude(file_path):
                results["files_searched"] += 1
                
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                    
                    file_matches = []
                    for line_num, line in enumerate(lines, 1):
                        match_found = False
                        
                        if regex:
                            if compiled_pattern.search(line):
                                match_found = True
                        else:
                            search_line = line if case_sensitive else line.lower()
                            if pattern in search_line:
                                match_found = True
                        
                        if match_found:
                            file_matches.append({
                                "line_number": line_num,
                                "line": line.strip(),
                                "preview": line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip()
                            })
                    
                    if file_matches:
                        results["matches"].append({
                            "file": str(file_path.relative_to(self.workspace_root)),
                            "matches_count": len(file_matches),
                            "matches": file_matches[:10]  # Limit to first 10 matches per file
                        })
                        results["total_matches"] += len(file_matches)
                
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")
        
        return results
    
    async def find_imports(self, module_name: str, import_type: str = "all") -> Dict[str, Any]:
        """Find imports of a specific module."""
        if not module_name:
            return {"error": "module_name is required"}
        
        results = {
            "module_name": module_name,
            "import_type": import_type,
            "imports": [],
            "total_found": 0
        }
        
        # Patterns for different import types
        patterns = []
        if import_type in ["all", "from"]:
            patterns.append(f"from {module_name}")
        if import_type in ["all", "import"]:
            patterns.append(f"import {module_name}")
        
        # Search Python files
        for py_file in self.workspace_root.rglob("*.py"):
            if self.should_exclude(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                file_imports = []
                for line_num, line in enumerate(lines, 1):
                    line_stripped = line.strip()
                    
                    for pattern in patterns:
                        if line_stripped.startswith(pattern):
                            import_info = {
                                "line_number": line_num,
                                "import_statement": line_stripped,
                                "type": "from" if "from" in line_stripped else "import"
                            }
                            
                            # Extract what's being imported
                            if "from" in line_stripped and "import" in line_stripped:
                                parts = line_stripped.split("import")
                                if len(parts) > 1:
                                    import_info["imported_items"] = [
                                        item.strip() for item in parts[1].split(",")
                                    ]
                            
                            file_imports.append(import_info)
                
                if file_imports:
                    results["imports"].append({
                        "file": str(py_file.relative_to(self.workspace_root)),
                        "import_count": len(file_imports),
                        "imports": file_imports
                    })
                    results["total_found"] += len(file_imports)
            
            except Exception as e:
                logger.warning(f"Error reading file {py_file}: {e}")
        
        return results
    
    async def find_functions(self, function_pattern: str, async_only: bool = False, 
                           include_methods: bool = True) -> Dict[str, Any]:
        """Find function definitions."""
        if not function_pattern:
            return {"error": "function_pattern is required"}
        
        results = {
            "pattern": function_pattern,
            "async_only": async_only,
            "functions": [],
            "total_found": 0
        }
        
        # Convert wildcard pattern to regex
        regex_pattern = function_pattern.replace('*', '.*')
        regex_pattern = f"^{regex_pattern}$"
        
        try:
            compiled_pattern = re.compile(regex_pattern)
        except re.error as e:
            return {"error": f"Invalid pattern: {str(e)}"}
        
        # Search Python files
        for py_file in self.workspace_root.rglob("*.py"):
            if self.should_exclude(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                file_functions = []
                in_class = False
                current_class = None
                
                for line_num, line in enumerate(lines, 1):
                    line_stripped = line.strip()
                    
                    # Track class context
                    if line_stripped.startswith('class '):
                        in_class = True
                        current_class = line_stripped.split('(')[0].replace('class ', '').strip(':').strip()
                    elif not line.startswith(' ') and not line.startswith('\t') and line_stripped:
                        in_class = False
                        current_class = None
                    
                    # Look for function definitions
                    is_def = False
                    is_async = False
                    
                    if line_stripped.startswith('async def '):
                        is_def = True
                        is_async = True
                        func_name = line_stripped[10:].split('(')[0].strip()
                    elif line_stripped.startswith('def '):
                        is_def = True
                        func_name = line_stripped[4:].split('(')[0].strip()
                    
                    if is_def:
                        # Skip if async_only and not async
                        if async_only and not is_async:
                            continue
                        
                        # Skip methods if not including them
                        if not include_methods and in_class:
                            continue
                        
                        # Check if function name matches pattern
                        if compiled_pattern.match(func_name):
                            func_info = {
                                "name": func_name,
                                "line_number": line_num,
                                "is_async": is_async,
                                "is_method": in_class,
                                "signature": line_stripped
                            }
                            
                            if in_class:
                                func_info["class"] = current_class
                            
                            file_functions.append(func_info)
                
                if file_functions:
                    results["functions"].append({
                        "file": str(py_file.relative_to(self.workspace_root)),
                        "function_count": len(file_functions),
                        "functions": file_functions
                    })
                    results["total_found"] += len(file_functions)
            
            except Exception as e:
                logger.warning(f"Error reading file {py_file}: {e}")
        
        return results
    
    async def find_classes(self, class_pattern: str, base_class: Optional[str] = None) -> Dict[str, Any]:
        """Find class definitions."""
        if not class_pattern:
            return {"error": "class_pattern is required"}
        
        results = {
            "pattern": class_pattern,
            "base_class": base_class,
            "classes": [],
            "total_found": 0
        }
        
        # Convert wildcard pattern to regex
        regex_pattern = class_pattern.replace('*', '.*')
        regex_pattern = f"^{regex_pattern}$"
        
        try:
            compiled_pattern = re.compile(regex_pattern)
        except re.error as e:
            return {"error": f"Invalid pattern: {str(e)}"}
        
        # Search Python files
        for py_file in self.workspace_root.rglob("*.py"):
            if self.should_exclude(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                file_classes = []
                
                for line_num, line in enumerate(lines, 1):
                    line_stripped = line.strip()
                    
                    if line_stripped.startswith('class '):
                        # Extract class name and base classes
                        class_def = line_stripped[6:].strip()
                        
                        if '(' in class_def:
                            class_name = class_def.split('(')[0].strip()
                            base_part = class_def.split('(')[1].split(')')[0]
                            bases = [b.strip() for b in base_part.split(',') if b.strip()]
                        else:
                            class_name = class_def.strip(':')
                            bases = []
                        
                        # Check if class name matches pattern
                        if compiled_pattern.match(class_name):
                            # Check base class filter if specified
                            if base_class and base_class not in bases:
                                continue
                            
                            class_info = {
                                "name": class_name,
                                "line_number": line_num,
                                "bases": bases,
                                "definition": line_stripped
                            }
                            
                            # Try to get docstring
                            if line_num < len(lines):
                                next_lines = lines[line_num:line_num+5]
                                for next_line in next_lines:
                                    if '"""' in next_line or "'''" in next_line:
                                        docstring_line = next_line.strip()
                                        if docstring_line.startswith('"""') or docstring_line.startswith("'''"):
                                            class_info["docstring"] = docstring_line.strip('"""').strip("'''")
                                        break
                            
                            file_classes.append(class_info)
                
                if file_classes:
                    results["classes"].append({
                        "file": str(py_file.relative_to(self.workspace_root)),
                        "class_count": len(file_classes),
                        "classes": file_classes
                    })
                    results["total_found"] += len(file_classes)
            
            except Exception as e:
                logger.warning(f"Error reading file {py_file}: {e}")
        
        return results
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)

def main():
    """Main entry point."""
    server = KarenCodebaseSearchBasicServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()