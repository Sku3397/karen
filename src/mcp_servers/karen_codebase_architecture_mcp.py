#!/usr/bin/env python
"""
Karen Codebase Architecture MCP Server - Phase 4
Project architecture and integration analysis tools (600-700 lines target)
"""

import os
import sys
import json
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
import ast
import re
from collections import defaultdict, Counter

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import stdio
from mcp.types import Tool, TextContent

# Global server instance
server = stdio.StdioServer(name="karen-codebase-architecture")

# Repository root
REPO_ROOT = "/workspace"

def get_file_extension(file_path: str) -> str:
    """Get file extension."""
    return Path(file_path).suffix.lower()

def is_code_file(file_path: str) -> bool:
    """Check if file is a code file."""
    code_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', 
                      '.cs', '.rb', '.go', '.rs', '.php', '.swift', '.kt', '.scala'}
    return get_file_extension(file_path) in code_extensions

def count_lines_of_code(file_path: str) -> Dict[str, int]:
    """Count lines of code in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                blank_lines += 1
                continue
            
            # Python multiline comments
            if file_path.endswith('.py'):
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if in_multiline_comment:
                        in_multiline_comment = False
                    else:
                        in_multiline_comment = True
                    comment_lines += 1
                    continue
                
                if in_multiline_comment:
                    comment_lines += 1
                    continue
                
                if stripped.startswith('#'):
                    comment_lines += 1
                    continue
            
            # JavaScript/TypeScript multiline comments
            elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                if '/*' in stripped:
                    in_multiline_comment = True
                if '*/' in stripped:
                    in_multiline_comment = False
                    comment_lines += 1
                    continue
                
                if in_multiline_comment:
                    comment_lines += 1
                    continue
                
                if stripped.startswith('//'):
                    comment_lines += 1
                    continue
            
            code_lines += 1
        
        return {
            'total': total_lines,
            'code': code_lines,
            'comment': comment_lines,
            'blank': blank_lines
        }
    except Exception:
        return {'total': 0, 'code': 0, 'comment': 0, 'blank': 0}

def analyze_python_imports(file_path: str) -> Dict[str, Any]:
    """Analyze imports in a Python file."""
    imports = {
        'standard': [],
        'third_party': [],
        'local': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    imports['third_party'].append(module_name)  # Simplified classification
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports['third_party'].append(node.module)
    
    except Exception:
        pass
    
    return imports

def analyze_javascript_imports(file_path: str) -> Dict[str, Any]:
    """Analyze imports in a JavaScript/TypeScript file."""
    imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # ES6 imports
        import_pattern = r'import\s+(?:(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)\s+from\s+)?[\'"]([^\'"]+)[\'"]'
        imports.extend(re.findall(import_pattern, content))
        
        # CommonJS requires
        require_pattern = r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        imports.extend(re.findall(require_pattern, content))
    
    except Exception:
        pass
    
    return {'modules': list(set(imports))}

@server.register_tool
async def karen_project_structure(max_depth: int = 3) -> List[TextContent]:
    """Get hierarchical project structure with file counts and types.
    
    Args:
        max_depth: Maximum directory depth to explore (default: 3)
    """
    def explore_directory(path: Path, current_depth: int = 0) -> Dict[str, Any]:
        """Recursively explore directory structure."""
        if current_depth >= max_depth:
            return {'type': 'directory', 'name': path.name, 'truncated': True}
        
        result = {
            'type': 'directory',
            'name': path.name,
            'children': [],
            'file_count': 0,
            'dir_count': 0
        }
        
        try:
            for item in sorted(path.iterdir()):
                # Skip hidden files and common ignore patterns
                if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules', '.git']:
                    continue
                
                if item.is_dir():
                    result['dir_count'] += 1
                    child_info = explore_directory(item, current_depth + 1)
                    result['children'].append(child_info)
                elif item.is_file():
                    result['file_count'] += 1
                    result['children'].append({
                        'type': 'file',
                        'name': item.name,
                        'extension': item.suffix
                    })
        except PermissionError:
            pass
        
        return result
    
    root_path = Path(REPO_ROOT)
    structure = explore_directory(root_path)
    
    # Format output
    output = [f"Project Structure (max depth: {max_depth}):\n"]
    
    def format_tree(node: Dict[str, Any], prefix: str = "", is_last: bool = True):
        """Format directory tree for display."""
        if node['type'] == 'directory':
            output.append(f"{prefix}{'└── ' if is_last else '├── '}{node['name']}/ "
                         f"({node.get('file_count', 0)} files, {node.get('dir_count', 0)} dirs)")
            
            if 'children' in node and not node.get('truncated'):
                children = node['children']
                for i, child in enumerate(children):
                    is_last_child = i == len(children) - 1
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    format_tree(child, new_prefix, is_last_child)
        else:
            output.append(f"{prefix}{'└── ' if is_last else '├── '}{node['name']}")
    
    format_tree(structure)
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_analyze_dependencies(file_path: str) -> List[TextContent]:
    """Analyze imports and dependencies for a specific file.
    
    Args:
        file_path: Path to the file to analyze
    """
    full_path = os.path.join(REPO_ROOT, file_path.lstrip('/'))
    
    if not os.path.exists(full_path):
        return [TextContent(type="text", text=f"File not found: {file_path}")]
    
    extension = get_file_extension(full_path)
    
    output = [f"Dependencies for {file_path}:\n"]
    
    if extension == '.py':
        imports = analyze_python_imports(full_path)
        
        if imports['standard']:
            output.append("Standard library imports:")
            for imp in sorted(set(imports['standard'])):
                output.append(f"  - {imp}")
        
        if imports['third_party']:
            output.append("\nThird-party imports:")
            for imp in sorted(set(imports['third_party'])):
                output.append(f"  - {imp}")
        
        if imports['local']:
            output.append("\nLocal imports:")
            for imp in sorted(set(imports['local'])):
                output.append(f"  - {imp}")
    
    elif extension in ['.js', '.jsx', '.ts', '.tsx']:
        imports = analyze_javascript_imports(full_path)
        
        if imports['modules']:
            output.append("Imported modules:")
            for module in sorted(imports['modules']):
                output.append(f"  - {module}")
    
    else:
        output.append(f"Dependency analysis not supported for {extension} files")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_file_dependencies(path: str) -> List[TextContent]:
    """Get files that depend on or are depended upon by the specified file.
    
    Args:
        path: File or directory path to analyze
    """
    full_path = os.path.join(REPO_ROOT, path.lstrip('/'))
    
    # For Python files, look for imports
    if path.endswith('.py'):
        module_name = path.replace('/', '.').replace('.py', '')
        if module_name.startswith('src.'):
            module_name = module_name[4:]
        
        dependents = []
        dependencies = []
        
        # Find files that import this module
        for root, dirs, files in os.walk(REPO_ROOT):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if f'from {module_name}' in content or f'import {module_name}' in content:
                            rel_path = os.path.relpath(file_path, REPO_ROOT)
                            dependents.append(rel_path)
                    except Exception:
                        pass
        
        # Get this file's dependencies
        if os.path.exists(full_path):
            imports = analyze_python_imports(full_path)
            dependencies = imports['local']
        
        output = [f"Dependencies for {path}:\n"]
        
        if dependencies:
            output.append("This file depends on:")
            for dep in sorted(set(dependencies)):
                output.append(f"  - {dep}")
        
        if dependents:
            output.append(f"\nFiles that depend on {path}:")
            for dep in sorted(set(dependents)):
                output.append(f"  - {dep}")
        
        if not dependencies and not dependents:
            output.append("No dependencies found")
    
    else:
        output = [f"Dependency analysis for {path} type not yet implemented"]
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_code_quality(path: str = "") -> List[TextContent]:
    """Analyze code quality metrics for files or directories.
    
    Args:
        path: File or directory path (default: entire project)
    """
    full_path = os.path.join(REPO_ROOT, path.lstrip('/')) if path else REPO_ROOT
    
    if not os.path.exists(full_path):
        return [TextContent(type="text", text=f"Path not found: {path}")]
    
    metrics = {
        'total_files': 0,
        'total_lines': 0,
        'code_lines': 0,
        'comment_lines': 0,
        'blank_lines': 0,
        'average_file_size': 0,
        'largest_files': [],
        'file_types': Counter()
    }
    
    files_to_analyze = []
    
    if os.path.isfile(full_path):
        files_to_analyze = [full_path]
    else:
        for root, dirs, files in os.walk(full_path):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
            
            for file in files:
                file_path = os.path.join(root, file)
                if is_code_file(file_path):
                    files_to_analyze.append(file_path)
    
    # Analyze each file
    file_sizes = []
    
    for file_path in files_to_analyze:
        extension = get_file_extension(file_path)
        metrics['file_types'][extension] += 1
        metrics['total_files'] += 1
        
        loc_data = count_lines_of_code(file_path)
        metrics['total_lines'] += loc_data['total']
        metrics['code_lines'] += loc_data['code']
        metrics['comment_lines'] += loc_data['comment']
        metrics['blank_lines'] += loc_data['blank']
        
        if loc_data['total'] > 0:
            rel_path = os.path.relpath(file_path, REPO_ROOT)
            file_sizes.append((rel_path, loc_data['total']))
    
    # Calculate averages and find largest files
    if metrics['total_files'] > 0:
        metrics['average_file_size'] = metrics['total_lines'] // metrics['total_files']
        metrics['largest_files'] = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:5]
    
    # Format output
    output = [f"Code Quality Metrics for {path or 'entire project'}:\n"]
    
    output.append(f"Total files analyzed: {metrics['total_files']}")
    output.append(f"Total lines: {metrics['total_lines']:,}")
    output.append(f"Code lines: {metrics['code_lines']:,} ({metrics['code_lines']*100//max(metrics['total_lines'],1)}%)")
    output.append(f"Comment lines: {metrics['comment_lines']:,} ({metrics['comment_lines']*100//max(metrics['total_lines'],1)}%)")
    output.append(f"Blank lines: {metrics['blank_lines']:,} ({metrics['blank_lines']*100//max(metrics['total_lines'],1)}%)")
    output.append(f"Average file size: {metrics['average_file_size']} lines")
    
    if metrics['file_types']:
        output.append("\nFile type distribution:")
        for ext, count in metrics['file_types'].most_common():
            output.append(f"  {ext}: {count} files")
    
    if metrics['largest_files']:
        output.append("\nLargest files:")
        for file_path, lines in metrics['largest_files']:
            output.append(f"  {file_path}: {lines:,} lines")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_project_metrics() -> List[TextContent]:
    """Get comprehensive project metrics including size, complexity, and composition."""
    metrics = {
        'languages': Counter(),
        'total_files': 0,
        'total_dirs': 0,
        'total_size': 0,
        'code_files': 0,
        'doc_files': 0,
        'config_files': 0,
        'test_files': 0
    }
    
    # Walk the project directory
    for root, dirs, files in os.walk(REPO_ROOT):
        # Skip common ignore directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'dist', 'build']]
        
        metrics['total_dirs'] += len(dirs)
        
        for file in files:
            metrics['total_files'] += 1
            file_path = os.path.join(root, file)
            
            try:
                metrics['total_size'] += os.path.getsize(file_path)
            except:
                pass
            
            # Categorize files
            extension = get_file_extension(file)
            
            if extension:
                metrics['languages'][extension] += 1
            
            if is_code_file(file_path):
                metrics['code_files'] += 1
            elif extension in ['.md', '.rst', '.txt']:
                metrics['doc_files'] += 1
            elif extension in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']:
                metrics['config_files'] += 1
            
            if 'test' in file.lower() or 'test' in root.lower():
                metrics['test_files'] += 1
    
    # Format output
    output = ["Project Metrics:\n"]
    
    output.append(f"Total files: {metrics['total_files']:,}")
    output.append(f"Total directories: {metrics['total_dirs']:,}")
    output.append(f"Total size: {metrics['total_size'] / (1024*1024):.2f} MB")
    output.append(f"Code files: {metrics['code_files']:,}")
    output.append(f"Documentation files: {metrics['doc_files']:,}")
    output.append(f"Configuration files: {metrics['config_files']:,}")
    output.append(f"Test files: {metrics['test_files']:,}")
    
    if metrics['languages']:
        output.append("\nLanguage distribution (by file extension):")
        for ext, count in metrics['languages'].most_common(10):
            output.append(f"  {ext}: {count} files")
    
    # Additional insights
    if metrics['code_files'] > 0:
        test_coverage = (metrics['test_files'] / metrics['code_files']) * 100
        output.append(f"\nTest coverage estimate: {test_coverage:.1f}% of code files have tests")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_circular_dependencies() -> List[TextContent]:
    """Find potential circular dependencies in the project."""
    # Build dependency graph for Python files
    dependency_graph = defaultdict(set)
    file_modules = {}
    
    # First pass: map files to module names
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, REPO_ROOT)
                module_path = rel_path.replace('/', '.').replace('.py', '')
                file_modules[file_path] = module_path
    
    # Second pass: build dependency graph
    for file_path, module_path in file_modules.items():
        imports = analyze_python_imports(file_path)
        
        for imp in imports['local']:
            # Try to resolve the import to a file
            for other_path, other_module in file_modules.items():
                if imp == other_module or other_module.endswith(f'.{imp}'):
                    dependency_graph[module_path].add(other_module)
    
    # Find circular dependencies using DFS
    def find_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Find cycles in dependency graph."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    cycles = find_cycles(dependency_graph)
    
    # Format output
    output = ["Circular Dependency Analysis:\n"]
    
    if cycles:
        output.append(f"Found {len(cycles)} potential circular dependencies:")
        
        for i, cycle in enumerate(cycles, 1):
            output.append(f"\nCycle {i}:")
            for j in range(len(cycle) - 1):
                output.append(f"  {cycle[j]} -> {cycle[j+1]}")
    else:
        output.append("No circular dependencies detected!")
    
    # Show dependency statistics
    output.append(f"\nDependency statistics:")
    output.append(f"Total modules analyzed: {len(file_modules)}")
    output.append(f"Modules with dependencies: {len(dependency_graph)}")
    
    # Find most connected modules
    dependency_counts = [(module, len(deps)) for module, deps in dependency_graph.items()]
    dependency_counts.sort(key=lambda x: x[1], reverse=True)
    
    if dependency_counts:
        output.append("\nMost connected modules:")
        for module, count in dependency_counts[:5]:
            output.append(f"  {module}: {count} dependencies")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_api_endpoints(framework: Optional[str] = None) -> List[TextContent]:
    """Discover API endpoints in the project.
    
    Args:
        framework: Specific framework to look for (e.g., 'fastapi', 'flask', 'django')
    """
    endpoints = []
    
    # Search for FastAPI endpoints
    fastapi_decorators = ['@app.get', '@app.post', '@app.put', '@app.delete', '@app.patch',
                         '@router.get', '@router.post', '@router.put', '@router.delete', '@router.patch']
    
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Find API endpoints using regex
                    for decorator in fastapi_decorators:
                        pattern = rf'{re.escape(decorator)}\s*\(\s*["\']([^"\']+)["\']'
                        matches = re.findall(pattern, content)
                        
                        for match in matches:
                            rel_path = os.path.relpath(file_path, REPO_ROOT)
                            endpoints.append({
                                'file': rel_path,
                                'method': decorator.split('.')[-1].upper(),
                                'path': match,
                                'framework': 'FastAPI'
                            })
                
                except Exception:
                    pass
    
    # Format output
    output = ["API Endpoints Discovery:\n"]
    
    if endpoints:
        # Group by file
        endpoints_by_file = defaultdict(list)
        for endpoint in endpoints:
            endpoints_by_file[endpoint['file']].append(endpoint)
        
        output.append(f"Found {len(endpoints)} endpoints in {len(endpoints_by_file)} files:")
        
        for file_path, file_endpoints in sorted(endpoints_by_file.items()):
            output.append(f"\n{file_path}:")
            for ep in sorted(file_endpoints, key=lambda x: (x['method'], x['path'])):
                output.append(f"  {ep['method']:6} {ep['path']}")
    else:
        output.append("No API endpoints found")
    
    # Summary by HTTP method
    if endpoints:
        method_counts = Counter(ep['method'] for ep in endpoints)
        output.append("\nEndpoints by HTTP method:")
        for method, count in sorted(method_counts.items()):
            output.append(f"  {method}: {count}")
    
    return [TextContent(type="text", text="\n".join(output))]

# Tool definitions for registration
TOOLS = [
    Tool(
        name="karen_project_structure",
        description="Get hierarchical project structure with file counts and types",
        inputSchema={
            "type": "object",
            "properties": {
                "max_depth": {"type": "integer", "description": "Maximum directory depth to explore", "default": 3}
            }
        }
    ),
    Tool(
        name="karen_analyze_dependencies",
        description="Analyze imports and dependencies for a specific file",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file to analyze"}
            },
            "required": ["file_path"]
        }
    ),
    Tool(
        name="karen_file_dependencies",
        description="Get files that depend on or are depended upon by the specified file",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory path to analyze"}
            },
            "required": ["path"]
        }
    ),
    Tool(
        name="karen_code_quality",
        description="Analyze code quality metrics for files or directories",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory path (default: entire project)", "default": ""}
            }
        }
    ),
    Tool(
        name="karen_project_metrics",
        description="Get comprehensive project metrics including size, complexity, and composition",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="karen_circular_dependencies",
        description="Find potential circular dependencies in the project",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="karen_api_endpoints",
        description="Discover API endpoints in the project",
        inputSchema={
            "type": "object",
            "properties": {
                "framework": {"type": "string", "description": "Specific framework to look for"}
            }
        }
    )
]

@server.list_tools
async def list_tools() -> List[Tool]:
    """List available tools."""
    return TOOLS

async def main():
    """Run the MCP server."""
    async with server:
        await server.run()

if __name__ == "__main__":
    asyncio.run(main())