#!/usr/bin/env python3
"""
AMUX Credential Manager

Centralized credential storage and management for AI tools.
Stores API keys, OAuth tokens, and config files securely.

Features:
- Encrypted credential storage
- Per-tool credential management
- Automatic injection into sessions
- Config file sharing (cursor, claude)
- Environment variable management

Storage location: ~/.amux/credentials/
"""

import json
import os
import base64
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialManager:
    """Manages credentials for AI tools."""
    
    AMUX_DIR = Path.home() / ".amux"
    CREDS_DIR = AMUX_DIR / "credentials"
    CREDS_FILE = CREDS_DIR / "credentials.enc"
    KEY_FILE = CREDS_DIR / ".key"
    
    SUPPORTED_TOOLS = {
        "claude_code": {
            "name": "Claude Code",
            "auth_types": ["anthropic_api_key", "session_token"],
            "config_files": ["~/.claude/"],
            "env_vars": ["ANTHROPIC_API_KEY", "CLAUDE_CODE_SSE_PORT"]
        },
        "cursor": {
            "name": "Cursor",
            "auth_types": ["oauth", "session"],
            "config_files": ["~/.cursor/cli-config.json"],
            "env_vars": []
        },
        "gemini": {
            "name": "Gemini CLI",
            "auth_types": ["google_api_key"],
            "config_files": [],
            "env_vars": ["GOOGLE_API_KEY", "GEMINI_API_KEY"]
        },
        "aider": {
            "name": "Aider",
            "auth_types": ["openai_api_key", "anthropic_api_key"],
            "config_files": ["~/.aider.conf.yml"],
            "env_vars": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        }
    }
    
    def __init__(self):
        """Initialize credential manager."""
        self.CREDS_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_encryption_key()
    
    def _ensure_encryption_key(self):
        """Ensure encryption key exists."""
        if not self.KEY_FILE.exists():
            # Generate a key from machine-specific data
            machine_id = self._get_machine_id()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"amux_credential_salt",
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            self.KEY_FILE.write_bytes(key)
            self.KEY_FILE.chmod(0o600)  # Owner read/write only
    
    def _get_machine_id(self) -> str:
        """Get machine-specific identifier."""
        import platform
        import uuid
        
        # Use hostname + architecture as machine ID
        machine_data = f"{platform.node()}-{platform.machine()}"
        
        # Try to get MAC address for better uniqueness
        try:
            mac = uuid.getnode()
            machine_data += f"-{mac}"
        except:
            pass
        
        return machine_data
    
    def _get_cipher(self) -> Fernet:
        """Get encryption cipher."""
        key = self.KEY_FILE.read_bytes()
        return Fernet(key)
    
    def _load_credentials(self) -> Dict[str, Any]:
        """Load encrypted credentials."""
        if not self.CREDS_FILE.exists():
            return {}
        
        try:
            cipher = self._get_cipher()
            encrypted_data = self.CREDS_FILE.read_bytes()
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Warning: Could not decrypt credentials: {e}")
            return {}
    
    def _save_credentials(self, creds: Dict[str, Any]):
        """Save encrypted credentials."""
        cipher = self._get_cipher()
        json_data = json.dumps(creds, indent=2).encode()
        encrypted_data = cipher.encrypt(json_data)
        self.CREDS_FILE.write_bytes(encrypted_data)
        self.CREDS_FILE.chmod(0o600)  # Owner read/write only
    
    def set_credential(self, tool: str, cred_type: str, value: str, account_id: str = "default"):
        """
        Set a credential for a tool.
        
        Args:
            tool: Tool name (e.g., "claude_code", "cursor")
            cred_type: Credential type (e.g., "api_key", "oauth_token")
            value: Credential value
            account_id: Account identifier for multi-account support
        """
        creds = self._load_credentials()
        
        if tool not in creds:
            creds[tool] = {"accounts": {}, "load_balancer": {"enabled": False, "strategy": "round_robin"}}
        
        if "accounts" not in creds[tool]:
            creds[tool]["accounts"] = {}
        
        if account_id not in creds[tool]["accounts"]:
            creds[tool]["accounts"][account_id] = {
                "credentials": {},
                "metadata": {
                    "created": int(time.time()),
                    "name": account_id,
                    "enabled": True,
                    "usage_count": 0,
                    "last_used": None
                }
            }
        
        creds[tool]["accounts"][account_id]["credentials"][cred_type] = value
        creds[tool]["accounts"][account_id]["metadata"]["updated"] = int(time.time())
        
        self._save_credentials(creds)
        
        print(f"✅ Credential '{cred_type}' saved for {tool} (account: {account_id})")
    
    def get_credential(self, tool: str, cred_type: str, account_id: str = "default") -> Optional[str]:
        """Get a credential for a tool."""
        creds = self._load_credentials()
        tool_creds = creds.get(tool, {})
        if "accounts" in tool_creds:
            return tool_creds["accounts"].get(account_id, {}).get("credentials", {}).get(cred_type)
        # Legacy format support
        return tool_creds.get(cred_type)
    
    def list_accounts(self, tool: str) -> List[Dict[str, Any]]:
        """List all accounts for a tool."""
        creds = self._load_credentials()
        tool_creds = creds.get(tool, {})
        
        if "accounts" not in tool_creds:
            return []
        
        accounts = []
        for account_id, account_data in tool_creds["accounts"].items():
            metadata = account_data.get("metadata", {})
            accounts.append({
                "id": account_id,
                "name": metadata.get("name", account_id),
                "enabled": metadata.get("enabled", True),
                "usage_count": metadata.get("usage_count", 0),
                "last_used": metadata.get("last_used"),
                "created": metadata.get("created"),
                "has_credentials": len(account_data.get("credentials", {})) > 0
            })
        
        return accounts
    
    def delete_account(self, tool: str, account_id: str):
        """Delete an account."""
        creds = self._load_credentials()
        
        if tool in creds and "accounts" in creds[tool]:
            if account_id in creds[tool]["accounts"]:
                del creds[tool]["accounts"][account_id]
                self._save_credentials(creds)
                print(f"✅ Account '{account_id}' deleted from {tool}")
                return True
        
        return False
    
    def set_load_balancing(self, tool: str, enabled: bool, strategy: str = "round_robin"):
        """Enable/disable load balancing for a tool."""
        creds = self._load_credentials()
        
        if tool not in creds:
            creds[tool] = {"accounts": {}, "load_balancer": {}}
        
        if "load_balancer" not in creds[tool]:
            creds[tool]["load_balancer"] = {}
        
        creds[tool]["load_balancer"]["enabled"] = enabled
        creds[tool]["load_balancer"]["strategy"] = strategy
        creds[tool]["load_balancer"]["current_index"] = 0
        
        self._save_credentials(creds)
        print(f"✅ Load balancing {'enabled' if enabled else 'disabled'} for {tool} (strategy: {strategy})")
    
    def get_next_account(self, tool: str) -> Optional[Dict[str, Any]]:
        """
        Get next account to use (load balancing).
        
        Returns account with credentials and increments usage.
        """
        creds = self._load_credentials()
        tool_creds = creds.get(tool, {})
        
        if "accounts" not in tool_creds or not tool_creds["accounts"]:
            return None
        
        load_balancer = tool_creds.get("load_balancer", {})
        enabled_accounts = [
            (aid, acc) for aid, acc in tool_creds["accounts"].items()
            if acc.get("metadata", {}).get("enabled", True)
        ]
        
        if not enabled_accounts:
            return None
        
        # Load balancing strategies
        if load_balancer.get("enabled", False):
            strategy = load_balancer.get("strategy", "round_robin")
            
            if strategy == "round_robin":
                current_idx = load_balancer.get("current_index", 0)
                account_id, account_data = enabled_accounts[current_idx % len(enabled_accounts)]
                # Update index for next call
                creds[tool]["load_balancer"]["current_index"] = (current_idx + 1) % len(enabled_accounts)
            
            elif strategy == "least_used":
                # Sort by usage_count
                enabled_accounts.sort(key=lambda x: x[1].get("metadata", {}).get("usage_count", 0))
                account_id, account_data = enabled_accounts[0]
            
            else:  # random
                import random
                account_id, account_data = random.choice(enabled_accounts)
        else:
            # No load balancing - use first enabled account (or "default")
            if "default" in tool_creds["accounts"] and tool_creds["accounts"]["default"]["metadata"]["enabled"]:
                account_id = "default"
                account_data = tool_creds["accounts"]["default"]
            else:
                account_id, account_data = enabled_accounts[0]
        
        # Update usage statistics
        metadata = account_data.get("metadata", {})
        metadata["usage_count"] = metadata.get("usage_count", 0) + 1
        metadata["last_used"] = int(time.time())
        
        self._save_credentials(creds)
        
        return {
            "id": account_id,
            "credentials": account_data.get("credentials", {}),
            "metadata": metadata
        }
    
    def delete_credential(self, tool: str, cred_type: str, account_id: str = "default"):
        """Delete a specific credential type from an account (deprecated - use delete_account instead)."""
        creds = self._load_credentials()
        
        if tool in creds:
            tool_data = creds[tool]
            if "accounts" in tool_data and account_id in tool_data["accounts"]:
                account = tool_data["accounts"][account_id]
                if cred_type in account.get("credentials", {}):
                    del account["credentials"][cred_type]
                    if not account["credentials"]:  # Remove account if no creds left
                        del tool_data["accounts"][account_id]
                    if not tool_data["accounts"]:  # Remove tool if no accounts left
                        del creds[tool]
                    self._save_credentials(creds)
                    print(f"✅ Credential '{cred_type}' deleted for {tool}.{account_id}")
                    return
        
        print(f"❌ Credential not found: {tool}.{account_id}.{cred_type}")
    
    def list_credentials(self) -> Dict[str, Dict]:
        """
        List all stored credentials with account information.
        
        Returns:
            {
                "tool_name": {
                    "accounts": ["account_id1", "account_id2"],
                    "load_balancing": {"enabled": bool, "strategy": str}
                }
            }
        """
        creds = self._load_credentials()
        result = {}
        
        for tool, tool_data in creds.items():
            if "accounts" in tool_data:
                result[tool] = {
                    "accounts": list(tool_data["accounts"].keys()),
                    "load_balancing": tool_data.get("load_balancer", {
                        "enabled": False,
                        "strategy": "round_robin"
                    })
                }
        
        return result
    
    def get_env_vars(self, tool: str, account_id: Optional[str] = None) -> Dict[str, str]:
        """
        Get environment variables for a tool using load balancing.
        
        Args:
            tool: Tool name
            account_id: Optional specific account ID. If None, uses load balancing
            
        Returns a dict of env var name -> value to inject into session.
        """
        # Get account (either specific or via load balancing)
        if account_id:
            account_data = self.get_credential(tool, account_id=account_id)
            if not account_data:
                print(f"⚠️  Account {account_id} not found for {tool}, using load balancing")
                account_data = self.get_next_account(tool)
        else:
            account_data = self.get_next_account(tool)
        
        if not account_data:
            return {}
        
        tool_creds = account_data.get("credentials", {})
        env_vars = {}
        
        # Map credentials to environment variables
        if tool == "claude_code":
            if "anthropic_api_key" in tool_creds:
                env_vars["ANTHROPIC_API_KEY"] = tool_creds["anthropic_api_key"]
        
        elif tool == "cursor":
            # Cursor uses config file, not env vars
            pass
        
        elif tool == "gemini":
            if "google_api_key" in tool_creds:
                env_vars["GOOGLE_API_KEY"] = tool_creds["google_api_key"]
                env_vars["GEMINI_API_KEY"] = tool_creds["google_api_key"]
        
        elif tool == "aider":
            if "openai_api_key" in tool_creds:
                env_vars["OPENAI_API_KEY"] = tool_creds["openai_api_key"]
            if "anthropic_api_key" in tool_creds:
                env_vars["ANTHROPIC_API_KEY"] = tool_creds["anthropic_api_key"]
        
        return env_vars
    
    def ensure_config_shared(self, tool: str) -> bool:
        """
        Ensure config files are accessible to all sessions.
        
        For tools that use config files (cursor, claude), this ensures
        the config is shared across all AMUX sessions.
        
        Returns: True if successful
        """
        if tool == "cursor":
            config_path = Path.home() / ".cursor" / "cli-config.json"
            if config_path.exists():
                # Config already in home dir, accessible to all sessions
                return True
            else:
                print(f"⚠️  Cursor config not found at {config_path}")
                print("    Please login to Cursor first: cursor --login")
                return False
        
        elif tool == "claude_code":
            claude_dir = Path.home() / ".claude"
            if claude_dir.exists():
                # Claude config in home dir, accessible to all sessions
                return True
            else:
                print(f"⚠️  Claude Code not initialized at {claude_dir}")
                print("    Please run Claude Code first to initialize")
                return False
        
        return True
    
    def detect_existing_credentials(self) -> Dict[str, Dict[str, Any]]:
        """
        Auto-detect existing credentials from config files.
        
        Returns: Dict of tool -> detected credentials info
        """
        detected = {}
        
        # Check Cursor
        cursor_config = Path.home() / ".cursor" / "cli-config.json"
        if cursor_config.exists():
            try:
                config = json.loads(cursor_config.read_text())
                if "authInfo" in config:
                    detected["cursor"] = {
                        "found": True,
                        "auth_method": "config_file",
                        "email": config["authInfo"].get("email", ""),
                        "team": config["authInfo"].get("teamName", ""),
                        "file": str(cursor_config)
                    }
            except:
                pass
        
        # Check Claude Code
        claude_dir = Path.home() / ".claude"
        if claude_dir.exists():
            detected["claude_code"] = {
                "found": True,
                "auth_method": "session",
                "directory": str(claude_dir)
            }
        
        # Check for API keys in environment
        for tool, config in self.SUPPORTED_TOOLS.items():
            for env_var in config.get("env_vars", []):
                if os.environ.get(env_var):
                    if tool not in detected:
                        detected[tool] = {"found": True, "auth_method": "env_var"}
                    detected[tool][env_var] = "***" + os.environ[env_var][-4:]
        
        return detected
    
    def import_from_env(self, tool: str):
        """Import credentials from environment variables."""
        imported = []
        
        for env_var in self.SUPPORTED_TOOLS.get(tool, {}).get("env_vars", []):
            value = os.environ.get(env_var)
            if value:
                # Store with normalized key name
                cred_type = env_var.lower().replace("_", "_")
                self.set_credential(tool, cred_type, value)
                imported.append(env_var)
        
        if imported:
            print(f"✅ Imported from environment: {', '.join(imported)}")
        else:
            print(f"ℹ️  No environment variables found for {tool}")
    
    def print_status(self):
        """Print credential status for all tools."""
        print("\n" + "="*70)
        print("🔐 AMUX Credential Manager Status")
        print("="*70 + "\n")
        
        stored = self.list_credentials()
        detected = self.detect_existing_credentials()
        
        for tool, config in self.SUPPORTED_TOOLS.items():
            print(f"📦 {config['name']} ({tool})")
            print("-" * 70)
            
            # Show stored credentials
            if tool in stored and stored[tool]:
                print(f"   ✅ Stored: {', '.join(stored[tool])}")
            else:
                print(f"   ⚠️  No credentials stored")
            
            # Show detected credentials
            if tool in detected:
                det = detected[tool]
                print(f"   🔍 Detected: {det.get('auth_method', 'unknown')}")
                if "email" in det:
                    print(f"      Email: {det['email']}")
                if "team" in det:
                    print(f"      Team: {det['team']}")
                if "file" in det:
                    print(f"      Config: {det['file']}")
            
            # Show supported auth types
            auth_types = config.get("auth_types", [])
            if auth_types:
                print(f"   💡 Supported: {', '.join(auth_types)}")
            
            print()


def main():
    """CLI for credential management."""
    import sys
    
    manager = CredentialManager()
    
    if len(sys.argv) < 2:
        manager.print_status()
        print("\nUsage:")
        print("  python3 credential-manager.py status")
        print("  python3 credential-manager.py set <tool> <type> <value>")
        print("  python3 credential-manager.py get <tool> <type>")
        print("  python3 credential-manager.py delete <tool> <type>")
        print("  python3 credential-manager.py import <tool>")
        print("  python3 credential-manager.py detect")
        print("\nExamples:")
        print("  python3 credential-manager.py set claude_code anthropic_api_key sk-xxx")
        print("  python3 credential-manager.py set gemini google_api_key AIza...")
        print("  python3 credential-manager.py import aider")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        manager.print_status()
    
    elif command == "set":
        if len(sys.argv) < 5:
            print("Usage: set <tool> <type> <value>")
            return
        tool, cred_type, value = sys.argv[2], sys.argv[3], sys.argv[4]
        manager.set_credential(tool, cred_type, value)
    
    elif command == "get":
        if len(sys.argv) < 4:
            print("Usage: get <tool> <type>")
            return
        tool, cred_type = sys.argv[2], sys.argv[3]
        value = manager.get_credential(tool, cred_type)
        if value:
            print(f"{tool}.{cred_type} = {value}")
        else:
            print(f"❌ Not found: {tool}.{cred_type}")
    
    elif command == "delete":
        if len(sys.argv) < 4:
            print("Usage: delete <tool> <type>")
            return
        tool, cred_type = sys.argv[2], sys.argv[3]
        manager.delete_credential(tool, cred_type)
    
    elif command == "import":
        if len(sys.argv) < 3:
            print("Usage: import <tool>")
            return
        tool = sys.argv[2]
        manager.import_from_env(tool)
    
    elif command == "detect":
        detected = manager.detect_existing_credentials()
        print("\n🔍 Detected Credentials:\n")
        print(json.dumps(detected, indent=2))
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
