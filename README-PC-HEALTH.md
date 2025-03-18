# Jarvis PC Health and Optimization Architecture

## Overview

The PC Health and Optimization system is designed as a modular extension to the Jarvis AI Assistant. It provides comprehensive system monitoring, analysis, and optimization capabilities to keep your computer running at peak performance.

## Architecture

The system follows a microservices architecture with two main components:

1. **Jarvis PC Health Service**: A standalone FastAPI application that runs independently and provides system monitoring and optimization functionality through a REST API.

2. **Jarvis PC Health Plugin**: A plugin for the main Jarvis AI Assistant that communicates with the PC Health service and makes its functionality available through Jarvis.

This separation of concerns allows for:

- Independent development and deployment of the PC Health service
- Cleaner codebase organization
- Ability to run the PC Health service on a different machine if needed
- Better resource management

## Components

### 1. Jarvis PC Health Service (`jarvis-pc-health/`)

The standalone service provides various endpoints for monitoring and optimizing system health:

- **System Monitoring**: Tracks CPU, memory, disk, network usage, and other system metrics
- **Performance Analysis**: Identifies bottlenecks and performance issues
- **Disk Cleanup**: Removes temporary files and browser caches
- **Startup Optimization**: Analyzes and provides recommendations for optimizing startup programs
- **Service Optimization**: Analyzes and provides recommendations for optimizing system services

Core modules:
- `app/core/system_monitor.py`: Comprehensive system monitoring
- `app/core/system_optimizer.py`: System optimization functionality
- `app/api/routes.py`: API endpoints for accessing the functionality

### 2. Jarvis PC Health Plugin (`jarvis/plugins/installed/pc_health_plugin/`)

The plugin integrates with the main Jarvis AI Assistant and provides:

- Connection to the PC Health service API
- Automatic monitoring of system health
- Tools for Jarvis to access system health information
- Commands for users to interact with PC health functionality
- Notifications for critical system issues

Key features:
- Implements both `SensorPlugin` and `ToolPlugin` interfaces
- Provides `pc_status`, `pc_cleanup`, and `pc_optimize` commands
- Defines intent patterns for natural language detection
- Formats system health data for user-friendly display

## API Integration

The PC Health service exposes a REST API with the following endpoints:

- `/api/v1/status`: Get current system status and health metrics
- `/api/v1/info`: Get detailed system information
- `/api/v1/history/{data_type}`: Get historical data for specific metrics
- `/api/v1/cleanup/temp`: Clean up temporary files
- `/api/v1/cleanup/browser-cache`: Clear browser caches
- `/api/v1/optimize/startup`: Analyze startup programs
- `/api/v1/optimize/services`: Analyze system services
- `/api/v1/optimize/summary`: Get optimization summary

The plugin communicates with these endpoints to retrieve information and perform actions.

## Installation and Setup

1. Start the PC Health service:
   ```
   cd jarvis-pc-health
   pip install -r requirements.txt
   python -m app.main
   ```

2. Ensure the Jarvis PC Health plugin is enabled in Jarvis:
   ```
   python main.py plugin enable pc_health
   ```

3. Configure the plugin settings if needed:
   ```
   python main.py plugin config pc_health api_url http://localhost:8001/api/v1
   ```

## Usage

### Through Jarvis commands:

```
pc_status              # Get current system health status
pc_cleanup             # Clean temporary files and browser caches
pc_optimize            # Get system optimization recommendations
```

### Through natural language:

```
"What's my system health status?"
"Can you clean up my disk space?"
"How can I optimize my computer?"
"What's using all my CPU?"
```

### Programmatically:

```python
# Via Jarvis plugin
jarvis.execute_plugin_command("pc_health", "pc_status")

# Via PC Health API directly
response = requests.get("http://localhost:8001/api/v1/status")
``` 