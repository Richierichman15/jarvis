"""FastAPI layer exposing the MCP client as HTTP endpoints.

Routes
- GET /tools → list available tools
- POST /run-tool → {"tool": "<name>", "args": {...}} → runs a tool

Design
- Uses the same stdio transport to spawn the MCP server subprocess.
- Keeps a single long-lived MCP session for the app lifespan.
- Reads server path from env MCP_SERVER_PATH; falls back to Jarvis default.
"""

from __future__ import annotations

import os
import sys
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
import contextlib
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from client.storage import load_servers as load_saved_servers, save_servers


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_server_path() -> Path:
    # Default to the Jarvis stdio server at repo root
    return _project_root() / "run_mcp_server.py"


def _resolve_python_executable() -> str:
    """Use a concrete Windows-friendly path for subprocess spawning."""
    exe = Path(sys.executable)
    if exe.is_file():
        return str(exe.resolve())
    return sys.executable


# Environment variables that can silently break a freshly spawned interpreter
# when inherited from an interactive shell (e.g. Git Bash / MSYS), causing the
# MCP child to die before it can emit any diagnostics.
_PYTHON_ENV_TO_STRIP = (
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONSTARTUP",
    "PYTHONEXECUTABLE",
    "PYTHONNOUSERSITE",
    "PYTHONCASEOK",
)


def _build_child_env() -> Dict[str, str]:
    """Return a sanitized environment for the Jarvis MCP child process.

    Strips inherited Python vars that can break a fresh interpreter and pins the
    venv / base interpreter directories to the FRONT of PATH so that an active
    conda base or another shell cannot shadow the venv's native DLLs (which
    would otherwise crash the child on import before it can print anything).
    """
    child_env = dict(os.environ)
    for key in _PYTHON_ENV_TO_STRIP:
        child_env.pop(key, None)
    child_env["JARVIS_MCP_STDIO_CHILD"] = "1"
    child_env["PYTHONUNBUFFERED"] = "1"
    # Force UTF-8 stdio so JSON-RPC framing is never corrupted by a locale
    # that defaults to cp1252 (common on Windows / MSYS).
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"

    exe = Path(_resolve_python_executable())
    priority_dirs = [
        str(exe.parent),                 # .venv/Scripts (or bin)
        str(Path(sys.base_prefix)),      # base interpreter (python3xx.dll lives here)
        str(Path(sys.base_prefix) / "Scripts"),
        str(Path(sys.base_prefix) / "DLLs"),
    ]
    existing_path = child_env.get("PATH", "")
    seen = set()
    ordered: List[str] = []
    for part in priority_dirs + existing_path.split(os.pathsep):
        if part and part not in seen and Path(part).exists():
            seen.add(part)
            ordered.append(part)
    child_env["PATH"] = os.pathsep.join(ordered)
    return child_env


def _jarvis_stdio_params(user_name: str = "Boss") -> StdioServerParameters:
    """Build stdio params for the Jarvis MCP child process."""
    root = _project_root()
    server_env = os.environ.get("MCP_SERVER_PATH")
    server_path = Path(server_env) if server_env else _default_server_path()
    return StdioServerParameters(
        command=_resolve_python_executable(),
        args=["-u", str(server_path.resolve()), user_name],
        cwd=str(root),
        env=_build_child_env(),
    )


async def preflight_jarvis_mcp() -> None:
    """Verify the Jarvis MCP child can start before binding the HTTP port.

    Captures the child's stderr so that, if it dies during startup, the real
    Python traceback is surfaced instead of an opaque "Connection closed".
    """
    import tempfile

    params = _jarvis_stdio_params()
    server_script = params.args[1] if len(params.args) > 1 else "?"
    print(f"Preflight MCP: python={params.command}")
    print(f"Preflight MCP: script={server_script}")
    print(f"Preflight MCP: cwd={params.cwd}")
    mcp_path = os.environ.get("MCP_SERVER_PATH")
    if mcp_path:
        print(f"Preflight MCP: MCP_SERVER_PATH={mcp_path}")
    if not Path(server_script).is_file():
        raise RuntimeError(f"MCP server script not found: {server_script}")

    err_path = Path(tempfile.gettempdir()) / "jarvis_mcp_preflight.err.log"
    err_file = open(err_path, "w+", encoding="utf-8", errors="replace")
    try:
        async with stdio_client(params, errlog=err_file) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
        print("Preflight MCP: Jarvis connection OK")
    except BaseException as exc:
        try:
            err_file.flush()
            err_file.seek(0)
            child_err = err_file.read().strip()
        except Exception:
            child_err = ""
        if child_err:
            print("\n--- Jarvis MCP child output (stderr) ---")
            print(child_err[-4000:])
            print("--- end child output ---")
        else:
            print("\n(The MCP child produced no stderr output before exiting.)")
        raise RuntimeError(f"{type(exc).__name__}: {exc}") from exc
    finally:
        try:
            err_file.close()
        except Exception:
            pass


def _extract_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    if hasattr(result, 'content') and getattr(result, 'content') is not None:
        texts: List[str] = []
        for content in result.content:
            if hasattr(content, 'text'):
                texts.append(getattr(content, 'text') or '')
            elif isinstance(content, dict) and 'text' in content:
                texts.append(str(content.get('text') or ''))
        return "\n".join(t for t in texts if t)
    return str(result)


def _result_to_json(result: Any) -> Dict[str, Any]:
    # Normalize MCP tool result to a JSON-friendly shape
    if isinstance(result, str):
        return {"type": "text", "text": result}
    if hasattr(result, 'content') and getattr(result, 'content') is not None:
        items: List[Dict[str, Any]] = []
        for content in result.content:
            if hasattr(content, 'text'):
                items.append({"type": "text", "text": getattr(content, 'text')})
            elif isinstance(content, dict) and 'text' in content:
                items.append({"type": "text", "text": content.get('text')})
            elif hasattr(content, 'data') or (isinstance(content, dict) and 'data' in content):
                mime = getattr(content, 'mimeType', None)
                if mime is None and isinstance(content, dict):
                    mime = content.get('mimeType')
                items.append({"type": "data", "mimeType": mime or 'application/octet-stream'})
            else:
                items.append({"type": "unknown", "value": str(content)})
        return {"type": "content_list", "items": items, "text": "\n".join(i.get('text','') for i in items if i.get('type')=='text')}
    # Fallback
    return {"type": "unknown", "value": str(result)}


def _normalize_mcp_result(result: Any) -> str:
    if isinstance(result, str):
        return result
    if hasattr(result, 'content') and getattr(result, 'content') is not None:
        texts: List[str] = []
        for content in result.content:
            if hasattr(content, 'text'):
                texts.append(getattr(content, 'text') or '')
            elif isinstance(content, dict) and 'text' in content:
                texts.append(str(content.get('text') or ''))
        joined = "\n".join(t for t in texts if t)
        if joined:
            return joined[:5000]
    try:
        dumped = json.dumps(result, ensure_ascii=False)
    except Exception:
        dumped = str(result)
    return dumped[:5000]


def _server_entry_usable(entry: Dict[str, Any]) -> bool:
    """Return False when a saved MCP server points at missing binaries/paths."""
    command = entry.get("command")
    if not command:
        return False
    cmd_path = Path(str(command))
    if cmd_path.suffix.lower() in {".exe", ".cmd", ".bat"} and not cmd_path.is_file():
        return False
    cwd = entry.get("cwd")
    if cwd and not Path(str(cwd)).exists():
        return False
    args = entry.get("args") or []
    if args:
        script = Path(str(args[-1]))
        if script.suffix.lower() == ".py" and not script.is_file():
            return False
    return True


class SessionManager:
    def __init__(self, default_params: StdioServerParameters, saved_servers: Dict[str, Dict[str, Any]]) -> None:
        self.default_alias = "jarvis"
        self.default_params = default_params
        self.saved_servers = saved_servers or {}
        self.sessions: Dict[str, ClientSession] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.tools_cache: Dict[str, Dict[str, Any]] = {}
        self.runtime_params: Dict[str, Dict[str, Any]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def start(self) -> None:
        await self.ensure_session(self.default_alias, force_default=True)
        logger.info("✅ Connected server '%s'", self.default_alias)
        
        for alias, entry in self.saved_servers.items():
            if alias == self.default_alias:
                continue
            if not isinstance(entry, dict) or not _server_entry_usable(entry):
                logger.warning("Skipping saved server '%s': command or script path not found on this machine", alias)
                continue
            try:
                await self.ensure_session(alias)
                logger.info("✅ Connected server '%s'", alias)
            except Exception as exc:
                logger.warning("❌ Failed to auto-connect server '%s': %s", alias, exc)
                # Log the full exception details for debugging
                import traceback
                logger.debug("Full traceback for server '%s':\n%s", alias, traceback.format_exc())

    async def shutdown(self) -> None:
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self.sessions.clear()
        self.tasks.clear()
        self.tools_cache.clear()
        self.runtime_params.clear()

    def list_aliases(self) -> List[str]:
        aliases = list(self.sessions.keys())
        if self.default_alias not in aliases:
            aliases.insert(0, self.default_alias)
        return sorted(set(aliases), key=lambda a: (0 if a == self.default_alias else 1, a))

    async def ensure_session(self, alias: str, force_default: bool = False) -> ClientSession:
        if alias in self.sessions:
            return self.sessions[alias]
        lock = self._locks.setdefault(alias, asyncio.Lock())
        async with lock:
            if alias in self.sessions:
                return self.sessions[alias]
            params = self._resolve_params(alias, force_default)
            await self._spawn_and_hold(alias, params)
            if alias not in self.sessions:
                raise RuntimeError(f"Failed to start session '{alias}'")
            return self.sessions[alias]

    def _resolve_params(self, alias: str, force_default: bool = False) -> StdioServerParameters:
        if alias == self.default_alias or force_default:
            return self.default_params
        entry = self.saved_servers.get(alias)
        if not entry:
            raise RuntimeError(f"Unknown server alias '{alias}'")
        command = entry.get("command")
        if not command:
            raise RuntimeError(f"Saved server '{alias}' missing command")
        args = entry.get("args") or []
        return StdioServerParameters(command=command, args=args)

    async def _spawn_and_hold(self, alias: str, params: StdioServerParameters) -> None:
        existing = self.tasks.get(alias)
        if existing is not None:
            if not existing.done():
                raise RuntimeError(f"Server alias '{alias}' already connected")
            self.tasks.pop(alias, None)

        ready: asyncio.Future = asyncio.get_running_loop().create_future()

        self.runtime_params[alias] = {
            "command": params.command,
            "args": list(params.args or []),
            "cwd": str(params.cwd) if params.cwd else None,
            "env": dict(params.env) if params.env else None,
        }

        import tempfile

        err_path = Path(tempfile.gettempdir()) / f"jarvis_mcp_{alias}.err.log"

        async def runner() -> None:
            err_file = open(err_path, "w+", encoding="utf-8", errors="replace")
            try:
                async with stdio_client(params, errlog=err_file) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        self.sessions[alias] = session
                        self.tools_cache.pop(alias, None)
                        if not ready.done():
                            ready.set_result(None)
                        while True:
                            await asyncio.sleep(3600)
            except Exception as exc:
                if not ready.done():
                    ready.set_exception(exc)
                logger.warning("Session '%s' stopped: %s", alias, exc)
                # Surface the child's own stderr so the real cause is visible.
                try:
                    err_file.flush()
                    err_file.seek(0)
                    child_err = err_file.read().strip()
                except Exception:
                    child_err = ""
                if child_err:
                    logger.error("Child stderr for session '%s':\n%s", alias, child_err[-4000:])
                import traceback
                logger.error("Full error for session '%s':\n%s", alias, traceback.format_exc())
            finally:
                try:
                    err_file.close()
                except Exception:
                    pass
                self.sessions.pop(alias, None)
                self.tools_cache.pop(alias, None)
                self.runtime_params.pop(alias, None)

        task = asyncio.create_task(runner(), name=f"mcp-session:{alias}")
        self.tasks[alias] = task
        await ready

    async def get_session(self, alias: str) -> ClientSession:
        return await self.ensure_session(alias)

    async def call_tool(self, alias: str, tool: str, args: Dict[str, Any]) -> Any:
        # Try up to 2 times (original + 1 retry on session closed)
        for attempt in range(2):
            try:
                session = await self.ensure_session(alias)
                return await session.call_tool(tool, args or {})
            except Exception as e:
                error_msg = str(e).lower()
                # Check if session is closed and we haven't retried yet
                if ("closed" in error_msg or "connection" in error_msg) and attempt == 0:
                    logger.warning(f"Session '{alias}' closed or disconnected, attempting to reconnect...")
                    # Remove the closed session so ensure_session will create a new one
                    self.sessions.pop(alias, None)
                    self.tasks.pop(alias, None)
                    self.tools_cache.pop(alias, None)
                    await asyncio.sleep(0.5)  # Brief delay before retry
                    continue
                # If it's not a connection error or we already retried, re-raise
                raise

    async def list_tools_cached(self, alias: str) -> List[Any]:
        await self.ensure_session(alias)
        cache = self.tools_cache.setdefault(alias, {"data": None, "expires": 0.0})
        now = time.time()
        if cache["data"] is None or now >= cache["expires"]:
            response = await self.sessions[alias].list_tools()
            cache["data"] = response.tools
            cache["expires"] = now + 60.0
        return cache["data"]

    def get_server_entry(self, alias: str) -> Dict[str, Any]:
        saved_entry = self.saved_servers.get(alias, {})
        runtime_entry = self.runtime_params.get(alias, {})
        connected = alias in self.sessions
        entry: Dict[str, Any] = {
            "alias": alias,
            "connected": connected,
            "default": alias == self.default_alias,
            "saved": alias in self.saved_servers,
            "command": runtime_entry.get("command") or saved_entry.get("command"),
            "args": runtime_entry.get("args") or saved_entry.get("args") or [],
            "cwd": runtime_entry.get("cwd") or saved_entry.get("cwd"),
            "env": runtime_entry.get("env") or saved_entry.get("env"),
            "status": "connected" if connected else ("saved" if alias in self.saved_servers else "unknown"),
        }
        return entry

    def list_servers(self) -> List[Dict[str, Any]]:
        known_aliases = set(self.sessions.keys()) | set(self.saved_servers.keys()) | {self.default_alias}
        return [self.get_server_entry(alias) for alias in sorted(known_aliases)]

    async def connect_server(
        self,
        alias: str,
        command: str,
        args: Optional[List[str]] = None,
        *,
        save: bool = True,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        alias = alias.strip()
        if not alias:
            raise RuntimeError("Alias is required")
        if alias == self.default_alias:
            raise RuntimeError("Use the default session without reconnecting it explicitly")
        if alias in self.tasks and alias in self.sessions and not self.tasks[alias].done():
            raise RuntimeError(f"Server alias '{alias}' already connected")

        command = command.strip()
        if not command:
            raise RuntimeError("Command is required")

        arg_list = list(args or [])
        params = StdioServerParameters(command=command, args=arg_list, cwd=cwd, env=env)
        await self._spawn_and_hold(alias, params)

        if save:
            entry: Dict[str, Any] = {"command": command, "args": arg_list}
            if cwd:
                entry["cwd"] = cwd
            if env:
                entry["env"] = env
            self.saved_servers[alias] = entry
            save_servers(self.saved_servers)

        return self.get_server_entry(alias)

    async def disconnect_server(self, alias: str, *, forget: bool = False) -> None:
        alias = alias.strip()
        if not alias:
            raise RuntimeError("Alias is required")
        if alias == self.default_alias:
            raise RuntimeError("Cannot disconnect the default Jarvis server")

        task = self.tasks.get(alias)
        was_saved = alias in self.saved_servers
        was_connected = alias in self.sessions or task is not None

        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        self.sessions.pop(alias, None)
        self.tasks.pop(alias, None)
        self.tools_cache.pop(alias, None)
        self.runtime_params.pop(alias, None)

        if forget and was_saved:
            self.saved_servers.pop(alias, None)
            save_servers(self.saved_servers)

        if not was_connected and not was_saved:
            raise RuntimeError(f"Server '{alias}' not connected")


class RunToolRequest(BaseModel):
    tool: str
    args: Dict[str, Any] = {}
    server: Optional[str] = None


class ConnectServerRequest(BaseModel):
    alias: str
    command: str
    args: List[str] = Field(default_factory=list)
    save: bool = True
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None


class DisconnectServerRequest(BaseModel):
    alias: str
    forget: bool = False


def create_app() -> FastAPI:
    default_params = _jarvis_stdio_params()
    saved_servers = {
        alias: entry
        for alias, entry in load_saved_servers().items()
        if isinstance(entry, dict) and _server_entry_usable(entry)
    }

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        manager = SessionManager(default_params, saved_servers)
        await manager.start()
        app.state.manager = manager
        try:
            yield
        finally:
            await manager.shutdown()

    app = FastAPI(lifespan=lifespan)

    # Enable CORS for common local dev ports (e.g., Vite)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/servers")
    async def list_servers():
        manager: SessionManager = app.state.manager
        return {"default": manager.default_alias, "servers": manager.list_servers()}

    @app.post("/servers/connect")
    async def connect_server(req: ConnectServerRequest):
        manager: SessionManager = app.state.manager
        try:
            entry = await manager.connect_server(
                req.alias,
                req.command,
                req.args,
                save=req.save,
                cwd=req.cwd,
                env=req.env,
            )
            return {"ok": True, "server": entry}
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/servers/disconnect")
    async def disconnect_server(req: DisconnectServerRequest):
        manager: SessionManager = app.state.manager
        try:
            await manager.disconnect_server(req.alias, forget=req.forget)
            return {"ok": True}
        except RuntimeError as exc:
            message = str(exc)
            status = 404 if "not connected" in message.lower() else 400
            raise HTTPException(status_code=status, detail=message)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.get("/tools")
    async def list_tools(server: Optional[str] = None):
        manager: SessionManager = app.state.manager
        alias = server or manager.default_alias
        try:
            tools = await manager.list_tools_cached(alias)
        except RuntimeError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        out: List[Dict[str, Any]] = []
        for t in tools:
            # Try to serialize schema
            schema = getattr(t, 'inputSchema', None)
            if schema is not None and not isinstance(schema, dict):
                # best effort: use attributes if available
                schema = {
                    "properties": getattr(schema, 'properties', None) or {},
                    "required": getattr(schema, 'required', None) or [],
                }
            out.append({
                "name": t.name,
                "description": t.description,
                "inputSchema": schema,
                "server": alias,
            })
        return out

    @app.post("/run-tool")
    async def run_tool(req: RunToolRequest):
        manager: SessionManager = app.state.manager
        alias = req.server or manager.default_alias
        try:
            result = await manager.call_tool(alias, req.tool, req.args or {})
            return {"ok": True, "server": alias, "tool": req.tool, "result": _result_to_json(result)}
        except RuntimeError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/run-plan")
    async def run_plan(body: Any = Body(...)):
        manager: SessionManager = app.state.manager

        # Accept either {"steps": [...]} or a bare list
        if isinstance(body, dict) and "steps" in body:
            steps = body["steps"]
        elif isinstance(body, list):
            steps = body
        else:
            raise HTTPException(status_code=400, detail="Expected request body to be {\"steps\": [...]} or a JSON array of steps")

        if not isinstance(steps, list):
            raise HTTPException(status_code=400, detail="steps must be a list")

        # If any step attempts server routing, reject with a clear message
        for s in steps:
            if isinstance(s, dict) and s.get("server") not in (None, "", "jarvis"):
                raise HTTPException(status_code=400, detail="server routing not supported in HTTP API")

        # Prefer orchestrator if available for retries/parallelism; else simple loop
        try:
            from orchestrator.executor import execute_plan  # type: ignore

            class _Router:
                def __init__(self, _manager: SessionManager):
                    self._manager = _manager

                async def call_tool_server(self, server, tool, args):
                    alias = server or self._manager.default_alias
                    return await self._manager.call_tool(alias, tool, args or {})

            router = _Router(manager)
            results = await execute_plan(steps, router)
            for step, res in zip(steps, results):
                alias = (step or {}).get("server") or manager.default_alias
                res.setdefault("server", alias)
            return results
        except Exception:
            # Fallback: sequential execution
            out: List[Dict[str, Any]] = []
            for s in steps:
                alias = (s or {}).get("server") or manager.default_alias
                tool = (s or {}).get("tool")
                args = (s or {}).get("args") or {}
                if not tool:
                    out.append({"server": alias, "tool": None, "ok": False, "error": "missing tool name"})
                    continue
                try:
                    res = await manager.call_tool(alias, tool, args)
                    out.append({"server": alias, "tool": tool, "ok": True, "data": _result_to_json(res)})
                except Exception as e:
                    out.append({"server": alias, "tool": tool, "ok": False, "error": str(e)})
            return out

    @app.post("/nl")
    async def natural_language(payload: Dict[str, Any]):
        manager: SessionManager = app.state.manager
        message = (payload or {}).get("message")
        if not message or not isinstance(message, str):
            return {"text": "Sorry, that failed: message is required", "meta": {"routed_tool": None}}

        try:
            # Step 1: collect tools
            alias_order = manager.list_aliases()
            tools_map: Dict[str, Any] = {}
            tool_alias_map: Dict[str, str] = {}
            for alias in alias_order:
                try:
                    tool_list = await manager.list_tools_cached(alias)
                except Exception:
                    continue
                for tool_obj in tool_list:
                    if tool_obj.name not in tools_map:
                        tools_map[tool_obj.name] = tool_obj
                        tool_alias_map[tool_obj.name] = alias

            routed_tool = "jarvis_chat"
            routed_args: Dict[str, Any] = {"message": message}
            routed_alias = manager.default_alias

            # Step 2: try NL routing
            try:
                sys.path.append(str(Path(__file__).resolve().parent))
                from llm_router import route_natural_language  # type: ignore

                route_tool, route_args = route_natural_language(message, tools_map)
                if route_tool:
                    routed_tool = route_tool
                    routed_args = route_args or {}
                    routed_alias = tool_alias_map.get(route_tool, manager.default_alias)
            except Exception:
                routed_tool = "jarvis_chat"
                routed_args = {"message": message}
                routed_alias = manager.default_alias

            # Call routed tool
            raw_result = await manager.call_tool(routed_alias, routed_tool, routed_args)
            raw_text = _normalize_mcp_result(raw_result)
            raw_payload = _result_to_json(raw_result)
            data_payload = raw_payload.get("text") or raw_payload.get("value") or raw_payload
            if isinstance(data_payload, str):
                try:
                    data_payload = json.loads(data_payload)
                except Exception:
                    pass

            # Step 4: summarise via jarvis_chat
            summary_text = raw_text
            if SUMMARIZER_ENABLED and routed_tool != "jarvis_chat":
                summary_prompt = (
                    "Summarize this tool output for the user in 3-6 concise bullet points or 1 short paragraph. "
                    "Remove raw JSON. Answer directly and plainly. Output only the summary.\n\n---\n"
                    f"{raw_text[:2000]}"
                )
                summary_result = await manager.call_tool(manager.default_alias, "jarvis_chat", {"message": summary_prompt})
                summary_text = _normalize_mcp_result(summary_result) or raw_text

            return {
                "text": summary_text,
                "meta": {
                    "routed_tool": routed_tool,
                    "server": routed_alias,
                    "data": data_payload,
                },
            }
        except Exception as e:
            return {"text": f"Sorry, that failed: {e}", "meta": {"routed_tool": None}}

    return app


# For local testing: uvicorn client.api:create_app --factory --port 8000
SUMMARIZER_ENABLED = True
logger = logging.getLogger(__name__)
