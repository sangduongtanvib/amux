#!/usr/bin/env python3
"""
Test script for Cursor session isolation.
Tests prepare_cursor_session() and cleanup_cursor_session() methods.
"""

import sys
from pathlib import Path
import importlib.util

# Import credential-manager.py dynamically (has hyphen in name)
spec = importlib.util.spec_from_file_location("credential_manager", "credential-manager.py")
credential_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(credential_manager)
CredentialManager = credential_manager.CredentialManager

def test_cursor_isolation():
    """Test Cursor session isolation end-to-end."""
    print("=" * 70)
    print("Testing Cursor Session Isolation")
    print("=" * 70)
    
    manager = CredentialManager()
    session_name = "test-session-cursor-isolation"
    
    # Test 1: Prepare session
    print("\n[Test 1] Preparing Cursor session...")
    try:
        env_vars = manager.prepare_cursor_session(session_name)
        print(f"✅ Session prepared")
        print(f"   Environment variables:")
        for key, value in env_vars.items():
            print(f"     {key} = {value}")
        
        # Verify isolated home was created
        isolated_home = Path(env_vars["HOME"])
        cursor_config = isolated_home / ".cursor" / "cli-config.json"
        
        if isolated_home.exists():
            print(f"✅ Isolated home created: {isolated_home}")
        else:
            print(f"❌ Isolated home NOT created: {isolated_home}")
            return False
        
        if cursor_config.exists():
            print(f"✅ Cursor config copied: {cursor_config}")
        else:
            print(f"❌ Cursor config NOT copied: {cursor_config}")
            return False
        
    except Exception as e:
        print(f"❌ Failed to prepare session: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Cleanup session
    print("\n[Test 2] Cleaning up Cursor session...")
    try:
        success = manager.cleanup_cursor_session(session_name)
        if success:
            print(f"✅ Session cleaned up")
        else:
            print(f"⚠️  Nothing to clean (already clean)")
        
        # Verify isolated home was removed
        if not isolated_home.exists():
            print(f"✅ Isolated home removed: {isolated_home}")
        else:
            print(f"❌ Isolated home still exists: {isolated_home}")
            return False
        
    except Exception as e:
        print(f"❌ Failed to cleanup session: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_cursor_isolation()
    sys.exit(0 if success else 1)
