#!/usr/bin/env python3
"""
Test script for Jarvis Intelligence Core

This script tests the IntentRouter with various natural language inputs
to validate that it correctly routes commands to the appropriate tools.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from jarvis.intelligence import IntentRouter, IntentType
    INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Could not import intelligence core: {e}")
    INTELLIGENCE_AVAILABLE = False
    sys.exit(1)


async def test_intent_router():
    """Test the intent router with various inputs."""
    print("🧠 Testing Jarvis Intelligence Core")
    print("=" * 50)
    
    # Initialize the intent router
    try:
        router = IntentRouter()
        print("✅ IntentRouter initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize IntentRouter: {e}")
        return
    
    # Test cases with expected results
    test_cases = [
        # Trading tests
        {
            "input": "show me my portfolio balance",
            "expected_intent": IntentType.TRADING,
            "expected_tool": "trading.portfolio.get_overview",
            "description": "Portfolio balance request"
        },
        {
            "input": "what's the current price of Bitcoin?",
            "expected_intent": IntentType.TRADING,
            "expected_tool": "trading.trading.get_price",
            "description": "Bitcoin price query"
        },
        {
            "input": "get my recent trades",
            "expected_intent": IntentType.TRADING,
            "expected_tool": "trading.trading.get_recent_executions",
            "description": "Recent trades request"
        },
        {
            "input": "show me momentum signals",
            "expected_intent": IntentType.TRADING,
            "expected_tool": "trading.trading.get_momentum_signals",
            "description": "Momentum signals request"
        },
        
        # Music tests
        {
            "input": "play some music",
            "expected_intent": IntentType.MUSIC,
            "expected_tool": "music_play_or_resume",
            "description": "General music play request"
        },
        {
            "input": "play 90210 by Travis Scott",
            "expected_intent": IntentType.MUSIC,
            "expected_tool": "music_play",
            "description": "Specific song request"
        },
        {
            "input": "pause the music",
            "expected_intent": IntentType.MUSIC,
            "expected_tool": "music_pause",
            "description": "Music pause request"
        },
        {
            "input": "skip to the next song",
            "expected_intent": IntentType.MUSIC,
            "expected_tool": "music_skip",
            "description": "Skip song request"
        },
        
        # Fitness tests
        {
            "input": "show me chest workouts",
            "expected_intent": IntentType.FITNESS,
            "expected_tool": "fitness.list_workouts",
            "description": "Chest workout request"
        },
        {
            "input": "what leg exercises can I do?",
            "expected_intent": IntentType.FITNESS,
            "expected_tool": "fitness.list_workouts",
            "description": "Leg exercise query"
        },
        
        # News tests
        {
            "input": "get the latest news",
            "expected_intent": IntentType.NEWS,
            "expected_tool": "jarvis_scan_news",
            "description": "Latest news request"
        },
        {
            "input": "scan tech news for me",
            "expected_intent": IntentType.NEWS,
            "expected_tool": "jarvis_scan_news",
            "description": "Tech news scan request"
        },
        
        # System tests
        {
            "input": "what's my system status?",
            "expected_intent": IntentType.SYSTEM,
            "expected_tool": "jarvis_get_status",
            "description": "System status query"
        },
        {
            "input": "show me my tasks",
            "expected_intent": IntentType.SYSTEM,
            "expected_tool": "jarvis_get_tasks",
            "description": "Tasks request"
        },
        
        # Search tests
        {
            "input": "search for AI developments",
            "expected_intent": IntentType.SEARCH,
            "expected_tool": "jarvis_web_search",
            "description": "Web search request"
        },
        {
            "input": "find information about Tesla stock",
            "expected_intent": IntentType.SEARCH,
            "expected_tool": "jarvis_web_search",
            "description": "Information search request"
        },
        
        # Chat tests
        {
            "input": "how are you doing?",
            "expected_intent": IntentType.CHAT,
            "expected_tool": "jarvis_chat",
            "description": "Casual conversation"
        },
        {
            "input": "hello there",
            "expected_intent": IntentType.CHAT,
            "expected_tool": "jarvis_chat",
            "description": "Greeting"
        }
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['description']}")
        print(f"Input: '{test_case['input']}'")
        
        try:
            # Analyze intent
            result = await router.analyze_intent(
                test_case['input'],
                "test_user",
                "test_channel"
            )
            
            # Check results
            intent_match = result.intent_type == test_case['expected_intent']
            tool_match = result.tool_name == test_case['expected_tool']
            
            print(f"Intent: {result.intent_type.value} (expected: {test_case['expected_intent'].value})")
            print(f"Tool: {result.tool_name} (expected: {test_case['expected_tool']})")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Reasoning: {result.reasoning}")
            print(f"Processing time: {result.processing_time:.3f}s")
            
            if intent_match and tool_match:
                print("✅ PASS")
                passed += 1
            else:
                print("❌ FAIL")
                if not intent_match:
                    print(f"   Intent mismatch: got {result.intent_type.value}, expected {test_case['expected_intent'].value}")
                if not tool_match:
                    print(f"   Tool mismatch: got {result.tool_name}, expected {test_case['expected_tool']}")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    # Show statistics
    try:
        stats = router.get_intent_statistics()
        print(f"\n📈 Intent Statistics:")
        print(f"Total requests: {stats.get('total_requests', 0)}")
        print(f"Average processing time: {stats.get('average_processing_time', 0):.3f}s")
        
        intent_types = stats.get('intent_types', {})
        if intent_types:
            print("Intent distribution:")
            for intent_type, count in intent_types.items():
                print(f"  {intent_type}: {count}")
        
        confidence_dist = stats.get('confidence_distribution', {})
        if confidence_dist:
            print("Confidence distribution:")
            print(f"  High (≥0.8): {confidence_dist.get('high', 0)}")
            print(f"  Medium (≥0.5): {confidence_dist.get('medium', 0)}")
            print(f"  Low (<0.5): {confidence_dist.get('low', 0)}")
            
    except Exception as e:
        print(f"⚠️ Could not get statistics: {e}")
    
    return passed, failed


async def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n🔬 Testing Edge Cases")
    print("=" * 30)
    
    try:
        router = IntentRouter()
    except Exception as e:
        print(f"❌ Failed to initialize router: {e}")
        return
    
    edge_cases = [
        "",  # Empty string
        "   ",  # Whitespace only
        "asdfghjkl",  # Random characters
        "123456789",  # Numbers only
        "!@#$%^&*()",  # Special characters only
        "show me my portfolio balance and also play some music",  # Multiple intents
        "what is the meaning of life the universe and everything",  # Philosophical question
    ]
    
    for i, test_input in enumerate(edge_cases, 1):
        print(f"\n🧪 Edge Case {i}: '{test_input}'")
        
        try:
            result = await router.analyze_intent(test_input, "test_user", "test_channel")
            print(f"Intent: {result.intent_type.value}")
            print(f"Tool: {result.tool_name}")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Reasoning: {result.reasoning}")
            
            if result.confidence < 0.5:
                print("✅ Correctly identified as low confidence")
            else:
                print("⚠️ High confidence for edge case")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Main test function."""
    print("🚀 Starting Jarvis Intelligence Core Tests")
    print("=" * 60)
    
    if not INTELLIGENCE_AVAILABLE:
        print("❌ Intelligence core not available")
        return
    
    # Run main tests
    passed, failed = await test_intent_router()
    
    # Run edge case tests
    await test_edge_cases()
    
    print("\n🎉 Testing Complete!")
    print(f"Overall Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎊 All tests passed! Intelligence core is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs for details.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)
