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

from fastapi import FastAPI, HTTPException
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

    return app


# For local testing: uvicorn client.api:create_app --factory --port 8000
