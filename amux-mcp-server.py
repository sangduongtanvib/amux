#!/usr/bin/env python3
"""AMUX MCP Server - Model Context Protocol server for AMUX orchestration.

Exposes AMUX operations as MCP tools for AI agent orchestration.
"""

import json
import sys
import urllib.request
import urllib.error
import ssl
from typing import Any, Dict, List, Optional

# AMUX API configuration
AMUX_URL = "https://localhost:8822"

# Create SSL context that doesn't verify certificates (for local dev)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def debug_log(msg: str):
    """Log to stderr for debugging (stdout is for MCP protocol)."""
    print(f"[AMUX-MCP] {msg}", file=sys.stderr, flush=True)


def amux_api_call(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
    """Make HTTP request to AMUX API."""
    url = f"{AMUX_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if data:
            req = urllib.request.Request(
                url, 
                data=json.dumps(data).encode(),
                headers=headers,
                method=method
            )
        else:
            req = urllib.request.Request(url, headers=headers, method=method)
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        try:
            error_data = json.loads(error_body)
            raise Exception(f"AMUX API error: {error_data.get('error', error_body)}")
        except json.JSONDecodeError:
            raise Exception(f"AMUX API error {e.code}: {error_body}")
    except Exception as e:
        raise Exception(f"Failed to connect to AMUX: {str(e)}")


# ═══════════════════════════════════════════
# MCP TOOL IMPLEMENTATIONS
# ═══════════════════════════════════════════

def tool_amux_list_sessions(args: Dict) -> Dict:
    """List all AMUX sessions with their status."""
    sessions = amux_api_call("/api/sessions")
    
    # Format response
    result = []
    for s in sessions:
        result.append({
            "name": s.get("name", ""),
            "status": s.get("status", ""),
            "running": s.get("running", False),
            "dir": s.get("dir", ""),
            "tool": s.get("tool", "claude_code"),
            "desc": s.get("desc", ""),
        })
    
    return {
        "sessions": result,
        "count": len(result),
        "message": f"Found {len(result)} sessions"
    }


def tool_amux_create_session(args: Dict) -> Dict:
    """Create a new AMUX session."""
    name = args.get("name")
    dir_path = args.get("dir", "")
    tool = args.get("tool", "claude_code")
    desc = args.get("desc", "")
    
    if not name:
        raise ValueError("Session name is required")
    
    data = {
        "name": name,
        "dir": dir_path,
        "tool": tool,
        "desc": desc,
        "creator": "mcp-orchestrator"
    }
    
    result = amux_api_call("/api/sessions", method="POST", data=data)
    return {
        "success": True,
        "name": name,
        "message": result.get("message", f"Created session '{name}'")
    }


def tool_amux_start_session(args: Dict) -> Dict:
    """Start an AMUX session."""
    name = args.get("name")
    if not name:
        raise ValueError("Session name is required")
    
    result = amux_api_call(f"/api/sessions/{name}/start", method="POST")
    return {
        "success": True,
        "name": name,
        "message": f"Started session '{name}'"
    }


def tool_amux_stop_session(args: Dict) -> Dict:
    """Stop an AMUX session."""
    name = args.get("name")
    if not name:
        raise ValueError("Session name is required")
    
    result = amux_api_call(f"/api/sessions/{name}/stop", method="POST")
    return {
        "success": True,
        "name": name,
        "message": f"Stopped session '{name}'"
    }


def tool_amux_send_message(args: Dict) -> Dict:
    """Send a message/prompt to an AMUX session."""
    name = args.get("name")
    text = args.get("text")
    
    if not name:
        raise ValueError("Session name is required")
    if not text:
        raise ValueError("Message text is required")
    
    data = {"text": text}
    result = amux_api_call(f"/api/sessions/{name}/send", method="POST", data=data)
    
    return {
        "success": True,
        "name": name,
        "message": f"Sent message to '{name}': {text[:50]}..."
    }


def tool_amux_get_status(args: Dict) -> Dict:
    """Get detailed status of one or all sessions."""
    name = args.get("name")
    
    if name:
        # Get specific session
        sessions = amux_api_call("/api/sessions")
        session = next((s for s in sessions if s["name"] == name), None)
        if not session:
            raise ValueError(f"Session '{name}' not found")
        return {
            "name": session.get("name"),
            "status": session.get("status", ""),
            "running": session.get("running", False),
            "preview": session.get("preview", ""),
            "dir": session.get("dir", ""),
            "tool": session.get("tool", "claude_code"),
        }
    else:
        # Get all sessions summary
        sessions = amux_api_call("/api/sessions")
        summary = {
            "total": len(sessions),
            "running": sum(1 for s in sessions if s.get("running")),
            "active": sum(1 for s in sessions if s.get("status") == "active"),
            "waiting": sum(1 for s in sessions if s.get("status") == "waiting"),
            "idle": sum(1 for s in sessions if s.get("status") == "idle"),
        }
        return {
            "summary": summary,
            "sessions": [
                {
                    "name": s.get("name"),
                    "status": s.get("status"),
                    "running": s.get("running"),
                }
                for s in sessions
            ]
        }


def tool_amux_peek_output(args: Dict) -> Dict:
    """Peek at the terminal output of a session."""
    name = args.get("name")
    lines = args.get("lines", 50)
    
    if not name:
        raise ValueError("Session name is required")
    
    result = amux_api_call(f"/api/sessions/{name}/peek?lines={lines}")
    return {
        "name": name,
        "output": result.get("output", ""),
        "lines": lines,
        "running": result.get("running", False),
    }


def tool_amux_list_board_tasks(args: Dict) -> Dict:
    """List tasks from the Kanban board."""
    status_filter = args.get("status", "")
    session_filter = args.get("session", "")
    
    board = amux_api_call("/api/board")
    
    # Apply filters
    tasks = board
    if status_filter:
        tasks = [t for t in tasks if t.get("status") == status_filter]
    if session_filter:
        tasks = [t for t in tasks if t.get("session") == session_filter]
    
    return {
        "tasks": [
            {
                "id": t.get("id"),
                "title": t.get("title"),
                "status": t.get("status"),
                "session": t.get("session"),
                "desc": t.get("desc", ""),
            }
            for t in tasks
        ],
        "count": len(tasks),
    }


def tool_amux_create_board_task(args: Dict) -> Dict:
    """Create a new task on the Kanban board."""
    title = args.get("title")
    if not title:
        raise ValueError("Task title is required")
    
    data = {
        "title": title,
        "desc": args.get("desc", ""),
        "status": args.get("status", "todo"),
        "session": args.get("session", ""),
        "owner_type": "agent",
    }
    
    result = amux_api_call("/api/board", method="POST", data=data)
    return {
        "success": True,
        "task_id": result.get("id", ""),
        "message": f"Created task: {title}"
    }


def tool_amux_claim_task(args: Dict) -> Dict:
    """Atomically claim a board task for a session."""
    task_id = args.get("task_id")
    session = args.get("session")
    
    if not task_id:
        raise ValueError("Task ID is required")
    if not session:
        raise ValueError("Session name is required")
    
    data = {"session": session}
    result = amux_api_call(f"/api/board/{task_id}/claim", method="POST", data=data)
    
    return {
        "success": result.get("ok", False),
        "task_id": task_id,
        "session": session,
        "message": result.get("message", f"Claimed task {task_id} for {session}")
    }


def tool_amux_update_task(args: Dict) -> Dict:
    """Update a board task (status, description, etc)."""
    task_id = args.get("task_id")
    if not task_id:
        raise ValueError("Task ID is required")
    
    data = {}
    if "status" in args:
        data["status"] = args["status"]
    if "desc" in args:
        data["desc"] = args["desc"]
    if "title" in args:
        data["title"] = args["title"]
    
    if not data:
        raise ValueError("At least one field to update is required")
    
    result = amux_api_call(f"/api/board/{task_id}", method="PATCH", data=data)
    return {
        "success": True,
        "task_id": task_id,
        "message": f"Updated task {task_id}"
    }


# ═══════════════════════════════════════════
# MCP PROTOCOL IMPLEMENTATION
# ═══════════════════════════════════════════

MCP_TOOLS = {
    "amux_list_sessions": {
        "description": "List all AMUX sessions with their current status",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "handler": tool_amux_list_sessions
    },
    "amux_create_session": {
        "description": "Create a new AMUX session for an AI coding agent",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Session name (alphanumeric, hyphens, underscores)"
                },
                "dir": {
                    "type": "string",
                    "description": "Working directory path for the session"
                },
                "tool": {
                    "type": "string",
                    "description": "AI tool to use: 'claude_code' or 'cursor'",
                    "enum": ["claude_code", "cursor"]
                },
                "desc": {
                    "type": "string",
                    "description": "Optional description of the session"
                }
            },
            "required": ["name"]
        },
        "handler": tool_amux_create_session
    },
    "amux_start_session": {
        "description": "Start an AMUX session (launches the AI agent)",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Session name to start"
                }
            },
            "required": ["name"]
        },
        "handler": tool_amux_start_session
    },
    "amux_stop_session": {
        "description": "Stop a running AMUX session",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Session name to stop"
                }
            },
            "required": ["name"]
        },
        "handler": tool_amux_stop_session
    },
    "amux_send_message": {
        "description": "Send a message/prompt to an AMUX session",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Session name to send message to"
                },
                "text": {
                    "type": "string",
                    "description": "Message text or prompt to send"
                }
            },
            "required": ["name", "text"]
        },
        "handler": tool_amux_send_message
    },
    "amux_get_status": {
        "description": "Get status of sessions (specific session or all sessions summary)",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Optional: specific session name. Omit for all sessions summary"
                }
            },
            "required": []
        },
        "handler": tool_amux_get_status
    },
    "amux_peek_output": {
        "description": "View the terminal output of a session without attaching",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Session name to peek at"
                },
                "lines": {
                    "type": "integer",
                    "description": "Number of lines to fetch (default: 50)",
                    "default": 50
                }
            },
            "required": ["name"]
        },
        "handler": tool_amux_peek_output
    },
    "amux_list_board_tasks": {
        "description": "List tasks from the Kanban board, with optional filters",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Optional: filter by status (todo, doing, done, etc)"
                },
                "session": {
                    "type": "string",
                    "description": "Optional: filter by assigned session"
                }
            },
            "required": []
        },
        "handler": tool_amux_list_board_tasks
    },
    "amux_create_board_task": {
        "description": "Create a new task on the Kanban board",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title"
                },
                "desc": {
                    "type": "string",
                    "description": "Task description"
                },
                "status": {
                    "type": "string",
                    "description": "Initial status (default: todo)"
                },
                "session": {
                    "type": "string",
                    "description": "Assign to specific session"
                }
            },
            "required": ["title"]
        },
        "handler": tool_amux_create_board_task
    },
    "amux_claim_task": {
        "description": "Atomically claim a board task for a session (prevents race conditions)",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Task ID to claim (e.g., PROJ-5)"
                },
                "session": {
                    "type": "string",
                    "description": "Session name claiming the task"
                }
            },
            "required": ["task_id", "session"]
        },
        "handler": tool_amux_claim_task
    },
    "amux_update_task": {
        "description": "Update a board task (change status, description, etc)",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Task ID to update"
                },
                "status": {
                    "type": "string",
                    "description": "New status"
                },
                "desc": {
                    "type": "string",
                    "description": "New description"
                },
                "title": {
                    "type": "string",
                    "description": "New title"
                }
            },
            "required": ["task_id"]
        },
        "handler": tool_amux_update_task
    },
}


def handle_initialize(params: Dict) -> Dict:
    """Handle MCP initialize request."""
    return {
        "protocolVersion": "0.1.0",
        "serverInfo": {
            "name": "amux-mcp-server",
            "version": "1.0.0"
        },
        "capabilities": {
            "tools": {}
        }
    }


def handle_list_tools(params: Dict) -> Dict:
    """Handle tools/list request."""
    tools = []
    for name, spec in MCP_TOOLS.items():
        tools.append({
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["input_schema"]
        })
    return {"tools": tools}


def handle_call_tool(params: Dict) -> Dict:
    """Handle tools/call request."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if tool_name not in MCP_TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    debug_log(f"Calling tool: {tool_name} with args: {arguments}")
    
    try:
        handler = MCP_TOOLS[tool_name]["handler"]
        result = handler(arguments)
        
        # Format result as text content
        result_text = json.dumps(result, indent=2)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": result_text
                }
            ]
        }
    except Exception as e:
        debug_log(f"Tool error: {str(e)}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"error": str(e)}, indent=2)
                }
            ],
            "isError": True
        }


def handle_request(request: Dict) -> Dict:
    """Handle MCP JSON-RPC request."""
    method = request.get("method")
    params = request.get("params", {})
    
    debug_log(f"Handling request: {method}")
    
    handlers = {
        "initialize": handle_initialize,
        "tools/list": handle_list_tools,
        "tools/call": handle_call_tool,
    }
    
    if method not in handlers:
        raise ValueError(f"Unknown method: {method}")
    
    return handlers[method](params)


def main():
    """Main MCP server loop - reads JSON-RPC from stdin, writes to stdout."""
    debug_log("AMUX MCP Server starting...")
    debug_log(f"Connecting to AMUX at {AMUX_URL}")
    
    try:
        # Read requests from stdin line by line
        # Note: for line in sys.stdin will block until data arrives or stdin closes
        while True:
            try:
                line = sys.stdin.readline()
                if not line:  # EOF reached, stdin closed
                    debug_log("stdin closed, server exiting")
                    break
                
                line = line.strip()
                if not line:
                    continue
            
                message = json.loads(line)
                message_id = message.get("id")
                method = message.get("method", "")
                
                # Distinguish between requests (with id) and notifications (without id)
                if message_id is None:
                    # This is a notification - no response needed
                    debug_log(f"Received notification: {method}")
                    if method == "notifications/initialized":
                        debug_log("Client initialized successfully")
                    # Silently ignore other notifications
                    continue
                
                # This is a request - must send response
                try:
                    result = handle_request(message)
                    response = {
                        "jsonrpc": "2.0",
                        "id": message_id,
                        "result": result
                    }
                except Exception as e:
                    debug_log(f"Error handling request: {str(e)}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": message_id,
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        }
                    }
                
                # Write response to stdout
                print(json.dumps(response), flush=True)
                debug_log(f"Response sent for {method} (id={message_id})")
                
            except json.JSONDecodeError as e:
                debug_log(f"Invalid JSON: {e}")
                continue
            except Exception as e:
                debug_log(f"Unexpected error processing message: {e}")
                import traceback
                debug_log(traceback.format_exc())
                continue
                
    except KeyboardInterrupt:
        debug_log("Server stopped by user")
    except Exception as e:
        debug_log(f"Fatal error: {e}")
        import traceback
        debug_log(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
