"""
Start and stop the Ollama server alongside Jarvis (e.g. Discord bot).

Only stops a process this module started — if Ollama was already running, we leave it alone.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

# Common Windows install location (not always on PATH)
_WINDOWS_OLLAMA_CANDIDATES = (
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
    Path("C:/Program Files/Ollama/ollama.exe"),
)


def find_ollama_executable() -> Optional[str]:
    """Resolve ollama.exe / ollama binary."""
    env_exe = os.environ.get("OLLAMA_EXE")
    if env_exe and Path(env_exe).is_file():
        return str(Path(env_exe).resolve())

    which = shutil.which("ollama")
    if which:
        return which

    if sys.platform == "win32":
        for candidate in _WINDOWS_OLLAMA_CANDIDATES:
            if candidate.is_file():
                return str(candidate.resolve())

    return None


class OllamaLifecycle:
    """Manage an Ollama ``serve`` subprocess for the lifetime of a Jarvis process."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self._process: Optional[subprocess.Popen] = None
        self._started_by_us = False

    async def is_api_reachable(self, timeout: float = 3.0) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/version",
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def wait_until_ready(self, timeout: float = 90.0) -> bool:
        """Poll until Ollama HTTP API responds."""
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            if await self.is_api_reachable():
                logger.info("Ollama API is ready at %s", self.base_url)
                return True
            await asyncio.sleep(1.0)
        logger.error("Timed out waiting for Ollama at %s", self.base_url)
        return False

    async def start(self) -> bool:
        """Ensure Ollama is running; start ``serve`` if needed."""
        if await self.is_api_reachable():
            logger.info("Ollama already running at %s (will not stop on exit)", self.base_url)
            return True

        exe = find_ollama_executable()
        if not exe:
            logger.error(
                "Ollama is not running and ollama.exe was not found. "
                "Install Ollama or set OLLAMA_EXE in .env"
            )
            return False

        logger.info("Starting Ollama: %s serve", exe)
        try:
            creationflags = 0
            if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
                creationflags = subprocess.CREATE_NO_WINDOW

            self._process = subprocess.Popen(
                [exe, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
            self._started_by_us = True
        except Exception as exc:
            logger.error("Failed to start Ollama: %s", exc)
            return False

        return await self.wait_until_ready()

    async def stop(self) -> None:
        """Stop Ollama only if this module started it."""
        if not self._started_by_us or self._process is None:
            return

        logger.info("Stopping Ollama (started by Jarvis)...")
        try:
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        except Exception as exc:
            logger.warning("Error stopping Ollama: %s", exc)
        finally:
            self._process = None
            self._started_by_us = False
            logger.info("Ollama stopped")
