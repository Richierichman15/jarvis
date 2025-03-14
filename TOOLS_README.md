# Jarvis Tools Implementation

This README provides an overview of the tools implemented for the Jarvis AI Assistant.

## Available Tools

### 1. Web Search
- **File**: `jarvis/tools/web_search.py`
- **Description**: Enables Jarvis to search the web for information using DuckDuckGo.
- **Key Features**:
  - Web search with configurable result limits
  - Result summarization for easier readability
  - Error handling and timeout configuration

### 2. Calculator
- **File**: `jarvis/tools/calculator.py`
- **Description**: Performs mathematical operations, unit conversions, and equation solving.
- **Key Features**:
  - Expression evaluation with sandboxed execution
  - Unit conversion (length, weight, temperature)
  - Basic equation solving
  - Input validation and error handling

### 3. File Operations
- **File**: `jarvis/tools/file_operations.py`
- **Description**: Handles file system operations safely.
- **Key Features**:
  - Reading files with size limits
  - Writing files with directory creation
  - Directory listing
  - Security checks for safe paths
  - Comprehensive error handling

### 4. System Information
- **File**: `jarvis/tools/system_info.py`
- **Description**: Provides system resource usage and hardware information.
- **Key Features**:
  - CPU usage and information
  - Memory usage statistics
  - Disk space monitoring
  - Network statistics
  - Overall system information

### 5. Debug Tool
- **File**: `jarvis/tools/debug.py`
- **Description**: Internal tool for debugging Jarvis components.
- **Key Features**:
  - Function timing for performance analysis
  - Tool call logging
  - Tool testing functionality
  - Log collection and reporting

## Tool Management

The `ToolManager` class in `jarvis/tools/tool_manager.py` manages all tools:

- Initializes available tools based on configuration
- Detects when user queries should trigger specific tools
- Handles tool execution and result formatting
- Provides debugging capabilities

## Debug Script

The `debug_tools.py` script allows testing all tools individually or together:

```bash
# Test all tools
./debug_tools.py --all

# Test specific tools
./debug_tools.py --web    # Test web search
./debug_tools.py --calc   # Test calculator
./debug_tools.py --file   # Test file operations
./debug_tools.py --sys    # Test system info
./debug_tools.py --manager # Test tool manager
```

## Configuration

Tool settings are configured in `jarvis/config.py`:

```python
# Tools configuration
AVAILABLE_TOOLS = [
    "web_search",
    "calculator",
    "file_operations",
    "system_info",
]

# Tool settings
FILE_MAX_SIZE = 1024 * 1024  # Maximum file size for file operations (1MB)
SAFE_DIRECTORIES = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.getcwd()
]
```

## Adding New Tools

To add a new tool:

1. Create a new file in `jarvis/tools/` for your tool
2. Implement a class with necessary methods and a `summarize_results()` method
3. Add the tool to `ToolManager.__init__()` in `jarvis/tools/tool_manager.py`
4. Add tool detection logic in `ToolManager.detect_tool_calls()`
5. Add tool execution logic in `ToolManager.execute_tool()`
6. Add the tool name to `AVAILABLE_TOOLS` in `jarvis/config.py`
7. Update the `debug_tools.py` script to test your new tool 