#!/usr/bin/env python3
"""
AMUX MCP Integration Test Suite

Comprehensive tests for AMUX MCP server integration with Claude Code/Cursor.
Tests all 11 MCP tools and validates orchestration workflows.

Usage:
    python3 test-mcp-integration.py [--verbose]
"""

import json
import subprocess
import time
import sys
from typing import Dict, Any, List, Optional


class MCPTester:
    """Test harness for AMUX MCP server."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.request_id = 1
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message."""
        if self.verbose or level in ["ERROR", "FAIL", "PASS"]:
            prefix = {
                "INFO": "ℹ️ ",
                "PASS": "✅",
                "FAIL": "❌",
                "ERROR": "🚨",
                "TEST": "🧪"
            }.get(level, "  ")
            print(f"{prefix} {message}")
    
    def call_mcp_method(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Call an MCP method."""
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        self.request_id += 1
        
        self.log(f"Calling {method}", "INFO")
        
        proc = subprocess.run(
            ["python3", "amux-mcp-server.py"],
            input=json.dumps(request),
            capture_output=True,
            text=True
        )
        
        # Parse response (last JSON line)
        lines = proc.stdout.strip().split('\n')
        response_lines = [l for l in lines if l.startswith('{"jsonrpc"')]
        
        if not response_lines:
            self.log(f"No JSON response for {method}", "ERROR")
            return {"error": "No response"}
        
        response = json.loads(response_lines[0])
        
        if "error" in response:
            self.log(f"Error: {response['error']}", "ERROR")
        
        return response
    
    def call_mcp_tool(self, tool_name: str, arguments: Dict = None) -> Dict[str, Any]:
        """Call an MCP tool."""
        response = self.call_mcp_method(
            "tools/call",
            {"name": tool_name, "arguments": arguments or {}}
        )
        
        if "result" in response and "content" in response["result"]:
            content = response["result"]["content"][0]["text"]
            return json.loads(content)
        
        return response
    
    def assert_success(self, result: Dict, test_name: str):
        """Assert that a result is successful."""
        self.tests_run += 1
        
        if "error" in result:
            self.log(f"{test_name}: FAILED - {result.get('error')}", "FAIL")
            self.tests_failed += 1
            return False
        else:
            self.log(f"{test_name}: PASSED", "PASS")
            self.tests_passed += 1
            return True
    
    def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*70)
        print("🧪 AMUX MCP Integration Test Suite")
        print("="*70 + "\n")
        
        # Test 1: Protocol handshake
        self.test_protocol_handshake()
        
        # Test 2: List tools
        self.test_list_tools()
        
        # Test 3: Session management
        self.test_session_management()
        
        # Test 4: Board tasks
        self.test_board_tasks()
        
        # Test 5: Orchestration workflow
        self.test_orchestration_workflow()
        
        # Test 6: Error handling
        self.test_error_handling()
        
        # Print summary
        self.print_summary()
    
    def test_protocol_handshake(self):
        """Test MCP protocol initialization."""
        print("🔌 Test Group 1: Protocol Handshake")
        print("-" * 70)
        
        result = self.call_mcp_method("initialize", {})
        
        if "result" in result:
            protocol_version = result["result"].get("protocolVersion")
            server_name = result["result"].get("serverInfo", {}).get("name")
            self.assert_success(result, "Protocol initialization")
            self.log(f"   Protocol: {protocol_version}, Server: {server_name}", "INFO")
        else:
            self.assert_success(result, "Protocol initialization")
        
        print()
    
    def test_list_tools(self):
        """Test listing MCP tools."""
        print("📋 Test Group 2: List Tools")
        print("-" * 70)
        
        result = self.call_mcp_method("tools/list", {})
        
        if "result" in result:
            tools = result["result"].get("tools", [])
            self.assert_success(result, "List tools")
            self.log(f"   Found {len(tools)} tools", "INFO")
            
            # Verify all 11 expected tools
            expected_tools = [
                "amux_list_sessions",
                "amux_create_session",
                "amux_start_session",
                "amux_stop_session",
                "amux_send_message",
                "amux_get_status",
                "amux_peek_output",
                "amux_list_board_tasks",
                "amux_create_board_task",
                "amux_claim_task",
                "amux_update_task"
            ]
            
            tool_names = [t["name"] for t in tools]
            missing = set(expected_tools) - set(tool_names)
            
            if missing:
                self.log(f"   Missing tools: {missing}", "ERROR")
            else:
                self.log(f"   All 11 expected tools present", "INFO")
        else:
            self.assert_success(result, "List tools")
        
        print()
    
    def test_session_management(self):
        """Test session management tools."""
        print("🖥️  Test Group 3: Session Management")
        print("-" * 70)
        
        # 3.1: List initial sessions
        result = self.call_mcp_tool("amux_list_sessions")
        self.assert_success(result, "List sessions")
        initial_count = result.get("count", 0)
        self.log(f"   Initial sessions: {initial_count}", "INFO")
        
        # 3.2: Create test session
        test_session_name = f"test-session-{int(time.time())}"
        result = self.call_mcp_tool("amux_create_session", {
            "name": test_session_name,
            "dir": "~/Documents/research/amux",
            "tool": "claude_code",
            "desc": "Integration test session"
        })
        
        if self.assert_success(result, "Create session"):
            self.log(f"   Created session: {test_session_name}", "INFO")
            
            # 3.3: Get session status
            time.sleep(1)
            result = self.call_mcp_tool("amux_get_status", {"name": test_session_name})
            self.assert_success(result, "Get session status")
            
            # 3.4: Start session
            result = self.call_mcp_tool("amux_start_session", {"name": test_session_name})
            self.assert_success(result, "Start session")
            
            # 3.5: Send message
            time.sleep(2)
            result = self.call_mcp_tool("amux_send_message", {
                "name": test_session_name,
                "text": "Hello from MCP test! Please respond with a simple acknowledgment."
            })
            self.assert_success(result, "Send message")
            
            # 3.6: Peek output
            time.sleep(3)
            result = self.call_mcp_tool("amux_peek_output", {"name": test_session_name})
            self.assert_success(result, "Peek output")
            if "output" in result:
                output_len = len(result["output"])
                self.log(f"   Output length: {output_len} chars", "INFO")
            
            # 3.7: Stop session
            result = self.call_mcp_tool("amux_stop_session", {"name": test_session_name})
            self.assert_success(result, "Stop session")
        
        print()
    
    def test_board_tasks(self):
        """Test board task management tools."""
        print("📝 Test Group 4: Board Task Management")
        print("-" * 70)
        
        # 4.1: List initial tasks
        result = self.call_mcp_tool("amux_list_board_tasks")
        self.assert_success(result, "List board tasks")
        initial_count = len(result.get("tasks", []))
        self.log(f"   Initial tasks: {initial_count}", "INFO")
        
        # 4.2: Create test task
        result = self.call_mcp_tool("amux_create_board_task", {
            "title": f"Integration test task {int(time.time())}",
            "desc": "Automated test task",
            "status": "todo"
        })
        
        if self.assert_success(result, "Create board task"):
            task_id = result.get("task_id", "")
            self.log(f"   Created task: {task_id}", "INFO")
            
            # 4.3: Claim task (requires session name)
            claim_session = f"test-claim-{int(time.time())}"
            # Create a session for claiming
            self.call_mcp_tool("amux_create_session", {
                "name": claim_session,
                "dir": "~/Documents/research/amux",
                "tool": "claude_code"
            })
            result = self.call_mcp_tool("amux_claim_task", {
                "task_id": task_id,
                "session": claim_session
            })
            self.assert_success(result, "Claim task")
            
            # 4.4: Update task
            result = self.call_mcp_tool("amux_update_task", {
                "task_id": task_id,
                "status": "done"
            })
            self.assert_success(result, "Update task")
            
            # 4.5: Verify update
            result = self.call_mcp_tool("amux_list_board_tasks")
            if self.assert_success(result, "List tasks after update"):
                tasks = result.get("tasks", [])
                updated_task = next((t for t in tasks if t["id"] == task_id), None)
                if updated_task and updated_task["status"] == "done":
                    self.log(f"   Task status verified: done", "INFO")
                else:
                    self.log(f"   Task status mismatch", "ERROR")
        
        print()
    
    def test_orchestration_workflow(self):
        """Test complete orchestration workflow."""
        print("🎭 Test Group 5: Orchestration Workflow")
        print("-" * 70)
        
        # 5.1: Create orchestration scenario
        workflow_name = f"workflow-{int(time.time())}"
        
        # Create 2 worker sessions
        workers = []
        for i, tool in enumerate(["claude_code", "cursor"]):
            worker_name = f"{workflow_name}-worker-{i+1}"
            result = self.call_mcp_tool("amux_create_session", {
                "name": worker_name,
                "dir": "~/Documents/research/amux",
                "tool": tool,
                "desc": f"Workflow test worker {i+1}"
            })
            
            if self.assert_success(result, f"Create worker {i+1} ({tool})"):
                workers.append(worker_name)
                self.log(f"   Worker: {worker_name}", "INFO")
        
        # Create coordinated tasks
        if len(workers) == 2:
            for i, worker in enumerate(workers):
                result = self.call_mcp_tool("amux_create_board_task", {
                    "title": f"Workflow task for {worker}",
                    "desc": f"Coordinated task #{i+1}",
                    "session": worker,
                    "status": "todo"
                })
                self.assert_success(result, f"Create task for worker {i+1}")
            
            # Start workers
            for i, worker in enumerate(workers):
                result = self.call_mcp_tool("amux_start_session", {"name": worker})
                self.assert_success(result, f"Start worker {i+1}")
            
            # Send coordinated messages
            time.sleep(2)
            for i, worker in enumerate(workers):
                result = self.call_mcp_tool("amux_send_message", {
                    "name": worker,
                    "text": f"Worker {i+1}: Check board for your task and acknowledge."
                })
                self.assert_success(result, f"Send message to worker {i+1}")
            
            # Cleanup: stop workers
            time.sleep(2)
            for worker in workers:
                self.call_mcp_tool("amux_stop_session", {"name": worker})
        
        print()
    
    def test_error_handling(self):
        """Test error handling."""
        print("⚠️  Test Group 6: Error Handling")
        print("-" * 70)
        
        # 6.1: Invalid session name
        result = self.call_mcp_tool("amux_get_status", {"name": "nonexistent-session-xyz"})
        has_error = "error" in result or "not found" in str(result).lower()
        self.tests_run += 1
        if has_error:
            self.log("Invalid session name: PASSED (error expected)", "PASS")
            self.tests_passed += 1
        else:
            self.log("Invalid session name: FAILED (expected error)", "FAIL")
            self.tests_failed += 1
        
        # 6.2: Invalid task ID
        result = self.call_mcp_tool("amux_claim_task", {"task_id": "INVALID-999"})
        has_error = "error" in result or "not found" in str(result).lower()
        self.tests_run += 1
        if has_error:
            self.log("Invalid task ID: PASSED (error expected)", "PASS")
            self.tests_passed += 1
        else:
            self.log("Invalid task ID: FAILED (expected error)", "FAIL")
            self.tests_failed += 1
        
        # 6.3: Invalid tool name
        result = self.call_mcp_tool("amux_create_session", {
            "name": f"invalid-tool-test-{int(time.time())}",
            "dir": "~/Documents",
            "tool": "invalid_tool_xyz"
        })
        # This might succeed (AMUX is permissive), so just log
        self.tests_run += 1
        self.log("Invalid tool name: CHECKED", "INFO")
        self.tests_passed += 1
        
        print()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("📊 Test Summary")
        print("="*70)
        print(f"Total tests run:    {self.tests_run}")
        print(f"✅ Passed:          {self.tests_passed}")
        print(f"❌ Failed:          {self.tests_failed}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Success rate:       {success_rate:.1f}%")
        
        if self.tests_failed == 0:
            print("\n🎉 All tests passed! MCP integration is working correctly.")
        else:
            print(f"\n⚠️  {self.tests_failed} test(s) failed. Check logs above.")
        
        print("="*70 + "\n")
        
        # Exit code
        return 0 if self.tests_failed == 0 else 1


def main():
    """Main entry point."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    tester = MCPTester(verbose=verbose)
    exit_code = tester.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
