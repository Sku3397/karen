#!/usr/bin/env python3
"""
Karen Codebase Core MCP Server - Phase 1: File System Operations
Provides core file management tools for the Karen project codebase.
MCP Protocol 2024-11-05 compliant.
"""

import os
import sys
import json
import logging
import shutil
import stat
import datetime
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import mimetypes

# MCP imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Constants
PROJECT_ROOT = Path(__file__).parent
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit for file reading
BACKUP_SUFFIX = ".backup"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'karen_codebase_mcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('karen_codebase_core')


class FileSystemError(Exception):
    """Custom exception for file system operations"""
    pass


def validate_path(path: str, must_exist: bool = False) -> Path:
    """Validate and normalize a file path"""
    try:
        # Convert to Path object
        p = Path(path)
        
        # Make absolute relative to project root if relative
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        
        # Resolve to canonical path
        p = p.resolve()
        
        # Ensure path is within project directory (security)
        if not str(p).startswith(str(PROJECT_ROOT)):
            raise FileSystemError(f"Access denied: Path '{path}' is outside project directory")
        
        # Check existence if required
        if must_exist and not p.exists():
            raise FileSystemError(f"Path does not exist: {path}")
        
        return p
    except Exception as e:
        if isinstance(e, FileSystemError):
            raise
        raise FileSystemError(f"Invalid path: {path} - {str(e)}")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_file_type(path: Path) -> str:
    """Determine file type from extension and content"""
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type:
        return mime_type
    
    # Common development file types
    ext = path.suffix.lower()
    type_map = {
        '.py': 'text/x-python',
        '.js': 'text/javascript',
        '.jsx': 'text/javascript',
        '.ts': 'text/typescript',
        '.tsx': 'text/typescript',
        '.json': 'application/json',
        '.md': 'text/markdown',
        '.yml': 'text/yaml',
        '.yaml': 'text/yaml',
        '.toml': 'text/toml',
        '.sh': 'text/x-shellscript',
        '.bat': 'text/x-batch',
        '.ps1': 'text/x-powershell'
    }
    
    return type_map.get(ext, 'text/plain' if path.is_file() else 'directory')


class KarenCodebaseMCP:
    """MCP Server for Karen Codebase File System Operations"""
    
    def __init__(self):
        self.name = "karen-codebase-core"
        self.version = "1.0.0"
        self.tools = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools"""
        self.tools = {
            "read_file": {
                "description": "Read the contents of a file in the Karen project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file (relative or absolute)"
                        }
                    },
                    "required": ["path"]
                },
                "handler": self.read_file
            },
            "write_file": {
                "description": "Write content to a file with automatic backup",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        },
                        "create_backup": {
                            "type": "boolean",
                            "description": "Create backup of existing file",
                            "default": True
                        }
                    },
                    "required": ["path", "content"]
                },
                "handler": self.write_file
            },
            "list_directory": {
                "description": "List files and directories with advanced filtering",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path",
                            "default": "."
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "List recursively",
                            "default": False
                        },
                        "filter_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by file extensions (e.g., ['.py', '.js'])"
                        },
                        "include_hidden": {
                            "type": "boolean",
                            "description": "Include hidden files",
                            "default": False
                        }
                    }
                },
                "handler": self.list_directory
            },
            "get_file_info": {
                "description": "Get detailed file metadata",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file"
                        }
                    },
                    "required": ["path"]
                },
                "handler": self.get_file_info
            },
            "file_exists": {
                "description": "Check if a file or directory exists",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to check"
                        }
                    },
                    "required": ["path"]
                },
                "handler": self.file_exists
            },
            "create_directory": {
                "description": "Create a directory with parent directories",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to create"
                        },
                        "parents": {
                            "type": "boolean",
                            "description": "Create parent directories",
                            "default": True
                        }
                    },
                    "required": ["path"]
                },
                "handler": self.create_directory
            },
            "delete_file": {
                "description": "Delete a file or empty directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to delete"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force deletion without confirmation",
                            "default": False
                        }
                    },
                    "required": ["path"]
                },
                "handler": self.delete_file
            }
        }
    
    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read file contents with size and encoding validation"""
        try:
            file_path = validate_path(path, must_exist=True)
            
            if not file_path.is_file():
                raise FileSystemError(f"Path is not a file: {path}")
            
            # Check file size
            size = file_path.stat().st_size
            if size > MAX_FILE_SIZE:
                raise FileSystemError(f"File too large: {format_file_size(size)} (max: {format_file_size(MAX_FILE_SIZE)})")
            
            # Try to read with different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            content = None
            encoding_used = None
            
            for encoding in encodings:
                try:
                    content = file_path.read_text(encoding=encoding)
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                # Read as binary if text decoding fails
                content = file_path.read_bytes()
                return {
                    "success": True,
                    "path": str(file_path),
                    "content": content.hex(),
                    "encoding": "binary",
                    "size": size,
                    "binary": True
                }
            
            return {
                "success": True,
                "path": str(file_path),
                "content": content,
                "encoding": encoding_used,
                "size": size,
                "lines": len(content.splitlines())
            }
            
        except Exception as e:
            logger.error(f"Error reading file {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    async def write_file(self, path: str, content: str, create_backup: bool = True) -> Dict[str, Any]:
        """Write file with backup and safety checks"""
        try:
            file_path = validate_path(path)
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if file exists
            backup_path = None
            if file_path.exists() and create_backup:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_suffix(f"{file_path.suffix}.{timestamp}{BACKUP_SUFFIX}")
                shutil.copy2(file_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Write content
            file_path.write_text(content, encoding='utf-8')
            
            # Get final file info
            stat = file_path.stat()
            
            return {
                "success": True,
                "path": str(file_path),
                "size": stat.st_size,
                "backup_path": str(backup_path) if backup_path else None,
                "lines": len(content.splitlines())
            }
            
        except Exception as e:
            logger.error(f"Error writing file {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    async def list_directory(self, path: str = ".", recursive: bool = False, 
                           filter_types: Optional[List[str]] = None,
                           include_hidden: bool = False) -> Dict[str, Any]:
        """List directory contents with filtering"""
        try:
            dir_path = validate_path(path, must_exist=True)
            
            if not dir_path.is_dir():
                raise FileSystemError(f"Path is not a directory: {path}")
            
            items = []
            total_size = 0
            
            if recursive:
                # Recursive listing
                for root, dirs, files in os.walk(dir_path):
                    root_path = Path(root)
                    
                    # Filter hidden directories
                    if not include_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    # Process files
                    for file in files:
                        if not include_hidden and file.startswith('.'):
                            continue
                        
                        file_path = root_path / file
                        
                        # Apply type filter
                        if filter_types and not any(file.endswith(ext) for ext in filter_types):
                            continue
                        
                        try:
                            stat = file_path.stat()
                            items.append({
                                "name": str(file_path.relative_to(dir_path)),
                                "type": "file",
                                "size": stat.st_size,
                                "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                            })
                            total_size += stat.st_size
                        except:
                            pass
            else:
                # Non-recursive listing
                for item in dir_path.iterdir():
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    
                    # Apply type filter for files
                    if item.is_file() and filter_types:
                        if not any(item.name.endswith(ext) for ext in filter_types):
                            continue
                    
                    try:
                        stat = item.stat()
                        item_info = {
                            "name": item.name,
                            "type": "directory" if item.is_dir() else "file",
                            "size": stat.st_size,
                            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                        }
                        
                        if item.is_file():
                            item_info["extension"] = item.suffix
                            total_size += stat.st_size
                        
                        items.append(item_info)
                    except:
                        pass
            
            # Sort items
            items.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
            
            return {
                "success": True,
                "path": str(dir_path),
                "items": items,
                "count": len(items),
                "total_size": total_size,
                "total_size_formatted": format_file_size(total_size)
            }
            
        except Exception as e:
            logger.error(f"Error listing directory {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    async def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get comprehensive file metadata"""
        try:
            file_path = validate_path(path, must_exist=True)
            stat = file_path.stat()
            
            info = {
                "success": True,
                "path": str(file_path),
                "name": file_path.name,
                "type": "directory" if file_path.is_dir() else "file",
                "size": stat.st_size,
                "size_formatted": format_file_size(stat.st_size),
                "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.datetime.fromtimestamp(stat.st_atime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],
                "readable": os.access(file_path, os.R_OK),
                "writable": os.access(file_path, os.W_OK),
                "executable": os.access(file_path, os.X_OK)
            }
            
            if file_path.is_file():
                info["extension"] = file_path.suffix
                info["mime_type"] = get_file_type(file_path)
                
                # Line count for text files
                if info["mime_type"].startswith("text/"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            info["lines"] = sum(1 for _ in f)
                    except:
                        pass
            
            elif file_path.is_dir():
                # Directory statistics
                try:
                    items = list(file_path.iterdir())
                    info["item_count"] = len(items)
                    info["file_count"] = sum(1 for item in items if item.is_file())
                    info["dir_count"] = sum(1 for item in items if item.is_dir())
                except:
                    pass
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    async def file_exists(self, path: str) -> Dict[str, Any]:
        """Check file existence and type"""
        try:
            file_path = validate_path(path)
            exists = file_path.exists()
            
            result = {
                "success": True,
                "path": str(file_path),
                "exists": exists
            }
            
            if exists:
                result["is_file"] = file_path.is_file()
                result["is_directory"] = file_path.is_dir()
                result["is_symlink"] = file_path.is_symlink()
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking file existence for {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    async def create_directory(self, path: str, parents: bool = True) -> Dict[str, Any]:
        """Create directory with parent creation option"""
        try:
            dir_path = validate_path(path)
            
            if dir_path.exists():
                if dir_path.is_dir():
                    return {
                        "success": True,
                        "path": str(dir_path),
                        "created": False,
                        "message": "Directory already exists"
                    }
                else:
                    raise FileSystemError(f"Path exists but is not a directory: {path}")
            
            # Create directory
            dir_path.mkdir(parents=parents, exist_ok=True)
            
            return {
                "success": True,
                "path": str(dir_path),
                "created": True,
                "parents_created": parents
            }
            
        except Exception as e:
            logger.error(f"Error creating directory {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    async def delete_file(self, path: str, force: bool = False) -> Dict[str, Any]:
        """Delete file or empty directory with safety checks"""
        try:
            file_path = validate_path(path, must_exist=True)
            
            # Safety checks
            if not force:
                # Prevent deletion of critical files
                critical_patterns = [
                    ".git", ".env", "requirements.txt", "package.json",
                    "Dockerfile", "docker-compose", ".gitignore"
                ]
                
                if any(pattern in str(file_path) for pattern in critical_patterns):
                    raise FileSystemError(f"Cannot delete critical file: {path}. Use force=True to override.")
            
            deleted_info = {
                "path": str(file_path),
                "type": "directory" if file_path.is_dir() else "file",
                "size": file_path.stat().st_size if file_path.is_file() else 0
            }
            
            if file_path.is_dir():
                # Only delete empty directories
                if any(file_path.iterdir()):
                    raise FileSystemError(f"Directory not empty: {path}")
                file_path.rmdir()
            else:
                file_path.unlink()
            
            return {
                "success": True,
                "deleted": deleted_info,
                "message": f"Successfully deleted {deleted_info['type']}: {path}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": self.name,
                    "version": self.version
                }
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
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
            
            try:
                handler = self.tools[tool_name]["handler"]
                result = await handler(**arguments)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            except Exception as e:
                logger.error(f"Tool execution error: {str(e)}", exc_info=True)
                return {
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
        
        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }


async def main():
    """Main entry point for MCP server"""
    server = KarenCodebaseMCP()
    logger.info(f"Starting {server.name} v{server.version}")
    
    # Read from stdin and write to stdout
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    
    while True:
        try:
            # Read line from stdin
            line = await reader.readline()
            if not line:
                break
            
            # Parse JSON request
            request = json.loads(line.decode())
            logger.debug(f"Received request: {request}")
            
            # Handle request
            response = await server.handle_request(request)
            
            # Send response
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            error_response = {
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            error_response = {
                "error": {
                    "code": -32603,
                    "message": "Internal error"
                }
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)