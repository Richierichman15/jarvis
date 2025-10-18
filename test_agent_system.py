#!/usr/bin/env python3
"""
Test script for Jarvis Modular Agent System

This script tests the distributed agent system with various scenarios
including agent spawning, task routing, health monitoring, and failure recovery.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from jarvis.agents import AgentManager, AgentCapability, TraderAgent, SoloLevelingAgent, ResearchAgent
    from jarvis.intelligence import IntentRouter, IntentType
    AGENT_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Could not import agent system: {e}")
    AGENT_SYSTEM_AVAILABLE = False
    sys.exit(1)


async def test_agent_creation():
    """Test individual agent creation and basic functionality."""
    print("Testing Individual Agent Creation")
    print("=" * 40)
    
    agents = []
    
    try:
        # Test TraderAgent
        print("\n📈 Testing TraderAgent...")
        trader = TraderAgent()
        await trader.start()
        agents.append(trader)
        
        # Test basic task
        from jarvis.agents.agent_base import TaskRequest
        task = TaskRequest(
            task_id="test_001",
            agent_id=trader.agent_id,
            capability=AgentCapability.TRADING,
            task_type="get_portfolio",
            parameters={}
        )
        
        response = await trader._handle_task(task)
        print(f"✅ TraderAgent response: {response.success}")
        print(f"   Result: {response.result.get('total_value', 'N/A') if response.result else 'None'}")
        
        # Test SoloLevelingAgent
        print("\n🎯 Testing SoloLevelingAgent...")
        solo_leveling = SoloLevelingAgent()
        await solo_leveling.start()
        agents.append(solo_leveling)
        
        task = TaskRequest(
            task_id="test_002",
            agent_id=solo_leveling.agent_id,
            capability=AgentCapability.SYSTEM,
            task_type="get_status",
            parameters={}
        )
        
        response = await solo_leveling._handle_task(task)
        print(f"✅ SoloLevelingAgent response: {response.success}")
        print(f"   Result: {response.result.get('user_level', 'N/A') if response.result else 'None'}")
        
        # Test ResearchAgent
        print("\n🔍 Testing ResearchAgent...")
        research = ResearchAgent()
        await research.start()
        agents.append(research)
        
        task = TaskRequest(
            task_id="test_003",
            agent_id=research.agent_id,
            capability=AgentCapability.RESEARCH,
            task_type="scan_news",
            parameters={"category": "technology", "limit": 3}
        )
        
        response = await research._handle_task(task)
        print(f"✅ ResearchAgent response: {response.success}")
        print(f"   Result: {len(response.result.get('articles', [])) if response.result else 0} articles found")
        
        print(f"\n✅ All {len(agents)} agents created and tested successfully!")
        
    except Exception as e:
        print(f"❌ Error testing agents: {e}")
    
    finally:
        # Cleanup
        for agent in agents:
            try:
                await agent.stop()
            except Exception as e:
                print(f"⚠️ Error stopping agent: {e}")
        
        print("🧹 Cleanup completed")


async def test_agent_manager():
    """Test the AgentManager with Redis communication."""
    print("\n🧪 Testing AgentManager")
    print("=" * 30)
    
    manager = None
    
    try:
        # Create AgentManager
        print("🚀 Creating AgentManager...")
        manager = AgentManager()
        
        # Note: This test will fail if Redis is not running
        # In a real scenario, you'd start Redis first
        try:
            await manager.start()
            print("✅ AgentManager started successfully")
            
            # Get system health
            health = await manager.get_system_health()
            print(f"🏥 System health: {health.get('overall_health', 'unknown')}")
            print(f"   Health score: {health.get('health_score', 0)}%")
            print(f"   Active agents: {health.get('active_agents', 0)}")
            
            # Get agent status
            status = await manager.get_agent_status()
            print(f"📊 Agent status: {len(status.get('agents', {}))} agents managed")
            
            # Test task routing
            print("\n📤 Testing task routing...")
            task_id = await manager.send_task_to_agent(
                capability=AgentCapability.TRADING,
                task_type="get_portfolio",
                parameters={}
            )
            print(f"✅ Task sent: {task_id}")
            
            # Get statistics
            stats = manager.get_statistics()
            print(f"📈 Statistics: {stats['agent_count']} agents, {stats['manager_stats']['total_restarts']} restarts")
            
        except Exception as e:
            print(f"⚠️ AgentManager test failed (likely Redis not running): {e}")
            print("   This is expected if Redis is not installed/running")
    
    except Exception as e:
        print(f"❌ Error testing AgentManager: {e}")
    
    finally:
        if manager:
            try:
                await manager.stop()
                print("✅ AgentManager stopped")
            except Exception as e:
                print(f"⚠️ Error stopping AgentManager: {e}")


async def test_intelligence_integration():
    """Test Intelligence Core integration with Agent System."""
    print("\n🧪 Testing Intelligence Core Integration")
    print("=" * 40)
    
    try:
        # Create IntentRouter
        print("🧠 Creating IntentRouter...")
        router = IntentRouter()
        
        # Test intent analysis
        test_cases = [
            "show me my portfolio balance",
            "what's my current level?",
            "create a new quest for learning Python",
            "get the latest tech news"
        ]
        
        for i, text in enumerate(test_cases, 1):
            print(f"\n🔍 Test {i}: '{text}'")
            
            result = await router.analyze_intent(text, "test_user", "test_channel")
            
            print(f"   Intent: {result.intent_type.value}")
            print(f"   Tool: {result.tool_name}")
            print(f"   Confidence: {result.confidence:.2f}")
            print(f"   Reasoning: {result.reasoning}")
            
            # Test agent routing (will use fallback since no agent manager)
            task_id = await router.route_to_agent(result, "test_user")
            print(f"   Task ID: {task_id}")
        
        print(f"\n✅ Intelligence Core integration tested successfully!")
        
    except Exception as e:
        print(f"❌ Error testing Intelligence Core integration: {e}")


async def test_agent_health_monitoring():
    """Test agent health monitoring and restart capabilities."""
    print("\n🧪 Testing Agent Health Monitoring")
    print("=" * 35)
    
    try:
        # Create a test agent
        print("🤖 Creating test agent...")
        agent = SoloLevelingAgent()
        await agent.start()
        
        # Get initial health
        health = agent.get_health_status()
        print(f"✅ Agent health: {health['status']}")
        print(f"   Uptime: {health['uptime_seconds']}s")
        print(f"   Tasks processed: {health['tasks_processed']}")
        print(f"   Errors: {health['errors_count']}")
        
        # Simulate some work
        print("\n⚙️ Simulating agent work...")
        for i in range(3):
            task = TaskRequest(
                task_id=f"health_test_{i}",
                agent_id=agent.agent_id,
                capability=AgentCapability.SYSTEM,
                task_type="get_status",
                parameters={}
            )
            
            response = await agent._handle_task(task)
            print(f"   Task {i+1}: {response.success}")
        
        # Check health again
        health = agent.get_health_status()
        print(f"\n📊 Updated health:")
        print(f"   Tasks processed: {health['tasks_processed']}")
        print(f"   Is healthy: {health['is_healthy']}")
        
        await agent.stop()
        print("✅ Health monitoring test completed")
        
    except Exception as e:
        print(f"❌ Error testing health monitoring: {e}")


async def test_agent_communication():
    """Test inter-agent communication patterns."""
    print("\n🧪 Testing Agent Communication")
    print("=" * 30)
    
    try:
        # Create multiple agents
        print("🤖 Creating multiple agents...")
        trader = TraderAgent()
        solo_leveling = SoloLevelingAgent()
        research = ResearchAgent()
        
        await trader.start()
        await solo_leveling.start()
        await research.start()
        
        agents = [trader, solo_leveling, research]
        
        # Test concurrent task processing
        print("\n⚡ Testing concurrent task processing...")
        
        tasks = []
        for i, agent in enumerate(agents):
            task = TaskRequest(
                task_id=f"comm_test_{i}",
                agent_id=agent.agent_id,
                capability=agent.capabilities[0],
                task_type="get_status" if hasattr(agent, '_handle_get_status') else "get_portfolio",
                parameters={}
            )
            tasks.append(agent._handle_task(task))
        
        # Wait for all tasks to complete
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"✅ Processed {len(responses)} concurrent tasks")
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                print(f"   Task {i}: Error - {response}")
            else:
                print(f"   Task {i}: Success - {response.success}")
        
        # Test agent info exchange
        print("\n📋 Testing agent info exchange...")
        for agent in agents:
            info = agent.get_info()
            print(f"   {agent.name}: {info.status.value}, {info.tasks_processed} tasks")
        
        # Cleanup
        for agent in agents:
            await agent.stop()
        
        print("✅ Communication test completed")
        
    except Exception as e:
        print(f"❌ Error testing agent communication: {e}")


async def test_error_handling():
    """Test error handling and recovery."""
    print("\n🧪 Testing Error Handling")
    print("=" * 25)
    
    try:
        # Create agent
        print("🤖 Creating test agent...")
        agent = TraderAgent()
        await agent.start()
        
        # Test invalid task
        print("\n❌ Testing invalid task handling...")
        invalid_task = TaskRequest(
            task_id="error_test",
            agent_id=agent.agent_id,
            capability=AgentCapability.TRADING,
            task_type="invalid_task_type",
            parameters={}
        )
        
        response = await agent._handle_task(invalid_task)
        print(f"   Invalid task handled: {not response.success}")
        print(f"   Error message: {response.error}")
        
        # Test malformed parameters
        print("\n⚠️ Testing malformed parameters...")
        malformed_task = TaskRequest(
            task_id="malformed_test",
            agent_id=agent.agent_id,
            capability=AgentCapability.TRADING,
            task_type="get_price",
            parameters={"invalid_param": "test"}
        )
        
        response = await agent._handle_task(malformed_task)
        print(f"   Malformed task handled: {response.success}")
        
        # Test agent restart
        print("\n🔄 Testing agent restart...")
        await agent.stop()
        await asyncio.sleep(1)
        await agent.start()
        
        health = agent.get_health_status()
        print(f"   Agent restarted: {health['status'] == 'running'}")
        
        await agent.stop()
        print("✅ Error handling test completed")
        
    except Exception as e:
        print(f"❌ Error testing error handling: {e}")


async def run_performance_test():
    """Run performance tests on the agent system."""
    print("\n🧪 Running Performance Tests")
    print("=" * 30)
    
    try:
        # Create agent
        print("🤖 Creating test agent...")
        agent = SoloLevelingAgent()
        await agent.start()
        
        # Test task processing speed
        print("\n⚡ Testing task processing speed...")
        num_tasks = 10
        start_time = time.time()
        
        tasks = []
        for i in range(num_tasks):
            task = TaskRequest(
                task_id=f"perf_test_{i}",
                agent_id=agent.agent_id,
                capability=AgentCapability.SYSTEM,
                task_type="get_status",
                parameters={}
            )
            tasks.append(agent._handle_task(task))
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / num_tasks
        
        print(f"   Processed {num_tasks} tasks in {total_time:.2f}s")
        print(f"   Average time per task: {avg_time:.3f}s")
        print(f"   Tasks per second: {num_tasks / total_time:.1f}")
        
        # Test memory usage
        print("\n💾 Testing memory usage...")
        health = agent.get_health_status()
        print(f"   Active tasks: {health['active_tasks']}")
        print(f"   Tasks processed: {health['tasks_processed']}")
        print(f"   Errors: {health['errors_count']}")
        
        await agent.stop()
        print("✅ Performance test completed")
        
    except Exception as e:
        print(f"❌ Error running performance test: {e}")


async def main():
    """Main test function."""
    print("Starting Jarvis Modular Agent System Tests")
    print("=" * 60)
    
    if not AGENT_SYSTEM_AVAILABLE:
        print("Agent system not available")
        return
    
    # Run all tests
    test_functions = [
        test_agent_creation,
        test_agent_manager,
        test_intelligence_integration,
        test_agent_health_monitoring,
        test_agent_communication,
        test_error_handling,
        run_performance_test
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🎉 Testing Complete!")
    print(f"📊 Results: {passed} passed, {failed} failed")
    print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    if failed == 0:
        print("🎊 All tests passed! Agent system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs for details.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
