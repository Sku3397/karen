#!/usr/bin/env python3
"""
Karen Codebase Search Basic MCP Server - Phase 2A: Basic Code Search
Provides basic code search tools for the Karen project codebase.
MCP Protocol 2024-11-05 compliant.
"""

import os
import sys
import json
import logging
import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict

# Constants
PROJECT_ROOT = Path(__file__).parent
SKIP_EXTS = {'.pyc', '.pyo', '.so', '.dll', '.exe', '.bin', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz'}
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', '.venv', 'dist', 'build'}
MAX_FILE_SIZE = 1024 * 1024  # 1MB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('karen_search_basic')


def is_searchable(path: Path) -> bool:
    """Check if file is searchable"""
    return (path.is_file() and 
            path.suffix.lower() not in SKIP_EXTS and 
            path.stat().st_size < MAX_FILE_SIZE)


class KarenSearchBasicMCP:
    """MCP Server for Basic Code Search Operations"""
    
    def __init__(self):
        self.name = "karen-codebase-search-basic"
        self.version = "1.0.0"
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Any]:
        """Register all available search tools"""
        return {
            "search_codebase": {
                "description": "Search for patterns in codebase files",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Search pattern (regex)"},
                        "file_types": {"type": "array", "items": {"type": "string"}, 
                                     "description": "File extensions (e.g., ['.py', '.js'])"},
                        "case_sensitive": {"type": "boolean", "default": False},
                        "whole_word": {"type": "boolean", "default": False},
                        "max_results": {"type": "integer", "default": 100}
                    },
                    "required": ["pattern"]
                },
                "handler": self.search_codebase
            },
            "find_function_definition": {
                "description": "Find function definitions by name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Function name"},
                        "language": {"type": "string", "description": "Language filter (python/javascript)"}
                    },
                    "required": ["name"]
                },
                "handler": self.find_function_definition
            },
            "find_class_definition": {
                "description": "Find class definitions by name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Class name"}
                    },
                    "required": ["name"]
                },
                "handler": self.find_class_definition
            },
            "search_imports": {
                "description": "Find all files importing a specific module",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "module_name": {"type": "string", "description": "Module name"}
                    },
                    "required": ["module_name"]
                },
                "handler": self.search_imports
            }
        }
    
    async def search_codebase(self, pattern: str, file_types: Optional[List[str]] = None,
                            case_sensitive: bool = False, whole_word: bool = False,
                            max_results: int = 100) -> Dict[str, Any]:
        """Advanced grep-like search across codebase"""
        try:
            # Prepare regex
            flags = 0 if case_sensitive else re.IGNORECASE
            if whole_word:
                pattern = r'\b' + pattern + r'\b'
            regex = re.compile(pattern, flags)
            
            results = []
            files_searched = 0
            
            # Walk project directory
            for root, dirs, files in os.walk(PROJECT_ROOT):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
                
                for file in files:
                    if len(results) >= max_results:
                        break
                    
                    file_path = Path(root) / file
                    
                    # Check file type filter
                    if file_types and not any(file.endswith(ext) for ext in file_types):
                        continue
                    
                    if not is_searchable(file_path):
                        continue
                    
                    files_searched += 1
                    
                    # Search in file
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                matches = list(regex.finditer(line))
                                if matches:
                                    for match in matches:
                                        results.append({
                                            "file": str(file_path.relative_to(PROJECT_ROOT)),
                                            "line": line_num,
                                            "column": match.start() + 1,
                                            "text": line.rstrip(),
                                            "match": match.group()
                                        })
                                        if len(results) >= max_results:
                                            break
                                if len(results) >= max_results:
                                    break
                    except:
                        pass
                
                if len(results) >= max_results:
                    break
            
            return {
                "success": True,
                "pattern": pattern,
                "results": results,
                "count": len(results),
                "files_searched": files_searched,
                "truncated": len(results) >= max_results
            }
        except Exception as e:
            return {"success": False, "error": str(e), "pattern": pattern}
    
    async def find_function_definition(self, name: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Find function definitions by name"""
        try:
            patterns = {
                "python": [f"^\\s*(async\\s+)?def\\s+{name}\\s*\\("],
                "javascript": [
                    f"^\\s*function\\s+{name}\\s*\\(",
                    f"^\\s*const\\s+{name}\\s*=\\s*(async\\s*)?\\(",
                    f"^\\s*{name}\\s*:\\s*function\\s*\\(",
                    f"^\\s*(async\\s+)?{name}\\s*\\(.*\\)\\s*{{"
                ]
            }
            
            # Determine file types
            file_types = None
            if language:
                if language.lower() == "python":
                    file_types = [".py"]
                elif language.lower() in ["javascript", "js", "typescript", "ts"]:
                    file_types = [".js", ".jsx", ".ts", ".tsx"]
            
            # Search patterns
            search_patterns = []
            if language:
                search_patterns.extend(patterns.get(language.lower(), []))
            else:
                for lang_patterns in patterns.values():
                    search_patterns.extend(lang_patterns)
            
            all_results = []
            for pattern in search_patterns:
                result = await self.search_codebase(pattern, file_types, False, False, 50)
                if result["success"] and result["results"]:
                    all_results.extend(result["results"])
            
            # Deduplicate
            seen = set()
            unique_results = []
            for r in all_results:
                key = (r["file"], r["line"])
                if key not in seen:
                    seen.add(key)
                    unique_results.append(r)
            
            return {
                "success": True,
                "function_name": name,
                "language": language,
                "definitions": unique_results,
                "count": len(unique_results)
            }
        except Exception as e:
            return {"success": False, "error": str(e), "function_name": name}
    
    async def find_class_definition(self, name: str) -> Dict[str, Any]:
        """Find class definitions by name"""
        try:
            patterns = [
                f"^\\s*class\\s+{name}\\s*[\\(:]",  # Python
                f"^\\s*(export\\s+)?(default\\s+)?class\\s+{name}\\s*[{{\\(]"  # JS/TS
            ]
            
            all_results = []
            for pattern in patterns:
                result = await self.search_codebase(pattern, None, False, False, 50)
                if result["success"] and result["results"]:
                    all_results.extend(result["results"])
            
            # Deduplicate
            seen = set()
            unique_results = []
            for r in all_results:
                key = (r["file"], r["line"])
                if key not in seen:
                    seen.add(key)
                    unique_results.append(r)
            
            return {
                "success": True,
                "class_name": name,
                "definitions": unique_results,
                "count": len(unique_results)
            }
        except Exception as e:
            return {"success": False, "error": str(e), "class_name": name}
    
    async def search_imports(self, module_name: str) -> Dict[str, Any]:
        """Find all files importing a specific module"""
        try:
            patterns = [
                f"^\\s*import\\s+.*{module_name}",
                f"^\\s*from\\s+{module_name}\\s+import",
                f"require\\(['\"].*{module_name}",
                f"import\\s+.*from\\s+['\"].*{module_name}"
            ]
            
            all_results = []
            for pattern in patterns:
                result = await self.search_codebase(pattern, None, False, False, 100)
                if result["success"] and result["results"]:
                    all_results.extend(result["results"])
            
            # Group by file
            imports_by_file = defaultdict(list)
            for r in all_results:
                imports_by_file[r["file"]].append({
                    "line": r["line"],
                    "text": r["text"].strip()
                })
            
            return {
                "success": True,
                "module_name": module_name,
                "imports": dict(imports_by_file),
                "file_count": len(imports_by_file),
                "total_imports": len(all_results)
            }
        except Exception as e:
            return {"success": False, "error": str(e), "module_name": module_name}
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": self.name, "version": self.version}
            }
        
        elif method == "tools/list":
            tools = []
            for name, tool in self.tools.items():
                tools.append({
                    "name": name,
                    "description": tool["description"],
                    "inputSchema": tool["inputSchema"]
                })
            return {"tools": tools}
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in self.tools:
                return {"error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}
            
            try:
                handler = self.tools[tool_name]["handler"]
                result = await handler(**arguments)
                return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
            except Exception as e:
                logger.error(f"Tool error: {str(e)}", exc_info=True)
                return {"error": {"code": -32603, "message": str(e)}}
        
        else:
            return {"error": {"code": -32601, "message": f"Method not found: {method}"}}


async def main():
    """Main entry point for MCP server"""
    server = KarenSearchBasicMCP()
    logger.info(f"Starting {server.name} v{server.version}")
    
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    
    while True:
        try:
            line = await reader.readline()
            if not line:
                break
            
            request = json.loads(line.decode())
            response = await server.handle_request(request)
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError:
            print(json.dumps({"error": {"code": -32700, "message": "Parse error"}}), flush=True)
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            print(json.dumps({"error": {"code": -32603, "message": "Internal error"}}), flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)