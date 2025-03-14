#!/usr/bin/env python3
"""
Debug script for testing Jarvis tools.
This script tests the functionality of all implemented tools.
"""
import os
import sys
import argparse
import logging
from typing import Dict, Any

from jarvis.tools.tool_manager import ToolManager
from jarvis.tools.web_search import WebSearch
from jarvis.tools.calculator import Calculator
from jarvis.tools.file_operations import FileOperations
from jarvis.tools.system_info import SystemInfo
from jarvis.tools.debug import DebugTool
from jarvis.config import AVAILABLE_TOOLS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_web_search():
    """Test the web search tool."""
    logger.info("Testing Web Search Tool...")
    
    web_search = WebSearch()
    test_query = "weather in new york"
    
    try:
        logger.info(f"Searching for: {test_query}")
        results = web_search.search(test_query)
        
        if results:
            logger.info(f"Found {len(results)} results")
            summary = web_search.summarize_results(results)
            logger.info("Search successful")
            print("\n" + "-" * 50)
            print("WEB SEARCH RESULTS:")
            print("-" * 50)
            print(summary)
            print("-" * 50 + "\n")
            return True
        else:
            logger.error("No search results found")
            return False
    except Exception as e:
        logger.error(f"Web search test failed: {str(e)}")
        return False


def test_calculator():
    """Test the calculator tool."""
    logger.info("Testing Calculator Tool...")
    
    calculator = Calculator()
    
    try:
        # Test expression evaluation
        expression = "2 + 2 * 3"
        logger.info(f"Evaluating expression: {expression}")
        eval_result = calculator.evaluate(expression)
        
        # Test unit conversion
        value = 100
        from_unit = "celsius"
        to_unit = "fahrenheit"
        logger.info(f"Converting {value} {from_unit} to {to_unit}")
        conv_result = calculator.convert_units(value, from_unit, to_unit)
        
        # Test equation solving
        equation = "2x + 3 = 7"
        logger.info(f"Solving equation: {equation}")
        eq_result = calculator.solve_equation(equation)
        
        # Display results
        print("\n" + "-" * 50)
        print("CALCULATOR RESULTS:")
        print("-" * 50)
        print("1. Expression Evaluation:")
        print(calculator.summarize_results(eval_result))
        print("\n2. Unit Conversion:")
        print(calculator.summarize_results(conv_result))
        print("\n3. Equation Solving:")
        print(calculator.summarize_results(eq_result))
        print("-" * 50 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Calculator test failed: {str(e)}")
        return False


def test_file_operations():
    """Test the file operations tool."""
    logger.info("Testing File Operations Tool...")
    
    file_ops = FileOperations()
    test_dir = os.getcwd()
    test_file = "test_file.txt"
    test_content = "This is a test file created by Jarvis debug script.\nLine 2 of the test file."
    
    try:
        # Test writing a file
        logger.info(f"Writing to file: {test_file}")
        write_result = file_ops.write_file(test_file, test_content)
        
        # Test reading a file
        logger.info(f"Reading file: {test_file}")
        read_result = file_ops.read_file(test_file)
        
        # Test listing a directory
        logger.info(f"Listing directory: {test_dir}")
        list_result = file_ops.list_directory(test_dir)
        
        # Display results
        print("\n" + "-" * 50)
        print("FILE OPERATIONS RESULTS:")
        print("-" * 50)
        print("1. File Write:")
        print(file_ops.summarize_results(write_result))
        print("\n2. File Read:")
        print(file_ops.summarize_results(read_result))
        print("\n3. Directory Listing:")
        print(file_ops.summarize_results(list_result))
        print("-" * 50 + "\n")
        
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
            logger.info(f"Cleaned up test file: {test_file}")
            
        return True
    except Exception as e:
        logger.error(f"File operations test failed: {str(e)}")
        return False


def test_system_info():
    """Test the system info tool."""
    logger.info("Testing System Info Tool...")
    
    sys_info = SystemInfo()
    
    try:
        # Test getting CPU info
        logger.info("Getting CPU info")
        cpu_result = sys_info.get_cpu_info()
        
        # Test getting memory info
        logger.info("Getting memory info")
        memory_result = sys_info.get_memory_info()
        
        # Test getting disk info
        logger.info("Getting disk info")
        disk_result = sys_info.get_disk_info()
        
        # Test getting all info
        logger.info("Getting all system info")
        all_result = sys_info.get_all_info()
        
        # Display results
        print("\n" + "-" * 50)
        print("SYSTEM INFO RESULTS:")
        print("-" * 50)
        print("1. CPU Info:")
        print(sys_info.summarize_results(cpu_result, "cpu"))
        print("\n2. Memory Info:")
        print(sys_info.summarize_results(memory_result, "memory"))
        print("\n3. Disk Info:")
        print(sys_info.summarize_results(disk_result, "disk"))
        print("\n4. All System Info (Partial):")
        print(sys_info.summarize_results(all_result, "all")[:500] + "...\n[Truncated for readability]")
        print("-" * 50 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"System info test failed: {str(e)}")
        return False


def test_tool_manager():
    """Test the tool manager."""
    logger.info("Testing Tool Manager...")
    
    tool_manager = ToolManager()
    
    try:
        # Test available tools
        available_tools = tool_manager.get_available_tools()
        logger.info(f"Available tools: {', '.join(available_tools)}")
        
        # Test tool descriptions
        descriptions = tool_manager.get_tool_descriptions()
        
        # Test tool detection
        test_queries = [
            "What's the weather in Paris?",
            "Calculate 15 * 7 - 3",
            "Show me the files in my Downloads folder",
            "What's my CPU usage?"
        ]
        
        detection_results = {}
        for query in test_queries:
            logger.info(f"Detecting tools for query: {query}")
            tool_calls = tool_manager.detect_tool_calls(query)
            detection_results[query] = tool_calls
            
        # Test tool execution
        execution_results = {}
        for query, tool_calls in detection_results.items():
            if tool_calls:
                tool_call = tool_calls[0]
                tool_name = tool_call["tool"]
                params = tool_call["params"]
                
                logger.info(f"Executing tool {tool_name} with params: {params}")
                result = tool_manager.execute_tool(tool_name, params)
                execution_results[query] = {
                    "tool": tool_name,
                    "params": params,
                    "result": result
                }
            
        # Display results
        print("\n" + "-" * 50)
        print("TOOL MANAGER RESULTS:")
        print("-" * 50)
        print(f"Available Tools: {', '.join(available_tools)}")
        print("\nTool Descriptions:")
        for tool, desc in descriptions.items():
            print(f"- {tool}: {desc}")
            
        print("\nTool Detection Results:")
        for query, tool_calls in detection_results.items():
            print(f"\nQuery: \"{query}\"")
            if tool_calls:
                for tool_call in tool_calls:
                    print(f"  Detected Tool: {tool_call['tool']}")
                    print(f"  Confidence: {tool_call['confidence']}")
                    print(f"  Parameters: {tool_call['params']}")
            else:
                print("  No tools detected")
                
        print("\nTool Execution Results (Sample):")
        if execution_results:
            for query, result in list(execution_results.items())[:2]:  # Show first 2 only
                print(f"\nQuery: \"{query}\"")
                print(f"Tool: {result['tool']}")
                print(f"Result Preview: {str(result['result'])[:200]}...")
        else:
            print("  No execution results available")
            
        print("-" * 50 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Tool manager test failed: {str(e)}")
        return False


def main():
    """Run the debug script."""
    parser = argparse.ArgumentParser(description="Debug Jarvis tools")
    parser.add_argument("--all", action="store_true", help="Test all tools")
    parser.add_argument("--web", action="store_true", help="Test web search tool")
    parser.add_argument("--calc", action="store_true", help="Test calculator tool")
    parser.add_argument("--file", action="store_true", help="Test file operations tool")
    parser.add_argument("--sys", action="store_true", help="Test system info tool")
    parser.add_argument("--manager", action="store_true", help="Test tool manager")
    
    args = parser.parse_args()
    
    # If no specific tests are specified, test all
    test_all = args.all or not (args.web or args.calc or args.file or args.sys or args.manager)
    
    results = {}
    
    # Run specified tests
    if test_all or args.web:
        results["Web Search"] = test_web_search()
        
    if test_all or args.calc:
        results["Calculator"] = test_calculator()
        
    if test_all or args.file:
        results["File Operations"] = test_file_operations()
        
    if test_all or args.sys:
        results["System Info"] = test_system_info()
        
    if test_all or args.manager:
        results["Tool Manager"] = test_tool_manager()
        
    # Display summary
    print("\n" + "=" * 50)
    print("JARVIS TOOLS DEBUG SUMMARY:")
    print("=" * 50)
    
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test}: {status}")
        
    print("=" * 50)
    
    # Return success if all tests passed
    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 