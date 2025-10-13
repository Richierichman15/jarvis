#!/usr/bin/env python3
"""
Test script for the AI Response Formatter
Tests both JSON and text formatting capabilities.
"""

import asyncio
import json
from formatter import format_response

try:
    from jarvis.models.model_manager import ModelManager
    MODEL_AVAILABLE = True
except ImportError:
    print("⚠️ Model manager not available - testing fallback formatting only")
    MODEL_AVAILABLE = False


async def test_formatter():
    """Test the response formatter with various inputs."""
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  AI Response Formatter Test Suite                          ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    # Initialize model if available
    model_manager = None
    if MODEL_AVAILABLE:
        try:
            model_manager = ModelManager()
            print("✅ AI Model initialized")
        except Exception as e:
            print(f"⚠️  Could not initialize AI model: {e}")
            print("Testing with fallback formatter only\n")
    else:
        print("Testing with fallback formatter only\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Trading Balance (JSON)",
            "input": json.dumps({
                "balance": {
                    "USD": 5234.67,
                    "BTC": 0.234
                },
                "total_value_usd": 15420.88,
                "last_updated": "2025-10-13T11:30:00Z"
            }),
            "context": "User asked: /balance"
        },
        {
            "name": "Recent Trades (JSON Array)",
            "input": json.dumps({
                "trades": [
                    {"symbol": "BTC/USDT", "side": "buy", "amount": 0.01, "price": 43250},
                    {"symbol": "ETH/USDT", "side": "sell", "amount": 0.5, "price": 2280}
                ],
                "total_trades": 2
            }),
            "context": "User asked: /trades"
        },
        {
            "name": "Portfolio Overview (Complex JSON)",
            "input": json.dumps({
                "cash": 10000,
                "portfolio_value": 15420.88,
                "positions": {
                    "BTC": {"shares": 0.234, "current_price": 43250, "pnl": 234.56},
                    "ETH": {"shares": 2.5, "current_price": 2280, "pnl": -45.23}
                },
                "total_return_percentage": 8.4,
                "daily_pnl": 156.78
            }),
            "context": "User asked: /portfolio"
        },
        {
            "name": "System Status (Plain Text)",
            "input": "System operational. CPU: 45%, Memory: 62%, Disk: 78%, Uptime: 3 days 14 hours 22 minutes. All services running normally.",
            "context": "User asked: /status"
        },
        {
            "name": "Error Message (JSON)",
            "input": json.dumps({
                "error": "API rate limit exceeded. Please wait 60 seconds before retrying."
            }),
            "context": "User asked: /price BTC"
        },
        {
            "name": "Simple Price Response (JSON)",
            "input": json.dumps({
                "symbol": "BTC/USDT",
                "price": 43250.50,
                "change_24h": 3.4,
                "volume_24h": 1234567890
            }),
            "context": "User asked: /price BTC"
        }
    ]
    
    # Run tests
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['name']}")
        print(f"{'='*60}")
        
        print("\n📥 INPUT:")
        print(test['input'][:200] + ('...' if len(test['input']) > 200 else ''))
        
        try:
            # Format the response
            formatted = await format_response(
                raw_response=test['input'],
                model_manager=model_manager,
                context=test['context']
            )
            
            print("\n📤 FORMATTED OUTPUT:")
            print(f"{'─'*60}")
            print(formatted)
            print(f"{'─'*60}")
            
            # Show metrics
            input_len = len(test['input'])
            output_len = len(formatted)
            compression = ((input_len - output_len) / input_len * 100) if input_len > 0 else 0
            
            print(f"\n📊 Metrics:")
            print(f"   Input length: {input_len} chars")
            print(f"   Output length: {output_len} chars")
            print(f"   Compression: {compression:+.1f}%")
            
            # Validate output
            if not formatted or formatted.strip() == "":
                print("   ⚠️  WARNING: Empty output!")
            elif len(formatted) > 2000:
                print(f"   ⚠️  WARNING: Output exceeds Discord limit (2000 chars)")
            else:
                print("   ✅ Output validated")
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Tested {len(test_cases)} scenarios")
    if model_manager:
        print("✅ AI formatting active")
    else:
        print("⚠️  Fallback formatting only (no AI model)")
    print("\nRecommendation: Review outputs above to ensure they match expected Jarvis tone.")


async def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n\n╔════════════════════════════════════════════════════════════╗")
    print("║  Edge Case Tests                                           ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    model_manager = None
    if MODEL_AVAILABLE:
        try:
            model_manager = ModelManager()
        except:
            pass
    
    edge_cases = [
        ("Empty string", ""),
        ("Very long JSON", json.dumps({"data": "x" * 5000})),
        ("Malformed JSON", '{"key": "value"'),
        ("None value", None),
        ("Unicode characters", "Portfolio: 💰 $1,234.56 • 📈 +5.2%"),
    ]
    
    for name, test_input in edge_cases:
        print(f"\nTest: {name}")
        try:
            if test_input is None:
                formatted = await format_response("", model_manager)
            else:
                formatted = await format_response(test_input, model_manager)
            print(f"✅ Handled: {formatted[:100]}...")
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Main test runner."""
    await test_formatter()
    await test_edge_cases()
    
    print("\n\n" + "="*60)
    print("🎉 Testing Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Review the formatted outputs above")
    print("2. Ensure they match Jarvis's personality (confident, clear)")
    print("3. Test in Discord with: /balance, /portfolio, /trades")
    print("4. Monitor logs for: '✨ Response formatted by AI'")


if __name__ == "__main__":
    asyncio.run(main())

