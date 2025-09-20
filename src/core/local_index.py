# src/core/local_index.py
from __future__ import annotations
import os, json
from functools import lru_cache
from typing import Set, Optional
from contextlib import suppress

from sqlalchemy import create_engine, text

_ENGINE = None
_IDS_CACHE: Optional[Set[int]] = None

def _init_engine():
    global _ENGINE
    db_url = os.getenv("DB_URL")
    if db_url and _ENGINE is None:
        try:
            _ENGINE = create_engine(db_url, pool_pre_ping=True)
        except Exception:
            _ENGINE = None

def _load_ids_from_json() -> Optional[Set[int]]:
    path = os.getenv("CATALOG_IDS_PATH", "data/catalog_ids.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {int(x) for x in data if x is not None}
    except Exception:
        return None

def _probe_db_has_id(tmdb_id: int) -> bool:
    """Tente plusieurs tables/colonnes courantes. Adapte si besoin."""
    if _ENGINE is None:
        return False
    candidates = [
        ("film", "tmdb_id"),
        ("films", "tmdb_id"),
        ("movie", "tmdb_id"),
        ("movies", "tmdb_id"),
    ]
    with _ENGINE.connect() as conn:
        for table, col in candidates:
            with suppress(Exception):
                row = conn.execute(
                    text(f"SELECT 1 FROM {table} WHERE {col} = :id LIMIT 1"),
                    {"id": int(tmdb_id)},
                ).first()
                if row:
                    return True
    return False

def init_local_index():
    """À appeler au démarrage de l'app."""
    global _IDS_CACHE
    _init_engine()
    # Priorité à un fichier JSON si dispo (rapide)
    _IDS_CACHE = _load_ids_from_json()

def has_local_data(tmdb_id: int) -> bool:
    """True si l'ID est dans le catalogue local (JSON ou DB)."""
    if tmdb_id is None:
        return False
    # Cache JSON → O(1)
    if _IDS_CACHE is not None:
        return int(tmdb_id) in _IDS_CACHE
    # Sinon, requête DB rapide (fallback)
    return _probe_db_has_id(int(tmdb_id))

def filter_to_local(ids: list[int]) -> list[int]:
    return [int(i) for i in ids if has_local_data(int(i))]
