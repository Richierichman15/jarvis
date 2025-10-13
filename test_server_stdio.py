#!/usr/bin/env python3
"""Test MCP server stdio communication."""

import asyncio
import sys
import subprocess
import json

async def test_server(script_path, cwd=None):
    """Test if an MCP server can be initialized."""
    print(f"\n{'='*60}")
    print(f"Testing: {script_path}")
    print(f"CWD: {cwd or 'current'}")
    print(f"{'='*60}")
    
    try:
        # Start the server process
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            script_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        # Send an initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        request_str = json.dumps(init_request) + "\n"
        print(f"Sending: {request_str[:100]}...")
        
        proc.stdin.write(request_str.encode())
        await proc.stdin.drain()
        
        # Wait for response (with timeout)
        try:
            response_bytes = await asyncio.wait_for(
                proc.stdout.readline(),
                timeout=5.0
            )
            
            if response_bytes:
                response_str = response_bytes.decode().strip()
                print(f"✅ Got response: {response_str[:200]}...")
                
                # Try to parse as JSON
                try:
                    response_json = json.loads(response_str)
                    if "result" in response_json:
                        print(f"✅ Server initialized successfully!")
                        print(f"   Server capabilities: {response_json.get('result', {}).get('capabilities', {})}")
                        return True
                    elif "error" in response_json:
                        print(f"❌ Server returned error: {response_json['error']}")
                        return False
                except json.JSONDecodeError as e:
                    print(f"⚠️  Response is not valid JSON: {e}")
                    return False
            else:
                print("❌ No response received (empty)")
                return False
                
        except asyncio.TimeoutError:
            print("❌ Timeout waiting for response")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Check if process is still running
        if proc.returncode is None:
            print("✅ Server process is still running")
            proc.kill()
            await proc.wait()
        else:
            print(f"❌ Server process exited with code: {proc.returncode}")
            
        # Get stderr output
        try:
            stderr = await asyncio.wait_for(proc.stderr.read(), timeout=1.0)
            if stderr:
                stderr_str = stderr.decode().strip()
                if stderr_str:
                    print(f"STDERR output:\n{stderr_str[:500]}")
        except:
            pass

async def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  MCP Server STDIO Communication Test                       ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    servers_to_test = [
        ("E:/Richie/github/system/system_server.py", "E:/Richie/github/system"),
        ("E:/Richie/github/finance/trading_mcp_server.py", "E:/Richie/github/finance"),
        ("E:/Richie/github/jarvis/search/mcp_server.py", "E:/Richie/github/jarvis"),
    ]
    
    results = {}
    for script_path, cwd in servers_to_test:
        name = script_path.split('/')[-1].replace('_server.py', '').replace('_mcp_server.py', '').replace('.py', '')
        results[name] = await test_server(script_path, cwd)
        await asyncio.sleep(0.5)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

if __name__ == "__main__":
    asyncio.run(main())

