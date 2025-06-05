"""
PC Health Plugin implementation.
This plugin provides system monitoring and optimization capabilities.
"""
import logging
import time
import requests
from typing import Dict, Any, List, Optional, Tuple

from jarvis.plugins.plugin_base import SensorPlugin, ToolPlugin

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PCHealthPlugin(SensorPlugin, ToolPlugin):
    """Plugin for PC health monitoring and optimization."""
    
    @property
    def name(self) -> str:
        """Return the name of the plugin."""
        return "pc_health"
    
    @property
    def version(self) -> str:
        """Return the version of the plugin."""
        return "0.1.0"
    
    @property
    def description(self) -> str:
        """Return a description of what the plugin does."""
        return "Monitors system health and provides optimization recommendations"
    
    @property
    def author(self) -> str:
        """Return the author of the plugin."""
        return "Jarvis Team"
    
    @property
    def required_permissions(self) -> List[str]:
        """Return a list of permissions required by this plugin."""
        return ["system_info"]
    
    @property
    def tool_name(self) -> str:
        """Return the name of the tool this plugin provides."""
        return "pc_health"
    
    @property
    def tool_description(self) -> str:
        """Return a description of the tool for the AI to understand its usage."""
        return "Provides system health information and optimization recommendations"
    
    @property
    def settings(self) -> Dict[str, Any]:
        """Return the default settings for this plugin."""
        return {
            "api_url": "http://localhost:8001/api/v1",  # Base URL for the PC Health API service
            "sampling_rate": 30.0,  # Seconds between samples
            "auto_cleanup": False,  # Whether to automatically clean up temp files
            "auto_cleanup_threshold": 1024 * 1024 * 1024,  # 1GB
            "notify_on_critical": True,  # Whether to notify when system status is critical
        }
    
    def __init__(self):
        """Initialize the plugin."""
        self.jarvis = None
        self.api_url = None
        self.last_sample_time = 0
        self.last_status = "normal"
    
    def initialize(self, jarvis_instance: Any) -> bool:
        """
        Initialize the plugin.
        
        Args:
            jarvis_instance: The instance of Jarvis this plugin is attached to
            
        Returns:
            True if initialization was successful, False otherwise
        """
        self.jarvis = jarvis_instance
        self.api_url = self.settings.get("api_url", "http://localhost:8001/api/v1")
        logger.info(f"PC Health Plugin v{self.version} initialized with API URL: {self.api_url}")
        
        # Check if API is available
        try:
            response = requests.get(f"{self.api_url.split('/api/v1')[0]}/health")
            if response.status_code == 200 and response.json().get("status") == "healthy":
                logger.info("PC Health API is available and healthy")
                return True
            else:
                logger.error(f"PC Health API health check failed: {response.text}")
                return False
        except requests.RequestException as e:
            logger.error(f"Failed to connect to PC Health API: {str(e)}")
            return False
    
    def shutdown(self) -> None:
        """Perform cleanup when the plugin is being disabled or Jarvis is shutting down."""
        logger.info("PC Health Plugin shutdown complete")
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        Get the current data from the system.
        
        Returns:
            Dictionary of system readings
        """
        # Check if it's time to sample again
        current_time = time.time()
        if current_time - self.last_sample_time < self.settings.get("sampling_rate", 30.0):
            # Return the cached data
            try:
                # Just get the status to see if there's a critical issue
                response = requests.get(f"{self.api_url}/status")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success", False):
                        status = data.get("data", {}).get("analysis", {}).get("status", "normal")
                        # If status changed to critical, force a full update
                        if self.last_status != "critical" and status == "critical":
                            logger.info("Status changed to critical, forcing full update")
                        else:
                            # Return the cached data from the last full update
                            return {"status": "cached"}
                    else:
                        logger.warning(f"Error getting system status: {data.get('message')}")
            except requests.RequestException as e:
                logger.error(f"Error connecting to PC Health API: {str(e)}")
                return {"error": f"Error connecting to PC Health API: {str(e)}"}
        
        # Get new data
        self.last_sample_time = current_time
        
        try:
            # Get system status and metrics
            response = requests.get(f"{self.api_url}/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    self.last_status = data.get("data", {}).get("analysis", {}).get("status", "normal")
                    
                    # Check if we should perform auto-cleanup
                    if (self.settings.get("auto_cleanup", False) and 
                        self.last_status in ["warning", "critical"]):
                        self._perform_auto_cleanup()
                    
                    # Notify on critical status
                    if (self.last_status == "critical" and 
                        self.settings.get("notify_on_critical", True) and
                        hasattr(self.jarvis, "notify")):
                        bottlenecks = data.get("data", {}).get("analysis", {}).get("bottlenecks", [])
                        bottleneck_msgs = [f"{b.get('component')}: {b.get('details')}" for b in bottlenecks]
                        self.jarvis.notify(
                            title="System Health Critical",
                            message="\n".join(bottleneck_msgs),
                            urgency="high"
                        )
                    
                    return data.get("data", {})
                else:
                    logger.warning(f"Error getting system status: {data.get('message')}")
                    return {"error": data.get("message")}
            else:
                logger.warning(f"Error getting system status: HTTP {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except requests.RequestException as e:
            logger.error(f"Error connecting to PC Health API: {str(e)}")
            return {"error": f"Error connecting to PC Health API: {str(e)}"}
    
    def _perform_auto_cleanup(self) -> None:
        """Perform automatic cleanup when system is in warning or critical state."""
        try:
            # Clean temp files
            requests.post(f"{self.api_url}/cleanup/temp")
            logger.info("Automatic temp file cleanup triggered")
            
            # Clean browser cache
            requests.post(f"{self.api_url}/cleanup/browser-cache")
            logger.info("Automatic browser cache cleanup triggered")
        except requests.RequestException as e:
            logger.error(f"Error performing auto cleanup: {str(e)}")
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.
        
        Args:
            params: Parameters for the tool
            
        Returns:
            Result of the tool execution
        """
        action = params.get("action", "status")
        
        if action == "status":
            return self._get_status()
        elif action == "info":
            return self._get_system_info()
        elif action == "cleanup_temp":
            return self._cleanup_temp_files()
        elif action == "cleanup_browser":
            return self._cleanup_browser_cache()
        elif action == "analyze_startup":
            return self._analyze_startup()
        elif action == "analyze_services":
            return self._analyze_services()
        elif action == "optimization_summary":
            return self._get_optimization_summary()
        else:
            logger.warning(f"Unknown action: {action}")
            return {
                "status": "error",
                "message": f"Unknown action: {action}",
                "data": None
            }
    
    def _get_status(self) -> Dict[str, Any]:
        """Get system status and metrics."""
        try:
            response = requests.get(f"{self.api_url}/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    return {
                        "status": "success",
                        "message": data.get("message"),
                        "data": self._format_status_for_jarvis(data.get("data", {}))
                    }
                else:
                    return {
                        "status": "error",
                        "message": data.get("message"),
                        "data": None
                    }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "data": None
                }
        except requests.RequestException as e:
            return {
                "status": "error",
                "message": f"Error connecting to PC Health API: {str(e)}",
                "data": None
            }
    
    def _format_status_for_jarvis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the status data for Jarvis."""
        # Extract the most important information
        result = {
            "system_status": data.get("analysis", {}).get("status", "unknown"),
            "bottlenecks": data.get("analysis", {}).get("bottlenecks", []),
            "recommendations": data.get("analysis", {}).get("recommendations", []),
        }
        
        # Add CPU data
        if data.get("metrics", {}).get("cpu"):
            cpu_data = data.get("metrics", {}).get("cpu", {})
            result["cpu"] = {
                "usage": cpu_data.get("cpu_percent"),
                "cores": cpu_data.get("cpu_count"),
                "frequency": cpu_data.get("cpu_freq_current")
            }
        
        # Add memory data
        if data.get("metrics", {}).get("memory"):
            memory_data = data.get("metrics", {}).get("memory", {})
            result["memory"] = {
                "usage_percent": memory_data.get("percent"),
                "total_gb": memory_data.get("total_gb"),
                "used_gb": memory_data.get("used_gb"),
                "available_gb": memory_data.get("available_gb")
            }
        
        # Add disk data (just the disks with >75% usage)
        if data.get("metrics", {}).get("disk", {}).get("disks"):
            disks = data.get("metrics", {}).get("disk", {}).get("disks", [])
            result["disk"] = {
                "critical_disks": [
                    {
                        "mountpoint": disk.get("mountpoint"),
                        "usage_percent": disk.get("percent"),
                        "free_gb": disk.get("free_gb")
                    }
                    for disk in disks if disk.get("percent", 0) > 75
                ]
            }
        
        return result
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information."""
        try:
            response = requests.get(f"{self.api_url}/info")
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    return {
                        "status": "success",
                        "message": data.get("message"),
                        "data": data.get("data")
                    }
                else:
                    return {
                        "status": "error",
                        "message": data.get("message"),
                        "data": None
                    }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "data": None
                }
        except requests.RequestException as e:
            return {
                "status": "error",
                "message": f"Error connecting to PC Health API: {str(e)}",
                "data": None
            }
    
    def _cleanup_temp_files(self) -> Dict[str, Any]:
        """Clean up temporary files."""
        try:
            response = requests.post(f"{self.api_url}/cleanup/temp")
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    return {
                        "status": "success",
                        "message": "Temporary file cleanup started",
                        "data": {
                            "initial_size_mb": data.get("data", {}).get("initial_size_mb")
                        }
                    }
                else:
                    return {
                        "status": "error",
                        "message": data.get("message"),
                        "data": None
                    }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "data": None
                }
        except requests.RequestException as e:
            return {
                "status": "error",
                "message": f"Error connecting to PC Health API: {str(e)}",
                "data": None
            }
    
    def _cleanup_browser_cache(self) -> Dict[str, Any]:
        """Clean up browser cache."""
        try:
            response = requests.post(f"{self.api_url}/cleanup/browser-cache")
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    return {
                        "status": "success",
                        "message": "Browser cache cleanup started",
                        "data": None
                    }
                else:
                    return {
                        "status": "error",
                        "message": data.get("message"),
                        "data": None
                    }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "data": None
                }
        except requests.RequestException as e:
            return {
                "status": "error",
                "message": f"Error connecting to PC Health API: {str(e)}",
                "data": None
            }
    
    def _analyze_startup(self) -> Dict[str, Any]:
        """Analyze startup programs."""
        try:
            response = requests.get(f"{self.api_url}/optimize/startup")
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    return {
                        "status": "success",
                        "message": data.get("message"),
                        "data": {
                            "recommendations": data.get("data", {}).get("recommendations", [])
                        }
                    }
                else:
                    return {
                        "status": "error",
                        "message": data.get("message"),
                        "data": None
                    }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "data": None
                }
        except requests.RequestException as e:
            return {
                "status": "error",
                "message": f"Error connecting to PC Health API: {str(e)}",
                "data": None
            }
    
    def _analyze_services(self) -> Dict[str, Any]:
        """Analyze system services."""
        try:
            response = requests.get(f"{self.api_url}/optimize/services")
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    return {
                        "status": "success",
                        "message": data.get("message"),
                        "data": {
                            "recommendations": data.get("data", {}).get("recommendations", [])
                        }
                    }
                else:
                    return {
                        "status": "error",
                        "message": data.get("message"),
                        "data": None
                    }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "data": None
                }
        except requests.RequestException as e:
            return {
                "status": "error",
                "message": f"Error connecting to PC Health API: {str(e)}",
                "data": None
            }
    
    def _get_optimization_summary(self) -> Dict[str, Any]:
        """Get optimization summary."""
        try:
            response = requests.get(f"{self.api_url}/optimize/summary")
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    return {
                        "status": "success",
                        "message": data.get("message"),
                        "data": data.get("data")
                    }
                else:
                    return {
                        "status": "error",
                        "message": data.get("message"),
                        "data": None
                    }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "data": None
                }
        except requests.RequestException as e:
            return {
                "status": "error",
                "message": f"Error connecting to PC Health API: {str(e)}",
                "data": None
            }
    
    @property
    def sampling_rate(self) -> float:
        """
        Return the recommended sampling rate in seconds.
        
        Returns:
            Sampling rate in seconds
        """
        return self.settings.get("sampling_rate", 30.0)
    
    @property
    def intent_patterns(self) -> List[str]:
        """
        Return a list of regex patterns that can be used to detect when this tool should be used.
        
        Returns:
            List of regex patterns
        """
        return [
            r"(?i)system\s+health",
            r"(?i)pc\s+health",
            r"(?i)computer\s+(status|health)",
            r"(?i)(clean(up)?|free(\s+up)?)\s+(disk|space|temp|temporary|system)",
            r"(?i)(optimize|speed\s+up)\s+(my\s+)?(pc|computer|laptop|system)",
            r"(?i)(analyze|check)\s+(startup|services)",
            r"(?i)(cpu|memory|disk)\s+usage",
            r"(?i)system\s+performance",
            r"(?i)what's\s+(slowing|running)\s+on\s+my\s+(pc|computer)"
        ]
    
    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """
        Handle a command directed to this plugin.
        
        Args:
            command: The command name
            args: List of command arguments
            
        Returns:
            Response string or None if command not handled
        """
        if command == "pc_status":
            result = self._get_status()
            
            if result.get("status") == "success":
                data = result.get("data", {})
                
                response = [f"System Status: {data.get('system_status', 'Unknown')}"]
                
                if data.get("bottlenecks"):
                    response.append("\nBottlenecks:")
                    for b in data.get("bottlenecks", []):
                        response.append(f"- {b.get('component')}: {b.get('details')}")
                
                if data.get("cpu"):
                    cpu = data.get("cpu", {})
                    response.append(f"\nCPU: {cpu.get('usage')}% used")
                
                if data.get("memory"):
                    memory = data.get("memory", {})
                    response.append(f"Memory: {memory.get('usage_percent')}% used ({memory.get('used_gb')}/{memory.get('total_gb')} GB)")
                
                if data.get("disk", {}).get("critical_disks"):
                    response.append("\nCritical Disk Usage:")
                    for disk in data.get("disk", {}).get("critical_disks", []):
                        response.append(f"- {disk.get('mountpoint')}: {disk.get('usage_percent')}% used ({disk.get('free_gb')} GB free)")
                
                return "\n".join(response)
            else:
                return f"Error getting system status: {result.get('message')}"
            
        elif command == "pc_cleanup":
            # Clean temp files
            temp_result = self._cleanup_temp_files()
            browser_result = self._cleanup_browser_cache()
            
            if temp_result.get("status") == "success" and browser_result.get("status") == "success":
                return "System cleanup started. This will free up disk space by removing temporary files and browser caches."
            else:
                error = "Error starting cleanup: "
                if temp_result.get("status") != "success":
                    error += temp_result.get("message")
                if browser_result.get("status") != "success":
                    error += " " + browser_result.get("message")
                return error
            
        elif command == "pc_optimize":
            # Get optimization recommendations
            startup_result = self._analyze_startup()
            services_result = self._analyze_services()
            
            if startup_result.get("status") == "success" and services_result.get("status") == "success":
                response = ["System Optimization Recommendations:"]
                
                # Get startup recommendations
                startup_recommendations = startup_result.get("data", {}).get("recommendations", [])
                if startup_recommendations:
                    response.append("\nStartup Items:")
                    for rec in startup_recommendations:
                        response.append(f"- {rec.get('item')}: {rec.get('action').upper()} - {rec.get('reason')}")
                
                # Get service recommendations
                service_recommendations = services_result.get("data", {}).get("recommendations", [])
                if service_recommendations:
                    response.append("\nSystem Services:")
                    for rec in service_recommendations:
                        response.append(f"- {rec.get('service')}: {rec.get('action').upper()} - {rec.get('reason')}")
                
                if not startup_recommendations and not service_recommendations:
                    response.append("\nNo optimization recommendations found. Your system appears to be well-optimized.")
                
                return "\n".join(response)
            else:
                error = "Error getting optimization recommendations: "
                if startup_result.get("status") != "success":
                    error += startup_result.get("message")
                if services_result.get("status") != "success":
                    error += " " + services_result.get("message")
                return error
        
        return None 