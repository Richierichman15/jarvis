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
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _default_server_path() -> Path:
    # Default to the Jarvis stdio server at repo root
    return Path(__file__).resolve().parent.parent / "run_mcp_server.py"


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


class RunToolRequest(BaseModel):
    tool: str
    args: Dict[str, Any] = {}


def create_app() -> FastAPI:
    server_env = os.environ.get("MCP_SERVER_PATH")
    server_path = Path(server_env) if server_env else _default_server_path()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Start server subprocess and hold open a session for app lifetime
        params = StdioServerParameters(command=sys.executable, args=[str(server_path)])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                app.state.session = session
                await session.initialize()
                yield
                # Contexts close automatically here

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

    @app.get("/tools")
    async def list_tools():
        session: ClientSession = app.state.session
        tools_resp = await session.list_tools()
        out: List[Dict[str, Any]] = []
        for t in tools_resp.tools:
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
            })
        return out

    @app.post("/run-tool")
    async def run_tool(req: RunToolRequest):
        session: ClientSession = app.state.session
        try:
            result = await session.call_tool(req.tool, req.args or {})
            return {"ok": True, "result": _result_to_json(result)}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/run-plan")
    async def run_plan(body: Any = Body(...)):
        session: ClientSession = app.state.session

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
                def __init__(self, _session: ClientSession):
                    self._session = _session

                async def call_tool_server(self, server, tool, args):
                    if server not in (None, "", "jarvis"):
                        raise HTTPException(status_code=400, detail="server routing not supported in HTTP API")
                    return await self._session.call_tool(tool, args or {})

            router = _Router(session)
            results = await execute_plan(steps, router)
            # results already contain normalized data strings
            return results
        except Exception:
            # Fallback: sequential execution
            out: List[Dict[str, Any]] = []
            for s in steps:
                tool = (s or {}).get("tool")
                args = (s or {}).get("args") or {}
                if not tool:
                    out.append({"tool": None, "ok": False, "error": "missing tool name"})
                    continue
                try:
                    res = await session.call_tool(tool, args)
                    out.append({"tool": tool, "ok": True, "data": _result_to_json(res)})
                except Exception as e:
                    out.append({"tool": tool, "ok": False, "error": str(e)})
            return out

    return app


# For local testing: uvicorn client.api:create_app --factory --port 8000
