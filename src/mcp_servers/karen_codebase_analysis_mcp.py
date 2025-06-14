"""
Karen Codebase Analysis MCP Server - Phase 2B
Provides code analysis and pattern detection capabilities for the Karen codebase.
"""

import os
import re
import ast
import json
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter

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
logger = logging.getLogger("karen_codebase_analysis_mcp")

class KarenCodebaseAnalysisServer:
    """MCP server for Karen codebase analysis and pattern detection."""
    
    def __init__(self, workspace_root: str = "/workspace"):
        self.workspace_root = Path(workspace_root)
        self.server = Server("karen-codebase-analysis")
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
                        name="karen_analyze_dependencies",
                        description="Analyze dependencies and imports for a file or module",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "target": {
                                    "type": "string",
                                    "description": "File path or module name to analyze"
                                },
                                "include_transitive": {
                                    "type": "boolean",
                                    "description": "Include transitive dependencies",
                                    "default": False
                                }
                            },
                            "required": ["target"]
                        }
                    ),
                    Tool(
                        name="karen_find_patterns",
                        description="Find common code patterns in the Karen codebase",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "pattern_type": {
                                    "type": "string",
                                    "enum": ["decorator", "error_handling", "async_pattern", "api_endpoint", "celery_task", "agent_pattern"],
                                    "description": "Type of pattern to find"
                                },
                                "directory": {
                                    "type": "string",
                                    "description": "Directory to search in",
                                    "default": "src"
                                }
                            },
                            "required": ["pattern_type"]
                        }
                    ),
                    Tool(
                        name="karen_analyze_complexity",
                        description="Analyze code complexity metrics for files or directories",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "target": {
                                    "type": "string",
                                    "description": "File or directory to analyze"
                                },
                                "metrics": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["cyclomatic", "lines", "functions", "classes"]
                                    },
                                    "description": "Metrics to calculate",
                                    "default": ["cyclomatic", "lines", "functions"]
                                }
                            },
                            "required": ["target"]
                        }
                    ),
                    Tool(
                        name="karen_find_todos",
                        description="Find TODO, FIXME, HACK, and other code markers",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "markers": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Markers to search for",
                                    "default": ["TODO", "FIXME", "HACK", "NOTE", "XXX"]
                                },
                                "include_context": {
                                    "type": "boolean",
                                    "description": "Include surrounding code context",
                                    "default": True
                                }
                            }
                        }
                    ),
                    Tool(
                        name="karen_analyze_api_structure",
                        description="Analyze API endpoints and structure",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "framework": {
                                    "type": "string",
                                    "enum": ["fastapi", "flask", "django"],
                                    "description": "API framework to analyze",
                                    "default": "fastapi"
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
                
                if tool_name == "karen_analyze_dependencies":
                    result = await self.analyze_dependencies(
                        arguments.get("target"),
                        arguments.get("include_transitive", False)
                    )
                elif tool_name == "karen_find_patterns":
                    result = await self.find_patterns(
                        arguments.get("pattern_type"),
                        arguments.get("directory", "src")
                    )
                elif tool_name == "karen_analyze_complexity":
                    result = await self.analyze_complexity(
                        arguments.get("target"),
                        arguments.get("metrics", ["cyclomatic", "lines", "functions"])
                    )
                elif tool_name == "karen_find_todos":
                    result = await self.find_todos(
                        arguments.get("markers", ["TODO", "FIXME", "HACK", "NOTE", "XXX"]),
                        arguments.get("include_context", True)
                    )
                elif tool_name == "karen_analyze_api_structure":
                    result = await self.analyze_api_structure(
                        arguments.get("framework", "fastapi")
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
        """Check if a path should be excluded from analysis."""
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False
    
    async def analyze_dependencies(self, target: str, include_transitive: bool = False) -> Dict[str, Any]:
        """Analyze dependencies for a file or module."""
        if not target:
            return {"error": "target is required"}
        
        # Resolve target path
        target_path = self.workspace_root / target
        if not target_path.exists():
            # Try as a module path
            target_path = self.workspace_root / "src" / f"{target.replace('.', '/')}.py"
            if not target_path.exists():
                return {"error": f"Target not found: {target}"}
        
        results = {
            "target": str(target_path.relative_to(self.workspace_root)),
            "direct_imports": [],
            "external_dependencies": [],
            "internal_dependencies": [],
            "import_errors": []
        }
        
        try:
            content = target_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_info = {
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        }
                        results["direct_imports"].append(import_info)
                        
                        # Categorize as internal or external
                        if alias.name.startswith("src.") or alias.name in ["agents", "communication_agent"]:
                            results["internal_dependencies"].append(alias.name)
                        else:
                            results["external_dependencies"].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        import_info = {
                            "from_module": module,
                            "import": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        }
                        results["direct_imports"].append(import_info)
                        
                        # Categorize
                        if module.startswith("src.") or module.startswith("."):
                            results["internal_dependencies"].append(f"{module}.{alias.name}")
                        else:
                            results["external_dependencies"].append(module)
            
            # Remove duplicates
            results["internal_dependencies"] = list(set(results["internal_dependencies"]))
            results["external_dependencies"] = list(set(results["external_dependencies"]))
            
            # Analyze transitive dependencies if requested
            if include_transitive and results["internal_dependencies"]:
                results["transitive_dependencies"] = {}
                for dep in results["internal_dependencies"][:5]:  # Limit to prevent recursion
                    dep_path = dep.replace(".", "/") + ".py"
                    dep_full_path = self.workspace_root / "src" / dep_path
                    if dep_full_path.exists():
                        sub_result = await self.analyze_dependencies(str(dep_full_path.relative_to(self.workspace_root)), False)
                        results["transitive_dependencies"][dep] = sub_result.get("external_dependencies", [])
        
        except SyntaxError as e:
            results["import_errors"].append(f"Syntax error: {str(e)}")
        except Exception as e:
            results["import_errors"].append(f"Analysis error: {str(e)}")
        
        return results
    
    async def find_patterns(self, pattern_type: str, directory: str = "src") -> Dict[str, Any]:
        """Find common code patterns."""
        if not pattern_type:
            return {"error": "pattern_type is required"}
        
        search_path = self.workspace_root / directory
        if not search_path.exists():
            return {"error": f"Directory not found: {directory}"}
        
        results = {
            "pattern_type": pattern_type,
            "directory": directory,
            "occurrences": [],
            "total_found": 0,
            "summary": {}
        }
        
        # Define patterns
        patterns = {
            "decorator": {
                "regex": r"@(\w+)(?:\([^)]*\))?",
                "description": "Python decorators"
            },
            "error_handling": {
                "regex": r"try:\s*\n(.*?)except\s+(\w+(?:\s*,\s*\w+)*)",
                "description": "Try-except blocks"
            },
            "async_pattern": {
                "regex": r"async\s+def\s+(\w+)|await\s+(\w+)",
                "description": "Async/await patterns"
            },
            "api_endpoint": {
                "regex": r"@(app|router)\.(get|post|put|delete|patch)\s*\(['\"]([^'\"]+)['\"]",
                "description": "API endpoint definitions"
            },
            "celery_task": {
                "regex": r"@(celery_app|app)\.task(?:\([^)]*\))?",
                "description": "Celery task definitions"
            },
            "agent_pattern": {
                "regex": r"class\s+(\w*Agent\w*)\s*\(|def\s+(\w*agent\w*)\s*\(",
                "description": "Agent class and function patterns"
            }
        }
        
        if pattern_type not in patterns:
            return {"error": f"Unknown pattern type: {pattern_type}"}
        
        pattern_info = patterns[pattern_type]
        pattern_regex = re.compile(pattern_info["regex"], re.MULTILINE | re.DOTALL)
        
        # Search files
        for py_file in search_path.rglob("*.py"):
            if self.should_exclude(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                matches = pattern_regex.findall(content)
                
                if matches:
                    file_occurrences = []
                    
                    # Get line numbers for matches
                    lines = content.split('\n')
                    for match in matches:
                        # Find line number
                        match_str = match[0] if isinstance(match, tuple) else match
                        for line_num, line in enumerate(lines, 1):
                            if match_str in line:
                                occurrence = {
                                    "match": match_str,
                                    "line_number": line_num,
                                    "context": line.strip()
                                }
                                
                                # Special handling for different pattern types
                                if pattern_type == "api_endpoint" and isinstance(match, tuple):
                                    occurrence["method"] = match[1]
                                    occurrence["path"] = match[2]
                                elif pattern_type == "error_handling" and isinstance(match, tuple):
                                    occurrence["exception_types"] = match[1].split(',')
                                
                                file_occurrences.append(occurrence)
                                break
                    
                    if file_occurrences:
                        results["occurrences"].append({
                            "file": str(py_file.relative_to(self.workspace_root)),
                            "count": len(file_occurrences),
                            "matches": file_occurrences[:10]  # Limit matches per file
                        })
                        results["total_found"] += len(file_occurrences)
            
            except Exception as e:
                logger.warning(f"Error analyzing file {py_file}: {e}")
        
        # Generate summary
        if pattern_type == "decorator":
            decorator_counts = Counter()
            for occ in results["occurrences"]:
                for match in occ["matches"]:
                    decorator_counts[match["match"]] += 1
            results["summary"]["most_common_decorators"] = decorator_counts.most_common(10)
        
        elif pattern_type == "api_endpoint":
            method_counts = Counter()
            path_patterns = []
            for occ in results["occurrences"]:
                for match in occ["matches"]:
                    if "method" in match:
                        method_counts[match["method"]] += 1
                    if "path" in match:
                        path_patterns.append(match["path"])
            results["summary"]["method_distribution"] = dict(method_counts)
            results["summary"]["sample_paths"] = path_patterns[:10]
        
        return results
    
    async def analyze_complexity(self, target: str, metrics: List[str] = None) -> Dict[str, Any]:
        """Analyze code complexity metrics."""
        if not target:
            return {"error": "target is required"}
        
        if metrics is None:
            metrics = ["cyclomatic", "lines", "functions"]
        
        target_path = self.workspace_root / target
        if not target_path.exists():
            return {"error": f"Target not found: {target}"}
        
        results = {
            "target": str(target_path.relative_to(self.workspace_root)),
            "is_directory": target_path.is_dir(),
            "metrics": {},
            "files": []
        }
        
        # Get files to analyze
        if target_path.is_file():
            files_to_analyze = [target_path] if target_path.suffix == '.py' else []
        else:
            files_to_analyze = list(target_path.rglob("*.py"))
        
        total_metrics = {
            "total_lines": 0,
            "code_lines": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "function_count": 0,
            "class_count": 0,
            "avg_complexity": 0,
            "max_complexity": 0
        }
        
        complexity_scores = []
        
        for py_file in files_to_analyze:
            if self.should_exclude(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                file_metrics = {
                    "file": str(py_file.relative_to(self.workspace_root)),
                    "total_lines": len(lines),
                    "code_lines": 0,
                    "comment_lines": 0,
                    "blank_lines": 0
                }
                
                # Count line types
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        file_metrics["blank_lines"] += 1
                    elif stripped.startswith('#'):
                        file_metrics["comment_lines"] += 1
                    else:
                        file_metrics["code_lines"] += 1
                
                # Parse AST for more metrics
                if "functions" in metrics or "classes" in metrics or "cyclomatic" in metrics:
                    try:
                        tree = ast.parse(content)
                        
                        # Count functions and classes
                        function_complexities = []
                        
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                                file_metrics.setdefault("functions", []).append(node.name)
                                
                                # Calculate cyclomatic complexity
                                if "cyclomatic" in metrics:
                                    complexity = self.calculate_cyclomatic_complexity(node)
                                    function_complexities.append(complexity)
                                    
                            elif isinstance(node, ast.ClassDef):
                                file_metrics.setdefault("classes", []).append(node.name)
                        
                        file_metrics["function_count"] = len(file_metrics.get("functions", []))
                        file_metrics["class_count"] = len(file_metrics.get("classes", []))
                        
                        if function_complexities:
                            file_metrics["avg_complexity"] = sum(function_complexities) / len(function_complexities)
                            file_metrics["max_complexity"] = max(function_complexities)
                            complexity_scores.extend(function_complexities)
                    
                    except SyntaxError:
                        file_metrics["parse_error"] = True
                
                # Update totals
                for key in ["total_lines", "code_lines", "comment_lines", "blank_lines", "function_count", "class_count"]:
                    total_metrics[key] += file_metrics.get(key, 0)
                
                results["files"].append(file_metrics)
            
            except Exception as e:
                logger.warning(f"Error analyzing file {py_file}: {e}")
        
        # Calculate averages
        if complexity_scores:
            total_metrics["avg_complexity"] = sum(complexity_scores) / len(complexity_scores)
            total_metrics["max_complexity"] = max(complexity_scores)
        
        results["metrics"] = total_metrics
        
        # Add summary
        results["summary"] = {
            "files_analyzed": len(results["files"]),
            "code_to_comment_ratio": (
                total_metrics["code_lines"] / total_metrics["comment_lines"] 
                if total_metrics["comment_lines"] > 0 else float('inf')
            ),
            "avg_file_size": total_metrics["total_lines"] / len(results["files"]) if results["files"] else 0
        }
        
        return results
    
    def calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function node."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    async def find_todos(self, markers: List[str] = None, include_context: bool = True) -> Dict[str, Any]:
        """Find TODO and other code markers."""
        if markers is None:
            markers = ["TODO", "FIXME", "HACK", "NOTE", "XXX"]
        
        results = {
            "markers": markers,
            "todos": [],
            "total_found": 0,
            "by_marker": {marker: 0 for marker in markers}
        }
        
        # Create regex pattern
        pattern = r'\b(' + '|'.join(re.escape(marker) for marker in markers) + r')\b\s*:?\s*(.+?)$'
        todo_regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        
        # Search all code files
        for file_path in self.workspace_root.rglob("*"):
            if file_path.is_file() and not self.should_exclude(file_path):
                # Check if it's a code file
                if file_path.suffix in ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs']:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        lines = content.split('\n')
                        
                        file_todos = []
                        
                        for line_num, line in enumerate(lines, 1):
                            match = todo_regex.search(line)
                            if match:
                                marker = match.group(1).upper()
                                message = match.group(2).strip()
                                
                                todo_item = {
                                    "marker": marker,
                                    "message": message,
                                    "line_number": line_num
                                }
                                
                                # Add context if requested
                                if include_context:
                                    context_start = max(0, line_num - 3)
                                    context_end = min(len(lines), line_num + 2)
                                    todo_item["context"] = '\n'.join(lines[context_start:context_end])
                                
                                file_todos.append(todo_item)
                                results["by_marker"][marker] += 1
                        
                        if file_todos:
                            results["todos"].append({
                                "file": str(file_path.relative_to(self.workspace_root)),
                                "count": len(file_todos),
                                "items": file_todos
                            })
                            results["total_found"] += len(file_todos)
                    
                    except Exception as e:
                        logger.warning(f"Error reading file {file_path}: {e}")
        
        # Sort by marker count
        results["by_marker"] = dict(sorted(results["by_marker"].items(), key=lambda x: x[1], reverse=True))
        
        return results
    
    async def analyze_api_structure(self, framework: str = "fastapi") -> Dict[str, Any]:
        """Analyze API endpoint structure."""
        results = {
            "framework": framework,
            "endpoints": [],
            "routers": [],
            "middleware": [],
            "total_endpoints": 0,
            "methods_distribution": {}
        }
        
        if framework == "fastapi":
            # Find FastAPI app instances
            app_pattern = re.compile(r'(\w+)\s*=\s*FastAPI\s*\(')
            router_pattern = re.compile(r'(\w+)\s*=\s*APIRouter\s*\(')
            endpoint_pattern = re.compile(r'@(\w+)\.(get|post|put|delete|patch|head|options)\s*\(\s*["\']([^"\']+)["\']')
            
            # Search for main app and routers
            for py_file in self.workspace_root.rglob("*.py"):
                if self.should_exclude(py_file):
                    continue
                
                try:
                    content = py_file.read_text(encoding='utf-8', errors='ignore')
                    
                    # Find app instances
                    app_matches = app_pattern.findall(content)
                    for app_name in app_matches:
                        results["routers"].append({
                            "type": "app",
                            "name": app_name,
                            "file": str(py_file.relative_to(self.workspace_root))
                        })
                    
                    # Find router instances
                    router_matches = router_pattern.findall(content)
                    for router_name in router_matches:
                        results["routers"].append({
                            "type": "router",
                            "name": router_name,
                            "file": str(py_file.relative_to(self.workspace_root))
                        })
                    
                    # Find endpoints
                    endpoint_matches = endpoint_pattern.findall(content)
                    if endpoint_matches:
                        file_endpoints = []
                        
                        for app_or_router, method, path in endpoint_matches:
                            endpoint = {
                                "method": method.upper(),
                                "path": path,
                                "handler": app_or_router
                            }
                            
                            # Try to find the function name
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if f'@{app_or_router}.{method}' in line and path in line:
                                    # Look for the function definition in the next few lines
                                    for j in range(i+1, min(i+5, len(lines))):
                                        func_match = re.match(r'\s*(?:async\s+)?def\s+(\w+)', lines[j])
                                        if func_match:
                                            endpoint["function"] = func_match.group(1)
                                            break
                            
                            file_endpoints.append(endpoint)
                            
                            # Update method distribution
                            results["methods_distribution"][method.upper()] = \
                                results["methods_distribution"].get(method.upper(), 0) + 1
                        
                        if file_endpoints:
                            results["endpoints"].append({
                                "file": str(py_file.relative_to(self.workspace_root)),
                                "count": len(file_endpoints),
                                "endpoints": file_endpoints
                            })
                            results["total_endpoints"] += len(file_endpoints)
                
                except Exception as e:
                    logger.warning(f"Error analyzing file {py_file}: {e}")
        
        # Group endpoints by path prefix
        path_groups = defaultdict(list)
        for file_data in results["endpoints"]:
            for endpoint in file_data["endpoints"]:
                path_parts = endpoint["path"].split('/')
                if len(path_parts) > 1:
                    prefix = f"/{path_parts[1]}"
                    path_groups[prefix].append(endpoint)
        
        results["path_groups"] = {
            prefix: len(endpoints) for prefix, endpoints in path_groups.items()
        }
        
        return results
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)

def main():
    """Main entry point."""
    server = KarenCodebaseAnalysisServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()