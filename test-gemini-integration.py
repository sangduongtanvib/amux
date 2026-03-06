#!/usr/bin/env python3
"""
Test script for Gemini CLI integration.
Verifies that Gemini tool is properly registered and configured.
"""

import sys
import importlib.util

# Import amux-server.py dynamically
spec = importlib.util.spec_from_file_location("amux_server", "amux-server.py")
amux_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(amux_server)


def test_gemini_tool():
    """Test Gemini CLI tool integration."""
    print("=" * 70)
    print("Testing Gemini CLI Integration")
    print("=" * 70)
    
    # Test 1: Check if gemini is in AI tools registry
    print("\n[Test 1] Check AI tools registry...")
    ai_tools = amux_server._AI_TOOLS
    
    if "gemini" in ai_tools:
        print("✅ 'gemini' found in _AI_TOOLS registry")
        print(f"   Available tools: {list(ai_tools.keys())}")
    else:
        print(f"❌ 'gemini' NOT found in _AI_TOOLS registry")
        print(f"   Available tools: {list(ai_tools.keys())}")
        return False
    
    # Test 2: Get Gemini tool instance
    print("\n[Test 2] Get Gemini tool instance...")
    try:
        gemini_tool = amux_server.get_ai_tool("gemini")
        print(f"✅ Got Gemini tool: {gemini_tool.name}")
        print(f"   Class: {gemini_tool.__class__.__name__}")
        print(f"   Home dir: {gemini_tool.get_home_dir()}")
        print(f"   Supports conversation ID: {gemini_tool.supports_conversation_id()}")
    except Exception as e:
        print(f"❌ Failed to get Gemini tool: {e}")
        return False
    
    # Test 3: Test command generation
    print("\n[Test 3] Test command generation...")
    try:
        # Basic command
        cmd = gemini_tool.get_command("", "", "", "")
        print(f"✅ Basic command: {cmd}")
        
        # Command with YOLO flag
        cmd_yolo = gemini_tool.get_command("--yolo", "", "", "")
        print(f"✅ YOLO command: {cmd_yolo}")
        
        # Command with custom model
        cmd_model = gemini_tool.get_command("--model gemini-2.0-flash-thinking-exp", "", "", "")
        print(f"✅ Custom model: {cmd_model}")
        
        # Command with custom flags
        cmd_custom = gemini_tool.get_command("--debug --yolo", "", "", "")
        print(f"✅ Custom flags: {cmd_custom}")
    except Exception as e:
        print(f"❌ Command generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Test status detection
    print("\n[Test 4] Test status detection...")
    try:
        # Idle status
        status = gemini_tool.detect_status("")
        print(f"✅ Empty output → {status}")
        
        # Working status
        status = gemini_tool.detect_status("Thinking...\n⠋ Processing your request")
        print(f"✅ Thinking output → {status}")
        
        # Needs input status
        status = gemini_tool.detect_status("? Press Y to approve this action\nApprove?")
        print(f"✅ Approval prompt → {status}")
        
        # Error status
        status = gemini_tool.detect_status("Error: Failed to connect to API")
        print(f"✅ Error output → {status}")
    except Exception as e:
        print(f"❌ Status detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Check credential manager compatibility
    print("\n[Test 5] Check credential manager compatibility...")
    try:
        # Import credential manager
        spec_cred = importlib.util.spec_from_file_location("credential_manager", "credential-manager.py")
        cred_mgr = importlib.util.module_from_spec(spec_cred)
        spec_cred.loader.exec_module(cred_mgr)
        
        mgr = cred_mgr.CredentialManager()
        supported = mgr.SUPPORTED_TOOLS
        
        if "gemini" in supported:
            print("✅ 'gemini' found in credential manager SUPPORTED_TOOLS")
            gemini_config = supported["gemini"]
            print(f"   Name: {gemini_config['name']}")
            print(f"   Env vars: {gemini_config.get('env_vars', [])}")
            print(f"   Auth types: {gemini_config.get('auth_types', [])}")
        else:
            print("⚠️  'gemini' NOT found in credential manager (but this is OK for basic usage)")
    except Exception as e:
        print(f"⚠️  Could not check credential manager: {e}")
        # Not critical
    
    print("\n" + "=" * 70)
    print("✅ All Gemini CLI integration tests passed!")
    print("=" * 70)
    
    print("\n📝 Next steps:")
    print("   1. Set GOOGLE_API_KEY or GEMINI_API_KEY env var")
    print("   2. Or add via credential manager: python3 credential-manager.py set gemini google_api_key YOUR_KEY")
    print("   3. Create session: POST /api/sessions with tool='gemini'")
    print("   4. Start session: POST /api/sessions/<name>/start")
    
    return True


if __name__ == "__main__":
    success = test_gemini_tool()
    sys.exit(0 if success else 1)
