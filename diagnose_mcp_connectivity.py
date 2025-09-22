#!/usr/bin/env python3
"""
MCP Connectivity Diagnostic Tool
This script helps diagnose why an external MCP server can't connect to Jarvis.
"""
import requests
import socket
import subprocess
import sys
import json
from datetime import datetime


def test_port_binding():
    """Test if the server is properly bound to all interfaces."""
    print("🔍 Testing Port Binding...")
    
    try:
        # Check netstat output
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        port_3010_lines = [line for line in lines if ':3010' in line and 'LISTEN' in line]
        
        if port_3010_lines:
            print("✅ Port 3010 is listening:")
            for line in port_3010_lines:
                print(f"   {line.strip()}")
                
            # Check if it's bound to all interfaces
            all_interfaces = any('*.3010' in line or '0.0.0.0:3010' in line for line in port_3010_lines)
            if all_interfaces:
                print("✅ Server is bound to all interfaces (0.0.0.0:3010)")
                return True
            else:
                print("❌ Server is NOT bound to all interfaces")
                return False
        else:
            print("❌ Port 3010 is not listening")
            return False
            
    except Exception as e:
        print(f"❌ Error checking port binding: {e}")
        return False


def test_local_connectivity():
    """Test local connectivity to the server."""
    print("\n🔍 Testing Local Connectivity...")
    
    test_urls = [
        "http://localhost:3010",
        "http://127.0.0.1:3010",
        "http://0.0.0.0:3010"
    ]
    
    results = {}
    
    for url in test_urls:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {url} - Status: {response.status_code}")
                results[url] = True
            else:
                print(f"❌ {url} - Status: {response.status_code}")
                results[url] = False
        except Exception as e:
            print(f"❌ {url} - Error: {e}")
            results[url] = False
    
    return any(results.values())


def test_network_interface():
    """Test connectivity via network interface."""
    print("\n🔍 Testing Network Interface...")
    
    try:
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        print(f"📍 Local IP: {local_ip}")
        
        # Test connectivity via local IP
        url = f"http://{local_ip}:3010"
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {url} - Status: {response.status_code}")
                return True
            else:
                print(f"❌ {url} - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ {url} - Error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting local IP: {e}")
        return False


def test_cors_headers():
    """Test CORS headers."""
    print("\n🔍 Testing CORS Headers...")
    
    try:
        response = requests.get("http://localhost:3010/health")
        headers = response.headers
        
        cors_headers = {
            'Access-Control-Allow-Origin': headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': headers.get('Access-Control-Allow-Headers')
        }
        
        print("CORS Headers:")
        for header, value in cors_headers.items():
            if value:
                print(f"✅ {header}: {value}")
            else:
                print(f"❌ {header}: Missing")
        
        return cors_headers['Access-Control-Allow-Origin'] == '*'
        
    except Exception as e:
        print(f"❌ Error testing CORS: {e}")
        return False


def test_mcp_endpoints():
    """Test MCP-specific endpoints."""
    print("\n🔍 Testing MCP Endpoints...")
    
    endpoints = [
        ("/health", "GET"),
        ("/status", "GET"),
        ("/help", "GET"),
        ("/mcp/tools", "GET"),
        ("/mcp/status", "GET")
    ]
    
    results = {}
    
    for endpoint, method in endpoints:
        try:
            url = f"http://localhost:3010{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {method} {endpoint} - Status: {response.status_code}")
                results[endpoint] = True
            else:
                print(f"❌ {method} {endpoint} - Status: {response.status_code}")
                results[endpoint] = False
                
        except Exception as e:
            print(f"❌ {method} {endpoint} - Error: {e}")
            results[endpoint] = False
    
    return all(results.values())


def test_tool_calling():
    """Test MCP tool calling."""
    print("\n🔍 Testing MCP Tool Calling...")
    
    try:
        url = "http://localhost:3010/mcp/tools/call"
        data = {
            "name": "jarvis_get_status",
            "arguments": {}
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Tool call successful - Status: {response.status_code}")
            print(f"   Response: {result.get('result', {}).get('status', 'No status')[:100]}...")
            return True
        else:
            print(f"❌ Tool call failed - Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing tool calling: {e}")
        return False


def generate_mcp_config():
    """Generate MCP server configuration suggestions."""
    print("\n🔧 MCP Server Configuration Suggestions...")
    
    try:
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        configs = {
            "localhost": "http://localhost:3010",
            "loopback": "http://127.0.0.1:3010",
            "network_ip": f"http://{local_ip}:3010"
        }
        
        print("Try these URLs in your MCP server configuration:")
        for name, url in configs.items():
            print(f"   {name}: {url}")
        
        print("\nExample MCP server configuration:")
        print(f"""
{{
  "mcpServers": {{
    "jarvis": {{
      "url": "http://localhost:3010",
      "endpoints": {{
        "health": "/health",
        "tools": "/mcp/tools",
        "call": "/mcp/tools/call"
      }}
    }}
  }}
}}
        """)
        
    except Exception as e:
        print(f"❌ Error generating config: {e}")


def main():
    """Run all diagnostic tests."""
    print("🧪 MCP Connectivity Diagnostic Tool")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    tests = [
        ("Port Binding", test_port_binding),
        ("Local Connectivity", test_local_connectivity),
        ("Network Interface", test_network_interface),
        ("CORS Headers", test_cors_headers),
        ("MCP Endpoints", test_mcp_endpoints),
        ("Tool Calling", test_tool_calling)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 Diagnostic Summary")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Jarvis server is working correctly.")
        print("The issue is likely with the MCP server configuration or environment.")
        print("\nPossible MCP server issues:")
        print("1. MCP server is running in a sandboxed environment")
        print("2. MCP server has network restrictions")
        print("3. MCP server is using wrong URL or configuration")
        print("4. MCP server is in a different network namespace/container")
        
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check Jarvis server configuration.")
    
    generate_mcp_config()
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
