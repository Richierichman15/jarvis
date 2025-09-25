"""Simple JSON-backed persistence for the Jarvis MCP client.

Stores a dict of projects to a JSON file so the client can remember
registrations across runs. This is intentionally light-weight for now;
we can switch to SQLite later without changing callers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


DEFAULT_FILE = ".jarvis_projects.json"
DEFAULT_SERVERS_FILE = ".jarvis_servers.json"


def load_projects(filepath: str = DEFAULT_FILE) -> Dict[str, dict]:
    """Load projects from JSON file.

    Args:
        filepath: Path to the JSON file. Defaults to `.jarvis_projects.json` in CWD.

    Returns:
        Dict of projects; empty dict if file missing or invalid.
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return {}
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        # On any error, return empty and let caller proceed
        return {}


def save_projects(projects: Dict[str, dict], filepath: str = DEFAULT_FILE) -> None:
    """Persist projects dict to JSON file (atomic-ish write).

    Args:
        projects: Dict of project entries.
        filepath: Path to write JSON into.
    """
    path = Path(filepath)
    path.write_text(json.dumps(projects, indent=2, sort_keys=True))


def load_servers(filepath: str = DEFAULT_SERVERS_FILE) -> Dict[str, dict]:
    """Load saved MCP server connections (alias -> {command, args})."""
    try:
        path = Path(filepath)
        if not path.exists():
            return {}
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}


def save_servers(servers: Dict[str, dict], filepath: str = DEFAULT_SERVERS_FILE) -> None:
    """Persist saved MCP server connections."""
    path = Path(filepath)
    path.write_text(json.dumps(servers, indent=2, sort_keys=True))
