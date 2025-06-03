"""
OBD-II Plugin implementation.
This plugin provides car diagnostics capabilities through OBD-II interface.
"""
import logging
import time
import requests
from typing import Dict, Any, List, Optional, Tuple

from jarvis.plugins.plugin_base import SensorPlugin, IntegrationPlugin

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OBDPlugin(SensorPlugin, IntegrationPlugin):
    """Plugin for OBD-II car diagnostics."""
    
    @property
    def name(self) -> str:
        """Return the name of the plugin."""
        return "obd_diagnostics"
    
    @property
    def version(self) -> str:
        """Return the version of the plugin."""
        return "0.2.0"
    
    @property
    def description(self) -> str:
        """Return a description of what the plugin does."""
        return "Connects to the Jarvis OBD service to retrieve car diagnostic data and engine health information"
    
    @property
    def author(self) -> str:
        """Return the author of the plugin."""
        return "Jarvis Team"
    
    @property
    def required_permissions(self) -> List[str]:
        """Return a list of permissions required by this plugin."""
        return ["network_access"]
    
    @property
    def service_name(self) -> str:
        """Return the name of the external service."""
        return "Jarvis OBD Service"
    
    @property
    def settings(self) -> Dict[str, Any]:
        """Return the default settings for this plugin."""
        return {
            "api_url": "http://localhost:8000/api/v1",  # Base URL for the OBD API service
            "connection_settings": {
                "port": None,  # Serial port for USB connection (None for auto)
                "baudrate": 38400,  # Baud rate for serial connection
                "timeout": 30,  # Connection timeout in seconds
                "fast": True,  # Fast mode for OBD connection
            },
            "sampling_rate": 10.0,  # Seconds between samples
            "history_size": 100,  # Number of samples to keep in history
            "dtc_check_interval": 300,  # Seconds between DTC checks
        }
    
    def __init__(self):
        """Initialize the plugin."""
        self.jarvis = None
        self.api_url = None
        self.is_connected = False
        self.last_sample_time = 0
        self.last_dtc_check_time = 0
        self.history = {}
        self.dtc_codes = []
        self.supported_commands = []
    
    def initialize(self, jarvis_instance: Any) -> bool:
        """
        Initialize the plugin.
        
        Args:
            jarvis_instance: The instance of Jarvis this plugin is attached to
            
        Returns:
            True if initialization was successful, False otherwise
        """
        self.jarvis = jarvis_instance
        self.api_url = self.settings.get("api_url", "http://localhost:8000/api/v1")
        logger.info(f"OBD Plugin v{self.version} initialized with API URL: {self.api_url}")
        
        # Check if API is available
        try:
            response = requests.get(f"{self.api_url.split('/api/v1')[0]}/health")
            if response.status_code == 200 and response.json().get("status") == "healthy":
                logger.info("OBD API is available and healthy")
                return True
            else:
                logger.error(f"OBD API health check failed: {response.text}")
                return False
        except requests.RequestException as e:
            logger.error(f"Failed to connect to OBD API: {str(e)}")
            return False
    
    def shutdown(self) -> None:
        """Perform cleanup when the plugin is being disabled or Jarvis is shutting down."""
        self.disconnect()
        logger.info("OBD Plugin shutdown complete")
    
    def is_authenticated(self) -> bool:
        """
        Check if the plugin is authenticated with the external service.
        
        Returns:
            True if authenticated, False otherwise
        """
        # For OBD, this is equivalent to checking if the OBD service is connected to a car
        try:
            response = requests.get(f"{self.api_url}/status")
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("connected", False)
            return False
        except requests.RequestException:
            return False
    
    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with the external service.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if authentication was successful, False otherwise
        """
        # For OBD, this is equivalent to connecting to the car
        return self.connect()
    
    def connect(self) -> bool:
        """
        Connect to the OBD-II interface through the OBD API service.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            # Check current connection status
            status_response = requests.get(f"{self.api_url}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("data", {}).get("connected", False):
                    logger.info("Already connected to OBD interface")
                    self.is_connected = True
                    self._get_supported_commands()
                    return True
            
            # Connect to the OBD interface
            connection_settings = self.settings.get("connection_settings", {})
            connect_response = requests.post(
                f"{self.api_url}/connect",
                json=connection_settings
            )
            
            if connect_response.status_code == 200:
                connect_data = connect_response.json()
                if connect_data.get("success"):
                    logger.info("Successfully connected to OBD interface")
                    self.is_connected = True
                    self._get_supported_commands()
                    return True
                else:
                    logger.error(f"Failed to connect to OBD interface: {connect_data.get('message')}")
                    return False
            else:
                logger.error(f"Failed to connect to OBD interface: HTTP {connect_response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Failed to connect to OBD API: {str(e)}")
            return False
    
    def _get_supported_commands(self) -> None:
        """Get the list of supported OBD commands."""
        try:
            response = requests.get(f"{self.api_url}/commands")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.supported_commands = data.get("data", {}).get("commands", [])
                    logger.info(f"Found {len(self.supported_commands)} supported OBD commands")
                    
                    # Initialize history for each command
                    for command in self.supported_commands:
                        if command not in self.history:
                            self.history[command] = []
                else:
                    logger.warning(f"Failed to get supported commands: {data.get('message')}")
            else:
                logger.warning(f"Failed to get supported commands: HTTP {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to get supported commands: {str(e)}")
    
    def disconnect(self) -> bool:
        """
        Disconnect from the OBD-II interface.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        if self.is_connected:
            try:
                response = requests.post(f"{self.api_url}/disconnect")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info("Disconnected from OBD interface")
                        self.is_connected = False
                        return True
                    else:
                        logger.warning(f"Failed to disconnect from OBD interface: {data.get('message')}")
                        return False
                else:
                    logger.warning(f"Failed to disconnect from OBD interface: HTTP {response.status_code}")
                    return False
            except requests.RequestException as e:
                logger.error(f"Failed to disconnect from OBD interface: {str(e)}")
                return False
        return True  # Already disconnected
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        Get the current data from the OBD-II interface.
        
        Returns:
            Dictionary of OBD-II readings
        """
        if not self.is_connected:
            if not self.connect():
                return {"error": "Not connected to OBD-II interface"}
        
        # Check if it's time to sample again
        current_time = time.time()
        if current_time - self.last_sample_time < self.settings.get("sampling_rate", 10.0):
            # Return the most recent data if available
            if self.history and all(len(self.history.get(cmd, [])) > 0 for cmd in ["RPM", "SPEED", "COOLANT_TEMP"]):
                return {
                    cmd: self.history.get(cmd, [])[-1] for cmd in self.history.keys()
                }
        
        # Get new data
        self.last_sample_time = current_time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Get engine health data
        try:
            response = requests.get(f"{self.api_url}/engine/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    health_data = data.get("data", {})
                    
                    # Format the data for consistency with the rest of the plugin
                    formatted_data = {}
                    
                    if "rpm" in health_data:
                        formatted_data["RPM"] = {
                            "timestamp": timestamp,
                            "value": health_data["rpm"],
                            "unit": "rpm"
                        }
                        self._update_history("RPM", formatted_data["RPM"])
                    
                    if "speed" in health_data:
                        formatted_data["SPEED"] = {
                            "timestamp": timestamp,
                            "value": health_data["speed"],
                            "unit": "km/h"
                        }
                        self._update_history("SPEED", formatted_data["SPEED"])
                    
                    if "coolant_temp" in health_data:
                        formatted_data["COOLANT_TEMP"] = {
                            "timestamp": timestamp,
                            "value": health_data["coolant_temp"],
                            "unit": "°C"
                        }
                        self._update_history("COOLANT_TEMP", formatted_data["COOLANT_TEMP"])
                    
                    if "load" in health_data:
                        formatted_data["ENGINE_LOAD"] = {
                            "timestamp": timestamp,
                            "value": health_data["load"],
                            "unit": "%"
                        }
                        self._update_history("ENGINE_LOAD", formatted_data["ENGINE_LOAD"])
                    
                    if "fuel_level" in health_data:
                        formatted_data["FUEL_LEVEL"] = {
                            "timestamp": timestamp,
                            "value": health_data["fuel_level"],
                            "unit": "%"
                        }
                        self._update_history("FUEL_LEVEL", formatted_data["FUEL_LEVEL"])
                    
                    if "throttle_position" in health_data:
                        formatted_data["THROTTLE_POS"] = {
                            "timestamp": timestamp,
                            "value": health_data["throttle_position"],
                            "unit": "%"
                        }
                        self._update_history("THROTTLE_POS", formatted_data["THROTTLE_POS"])
                    
                    if "intake_temp" in health_data:
                        formatted_data["INTAKE_TEMP"] = {
                            "timestamp": timestamp,
                            "value": health_data["intake_temp"],
                            "unit": "°C"
                        }
                        self._update_history("INTAKE_TEMP", formatted_data["INTAKE_TEMP"])
                    
                    # Add status and issues to the response
                    formatted_data["STATUS"] = {
                        "timestamp": timestamp,
                        "value": health_data.get("status", "Unknown"),
                        "issues": health_data.get("issues", [])
                    }
                    
                    # Check for DTCs if it's time
                    if current_time - self.last_dtc_check_time > self.settings.get("dtc_check_interval", 300):
                        self.check_dtc()
                        self.last_dtc_check_time = current_time
                    
                    # Add DTCs to the data
                    formatted_data["DTC"] = {
                        "timestamp": timestamp,
                        "codes": self.dtc_codes
                    }
                    
                    return formatted_data
                else:
                    logger.warning(f"Failed to get engine health data: {data.get('message')}")
            else:
                logger.warning(f"Failed to get engine health data: HTTP {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to get engine health data: {str(e)}")
        
        # Return an error if we couldn't get the data
        return {"error": "Failed to retrieve OBD data"}
    
    def _update_history(self, pid: str, data: Dict[str, Any]) -> None:
        """
        Update the history for a specific PID.
        
        Args:
            pid: The PID to update
            data: The new data
        """
        if pid not in self.history:
            self.history[pid] = []
        
        self.history[pid].append(data)
        
        # Limit history size
        history_size = self.settings.get("history_size", 100)
        if len(self.history[pid]) > history_size:
            self.history[pid] = self.history[pid][-history_size:]
    
    def get_history(self, pid: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the history for a specific PID or all PIDs.
        
        Args:
            pid: The PID to get history for, or None for all PIDs
            
        Returns:
            Dictionary of PID histories
        """
        if pid:
            if pid in self.history:
                return {pid: self.history[pid]}
            return {pid: []}
        return self.history
    
    def check_dtc(self) -> List[Dict[str, Any]]:
        """
        Check for diagnostic trouble codes.
        
        Returns:
            List of DTCs with interpretations
        """
        try:
            response = requests.get(f"{self.api_url}/engine/dtc")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    dtc_data = data.get("data", {})
                    self.dtc_codes = dtc_data.get("codes", [])
                    return dtc_data.get("interpretations", [])
                else:
                    logger.warning(f"Failed to get DTC codes: {data.get('message')}")
            else:
                logger.warning(f"Failed to get DTC codes: HTTP {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to get DTC codes: {str(e)}")
        
        return []
    
    def clear_dtc(self) -> bool:
        """
        Clear diagnostic trouble codes.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(f"{self.api_url}/engine/dtc/clear")
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data", {}).get("cleared", False):
                    logger.info("Successfully cleared DTC codes")
                    self.dtc_codes = []
                    return True
                else:
                    logger.warning(f"Failed to clear DTC codes: {data.get('message')}")
            else:
                logger.warning(f"Failed to clear DTC codes: HTTP {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to clear DTC codes: {str(e)}")
        
        return False
    
    def get_engine_health(self) -> Dict[str, Any]:
        """
        Get a comprehensive assessment of engine health.
        
        Returns:
            Dictionary containing engine health status and details
        """
        try:
            response = requests.get(f"{self.api_url}/engine/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    health_data = data.get("data", {})
                    
                    # Format the response for the Jarvis system
                    return {
                        "status": health_data.get("status", "Unknown"),
                        "issues": health_data.get("issues", []),
                        "metrics": {
                            "rpm": health_data.get("rpm"),
                            "speed": health_data.get("speed"),
                            "coolant_temp": health_data.get("coolant_temp"),
                            "engine_load": health_data.get("load"),
                            "fuel_level": health_data.get("fuel_level"),
                            "throttle_position": health_data.get("throttle_position"),
                            "intake_temp": health_data.get("intake_temp"),
                        },
                        "dtc_codes": health_data.get("trouble_codes", []),
                        "timestamp": health_data.get("timestamp", time.time())
                    }
                else:
                    logger.warning(f"Failed to get engine health: {data.get('message')}")
            else:
                logger.warning(f"Failed to get engine health: HTTP {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to get engine health: {str(e)}")
        
        return {
            "status": "Unknown",
            "issues": ["Failed to retrieve engine health data"],
            "metrics": {},
            "dtc_codes": [],
            "timestamp": time.time()
        }
    
    @property
    def sampling_rate(self) -> float:
        """
        Return the recommended sampling rate in seconds.
        
        Returns:
            Sampling rate in seconds
        """
        return self.settings.get("sampling_rate", 10.0)
    
    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """
        Handle a command directed to this plugin.
        
        Args:
            command: The command name
            args: List of command arguments
            
        Returns:
            Response string or None if command not handled
        """
        if command == "obd_status":
            if self.is_connected:
                return "OBD connection is active"
            else:
                return "OBD connection is inactive"
        
        elif command == "obd_connect":
            if self.connect():
                return "Successfully connected to OBD interface"
            else:
                return "Failed to connect to OBD interface"
        
        elif command == "obd_disconnect":
            if self.disconnect():
                return "Successfully disconnected from OBD interface"
            else:
                return "Failed to disconnect from OBD interface"
        
        elif command == "obd_get_data":
            data = self.get_current_data()
            if "error" in data:
                return f"Error: {data['error']}"
            
            # Format the response
            response = []
            for key, value in data.items():
                if key not in ["DTC", "STATUS"]:
                    if "value" in value and "unit" in value:
                        response.append(f"{key}: {value['value']} {value['unit']}")
            
            return "\n".join(response)
        
        elif command == "obd_clear_dtc":
            if self.clear_dtc():
                return "Successfully cleared DTC codes"
            else:
                return "Failed to clear DTC codes"
        
        elif command == "obd_check_health":
            health = self.get_engine_health()
            
            status = health.get("status", "Unknown")
            issues = health.get("issues", [])
            metrics = health.get("metrics", {})
            
            response = [f"Engine Health Status: {status}"]
            
            if issues:
                response.append("\nIssues:")
                for issue in issues:
                    response.append(f"- {issue}")
            else:
                response.append("\nNo issues detected")
            
            response.append("\nMetrics:")
            for key, value in metrics.items():
                if value is not None:
                    # Format the metric name and add appropriate units
                    formatted_key = key.replace("_", " ").title()
                    unit = ""
                    if "temp" in key:
                        unit = "°C"
                    elif key == "rpm":
                        unit = "RPM"
                    elif key == "speed":
                        unit = "km/h"
                    elif key in ["engine_load", "throttle_position", "fuel_level"]:
                        unit = "%"
                    
                    response.append(f"- {formatted_key}: {value}{unit}")
            
            return "\n".join(response)
            
        return None 