"""Extract stock/crypto tickers from natural-language queries."""

from __future__ import annotations

import re
from typing import Any, Dict, List

_TICKER_STOPWORDS = frozenset({
    "THE", "AND", "FOR", "WHAT", "HOW", "WHEN", "WHERE", "WHY", "WHO", "WITH",
    "FROM", "THIS", "THAT", "THESE", "THOSE", "PRICE", "CURRENT", "GET", "SHOW",
    "CHECK", "FIND", "LOOK", "SEE", "TRADING", "STOCK", "MARKET", "QUOTE",
    "WORTH", "AT", "IS", "IT", "AN", "OR", "TO", "ON", "IN", "MY", "ME", "US",
    "ARE", "WAS", "HAS", "HAD", "CAN", "MAY", "NEW", "OLD", "TOP", "ALL",
})

_SYMBOL_TOOLS = frozenset({
    "trading.get_quote",
    "trading.get_snapshot",
    "trading.get_bars",
    "trading.search_symbols",
})


def extract_ticker_symbols(text: str) -> List[str]:
    """Return ticker candidates, best match first.

    Prefer user-typed ALL-CAPS tokens (e.g. AAPL in "what's AAPL trading at") so
    apostrophe fragments like the S in WHAT'S are ignored.
    """
    found: List[str] = []
    for match in re.findall(r"\b([A-Z]{1,5})\b", text):
        if match not in _TICKER_STOPWORDS and match not in found:
            found.append(match)
    if found:
        return sorted(found, key=len, reverse=True)

    for match in re.findall(r"\b([A-Z]{2,5})\b", text.upper()):
        if match not in _TICKER_STOPWORDS and match not in found:
            found.append(match)
    return sorted(found, key=len, reverse=True)


def enrich_trading_arguments(
    tool_name: str,
    arguments: Dict[str, Any] | None,
    user_text: str,
) -> Dict[str, Any]:
    """Fill missing trading tool args (especially symbol) from the user's message."""
    args = dict(arguments or {})
    if not tool_name.startswith("trading."):
        return args

    if not args.get("symbol"):
        for key in ("ticker", "stock", "sym"):
            if args.get(key):
                args["symbol"] = str(args[key]).strip().upper()
                break

    if tool_name in _SYMBOL_TOOLS and not args.get("symbol"):
        symbols = extract_ticker_symbols(user_text)
        if symbols:
            args["symbol"] = symbols[0]

    if tool_name == "trading.get_momentum" and not args.get("symbols"):
        symbols = extract_ticker_symbols(user_text)
        if symbols:
            args["symbols"] = symbols[:10]
        elif args.get("symbol"):
            args["symbols"] = [str(args["symbol"]).strip().upper()]

    return args
