"""
Jarvis Monitoring Package

This package provides comprehensive system monitoring capabilities for Jarvis,
including real-time metrics collection, health monitoring, and Discord notifications.

Modules:
    system_monitor: Core system monitoring with self-awareness
    diagnostics_dashboard: Web-based dashboard for system diagnostics
"""

from .system_monitor import SystemMonitor, start_system_monitoring, get_system_monitor, stop_system_monitoring
from .diagnostics_dashboard import DiagnosticsDashboard

__all__ = [
    'SystemMonitor',
    'start_system_monitoring', 
    'get_system_monitor',
    'stop_system_monitoring',
    'DiagnosticsDashboard'
]
