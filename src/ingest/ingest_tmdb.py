from __future__ import annotations

from sqlalchemy import text
from src.core.db import engine, exec_many
from src.core.tmdb_client import movie_details

def upsert_movie(m: dict):
    poster = m.get("poster_path")
    year = 0
    rd = m.get("release_date") or ""
    try:
        year = int(rd[:4]) if len(rd) >= 4 else 0
    except Exception:
        year = 0

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO film (tmdb_id, title, release_year, poster_path)
                VALUES (:id, :title, :year, :poster)
                ON DUPLICATE KEY UPDATE
                    title=VALUES(title),
                    release_year=VALUES(release_year),
                    poster_path=VALUES(poster_path)
            """),
            {"id": m["id"], "title": m.get("title", ""), "year": year, "poster": poster},
        )

def upsert_directors(movie_id: int, credits: dict):
    crew = (credits or {}).get("crew", [])
    directors = [c for c in crew if (c.get("job") == "Director" or c.get("known_for_department") == "Directing")]
    exec_many(
        "INSERT IGNORE INTO directors (film_tmdb_id, tmdb_id, name) VALUES (:f,:t,:n)",
        [{"f": movie_id, "t": d.get("id"), "n": d.get("name", "")} for d in directors],
    )

def upsert_genres(movie_id: int, genres: list[dict]):
    exec_many(
        "INSERT IGNORE INTO genre (id, name) VALUES (:id,:name)",
        [{"id": g["id"], "name": g["name"]} for g in (genres or [])],
    )
    exec_many(
        "INSERT IGNORE INTO film_genre (film_id, genre_id) VALUES (:f,:g)",
        [{"f": movie_id, "g": g["id"]} for g in (genres or [])],
    )

def ingest_one(tmdb_id: int):
    m = movie_details(int(tmdb_id))
    upsert_movie(m)
    upsert_directors(m["id"], m.get("credits"))
    upsert_genres(m["id"], m.get("genres"))
    return {"ingested": m["id"], "title": m.get("title", "")}
