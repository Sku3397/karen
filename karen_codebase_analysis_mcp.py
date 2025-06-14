#!/usr/bin/env python3
"""
Karen Codebase Analysis MCP Server - Phase 2B: Advanced Code Analysis
Provides advanced code analysis tools for the Karen project codebase.
MCP Protocol 2024-11-05 compliant.
"""

import os
import sys
import json
import logging
import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

# Constants
PROJECT_ROOT = Path(__file__).parent
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', '.venv', 'dist', 'build'}
CODE_EXTS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.cs', '.go', '.rs'}
MAX_SIZE = 1024 * 1024  # 1MB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('karen_analysis')


def is_code_file(path: Path) -> bool:
    """Check if file is a code file"""
    try:
        return path.is_file() and path.suffix in CODE_EXTS and path.stat().st_size < MAX_SIZE
    except:
        return False


def count_lines(content: str) -> Tuple[int, int, int]:
    """Count total, code, and comment lines"""
    lines = content.splitlines()
    total = len(lines)
    blank = sum(1 for line in lines if not line.strip())
    comment = sum(1 for line in lines if line.strip().startswith(('#', '//', '/*', '*')))
    return total, total - blank - comment, comment


class KarenAnalysisMCP:
    """MCP Server for Advanced Code Analysis Operations"""
    
    def __init__(self):
        self.name = "karen-codebase-analysis"
        self.version = "1.0.0"
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Any]:
        """Register all available analysis tools"""
        return {
            "find_function_usage": {
                "description": "Find where functions are called/used in the codebase",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Function name"},
                        "exclude_definitions": {"type": "boolean", "default": True}
                    },
                    "required": ["name"]
                },
                "handler": self.find_function_usage
            },
            "find_todos_fixmes": {
                "description": "Find TODO, FIXME, HACK, and XXX comments",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "types": {"type": "array", "items": {"type": "string"},
                                "default": ["TODO", "FIXME", "HACK", "XXX"]}
                    }
                },
                "handler": self.find_todos_fixmes
            },
            "get_code_complexity": {
                "description": "Analyze code complexity metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to analyze", "default": "."}
                    }
                },
                "handler": self.get_code_complexity
            },
            "analyze_code_patterns": {
                "description": "Detect common code patterns and issues",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "default": "."},
                        "patterns": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "handler": self.analyze_code_patterns
            }
        }
    
    async def find_function_usage(self, name: str, exclude_definitions: bool = True) -> Dict[str, Any]:
        """Find where functions are called"""
        try:
            # Usage patterns
            patterns = [
                f"{name}\\s*\\(", f"\\.{name}\\s*\\(", f"\\b{name}\\b(?!\\s*[:=])",
                f"callback\\s*=\\s*{name}", f"\\({name}\\)"
            ]
            
            # Definition patterns to exclude
            exclude = [
                f"def\\s+{name}\\s*\\(", f"function\\s+{name}\\s*\\(",
                f"(const|let|var)\\s+{name}\\s*=", f"class\\s+{name}\\b"
            ] if exclude_definitions else []
            
            results = []
            files_searched = 0
            
            for root, dirs, files in os.walk(PROJECT_ROOT):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
                
                for file in files:
                    file_path = Path(root) / file
                    if not is_code_file(file_path):
                        continue
                    
                    files_searched += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                # Check patterns
                                if any(re.search(p, line, re.I) for p in patterns):
                                    if not any(re.search(e, line, re.I) for e in exclude):
                                        results.append({
                                            "file": str(file_path.relative_to(PROJECT_ROOT)),
                                            "line": line_num,
                                            "text": line.strip()
                                        })
                    except:
                        pass
            
            return {
                "success": True,
                "function_name": name,
                "usages": results,
                "count": len(results),
                "files_searched": files_searched
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def find_todos_fixmes(self, types: List[str] = None) -> Dict[str, Any]:
        """Find TODO/FIXME comments"""
        try:
            types = types or ["TODO", "FIXME", "HACK", "XXX"]
            pattern = r'\b(' + '|'.join(types) + r')\b[:\s]*(.*)$'
            regex = re.compile(pattern, re.IGNORECASE)
            
            results = defaultdict(list)
            total = 0
            
            for root, dirs, files in os.walk(PROJECT_ROOT):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
                
                for file in files:
                    file_path = Path(root) / file
                    if not is_code_file(file_path):
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                match = regex.search(line)
                                if match:
                                    comment_type = match.group(1).upper()
                                    results[comment_type].append({
                                        "file": str(file_path.relative_to(PROJECT_ROOT)),
                                        "line": line_num,
                                        "text": match.group(2).strip() or "(no description)"
                                    })
                                    total += 1
                    except:
                        pass
            
            return {
                "success": True,
                "results": dict(results),
                "total_count": total,
                "summary": {t: len(results.get(t, [])) for t in types}
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_code_complexity(self, path: str = ".") -> Dict[str, Any]:
        """Analyze code complexity metrics"""
        try:
            target = Path(PROJECT_ROOT) / path if not Path(path).is_absolute() else Path(path)
            if not target.exists():
                return {"success": False, "error": f"Path not found: {path}"}
            
            metrics = {
                "total_files": 0, "total_lines": 0, "code_lines": 0,
                "comment_lines": 0, "by_language": defaultdict(lambda: {"files": 0, "lines": 0}),
                "largest_files": []
            }
            
            files_to_analyze = [target] if target.is_file() else []
            if target.is_dir():
                for root, dirs, files in os.walk(target):
                    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
                    for file in files:
                        fp = Path(root) / file
                        if is_code_file(fp):
                            files_to_analyze.append(fp)
            
            file_sizes = []
            for fp in files_to_analyze:
                try:
                    content = fp.read_text(encoding='utf-8', errors='ignore')
                    total, code, comment = count_lines(content)
                    
                    metrics["total_files"] += 1
                    metrics["total_lines"] += total
                    metrics["code_lines"] += code
                    metrics["comment_lines"] += comment
                    
                    lang = fp.suffix
                    metrics["by_language"][lang]["files"] += 1
                    metrics["by_language"][lang]["lines"] += total
                    
                    file_sizes.append({
                        "file": str(fp.relative_to(PROJECT_ROOT)),
                        "lines": total
                    })
                except:
                    pass
            
            # Top 10 largest files
            file_sizes.sort(key=lambda x: x["lines"], reverse=True)
            metrics["largest_files"] = file_sizes[:10]
            metrics["by_language"] = dict(metrics["by_language"])
            
            return {"success": True, "path": str(target), "metrics": metrics}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def analyze_code_patterns(self, path: str = ".", patterns: List[str] = None) -> Dict[str, Any]:
        """Detect code patterns and issues"""
        try:
            target = Path(PROJECT_ROOT) / path if not Path(path).is_absolute() else Path(path)
            
            # Default patterns
            default_patterns = {
                "long_lines": r'^.{120,}$',
                "hardcoded_secrets": r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']',
                "print_debug": r'\b(print|console\.log)\s*\(',
                "empty_except": r'except\s*:\s*pass',
                "global_vars": r'\bglobal\s+\w+',
                "eval_usage": r'\beval\s*\('
            }
            
            pattern_dict = {f"custom_{i}": p for i, p in enumerate(patterns)} if patterns else default_patterns
            
            results = defaultdict(list)
            files_analyzed = 0
            
            files_to_check = [target] if target.is_file() and is_code_file(target) else []
            if target.is_dir():
                for root, dirs, files in os.walk(target):
                    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
                    for file in files:
                        fp = Path(root) / file
                        if is_code_file(fp):
                            files_to_check.append(fp)
            
            for fp in files_to_check:
                files_analyzed += 1
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            for name, pattern in pattern_dict.items():
                                if re.search(pattern, line, re.I):
                                    results[name].append({
                                        "file": str(fp.relative_to(PROJECT_ROOT)),
                                        "line": line_num,
                                        "match": line.strip()[:80]
                                    })
                except:
                    pass
            
            return {
                "success": True,
                "path": str(target),
                "files_analyzed": files_analyzed,
                "findings": dict(results),
                "summary": {name: len(items) for name, items in results.items()}
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
    server = KarenAnalysisMCP()
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