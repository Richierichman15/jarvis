"""
System Monitor Plugin implementation.
This plugin provides system monitoring capabilities.
"""
import os
import time
import platform
import logging
import psutil
from typing import Dict, Any, List, Optional

from jarvis.plugins.plugin_base import SensorPlugin

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemMonitorPlugin(SensorPlugin):
    """Plugin for monitoring system resources."""
    
    @property
    def name(self) -> str:
        """Return the name of the plugin."""
        return "system_monitor"
    
    @property
    def version(self) -> str:
        """Return the version of the plugin."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Return a description of what the plugin does."""
        return "Monitors system resources like CPU, memory, disk, and temperature"
    
    @property
    def author(self) -> str:
        """Return the author of the plugin."""
        return "Jarvis Team"
    
    @property
    def required_permissions(self) -> List[str]:
        """Return a list of permissions required by this plugin."""
        return ["system_info"]
    
    @property
    def settings(self) -> Dict[str, Any]:
        """Return the default settings for this plugin."""
        return {
            "sampling_rate": 5.0,  # Seconds between samples
            "history_size": 60,    # Number of samples to keep in history
            "enable_temperature": True,  # Whether to monitor temperature
            "enable_disk_io": True,      # Whether to monitor disk I/O
            "enable_network": True,      # Whether to monitor network
            "critical_cpu_threshold": 90.0,  # Critical CPU usage threshold (%)
            "critical_memory_threshold": 90.0,  # Critical memory usage threshold (%)
            "critical_disk_threshold": 90.0,   # Critical disk usage threshold (%)
        }
    
    def __init__(self):
        """Initialize the plugin."""
        self.jarvis = None
        self.history = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "temperature": [],
            "network": []
        }
        self.last_sample_time = 0
        self.is_monitoring = False
        self.monitor_thread = None
    
    def initialize(self, jarvis_instance: Any) -> bool:
        """
        Initialize the plugin.
        
        Args:
            jarvis_instance: The instance of Jarvis this plugin is attached to
            
        Returns:
            True if initialization was successful, False otherwise
        """
        self.jarvis = jarvis_instance
        logger.info(f"System Monitor Plugin v{self.version} initialized")
        return True
    
    def shutdown(self) -> None:
        """Perform cleanup when the plugin is being disabled or Jarvis is shutting down."""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        logger.info("System Monitor Plugin shutdown complete")
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        Get the current data from the system.
        
        Returns:
            Dictionary of system readings
        """
        # Check if it's time to sample again
        current_time = time.time()
        if current_time - self.last_sample_time < self.settings.get("sampling_rate", 5.0):
            # Return the most recent data if available
            if self.history["cpu"] and self.history["memory"] and self.history["disk"]:
                return {
                    "cpu": self.history["cpu"][-1],
                    "memory": self.history["memory"][-1],
                    "disk": self.history["disk"][-1],
                    "temperature": self.history["temperature"][-1] if self.history["temperature"] else None,
                    "network": self.history["network"][-1] if self.history["network"] else None
                }
        
        # Get new data
        self.last_sample_time = current_time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # CPU data
        cpu_percent = psutil.cpu_percent(interval=0.1)
        per_cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_count = psutil.cpu_count()
        
        # Get top CPU processes
        top_processes = []
        for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent']), 
                          key=lambda p: p.info['cpu_percent'] if p.info['cpu_percent'] is not None else 0, 
                          reverse=True)[:5]:
            try:
                top_processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cpu_percent": proc.info['cpu_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        cpu_data = {
            "timestamp": timestamp,
            "cpu_percent": cpu_percent,
            "per_cpu_percent": per_cpu_percent,
            "cpu_count": cpu_count,
            "top_processes": top_processes
        }
        
        # Memory data
        memory = psutil.virtual_memory()
        memory_data = {
            "timestamp": timestamp,
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent
        }
        
        # Disk data
        disk_data = {
            "timestamp": timestamp,
            "disks": []
        }
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_data["disks"].append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": usage.percent
                })
            except (PermissionError, OSError):
                # Some mountpoints may not be accessible
                pass
        
        # Temperature data (if enabled and available)
        temperature_data = None
        if self.settings.get("enable_temperature", True):
            try:
                temperatures = psutil.sensors_temperatures()
                if temperatures:
                    temperature_data = {
                        "timestamp": timestamp,
                        "temperatures": temperatures
                    }
            except (AttributeError, OSError):
                # Temperature sensors may not be available on all systems
                pass
        
        # Network data (if enabled)
        network_data = None
        if self.settings.get("enable_network", True):
            try:
                network_io = psutil.net_io_counters(pernic=True)
                network_data = {
                    "timestamp": timestamp,
                    "interfaces": {}
                }
                
                for interface, stats in network_io.items():
                    network_data["interfaces"][interface] = {
                        "bytes_sent": stats.bytes_sent,
                        "bytes_recv": stats.bytes_recv,
                        "packets_sent": stats.packets_sent,
                        "packets_recv": stats.packets_recv,
                        "errin": stats.errin if hasattr(stats, "errin") else 0,
                        "errout": stats.errout if hasattr(stats, "errout") else 0,
                        "dropin": stats.dropin if hasattr(stats, "dropin") else 0,
                        "dropout": stats.dropout if hasattr(stats, "dropout") else 0
                    }
            except (AttributeError, OSError):
                # Network stats may not be available on all systems
                pass
        
        # Update history
        self._update_history("cpu", cpu_data)
        self._update_history("memory", memory_data)
        self._update_history("disk", disk_data)
        if temperature_data:
            self._update_history("temperature", temperature_data)
        if network_data:
            self._update_history("network", network_data)
        
        # Return the current data
        return {
            "cpu": cpu_data,
            "memory": memory_data,
            "disk": disk_data,
            "temperature": temperature_data,
            "network": network_data
        }
    
    def _update_history(self, data_type: str, data: Dict[str, Any]) -> None:
        """
        Update the history for a specific data type.
        
        Args:
            data_type: Type of data (cpu, memory, disk, temperature, network)
            data: Data to add to history
        """
        history_size = self.settings.get("history_size", 60)
        self.history[data_type].append(data)
        
        # Trim history if it exceeds the maximum size
        if len(self.history[data_type]) > history_size:
            self.history[data_type] = self.history[data_type][-history_size:]
    
    def get_history(self, data_type: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the history of system readings.
        
        Args:
            data_type: Type of data to get history for (cpu, memory, disk, temperature, network)
                      If None, returns history for all data types
                      
        Returns:
            Dictionary of data type to list of readings
        """
        if data_type:
            if data_type in self.history:
                return {data_type: self.history[data_type]}
            else:
                return {}
        else:
            return self.history
    
    def check_thresholds(self) -> Dict[str, Any]:
        """
        Check if any system metrics exceed critical thresholds.
        
        Returns:
            Dictionary of alerts
        """
        alerts = []
        
        # Get the most recent data
        if not self.history["cpu"] or not self.history["memory"] or not self.history["disk"]:
            return {"alerts": alerts}
        
        cpu_data = self.history["cpu"][-1]
        memory_data = self.history["memory"][-1]
        disk_data = self.history["disk"][-1]
        
        # Check CPU threshold
        cpu_threshold = self.settings.get("critical_cpu_threshold", 90.0)
        if cpu_data["cpu_percent"] > cpu_threshold:
            alerts.append({
                "type": "cpu",
                "level": "critical",
                "message": f"CPU usage is {cpu_data['cpu_percent']}%, which exceeds the threshold of {cpu_threshold}%"
            })
        
        # Check memory threshold
        memory_threshold = self.settings.get("critical_memory_threshold", 90.0)
        if memory_data["percent"] > memory_threshold:
            alerts.append({
                "type": "memory",
                "level": "critical",
                "message": f"Memory usage is {memory_data['percent']}%, which exceeds the threshold of {memory_threshold}%"
            })
        
        # Check disk threshold
        disk_threshold = self.settings.get("critical_disk_threshold", 90.0)
        for disk in disk_data["disks"]:
            if disk["percent"] > disk_threshold:
                alerts.append({
                    "type": "disk",
                    "level": "critical",
                    "message": f"Disk usage on {disk['mountpoint']} is {disk['percent']}%, which exceeds the threshold of {disk_threshold}%"
                })
        
        return {"alerts": alerts}
    
    @property
    def sampling_rate(self) -> float:
        """
        Return the recommended sampling rate in seconds.
        
        Returns:
            Sampling rate in seconds
        """
        return self.settings.get("sampling_rate", 5.0) 