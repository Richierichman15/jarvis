"""
Orchestrator executor for multi-tool plans.

execute_plan(steps, mcp_client) -> list[dict]
 - steps: list of dicts { server?: str, tool: str, args: dict, parallel?: bool }
 - mcp_client: object with async method call_tool_server(server, tool, args)

Runs sequentially by default. If consecutive steps have parallel=True,
they are grouped and executed concurrently. Retries each failed step up to
2 times with exponential backoff. Returns per-step structured results:
{ tool, ok: bool, data?: any, error?: str } in the same order as submitted
(for parallel groups, returned in the original ordering).
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List


async def _run_with_retries(
    mcp_client,
    server: str | None,
    tool: str,
    args: Dict[str, Any],
    max_retries: int = 2,
) -> Dict[str, Any]:
    attempt = 0
    delay = 0.5
    while True:
        try:
            # Delegate to the client's router so it can choose the server
            result = await mcp_client.call_tool_server(server, tool, args or {})
            return {"tool": tool, "ok": True, "data": _normalize_result(result)}
        except Exception as e:
            if attempt >= max_retries:
                return {"tool": tool, "ok": False, "error": str(e)}
            await asyncio.sleep(delay)
            delay *= 2
            attempt += 1


def _normalize_result(result: Any) -> Any:
    # Try to extract user-friendly text if it looks like an MCP ToolResponse
    try:
        if hasattr(result, "content") and result.content is not None:
            texts = []
            for c in result.content:
                if hasattr(c, "text") and getattr(c, "text"):
                    texts.append(getattr(c, "text"))
                elif isinstance(c, dict) and c.get("text"):
                    texts.append(str(c.get("text")))
            if texts:
                return "\n".join(texts)
        # If it's a list of TextContent-like objects
        if isinstance(result, list):
            texts = []
            for c in result:
                if hasattr(c, "text") and getattr(c, "text"):
                    texts.append(getattr(c, "text"))
                elif isinstance(c, dict) and c.get("text"):
                    texts.append(str(c.get("text")))
                else:
                    # Fallback to string repr
                    texts.append(str(c))
            return "\n".join([t for t in texts if t])
        return result
    except Exception:
        return str(result)


async def execute_plan(steps: List[Dict[str, Any]], mcp_client) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    i = 0
    n = len(steps)
    while i < n:
        step = steps[i] or {}
        is_parallel = bool(step.get("parallel"))
        if not is_parallel:
            # Run sequential step
            res = await _run_with_retries(
                mcp_client,
                step.get("server"),
                step.get("tool", ""),
                step.get("args") or {},
            )
            results.append(res)
            i += 1
            continue

        # Collect a batch of consecutive parallel steps
        batch: List[Dict[str, Any]] = [step]
        j = i + 1
        while j < n and bool((steps[j] or {}).get("parallel")):
            batch.append(steps[j] or {})
            j += 1

        # Launch all in parallel, preserving order
        coros = [
            _run_with_retries(
                mcp_client,
                s.get("server"),
                s.get("tool", ""),
                s.get("args") or {},
            )
            for s in batch
        ]
        batch_results = await asyncio.gather(*coros, return_exceptions=False)
        results.extend(batch_results)
        i = j

    return results
