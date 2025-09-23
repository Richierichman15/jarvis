"""
Fitness workouts helper.

Loads and caches workouts from jarvis/tools/workouts.json and exposes
utility functions for listing and searching.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@lru_cache(maxsize=1)
def _load_raw() -> Dict[str, Any]:
    """Load raw workouts JSON once and cache it."""
    here = Path(__file__).parent
    json_path = here / "workouts.json"
    if not json_path.exists():
        return {}
    return json.loads(json_path.read_text())


def _index_categories() -> List[Tuple[str, str, List[Dict[str, Any]]]]:
    """Return a list of (id_lower, name_lower, workouts) for matching."""
    raw = _load_raw()
    cats = raw.get("categories") if isinstance(raw, dict) else None
    out: List[Tuple[str, str, List[Dict[str, Any]]]] = []
    if isinstance(cats, list):
        for cat in cats:
            cid = str(cat.get("id", "")).strip()
            cname = str(cat.get("name", "")).strip()
            items = cat.get("workouts") or []
            if not isinstance(items, list):
                items = []
            out.append((cid.lower(), cname.lower(), items))
    return out


def list_workouts(muscle_group: Optional[str] = None) -> Dict[str, Any]:
    """List workouts.

    - If muscle_group is None, return the full source structure (categories).
    - Else, return {"muscle_group": <matched>, "workouts": [...]} with fuzzy matching
      over category id or name (case-insensitive, substring allowed).
    """
    if not muscle_group:
        return {"categories": _load_raw().get("categories", [])}
    key = str(muscle_group).strip().lower()
    best: Optional[Tuple[str, str, List[Dict[str, Any]]]] = None
    # Exact id or name match
    for cid, cname, items in _index_categories():
        if key == cid or key == cname:
            best = (cid, cname, items)
            break
    # Substring match fallback (e.g., "leg" -> "legs")
    if best is None:
        for cid, cname, items in _index_categories():
            if key in cid or key in cname or cid in key or cname in key:
                best = (cid, cname, items)
                break
    if best is None:
        return {"muscle_group": muscle_group, "workouts": []}
    cid, cname, items = best
    return {"muscle_group": muscle_group, "workouts": items}


def search_workouts(query: str) -> Dict[str, Any]:
    """Simple case-insensitive search across all workouts.

    Returns list of matches with their muscle group.
    Each result: { group: <muscle_group>, item: <workout> }
    """
    q = (query or "").strip().lower()
    results: List[Dict[str, Any]] = []
    if not q:
        return {"results": results}

    for cid, cname, items in _index_categories():
        group = cid or cname
        for it in items:
            if isinstance(it, str):
                hay = it.lower()
                if q in hay:
                    results.append({"group": group, "item": it})
            elif isinstance(it, dict):
                # Search in name/description fields if present, else dump string
                text = " ".join(str(it.get(k, "")) for k in ("name", "description", "title"))
                if not text:
                    text = json.dumps(it)
                if q in text.lower():
                    results.append({"group": group, "item": it})
            else:
                # Fallback to string compare
                text = str(it)
                if q in text.lower():
                    results.append({"group": group, "item": it})

    return {"results": results}
