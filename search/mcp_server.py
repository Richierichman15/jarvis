#!/usr/bin/env python3
"""Minimal MCP server exposing Google News-backed web search."""

from __future__ import annotations

import asyncio
import json
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

SERVER = Server("search-mcp-server")
RESULT_LIMIT = 10


async def _fetch_google_news(query: str) -> str:
    params = {
        "q": query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    }
    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "JarvisSearchMCP/1.0"}) as client:
        response = await client.get("https://news.google.com/rss/search", params=params)
        response.raise_for_status()
        return response.text


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    return re.sub(r"\s+", " ", text).strip()


def _extract_results(feed_xml: str) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    try:
        root = ET.fromstring(feed_xml)
    except ET.ParseError:
        return results

    channel = root.find("channel")
    if channel is None:
        return results

    for item in channel.findall("item")[:RESULT_LIMIT]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = _strip_html(item.findtext("description") or "")
        if title and link:
            results.append({
                "title": title,
                "url": link,
                "snippet": description,
            })

    return results


@SERVER.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="web.search",
            description="Search recent news via Google News RSS feed and return top results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        )
    ]


@SERVER.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name != "web.search":
        raise ValueError(f"Unknown tool: {name}")

    query = (arguments or {}).get("query", "").strip()
    if not query:
        return [TextContent(type="text", text="Error: 'query' parameter is required")]

    try:
        feed_xml = await _fetch_google_news(query)
        results = _extract_results(feed_xml)
        return [
            TextContent(
                type="text",
                text=json.dumps({"query": query, "results": results}, indent=2, ensure_ascii=False),
            )
        ]
    except Exception as exc:  # pragma: no cover - network errors are reported as text
        return [
            TextContent(
                type="text",
                text=f"Search failed: {exc}",
            )
        ]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await SERVER.run(read_stream, write_stream, SERVER.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
