#!/usr/bin/env python3
"""
Simulate MCP Client Connection
This script simulates how an external MCP server would connect to Jarvis.
"""
import requests
import json
import time
import sys
from datetime import datetime


class MCPClientSimulator:
    """Simulates an MCP client connecting to Jarvis."""
    
    def __init__(self, base_url="http://localhost:3010"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MCP-Client/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def test_connection(self):
        """Test basic connection to Jarvis."""
        print(f"🔗 Testing connection to {self.base_url}...")
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Connection successful!")
                print(f"   Status: {data.get('status')}")
                print(f"   Server: {data.get('server')}")
                print(f"   User: {data.get('user')}")
                print(f"   Host: {data.get('host')}")
                return True
            else:
                print(f"❌ Connection failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def discover_tools(self):
        """Discover available tools."""
        print(f"\n🔍 Discovering tools...")
        
        try:
            response = self.session.get(f"{self.base_url}/mcp/tools", timeout=10)
            if response.status_code == 200:
                data = response.json()
                tools = data.get('tools', [])
                print(f"✅ Found {len(tools)} tools:")
                
                for tool in tools:
                    print(f"   • {tool.get('name')}: {tool.get('description', '')[:60]}...")
                
                return tools
            else:
                print(f"❌ Tool discovery failed - Status: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Tool discovery error: {e}")
            return []
    
    def call_tool(self, tool_name, arguments=None):
        """Call a specific tool."""
        print(f"\n🛠️  Calling tool: {tool_name}")
        
        try:
            data = {
                "name": tool_name,
                "arguments": arguments or {}
            }
            
            response = self.session.post(
                f"{self.base_url}/mcp/tools/call",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Tool call successful!")
                
                if 'result' in result:
                    tool_result = result['result']
                    if 'response' in tool_result:
                        print(f"   Response: {tool_result['response'][:100]}...")
                    elif 'message' in tool_result:
                        print(f"   Message: {tool_result['message']}")
                    elif 'status' in tool_result:
                        print(f"   Status: {tool_result['status'][:100]}...")
                    else:
                        print(f"   Result: {str(tool_result)[:100]}...")
                
                return result
            else:
                print(f"❌ Tool call failed - Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Tool call error: {e}")
            return None
    
    def run_comprehensive_test(self):
        """Run a comprehensive test simulating MCP client behavior."""
        print("🧪 MCP Client Simulation Test")
        print("=" * 50)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now().isoformat()}")
        
        # Test 1: Basic connection
        if not self.test_connection():
            print("\n❌ Basic connection failed. MCP server cannot connect.")
            return False
        
        # Test 2: Discover tools
        tools = self.discover_tools()
        if not tools:
            print("\n❌ Tool discovery failed. MCP server cannot discover tools.")
            return False
        
        # Test 3: Call various tools
        test_tools = [
            ("jarvis_get_status", {}),
            ("jarvis_get_settings", {}),
            ("jarvis_schedule_task", {"description": "Test task from MCP client", "priority": "medium"}),
            ("jarvis_get_tasks", {"status": "pending"}),
            ("jarvis_chat", {"message": "Hello from MCP client!"})
        ]
        
        successful_calls = 0
        for tool_name, args in test_tools:
            if any(t['name'] == tool_name for t in tools):
                result = self.call_tool(tool_name, args)
                if result:
                    successful_calls += 1
                time.sleep(0.5)  # Small delay between calls
            else:
                print(f"⚠️  Tool {tool_name} not available")
        
        # Summary
        print(f"\n📊 Test Summary")
        print("=" * 50)
        print(f"✅ Connection: Successful")
        print(f"✅ Tool Discovery: {len(tools)} tools found")
        print(f"✅ Tool Calls: {successful_calls}/{len(test_tools)} successful")
        
        if successful_calls == len(test_tools):
            print(f"\n🎉 All tests passed! MCP client can successfully connect to Jarvis.")
            print(f"\nYour MCP server should be able to connect using:")
            print(f"   URL: {self.base_url}")
            print(f"   Health: {self.base_url}/health")
            print(f"   Tools: {self.base_url}/mcp/tools")
            print(f"   Call: {self.base_url}/mcp/tools/call")
            return True
        else:
            print(f"\n⚠️  Some tool calls failed. Check individual tool implementations.")
            return False


def main():
    """Main function to run MCP client simulation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulate MCP client connection to Jarvis')
    parser.add_argument('--url', default='http://localhost:3010', help='Jarvis server URL')
    parser.add_argument('--test-all', action='store_true', help='Test all available URLs')
    
    args = parser.parse_args()
    
    if args.test_all:
        # Test multiple URLs
        test_urls = [
            "http://localhost:3010",
            "http://127.0.0.1:3010",
            "http://0.0.0.0:3010"
        ]
        
        # Add network IP if available
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            test_urls.append(f"http://{local_ip}:3010")
        except:
            pass
        
        all_passed = True
        for url in test_urls:
            print(f"\n{'='*60}")
            print(f"Testing URL: {url}")
            print(f"{'='*60}")
            
            client = MCPClientSimulator(url)
            if not client.run_comprehensive_test():
                all_passed = False
        
        if all_passed:
            print(f"\n🎉 All URL tests passed!")
            return 0
        else:
            print(f"\n❌ Some URL tests failed.")
            return 1
    else:
        # Test single URL
        client = MCPClientSimulator(args.url)
        success = client.run_comprehensive_test()
        return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
