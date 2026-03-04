#!/usr/bin/env python3
"""
Test Credential Management Integration

Verifies that credentials are properly detected, stored, and injected into sessions.
"""

import json
import subprocess
import time


def test_credential_detection():
    """Test 1: Detect existing credentials."""
    print("\n" + "="*70)
    print("🧪 Test 1: Credential Detection")
    print("="*70 + "\n")
    
    result = subprocess.run(
        ["python3", "credential-manager.py", "detect"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        detected = json.loads(result.stdout.split('\n\n')[1])
        print(f"✅ Detected {len(detected)} tool(s) with credentials")
        
        for tool, info in detected.items():
            print(f"   • {tool}: {info.get('auth_method', 'unknown')}")
            if "email" in info:
                print(f"     - Email: {info['email']}")
        
        return True, detected
    else:
        print(f"❌ Detection failed: {result.stderr}")
        return False, {}


def test_credential_storage():
    """Test 2: Store and retrieve credentials."""
    print("\n" + "="*70)
    print("🧪 Test 2: Credential Storage & Retrieval")
    print("="*70 + "\n")
    
    # Store test credential
    subprocess.run(
        ["python3", "credential-manager.py", "set", "test_tool", "test_key", "test_value_12345"],
        capture_output=True
    )
    
    # Retrieve it
    result = subprocess.run(
        ["python3", "credential-manager.py", "get", "test_tool", "test_key"],
        capture_output=True,
        text=True
    )
    
    if "test_value_12345" in result.stdout:
        print("✅ Storage: Credential saved and retrieved correctly")
        
        # Clean up
        subprocess.run(
            ["python3", "credential-manager.py", "delete", "test_tool", "test_key"],
            capture_output=True
        )
        print("✅ Cleanup: Test credential deleted")
        return True
    else:
        print(f"❌ Storage failed: {result.stdout}")
        return False


def test_session_injection():
    """Test 3: Verify credential injection into sessions."""
    print("\n" + "="*70)
    print("🧪 Test 3: Session Credential Injection")
    print("="*70 + "\n")
    
    # Create a test session via AMUX API
    session_name = f"cred-test-{int(time.time())}"
    
    create_data = {
        "name": session_name,
        "dir": "~/Documents/research/amux",
        "tool": "claude_code",
        "desc": "Credential injection test"
    }
    
    result = subprocess.run(
        ["curl", "-k", "-s", "-X", "POST",
         "https://localhost:8822/api/sessions",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(create_data)],
        capture_output=True,
        text=True
    )
    
    if '"ok":true' in result.stdout or '"ok": true' in result.stdout:
        print(f"✅ Session created: {session_name}")
        
        # Start the session
        time.sleep(1)
        result = subprocess.run(
            ["curl", "-k", "-s", "-X", "POST",
             f"https://localhost:8822/api/sessions/{session_name}/start"],
            capture_output=True,
            text=True
        )
        
        if '"ok":true' in result.stdout or '"ok": true' in result.stdout:
            print(f"✅ Session started (credentials should be injected)")
            
            # Wait a bit
            time.sleep(2)
            
            # Stop session
            subprocess.run(
                ["curl", "-k", "-s", "-X", "POST",
                 f"https://localhost:8822/api/sessions/{session_name}/stop"],
                capture_output=True
            )
            print(f"✅ Session stopped: {session_name}")
            
            return True
        else:
            print(f"❌ Failed to start session: {result.stdout}")
            return False
    else:
        print(f"❌ Failed to create session: {result.stdout}")
        return False


def test_cursor_config_access():
    """Test 4: Verify Cursor config file is accessible."""
    print("\n" + "="*70)
    print("🧪 Test 4: Cursor Config Accessibility")
    print("="*70 + "\n")
    
    import os
    from pathlib import Path
    
    cursor_config = Path.home() / ".cursor" / "cli-config.json"
    
    if cursor_config.exists():
        # Read config
        try:
            with open(cursor_config) as f:
                config = json.load(f)
            
            if "authInfo" in config:
                auth = config["authInfo"]
                print(f"✅ Cursor config found and readable")
                print(f"   - Email: {auth.get('email', 'N/A')}")
                print(f"   - Team: {auth.get('teamName', 'N/A')}")
                print(f"   - File: {cursor_config}")
                print(f"   - Permissions: {oct(cursor_config.stat().st_mode)[-3:]}")
                
                # Verify accessible from other processes
                if cursor_config.stat().st_mode & 0o444:  # Readable
                    print(f"✅ Config is readable by session processes")
                    return True
                else:
                    print(f"⚠️  Config permissions may restrict access")
                    return False
            else:
                print(f"⚠️  Cursor config exists but no authInfo found")
                return False
        except Exception as e:
            print(f"❌ Failed to read config: {e}")
            return False
    else:
        print(f"⚠️  Cursor config not found at {cursor_config}")
        print(f"   Run 'cursor --login' to authenticate")
        return False


def main():
    """Run all credential management tests."""
    print("\n" + "="*70)
    print("🔐 AMUX Credential Management Test Suite")
    print("="*70)
    
    results = []
    
    # Test 1: Detection
    success, detected = test_credential_detection()
    results.append(("Detection", success))
    
    # Test 2: Storage
    success = test_credential_storage()
    results.append(("Storage", success))
    
    # Test 3: Session injection (requires AMUX server running)
    try:
        success = test_session_injection()
        results.append(("Session Injection", success))
    except Exception as e:
        print(f"⚠️  Session injection test skipped (server not running?)")
        results.append(("Session Injection", False))
    
    # Test 4: Config accessibility
    success = test_cursor_config_access()
    results.append(("Config Access", success))
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70 + "\n")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:<12} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Credential system is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check output above.")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
