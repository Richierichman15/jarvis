"""
System monitoring tool for Jarvis.
This tool extends the SystemInfo tool to provide advanced monitoring capabilities:
- Disk usage analysis and visualization
- Large file detection and cleanup recommendations
- Temperature monitoring
- System optimization suggestions
"""
import os
import platform
import logging
import psutil
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemMonitor:
    """Advanced system monitoring tool for Jarvis."""
    
    def __init__(self):
        """Initialize the system monitoring tool."""
        self.platform = platform.system()
        self.is_mac = self.platform == "Darwin"
        self.is_linux = self.platform == "Linux"
        self.is_windows = self.platform == "Windows"
        
        # Historical data storage
        self.history = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "temperature": []
        }
        
        # Maximum history points to store
        self.max_history_points = 60  # 1 hour if collecting every minute
        
        logger.info(f"System monitor initialized on {self.platform}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including CPU, memory, disk, and temperature.
        
        Returns:
            Dictionary with system status information
        """
        # Collect all system information in one call
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(),
            "temperature": self.get_temperature_info(),
            "battery": self.get_battery_info() if hasattr(psutil, "sensors_battery") else {"success": False, "error": "Battery info not available"}
        }
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information.
        
        Returns:
            Dictionary with CPU information
        """
        try:
            # Get CPU info
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            
            per_cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # Get process using most CPU
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent']):
                processes.append(proc.info)
                
            # Sort by CPU usage and get top 5
            top_processes = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:5]
            
            result = {
                "success": True,
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "per_cpu_percent": per_cpu_percent,
                "top_processes": top_processes
            }
            
            # Add frequency if available - with safeguards for None values
            if cpu_freq:
                # Some macOS systems may return None for cpu_freq.current
                if hasattr(cpu_freq, "current") and cpu_freq.current is not None:
                    result["cpu_freq_current"] = cpu_freq.current
                
                # Handle cpu_freq.min which might be None on some systems
                if hasattr(cpu_freq, "min") and cpu_freq.min is not None:
                    result["cpu_freq_min"] = cpu_freq.min
                
                # Handle cpu_freq.max which might be None on some systems
                if hasattr(cpu_freq, "max") and cpu_freq.max is not None:
                    result["cpu_freq_max"] = cpu_freq.max
            
            # Add to history
            self._add_to_history("cpu", {
                "timestamp": datetime.now().isoformat(),
                "percent": cpu_percent
            })
            
            return result
        except Exception as e:
            logger.error(f"Error getting CPU info: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information.
        
        Returns:
            Dictionary with memory information
        """
        try:
            # Get memory info
            virtual_memory = psutil.virtual_memory()
            swap_memory = psutil.swap_memory()
            
            # Calculate memory usage by process
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info']):
                try:
                    memory_mb = proc.info['memory_info'].rss / (1024 * 1024) if proc.info['memory_info'] else 0
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'username': proc.info['username'],
                        'memory_mb': round(memory_mb, 2)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
            # Sort by memory usage and get top 5
            top_processes = sorted(processes, key=lambda x: x.get('memory_mb', 0), reverse=True)[:5]
            
            result = {
                "success": True,
                "total_gb": round(virtual_memory.total / (1024**3), 2),
                "available_gb": round(virtual_memory.available / (1024**3), 2),
                "used_gb": round(virtual_memory.used / (1024**3), 2),
                "percent": virtual_memory.percent,
                "swap_total_gb": round(swap_memory.total / (1024**3), 2),
                "swap_used_gb": round(swap_memory.used / (1024**3), 2),
                "swap_percent": swap_memory.percent,
                "top_processes": top_processes
            }
            
            # Add to history
            self._add_to_history("memory", {
                "timestamp": datetime.now().isoformat(),
                "percent": virtual_memory.percent
            })
            
            return result
        except Exception as e:
            logger.error(f"Error getting memory info: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_disk_info(self) -> Dict[str, Any]:
        """Get disk information.
        
        Returns:
            Dictionary with disk information
        """
        try:
            # Get disk partitions
            partitions = psutil.disk_partitions()
            
            # Get disk info for each partition
            disks = []
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": usage.percent
                    }
                    disks.append(disk_info)
                except PermissionError:
                    # Skip if we don't have permission to access this partition
                    continue
            
            # Get disk IO
            disk_io = psutil.disk_io_counters(perdisk=True)
            io_stats = {}
            if disk_io:
                for disk, stats in disk_io.items():
                    io_stats[disk] = {
                        "read_count": stats.read_count,
                        "write_count": stats.write_count,
                        "read_bytes": stats.read_bytes,
                        "write_bytes": stats.write_bytes
                    }
            
            result = {
                "success": True,
                "disks": disks,
                "io_stats": io_stats
            }
            
            # Add to history (using main disk)
            if disks:
                self._add_to_history("disk", {
                    "timestamp": datetime.now().isoformat(),
                    "percent": disks[0]["percent"]
                })
                
            return result
        except Exception as e:
            logger.error(f"Error getting disk info: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_temperature_info(self) -> Dict[str, Any]:
        """Get temperature information if available.
        
        Returns:
            Dictionary with temperature information
        """
        temps = {}
        
        try:
            if hasattr(psutil, "sensors_temperatures"):
                sys_temps = psutil.sensors_temperatures()
                if sys_temps:
                    for chip, values in sys_temps.items():
                        temps[chip] = []
                        for entry in values:
                            # Safely handle None values
                            current_temp = entry.current if hasattr(entry, "current") else None
                            high_temp = entry.high if hasattr(entry, "high") and entry.high is not None else None
                            critical_temp = entry.critical if hasattr(entry, "critical") and entry.critical is not None else None
                            
                            temps[chip].append({
                                "label": entry.label or "Unknown",
                                "current": current_temp,
                                "high": high_temp,
                                "critical": critical_temp
                            })
            
            # On macOS, try using system_profiler
            if self.is_mac and not temps:
                try:
                    output = subprocess.check_output(["system_profiler", "SPHardwareDataType"]).decode('utf-8')
                    for line in output.split('\n'):
                        if 'Temperature' in line:
                            try:
                                value = line.split(':')[1].strip()
                                temps['system'] = [{'label': 'System', 'current': float(value.replace('°C', '').strip())}]
                            except (ValueError, IndexError):
                                # Fallback if temperature parsing fails
                                temps['system'] = [{'label': 'System', 'current': 0, 'note': 'Could not parse temperature value'}]
                except (subprocess.SubprocessError, ValueError):
                    # Fallback for macOS when system_profiler fails
                    temps['system'] = [{'label': 'System', 'current': 0, 'note': 'Temperature data unavailable'}]
            
            # If no temperatures found at all, provide a fallback
            if not temps:
                temps['system'] = [{'label': 'System', 'current': 0, 'note': 'Temperature data unavailable on this system'}]
            
            # Add to history if available
            for chip in temps:
                for sensor in temps[chip]:
                    if 'current' in sensor and sensor['current'] is not None:
                        self._add_to_history("temperature", {
                            "timestamp": datetime.now().isoformat(),
                            "value": sensor['current']
                        })
                        break
                else:
                    continue
                break
            
            return {"success": True, "temperatures": temps}
        except Exception as e:
            logger.error(f"Error getting temperature info: {str(e)}")
            # Return a fallback dummy value
            return {
                "success": False, 
                "error": str(e),
                "temperatures": {'system': [{'label': 'System', 'current': 0, 'note': 'Error retrieving temperature'}]}
            }
    
    def get_battery_info(self) -> Dict[str, Any]:
        """Get battery information if available.
        
        Returns:
            Dictionary with battery information
        """
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "success": True,
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "seconds_left": battery.secsleft if battery.secsleft != -1 else None
                }
            else:
                return {"success": False, "error": "Battery not detected"}
        except Exception as e:
            logger.error(f"Error getting battery info: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def find_large_files(self, path: str, min_size_mb: int = 100, top_n: int = 20) -> Dict[str, Any]:
        """Find large files in the specified directory.
        
        Args:
            path: Directory path to search
            min_size_mb: Minimum file size in MB to consider
            top_n: Number of largest files to return
            
        Returns:
            Dictionary with list of large files
        """
        try:
            # Convert min_size to bytes
            min_size = min_size_mb * 1024 * 1024
            
            # Use different approaches based on OS
            if self.is_mac or self.is_linux:
                return self._find_large_files_unix(path, min_size, top_n)
            elif self.is_windows:
                return self._find_large_files_windows(path, min_size, top_n)
            else:
                return self._find_large_files_python(path, min_size, top_n)
        except Exception as e:
            logger.error(f"Error finding large files: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _find_large_files_unix(self, path: str, min_size: int, top_n: int) -> Dict[str, Any]:
        """Find large files using Unix commands."""
        try:
            # Use find command to locate large files
            cmd = [
                "find", path, "-type", "f", "-size", f"+{min_size}c", 
                "-exec", "ls", "-lh", "{}", "\\;", "2>/dev/null"
            ]
            
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=60).decode('utf-8')
            
            # Parse the output
            large_files = []
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 8:
                    size_str = parts[4]
                    path = ' '.join(parts[8:])
                    
                    # Convert size string to bytes
                    size_bytes = self._parse_size_string(size_str)
                    
                    # Ensure size is at least min_size
                    if size_bytes >= min_size:
                        large_files.append({
                            "path": path,
                            "size_bytes": size_bytes,
                            "size_human": self._format_size(size_bytes),
                            "last_modified": ' '.join(parts[5:8])
                        })
            
            # Sort by size and limit to top_n
            large_files.sort(key=lambda x: x["size_bytes"], reverse=True)
            large_files = large_files[:top_n]
            
            return {"success": True, "files": large_files}
        except subprocess.SubprocessError as e:
            logger.warning(f"Command approach failed, falling back to Python: {str(e)}")
            return self._find_large_files_python(path, min_size, top_n)
    
    def _find_large_files_windows(self, path: str, min_size: int, top_n: int) -> Dict[str, Any]:
        """Find large files using Windows commands."""
        try:
            # Use PowerShell to find large files
            cmd = [
                "powershell", "-Command",
                f"Get-ChildItem -Path '{path}' -File -Recurse -ErrorAction SilentlyContinue | Where-Object {{$_.Length -gt {min_size}}} | Sort-Object -Property Length -Descending | Select-Object -First {top_n} | ForEach-Object {{ $_.FullName + '|' + $_.Length + '|' + $_.LastWriteTime }}"
            ]
            
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=60).decode('utf-8')
            
            # Parse the output
            large_files = []
            for line in output.splitlines():
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 3:
                        path = parts[0]
                        size_bytes = int(parts[1])
                        last_modified = parts[2]
                        
                        large_files.append({
                            "path": path,
                            "size_bytes": size_bytes,
                            "size_human": self._format_size(size_bytes),
                            "last_modified": last_modified
                        })
            
            return {"success": True, "files": large_files}
        except subprocess.SubprocessError as e:
            logger.warning(f"Command approach failed, falling back to Python: {str(e)}")
            return self._find_large_files_python(path, min_size, top_n)
    
    def _find_large_files_python(self, path: str, min_size: int, top_n: int) -> Dict[str, Any]:
        """Find large files using pure Python."""
        large_files = []
        
        try:
            # Walk through the directory tree
            for root, _, files in os.walk(path):
                for filename in files:
                    try:
                        filepath = os.path.join(root, filename)
                        size = os.path.getsize(filepath)
                        
                        if size >= min_size:
                            last_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                            
                            large_files.append({
                                "path": filepath,
                                "size_bytes": size,
                                "size_human": self._format_size(size),
                                "last_modified": last_modified.strftime("%Y-%m-%d %H:%M:%S")
                            })
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        continue
            
            # Sort by size and limit to top_n
            large_files.sort(key=lambda x: x["size_bytes"], reverse=True)
            large_files = large_files[:top_n]
            
            return {"success": True, "files": large_files}
        except Exception as e:
            logger.error(f"Error finding large files with Python: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def analyze_directory_usage(self, path: str, depth: int = 1) -> Dict[str, Any]:
        """Analyze disk usage by directory.
        
        Args:
            path: Directory path to analyze
            depth: Depth of directories to analyze (1 = immediate subdirectories)
            
        Returns:
            Dictionary with directory sizes
        """
        try:
            if not os.path.isdir(path):
                return {"success": False, "error": f"Path is not a directory: {path}"}
            
            # Use different approaches based on OS
            if self.is_mac or self.is_linux:
                return self._analyze_directory_usage_unix(path, depth)
            elif self.is_windows:
                return self._analyze_directory_usage_windows(path, depth)
            else:
                return self._analyze_directory_usage_python(path, depth)
        except Exception as e:
            logger.error(f"Error analyzing directory usage: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _analyze_directory_usage_unix(self, path: str, depth: int) -> Dict[str, Any]:
        """Analyze directory usage using Unix commands."""
        try:
            # Use du command to get directory sizes
            cmd = ["du", "-d", str(depth), "-h", path]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=60).decode('utf-8')
            
            directories = []
            for line in output.splitlines():
                parts = line.split('\t')
                if len(parts) == 2:
                    size_str = parts[0]
                    dir_path = parts[1]
                    
                    # Convert size string to bytes
                    size_bytes = self._parse_size_string(size_str)
                    
                    directories.append({
                        "path": dir_path,
                        "size_bytes": size_bytes,
                        "size_human": self._format_size(size_bytes)
                    })
            
            # Sort by size in descending order
            directories.sort(key=lambda x: x["size_bytes"], reverse=True)
            
            return {"success": True, "directories": directories}
        except subprocess.SubprocessError as e:
            logger.warning(f"Command approach failed, falling back to Python: {str(e)}")
            return self._analyze_directory_usage_python(path, depth)
    
    def _analyze_directory_usage_windows(self, path: str, depth: int) -> Dict[str, Any]:
        """Analyze directory usage using Windows commands."""
        try:
            # Build a PowerShell command to calculate directory sizes
            ps_command = f"""
            function Get-DirSize {{
                param ([string]$Path, [int]$Depth = 0, [int]$CurrentDepth = 0)
                
                $size = 0
                if (Test-Path -Path $Path) {{
                    $size = (Get-ChildItem -Path $Path -File -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
                    
                    if ($CurrentDepth -lt $Depth) {{
                        $dirs = Get-ChildItem -Path $Path -Directory -ErrorAction SilentlyContinue
                        foreach ($dir in $dirs) {{
                            $dirSize = Get-DirSize -Path $dir.FullName -Depth $Depth -CurrentDepth ($CurrentDepth + 1)
                            "$($dir.FullName)|$dirSize"
                        }}
                    }}
                }}
                return $size
            }}
            
            $totalSize = Get-DirSize -Path '{path}' -Depth {depth}
            "{path}|$totalSize"
            """
            
            cmd = ["powershell", "-Command", ps_command]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=60).decode('utf-8')
            
            directories = []
            for line in output.splitlines():
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) == 2:
                        dir_path = parts[0]
                        size_bytes = int(parts[1]) if parts[1].strip() else 0
                        
                        directories.append({
                            "path": dir_path,
                            "size_bytes": size_bytes,
                            "size_human": self._format_size(size_bytes)
                        })
            
            # Sort by size in descending order
            directories.sort(key=lambda x: x["size_bytes"], reverse=True)
            
            return {"success": True, "directories": directories}
        except subprocess.SubprocessError as e:
            logger.warning(f"Command approach failed, falling back to Python: {str(e)}")
            return self._analyze_directory_usage_python(path, depth)
    
    def _analyze_directory_usage_python(self, path: str, depth: int) -> Dict[str, Any]:
        """Analyze directory usage using pure Python."""
        directories = []
        
        try:
            # Get total size for the main directory
            main_dir_size = self._get_dir_size(path)
            directories.append({
                "path": path,
                "size_bytes": main_dir_size,
                "size_human": self._format_size(main_dir_size)
            })
            
            # Get sizes for immediate subdirectories if depth > 0
            if depth > 0:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        try:
                            dir_size = self._get_dir_size(item_path)
                            directories.append({
                                "path": item_path,
                                "size_bytes": dir_size,
                                "size_human": self._format_size(dir_size)
                            })
                        except (OSError, PermissionError):
                            # Skip directories we can't access
                            continue
            
            # Sort by size in descending order
            directories.sort(key=lambda x: x["size_bytes"], reverse=True)
            
            return {"success": True, "directories": directories}
        except Exception as e:
            logger.error(f"Error analyzing directory usage with Python: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_dir_size(self, path: str) -> int:
        """Get directory size using Python."""
        total_size = 0
        try:
            for dirpath, _, filenames in os.walk(path):
                for filename in filenames:
                    try:
                        file_path = os.path.join(dirpath, filename)
                        if not os.path.islink(file_path):
                            total_size += os.path.getsize(file_path)
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        continue
        except (OSError, PermissionError):
            # Skip directories we can't access
            pass
        
        return total_size
    
    def cleanup_suggestions(self, path: str = None) -> Dict[str, Any]:
        """Generate suggestions for cleanup.
        
        Args:
            path: Directory path to analyze (default is user home directory)
            
        Returns:
            Dictionary with cleanup suggestions
        """
        if not path:
            path = os.path.expanduser("~")
        
        suggestions = []
        
        try:
            # Find large files
            large_files_result = self.find_large_files(path, min_size_mb=100, top_n=10)
            if large_files_result["success"] and large_files_result["files"]:
                total_size = sum(file["size_bytes"] for file in large_files_result["files"])
                suggestions.append({
                    "type": "large_files",
                    "description": f"Found {len(large_files_result['files'])} large files (>100MB) totaling {self._format_size(total_size)}",
                    "potential_saving": self._format_size(total_size),
                    "files": large_files_result["files"]
                })
            
            # Check for specific locations known to accumulate temp files
            locations_to_check = []
            
            # Common temp locations based on OS
            if self.is_mac:
                locations_to_check = [
                    {"path": os.path.expanduser("~/Library/Caches"), "description": "Application Caches"},
                    {"path": os.path.expanduser("~/Downloads"), "description": "Downloads folder"},
                    {"path": "/private/var/folders", "description": "System temp files"},
                    {"path": os.path.expanduser("~/Library/Application Support"), "description": "Application support files"}
                ]
            elif self.is_linux:
                locations_to_check = [
                    {"path": "/tmp", "description": "Temporary files"},
                    {"path": os.path.expanduser("~/.cache"), "description": "User cache files"},
                    {"path": os.path.expanduser("~/Downloads"), "description": "Downloads folder"}
                ]
            elif self.is_windows:
                locations_to_check = [
                    {"path": os.path.expanduser("C:\\Windows\\Temp"), "description": "Windows temp files"},
                    {"path": os.path.expanduser(f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Temp"), "description": "User temp files"},
                    {"path": os.path.expanduser("C:\\Windows\\SoftwareDistribution\\Download"), "description": "Windows Update files"},
                    {"path": os.path.expanduser(f"C:\\Users\\{os.getlogin()}\\Downloads"), "description": "Downloads folder"}
                ]
            
            # Check each location
            for location in locations_to_check:
                if os.path.exists(location["path"]):
                    try:
                        total_size = self._get_dir_size(location["path"])
                        if total_size > 100 * 1024 * 1024:  # More than 100MB
                            suggestions.append({
                                "type": "cleanup_location",
                                "description": f"{location['description']} contains {self._format_size(total_size)} of data",
                                "path": location["path"],
                                "potential_saving": self._format_size(total_size * 0.7)  # Assume 70% can be cleaned
                            })
                    except (OSError, PermissionError):
                        # Skip locations we can't access
                        continue
            
            return {"success": True, "suggestions": suggestions}
        except Exception as e:
            logger.error(f"Error generating cleanup suggestions: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_optimization_suggestions(self) -> Dict[str, Any]:
        """Get optimization suggestions based on system status.
        
        Returns:
            Dictionary with optimization suggestions
        """
        suggestions = []
        
        try:
            # Get current system status
            status = self.get_system_status()
            
            # Check CPU usage
            if status["cpu"]["success"]:
                if status["cpu"]["cpu_percent"] > 80:
                    high_cpu_procs = status["cpu"].get("top_processes", [])
                    proc_names = ", ".join([p.get("name", "Unknown") for p in high_cpu_procs[:3]])
                    suggestions.append({
                        "type": "high_cpu",
                        "severity": "high",
                        "description": f"High CPU usage detected ({status['cpu']['cpu_percent']}%)",
                        "recommendation": f"Consider closing high CPU applications: {proc_names}"
                    })
            
            # Check memory usage
            if status["memory"]["success"]:
                if status["memory"]["percent"] > 85:
                    high_mem_procs = status["memory"].get("top_processes", [])
                    proc_names = ", ".join([p.get("name", "Unknown") for p in high_mem_procs[:3]])
                    suggestions.append({
                        "type": "high_memory",
                        "severity": "high",
                        "description": f"High memory usage detected ({status['memory']['percent']}%)",
                        "recommendation": f"Consider closing memory-intensive applications: {proc_names}"
                    })
                elif status["memory"]["percent"] > 70:
                    suggestions.append({
                        "type": "moderate_memory",
                        "severity": "medium",
                        "description": f"Moderate memory usage detected ({status['memory']['percent']}%)",
                        "recommendation": "Consider closing unnecessary applications to improve performance"
                    })
            
            # Check disk usage
            if status["disk"]["success"]:
                for disk in status["disk"].get("disks", []):
                    if disk["percent"] > 90:
                        suggestions.append({
                            "type": "high_disk",
                            "severity": "high",
                            "description": f"Disk {disk['mountpoint']} is nearly full ({disk['percent']}%)",
                            "recommendation": "Run cleanup to free up space",
                            "mountpoint": disk["mountpoint"],
                            "free_space": disk["free_gb"]
                        })
                    elif disk["percent"] > 80:
                        suggestions.append({
                            "type": "moderate_disk",
                            "severity": "medium",
                            "description": f"Disk {disk['mountpoint']} is getting full ({disk['percent']}%)",
                            "recommendation": "Consider freeing up space",
                            "mountpoint": disk["mountpoint"],
                            "free_space": disk["free_gb"]
                        })
            
            # Check temperature if available
            if status["temperature"]["success"]:
                temps = status["temperature"].get("temperatures", {})
                for chip, sensors in temps.items():
                    for sensor in sensors:
                        if sensor.get("current") and sensor.get("critical") and sensor["current"] > sensor["critical"] * 0.9:
                            suggestions.append({
                                "type": "high_temperature",
                                "severity": "high",
                                "description": f"High temperature detected: {sensor['label']} at {sensor['current']}°C",
                                "recommendation": "Check cooling system and clean fans"
                            })
                        elif sensor.get("current") and sensor.get("high") and sensor["current"] > sensor["high"] * 0.9:
                            suggestions.append({
                                "type": "moderate_temperature",
                                "severity": "medium",
                                "description": f"Elevated temperature detected: {sensor['label']} at {sensor['current']}°C",
                                "recommendation": "Check for airflow issues or high utilization"
                            })
            
            # Battery optimization (if available)
            if status["battery"]["success"] and not status["battery"].get("power_plugged"):
                if status["battery"]["percent"] < 20:
                    suggestions.append({
                        "type": "low_battery",
                        "severity": "high",
                        "description": f"Battery is low ({status['battery']['percent']}%)",
                        "recommendation": "Connect to power source"
                    })
            
            return {"success": True, "suggestions": suggestions}
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _add_to_history(self, category: str, data_point: Dict[str, Any]) -> None:
        """Add a data point to historical data with timestamps.
        
        Args:
            category: Category of data (cpu, memory, etc.)
            data_point: Data point to add
        """
        if category in self.history:
            self.history[category].append(data_point)
            
            # Keep history size limited
            while len(self.history[category]) > self.max_history_points:
                self.history[category].pop(0)
    
    def get_history(self, category: str = None) -> Dict[str, Any]:
        """Get historical data for visualization.
        
        Args:
            category: Category to get history for (None for all)
            
        Returns:
            Dictionary with historical data
        """
        if category:
            if category in self.history:
                return {"success": True, category: self.history[category]}
            else:
                return {"success": False, "error": f"Category {category} not found"}
        else:
            return {"success": True, "history": self.history}
    
    def _parse_size_string(self, size_str: str) -> int:
        """Parse a human-readable size string into bytes.
        
        Args:
            size_str: Size string like "4.2M" or "1.5G"
            
        Returns:
            Size in bytes
        """
        try:
            # Try to convert directly to float if it's just a number
            size_bytes = float(size_str)
            return int(size_bytes)
        except ValueError:
            pass
            
        # Otherwise, parse with unit
        multipliers = {
            'K': 1024,
            'M': 1024**2,
            'G': 1024**3,
            'T': 1024**4,
            'P': 1024**5
        }
        
        size_str = size_str.upper()
        
        for unit, multiplier in multipliers.items():
            if unit in size_str:
                try:
                    value = float(size_str.replace(unit, ''))
                    return int(value * multiplier)
                except ValueError:
                    continue
        
        # If we couldn't parse, return 0
        return 0
    
    def _format_size(self, size_bytes: int) -> str:
        """Format a size in bytes to a human-readable string.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/1024**2:.1f} MB"
        elif size_bytes < 1024**4:
            return f"{size_bytes/1024**3:.1f} GB"
        else:
            return f"{size_bytes/1024**4:.1f} TB"

# Create an instance of the system monitor
system_monitor = SystemMonitor() 