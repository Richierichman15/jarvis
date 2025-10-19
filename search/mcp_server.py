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
    import time
    # Add cache-busting parameters to get fresh results
    params = {
        "q": query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
        "when": "1d",  # Last 24 hours
        "_": str(int(time.time())),  # Cache buster
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Accept": "application/rss+xml, application/xml, text/xml",
    }
    
    # Try multiple endpoints for better results
    endpoints = [
        "https://news.google.com/rss/search",
        "https://news.google.com/rss/headlines",
    ]
    
    for endpoint in endpoints:
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                content = response.text
                
                # Check if we got actual content
                if content and len(content) > 100:
                    return content
                    
        except Exception as e:
            print(f"Failed to fetch from {endpoint}: {e}")
            continue
    
    # Fallback: try without cache busting
    try:
        fallback_params = {
            "q": query,
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        }
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            response = await client.get("https://news.google.com/rss/search", params=fallback_params)
            response.raise_for_status()
            return response.text
    except Exception as e:
        raise Exception(f"All news sources failed: {e}")


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
        pub_date = (item.findtext("pubDate") or "").strip()
        
        if title and link:
            result = {
                "title": title,
                "url": link,
                "snippet": description,
            }
            if pub_date:
                result["published"] = pub_date
            results.append(result)

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
        import datetime
        feed_xml = await _fetch_google_news(query)
        results = _extract_results(feed_xml)
        
        # Add metadata about the search
        search_metadata = {
            "query": query,
            "results": results,
            "search_timestamp": datetime.datetime.now().isoformat(),
            "results_count": len(results),
            "source": "Google News RSS"
        }
        
        return [
            TextContent(
                type="text",
                text=json.dumps(search_metadata, indent=2, ensure_ascii=False),
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
