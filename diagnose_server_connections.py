#!/usr/bin/env python3
"""
Diagnostic tool for Jarvis MCP server connections.
Helps identify why servers fail to auto-connect.
"""

import json
import sys
import os
from pathlib import Path
import subprocess

def load_servers():
    """Load saved servers configuration."""
    servers_file = Path(".jarvis_servers.json")
    if not servers_file.exists():
        print("❌ No .jarvis_servers.json file found")
        return {}
    
    with open(servers_file) as f:
        return json.load(f)

def check_server(alias, config):
    """Check if a server configuration is valid."""
    print(f"\n{'='*60}")
    print(f"🔍 Checking server: {alias}")
    print(f"{'='*60}")
    
    command = config.get('command')
    args = config.get('args', [])
    cwd = config.get('cwd')
    
    print(f"Command: {command}")
    print(f"Args: {args}")
    print(f"CWD: {cwd}")
    
    issues = []
    
    # Check if command exists
    if command == 'python':
        # Check if Python is available
        try:
            result = subprocess.run([sys.executable, '--version'], 
                                   capture_output=True, text=True, timeout=5)
            print(f"✅ Python available: {result.stdout.strip()}")
        except Exception as e:
            issues.append(f"❌ Python not accessible: {e}")
    elif command == 'bash':
        # Check if bash is available (unlikely on Windows)
        try:
            result = subprocess.run(['bash', '--version'], 
                                   capture_output=True, text=True, timeout=5)
            print(f"✅ Bash available: {result.stdout.splitlines()[0]}")
        except Exception as e:
            issues.append(f"❌ Bash not accessible (Windows doesn't have bash by default): {e}")
    else:
        # Generic command check
        print(f"⚠️  Command '{command}' - not validated")
    
    # Check if script files exist
    for arg in args:
        if arg.endswith('.py') or arg.endswith('.ts'):
            script_path = Path(arg)
            if script_path.exists():
                print(f"✅ Script file exists: {arg}")
            else:
                issues.append(f"❌ Script file missing: {arg}")
    
    # Check if working directory exists
    if cwd:
        cwd_path = Path(cwd)
        if cwd_path.exists():
            print(f"✅ Working directory exists: {cwd}")
        else:
            issues.append(f"❌ Working directory missing: {cwd}")
    
    # Try to run the server for 2 seconds to see if it starts
    print("\n🧪 Testing server startup...")
    try:
        full_command = [command] + args
        if cwd:
            proc = subprocess.Popen(
                full_command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else:
            proc = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        # Wait 2 seconds
        try:
            stdout, stderr = proc.communicate(timeout=2)
            print(f"❌ Server exited immediately")
            if stdout:
                print(f"STDOUT: {stdout[:500]}")
            if stderr:
                print(f"STDERR: {stderr[:500]}")
            issues.append("Server exits immediately instead of running")
        except subprocess.TimeoutExpired:
            # This is actually good - server is still running
            print("✅ Server appears to start successfully (running after 2s)")
            proc.kill()
            proc.communicate()
    except FileNotFoundError:
        issues.append(f"❌ Command '{command}' not found in system PATH")
    except Exception as e:
        issues.append(f"❌ Error starting server: {e}")
    
    # Summary
    print(f"\n{'─'*60}")
    if issues:
        print(f"❌ {len(issues)} issue(s) found:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("✅ Server configuration looks good!")
        return True

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Jarvis MCP Server Connection Diagnostics                  ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    servers = load_servers()
    
    if not servers:
        print("\n❌ No servers configured")
        return
    
    print(f"\n📋 Found {len(servers)} configured server(s): {', '.join(servers.keys())}")
    
    results = {}
    for alias, config in servers.items():
        results[alias] = check_server(alias, config)
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    working = [alias for alias, ok in results.items() if ok]
    broken = [alias for alias, ok in results.items() if not ok]
    
    if working:
        print(f"✅ Working servers ({len(working)}): {', '.join(working)}")
    
    if broken:
        print(f"❌ Broken servers ({len(broken)}): {', '.join(broken)}")
        print("\n💡 RECOMMENDATIONS:")
        for alias in broken:
            config = servers[alias]
            print(f"\n   {alias}:")
            
            # Check for common issues
            if config.get('command') == 'bash' and sys.platform == 'win32':
                print(f"      - Windows doesn't have bash by default")
                print(f"      - Consider removing this server or fixing the configuration")
            
            for arg in config.get('args', []):
                if '/Users/' in arg:
                    print(f"      - Contains Mac-specific path: {arg}")
                    print(f"      - Update to Windows path or remove this server")
            
            cwd = config.get('cwd', '')
            if cwd and not Path(cwd).exists():
                print(f"      - Working directory doesn't exist: {cwd}")
                print(f"      - Create the directory or update the path")
    
    print("\n" + "="*60)
    print("🔧 TO FIX ISSUES:")
    print("="*60)
    print("1. Remove broken servers:")
    print("   - Edit .jarvis_servers.json and remove entries")
    print("   - Or use the client CLI to disconnect with --forget")
    print()
    print("2. Fix server paths:")
    print("   - Update paths in .jarvis_servers.json to match your system")
    print()
    print("3. Reconnect servers:")
    print("   - Use the client CLI to connect servers with correct paths")
    print("   - python -m client.cli")

if __name__ == "__main__":
    main()

