#!/usr/bin/env python
"""
Karen Codebase Git MCP Server - Phase 3
Git and version control analysis tools (500-600 lines target)
"""

import os
import sys
import json
import asyncio
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import stdio
from mcp.types import Tool, TextContent

# Global server instance
server = stdio.StdioServer(name="karen-codebase-git")

# Repository root
REPO_ROOT = "/workspace"

def run_git_command(cmd: List[str], cwd: str = REPO_ROOT) -> Optional[str]:
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None
    except Exception:
        return None

def parse_git_status(status_output: str) -> Dict[str, Any]:
    """Parse git status output into structured data."""
    result = {
        "branch": "",
        "ahead": 0,
        "behind": 0,
        "staged": [],
        "unstaged": [],
        "untracked": []
    }
    
    lines = status_output.split('\n')
    
    for line in lines:
        # Branch info
        if line.startswith("On branch"):
            result["branch"] = line.split("On branch")[1].strip()
        elif "Your branch is ahead" in line:
            match = re.search(r'by (\d+) commit', line)
            if match:
                result["ahead"] = int(match.group(1))
        elif "Your branch is behind" in line:
            match = re.search(r'by (\d+) commit', line)
            if match:
                result["behind"] = int(match.group(1))
        
        # File changes
        if line.startswith("  "):
            file_line = line.strip()
            if file_line.startswith("modified:"):
                result["unstaged"].append(file_line.replace("modified:", "").strip())
            elif file_line.startswith("new file:"):
                result["staged"].append(file_line.replace("new file:", "").strip())
            elif file_line.startswith("deleted:"):
                result["staged"].append(file_line.replace("deleted:", "").strip())
        elif line.startswith("\t"):
            # Unstaged changes
            file_line = line.strip()
            if file_line.startswith("modified:"):
                result["unstaged"].append(file_line.replace("modified:", "").strip())
        elif line.startswith("??"):
            # Untracked files
            result["untracked"].append(line[3:])
    
    return result

def parse_git_log(log_output: str) -> List[Dict[str, Any]]:
    """Parse git log output into structured data."""
    commits = []
    
    if not log_output:
        return commits
    
    # Split by commit separator
    commit_blocks = log_output.strip().split('\n\n')
    
    for block in commit_blocks:
        lines = block.strip().split('\n')
        if not lines:
            continue
            
        commit = {}
        for line in lines:
            if line.startswith('commit '):
                commit['hash'] = line.replace('commit ', '').strip()
            elif line.startswith('Author: '):
                commit['author'] = line.replace('Author: ', '').strip()
            elif line.startswith('Date: '):
                commit['date'] = line.replace('Date: ', '').strip()
            elif line.strip() and 'message' not in commit:
                commit['message'] = line.strip()
        
        if commit:
            commits.append(commit)
    
    return commits

@server.register_tool
async def karen_git_status() -> List[TextContent]:
    """Get comprehensive git repository status including branch, staged/unstaged changes, and untracked files."""
    status_output = run_git_command(["status"])
    
    if not status_output:
        return [TextContent(type="text", text="Not a git repository or git not available")]
    
    # Get additional status info
    status_data = parse_git_status(status_output)
    
    # Get last commit info
    last_commit = run_git_command(["log", "-1", "--oneline"])
    if last_commit:
        status_data["last_commit"] = last_commit
    
    # Format output
    output = []
    output.append(f"Branch: {status_data['branch']}")
    
    if status_data['ahead'] > 0:
        output.append(f"Ahead by {status_data['ahead']} commit(s)")
    if status_data['behind'] > 0:
        output.append(f"Behind by {status_data['behind']} commit(s)")
    
    if status_data.get('last_commit'):
        output.append(f"Last commit: {status_data['last_commit']}")
    
    if status_data['staged']:
        output.append("\nStaged changes:")
        for file in status_data['staged']:
            output.append(f"  + {file}")
    
    if status_data['unstaged']:
        output.append("\nUnstaged changes:")
        for file in status_data['unstaged']:
            output.append(f"  M {file}")
    
    if status_data['untracked']:
        output.append("\nUntracked files:")
        for file in status_data['untracked']:
            output.append(f"  ? {file}")
    
    if not (status_data['staged'] or status_data['unstaged'] or status_data['untracked']):
        output.append("\nWorking tree is clean")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_git_log(count: int = 10, author: Optional[str] = None, since: Optional[str] = None) -> List[TextContent]:
    """Get git commit history with filtering options.
    
    Args:
        count: Number of commits to retrieve (default: 10)
        author: Filter by author name/email
        since: Filter commits since date (e.g., '2024-01-01', '1 week ago')
    """
    cmd = ["log", f"-{count}", "--pretty=format:commit %H%nAuthor: %an <%ae>%nDate: %ad%n%n    %s%n"]
    
    if author:
        cmd.append(f"--author={author}")
    
    if since:
        cmd.append(f"--since={since}")
    
    log_output = run_git_command(cmd)
    
    if not log_output:
        return [TextContent(type="text", text="No commits found matching criteria")]
    
    commits = parse_git_log(log_output)
    
    # Format output
    output = [f"Showing {len(commits)} commit(s):\n"]
    
    for commit in commits:
        output.append(f"Commit: {commit.get('hash', 'Unknown')}")
        output.append(f"Author: {commit.get('author', 'Unknown')}")
        output.append(f"Date: {commit.get('date', 'Unknown')}")
        output.append(f"Message: {commit.get('message', 'No message')}")
        output.append("")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_git_branches() -> List[TextContent]:
    """List all git branches and identify the current branch."""
    branches_output = run_git_command(["branch", "-a", "-v"])
    
    if not branches_output:
        return [TextContent(type="text", text="Could not retrieve branch information")]
    
    lines = branches_output.split('\n')
    local_branches = []
    remote_branches = []
    current_branch = None
    
    for line in lines:
        if not line.strip():
            continue
            
        if line.startswith('*'):
            # Current branch
            parts = line[2:].split(None, 2)
            if parts:
                current_branch = parts[0]
                local_branches.append({
                    'name': parts[0],
                    'current': True,
                    'commit': parts[1] if len(parts) > 1 else '',
                    'message': parts[2] if len(parts) > 2 else ''
                })
        elif line.strip().startswith('remotes/'):
            # Remote branch
            parts = line.strip().split(None, 2)
            if parts:
                remote_branches.append({
                    'name': parts[0].replace('remotes/', ''),
                    'commit': parts[1] if len(parts) > 1 else '',
                    'message': parts[2] if len(parts) > 2 else ''
                })
        else:
            # Local branch
            parts = line.strip().split(None, 2)
            if parts:
                local_branches.append({
                    'name': parts[0],
                    'current': False,
                    'commit': parts[1] if len(parts) > 1 else '',
                    'message': parts[2] if len(parts) > 2 else ''
                })
    
    # Format output
    output = []
    if current_branch:
        output.append(f"Current branch: {current_branch}")
    
    output.append("\nLocal branches:")
    for branch in local_branches:
        marker = "* " if branch['current'] else "  "
        output.append(f"{marker}{branch['name']} {branch['commit']} {branch['message']}")
    
    if remote_branches:
        output.append("\nRemote branches:")
        for branch in remote_branches:
            output.append(f"  {branch['name']} {branch['commit']} {branch['message']}")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_git_diff(file_path: Optional[str] = None, staged: bool = False) -> List[TextContent]:
    """Show git diff for files.
    
    Args:
        file_path: Specific file to diff (optional, shows all if not specified)
        staged: Show staged changes instead of unstaged
    """
    cmd = ["diff"]
    
    if staged:
        cmd.append("--cached")
    
    if file_path:
        cmd.append(file_path)
    
    diff_output = run_git_command(cmd)
    
    if not diff_output:
        return [TextContent(type="text", text="No differences found")]
    
    # Parse and format diff output
    lines = diff_output.split('\n')
    formatted_output = []
    current_file = None
    
    for line in lines:
        if line.startswith('diff --git'):
            # New file diff
            match = re.search(r'a/(.*) b/', line)
            if match:
                current_file = match.group(1)
                formatted_output.append(f"\nFile: {current_file}")
        elif line.startswith('@@'):
            # Hunk header
            formatted_output.append(f"  {line}")
        elif line.startswith('+') and not line.startswith('+++'):
            # Added line
            formatted_output.append(f"  + {line[1:]}")
        elif line.startswith('-') and not line.startswith('---'):
            # Removed line
            formatted_output.append(f"  - {line[1:]}")
        elif line.startswith(' '):
            # Context line
            formatted_output.append(f"    {line[1:]}")
    
    return [TextContent(type="text", text="\n".join(formatted_output))]

@server.register_tool
async def karen_git_blame(file_path: str, line_start: Optional[int] = None, line_end: Optional[int] = None) -> List[TextContent]:
    """Show git blame information for a file.
    
    Args:
        file_path: File to analyze
        line_start: Starting line number (optional)
        line_end: Ending line number (optional)
    """
    cmd = ["blame", "--line-porcelain", file_path]
    
    if line_start and line_end:
        cmd.extend(["-L", f"{line_start},{line_end}"])
    elif line_start:
        cmd.extend(["-L", f"{line_start},+10"])
    
    blame_output = run_git_command(cmd)
    
    if not blame_output:
        return [TextContent(type="text", text=f"Could not get blame information for {file_path}")]
    
    # Parse blame output
    lines = blame_output.split('\n')
    blame_data = []
    current_commit = {}
    
    for line in lines:
        if line.startswith('author '):
            current_commit['author'] = line[7:]
        elif line.startswith('author-time '):
            timestamp = int(line[12:])
            current_commit['date'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        elif line.startswith('summary '):
            current_commit['summary'] = line[8:]
        elif line.startswith('\t'):
            # Actual line content
            if current_commit:
                blame_data.append({
                    'author': current_commit.get('author', 'Unknown'),
                    'date': current_commit.get('date', 'Unknown'),
                    'summary': current_commit.get('summary', ''),
                    'content': line[1:]
                })
                current_commit = {}
    
    # Format output
    output = [f"Blame for {file_path}:\n"]
    
    for i, data in enumerate(blame_data, 1):
        output.append(f"{i:4d} | {data['author'][:20]:20} | {data['date']} | {data['content']}")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_git_file_history(file_path: str, limit: int = 10) -> List[TextContent]:
    """Get commit history for a specific file.
    
    Args:
        file_path: File to get history for
        limit: Maximum number of commits to show
    """
    cmd = ["log", f"-{limit}", "--follow", "--pretty=format:%H|%an|%ad|%s", "--", file_path]
    
    history_output = run_git_command(cmd)
    
    if not history_output:
        return [TextContent(type="text", text=f"No history found for {file_path}")]
    
    lines = history_output.split('\n')
    commits = []
    
    for line in lines:
        if '|' in line:
            parts = line.split('|', 3)
            if len(parts) >= 4:
                commits.append({
                    'hash': parts[0][:8],
                    'author': parts[1],
                    'date': parts[2],
                    'message': parts[3]
                })
    
    # Format output
    output = [f"File history for {file_path} ({len(commits)} commits):\n"]
    
    for commit in commits:
        output.append(f"{commit['hash']} - {commit['author']} - {commit['date']}")
        output.append(f"  {commit['message']}")
        output.append("")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_uncommitted_changes() -> List[TextContent]:
    """Get all uncommitted changes including file diffs."""
    # Get status first
    status_output = run_git_command(["status", "--porcelain"])
    
    if not status_output:
        return [TextContent(type="text", text="No uncommitted changes found")]
    
    lines = status_output.split('\n')
    staged_files = []
    unstaged_files = []
    untracked_files = []
    
    for line in lines:
        if not line:
            continue
            
        status = line[:2]
        file_path = line[3:]
        
        if status[0] != ' ' and status[0] != '?':
            staged_files.append(file_path)
        if status[1] != ' ' and status[1] != '?':
            unstaged_files.append(file_path)
        if status == '??':
            untracked_files.append(file_path)
    
    output = ["Uncommitted changes summary:\n"]
    
    # Show staged changes
    if staged_files:
        output.append("Staged changes:")
        for file in staged_files:
            output.append(f"  + {file}")
        
        # Get staged diff
        diff_output = run_git_command(["diff", "--cached", "--stat"])
        if diff_output:
            output.append("\nStaged diff statistics:")
            output.append(diff_output)
    
    # Show unstaged changes
    if unstaged_files:
        output.append("\nUnstaged changes:")
        for file in unstaged_files:
            output.append(f"  M {file}")
        
        # Get unstaged diff
        diff_output = run_git_command(["diff", "--stat"])
        if diff_output:
            output.append("\nUnstaged diff statistics:")
            output.append(diff_output)
    
    # Show untracked files
    if untracked_files:
        output.append("\nUntracked files:")
        for file in untracked_files:
            output.append(f"  ? {file}")
    
    return [TextContent(type="text", text="\n".join(output))]

# Tool definitions for registration
TOOLS = [
    Tool(
        name="karen_git_status",
        description="Get comprehensive git repository status including branch, staged/unstaged changes, and untracked files",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="karen_git_log",
        description="Get git commit history with filtering options",
        inputSchema={
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of commits to retrieve", "default": 10},
                "author": {"type": "string", "description": "Filter by author name/email"},
                "since": {"type": "string", "description": "Filter commits since date (e.g., '2024-01-01', '1 week ago')"}
            }
        }
    ),
    Tool(
        name="karen_git_branches",
        description="List all git branches and identify the current branch",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="karen_git_diff",
        description="Show git diff for files",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Specific file to diff"},
                "staged": {"type": "boolean", "description": "Show staged changes instead of unstaged", "default": False}
            }
        }
    ),
    Tool(
        name="karen_git_blame",
        description="Show git blame information for a file",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "File to analyze"},
                "line_start": {"type": "integer", "description": "Starting line number"},
                "line_end": {"type": "integer", "description": "Ending line number"}
            },
            "required": ["file_path"]
        }
    ),
    Tool(
        name="karen_git_file_history",
        description="Get commit history for a specific file",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "File to get history for"},
                "limit": {"type": "integer", "description": "Maximum number of commits to show", "default": 10}
            },
            "required": ["file_path"]
        }
    ),
    Tool(
        name="karen_uncommitted_changes",
        description="Get all uncommitted changes including file diffs",
        inputSchema={"type": "object", "properties": {}}
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