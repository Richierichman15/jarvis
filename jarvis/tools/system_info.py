"""
System information tool for Jarvis.
This tool provides system information like CPU usage, memory usage, etc.
"""
import os
import platform
import logging
import psutil
from typing import Dict, Any
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemInfo:
    """System information tool for getting resource usage and system details."""
    
    def __init__(self):
        """Initialize the system information tool."""
        # Check if we're running on a supported platform
        self.platform = platform.system()
        logger.info(f"System info tool initialized on {self.platform}")
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information.
        
        Returns:
            Dictionary with CPU information
        """
        try:
            # Get CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)
            cpu_freq = psutil.cpu_freq()
            
            # Get load average if available
            load_avg = None
            if hasattr(os, "getloadavg") and callable(getattr(os, "getloadavg")):
                try:
                    load_avg = os.getloadavg()
                except (AttributeError, OSError):
                    pass
            
            result = {
                "success": True,
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "cpu_count_physical": cpu_count_physical,
                "processor": platform.processor(),
                "platform": self.platform,
                "timestamp": datetime.now().isoformat()
            }
            
            if cpu_freq:
                result["cpu_freq_current"] = cpu_freq.current
                if hasattr(cpu_freq, "min") and cpu_freq.min:
                    result["cpu_freq_min"] = cpu_freq.min
                if hasattr(cpu_freq, "max") and cpu_freq.max:
                    result["cpu_freq_max"] = cpu_freq.max
                    
            if load_avg:
                result["load_avg_1min"] = load_avg[0]
                result["load_avg_5min"] = load_avg[1]
                result["load_avg_15min"] = load_avg[2]
                
            logger.info(f"CPU usage: {cpu_percent}%")
            return result
            
        except Exception as e:
            error_msg = f"Error getting CPU info: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information.
        
        Returns:
            Dictionary with memory information
        """
        try:
            # Get memory info
            virtual_memory = psutil.virtual_memory()
            swap_memory = psutil.swap_memory()
            
            result = {
                "success": True,
                "total_memory": virtual_memory.total,
                "available_memory": virtual_memory.available,
                "used_memory": virtual_memory.used,
                "memory_percent": virtual_memory.percent,
                "total_swap": swap_memory.total,
                "used_swap": swap_memory.used,
                "swap_percent": swap_memory.percent,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Memory usage: {virtual_memory.percent}%")
            return result
            
        except Exception as e:
            error_msg = f"Error getting memory info: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def get_disk_info(self) -> Dict[str, Any]:
        """Get disk information.
        
        Returns:
            Dictionary with disk information
        """
        try:
            # Get disk info
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            result = {
                "success": True,
                "total_disk": disk_usage.total,
                "used_disk": disk_usage.used,
                "free_disk": disk_usage.free,
                "disk_percent": disk_usage.percent,
                "timestamp": datetime.now().isoformat()
            }
            
            if disk_io:
                result["read_count"] = disk_io.read_count
                result["write_count"] = disk_io.write_count
                result["read_bytes"] = disk_io.read_bytes
                result["write_bytes"] = disk_io.write_bytes
                
            logger.info(f"Disk usage: {disk_usage.percent}%")
            return result
            
        except Exception as e:
            error_msg = f"Error getting disk info: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information.
        
        Returns:
            Dictionary with network information
        """
        try:
            # Get network info
            net_io = psutil.net_io_counters()
            net_connections = psutil.net_connections(kind='inet')
            
            result = {
                "success": True,
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "active_connections": len(net_connections),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Network: Sent {net_io.bytes_sent / 1024 / 1024:.2f} MB, Received {net_io.bytes_recv / 1024 / 1024:.2f} MB")
            return result
            
        except Exception as e:
            error_msg = f"Error getting network info: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def get_all_info(self) -> Dict[str, Any]:
        """Get all system information.
        
        Returns:
            Dictionary with all system information
        """
        try:
            # Get all system info
            cpu_info = self.get_cpu_info()
            memory_info = self.get_memory_info()
            disk_info = self.get_disk_info()
            network_info = self.get_network_info()
            
            # Check for any errors
            components = [cpu_info, memory_info, disk_info, network_info]
            for component in components:
                if not component.get("success", False):
                    return component  # Return the first error encountered
            
            # Get other system information
            boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()
            
            result = {
                "success": True,
                "cpu": {k: v for k, v in cpu_info.items() if k != "success"},
                "memory": {k: v for k, v in memory_info.items() if k != "success"},
                "disk": {k: v for k, v in disk_info.items() if k != "success"},
                "network": {k: v for k, v in network_info.items() if k != "success"},
                "system": {
                    "system": platform.system(),
                    "node": platform.node(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "boot_time": boot_time,
                    "python_version": platform.python_version(),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info("Successfully retrieved all system information")
            return result
            
        except Exception as e:
            error_msg = f"Error getting system info: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def summarize_results(self, result: Dict[str, Any], info_type: str = "all") -> str:
        """Summarize system information into a readable format.
        
        Args:
            result: System information result dictionary
            info_type: Type of information to summarize (cpu, memory, disk, network, all)
            
        Returns:
            Formatted summary string
        """
        if not result.get("success", False):
            return f"System Information Error: {result.get('error', 'Unknown error')}"
        
        summary = "System Information:\n\n"
        
        # Format different types of information
        if info_type == "cpu" or info_type == "all":
            if "cpu" in result:
                cpu_data = result["cpu"]
            else:
                cpu_data = result  # Direct CPU info result
                
            summary += "CPU Information:\n"
            summary += f"- Usage: {cpu_data.get('cpu_percent', 'N/A')}%\n"
            summary += f"- Cores: {cpu_data.get('cpu_count', 'N/A')} logical, {cpu_data.get('cpu_count_physical', 'N/A')} physical\n"
            summary += f"- Processor: {cpu_data.get('processor', 'N/A')}\n"
            
            if "cpu_freq_current" in cpu_data:
                summary += f"- Frequency: {cpu_data['cpu_freq_current']:.2f} MHz\n"
                
            if "load_avg_1min" in cpu_data:
                summary += f"- Load Average: {cpu_data['load_avg_1min']:.2f} (1m), {cpu_data['load_avg_5min']:.2f} (5m), {cpu_data['load_avg_15min']:.2f} (15m)\n"
            
            summary += "\n"
            
        if info_type == "memory" or info_type == "all":
            if "memory" in result:
                mem_data = result["memory"]
            else:
                mem_data = result  # Direct memory info result
                
            summary += "Memory Information:\n"
            summary += f"- Usage: {mem_data.get('memory_percent', 'N/A')}%\n"
            
            if "total_memory" in mem_data:
                total_gb = mem_data["total_memory"] / (1024 ** 3)
                used_gb = mem_data["used_memory"] / (1024 ** 3)
                available_gb = mem_data["available_memory"] / (1024 ** 3)
                summary += f"- Total: {total_gb:.2f} GB\n"
                summary += f"- Used: {used_gb:.2f} GB\n"
                summary += f"- Available: {available_gb:.2f} GB\n"
                
            if "total_swap" in mem_data and mem_data["total_swap"] > 0:
                swap_gb = mem_data["total_swap"] / (1024 ** 3)
                swap_used_gb = mem_data["used_swap"] / (1024 ** 3)
                summary += f"- Swap: {mem_data['swap_percent']}% of {swap_gb:.2f} GB ({swap_used_gb:.2f} GB used)\n"
                
            summary += "\n"
            
        if info_type == "disk" or info_type == "all":
            if "disk" in result:
                disk_data = result["disk"]
            else:
                disk_data = result  # Direct disk info result
                
            summary += "Disk Information:\n"
            summary += f"- Usage: {disk_data.get('disk_percent', 'N/A')}%\n"
            
            if "total_disk" in disk_data:
                total_gb = disk_data["total_disk"] / (1024 ** 3)
                used_gb = disk_data["used_disk"] / (1024 ** 3)
                free_gb = disk_data["free_disk"] / (1024 ** 3)
                summary += f"- Total: {total_gb:.2f} GB\n"
                summary += f"- Used: {used_gb:.2f} GB\n"
                summary += f"- Free: {free_gb:.2f} GB\n"
                
            summary += "\n"
            
        if info_type == "network" or info_type == "all":
            if "network" in result:
                net_data = result["network"]
            else:
                net_data = result  # Direct network info result
                
            summary += "Network Information:\n"
            
            if "bytes_sent" in net_data:
                sent_mb = net_data["bytes_sent"] / (1024 ** 2)
                recv_mb = net_data["bytes_recv"] / (1024 ** 2)
                summary += f"- Sent: {sent_mb:.2f} MB\n"
                summary += f"- Received: {recv_mb:.2f} MB\n"
                summary += f"- Packets Sent: {net_data.get('packets_sent', 'N/A')}\n"
                summary += f"- Packets Received: {net_data.get('packets_recv', 'N/A')}\n"
                summary += f"- Active Connections: {net_data.get('active_connections', 'N/A')}\n"
                
            summary += "\n"
            
        if info_type == "all" and "system" in result:
            sys_data = result["system"]
            
            summary += "System Information:\n"
            summary += f"- System: {sys_data.get('system', 'N/A')}\n"
            summary += f"- Node: {sys_data.get('node', 'N/A')}\n"
            summary += f"- Release: {sys_data.get('release', 'N/A')}\n"
            summary += f"- Version: {sys_data.get('version', 'N/A')}\n"
            summary += f"- Machine: {sys_data.get('machine', 'N/A')}\n"
            summary += f"- Python Version: {sys_data.get('python_version', 'N/A')}\n"
            
            if "boot_time" in sys_data:
                boot_time = sys_data["boot_time"]
                summary += f"- Boot Time: {boot_time}\n"
                
        # Add timestamp
        if "timestamp" in result:
            summary += f"\nTimestamp: {result['timestamp']}"
        elif info_type == "all":
            if "cpu" in result and "timestamp" in result["cpu"]:
                summary += f"\nTimestamp: {result['cpu']['timestamp']}"
                
        logger.info(f"Summarized {info_type} information")
        return summary 