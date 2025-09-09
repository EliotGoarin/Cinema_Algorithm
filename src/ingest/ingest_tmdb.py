from sqlalchemy import text
from datetime import datetime
from src.core.db import engine, exec_many
from src.core.tmdb_client import movie_details

def upsert_movie(m):
    poster = m.get("poster_path")  # path TMDb (ex: /abc.jpg)
    year = 0
    if m.get("release_date"):
        try:
            year = int(m["release_date"][:4])
        except Exception:
            year = 0

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO film (tmdb_id, title, release_year, poster_path, last_tmdb_sync)
            VALUES (:id, :title, :year, :poster, :sync)
            ON DUPLICATE KEY UPDATE
              title=VALUES(title),
              release_year=VALUES(release_year),
              poster_path=VALUES(poster_path),
              last_tmdb_sync=VALUES(last_tmdb_sync)
        """), {
            "id": m["id"],
            "title": m.get("title", ""),
            "year": year if year > 0 else None,
            "poster": poster,
            "sync": datetime.utcnow()
        })

def upsert_directors(movie_id, credits):
    rows = []
    for c in credits.get("crew", []):
        if c.get("job") == "Director":
            rows.append({"film_tmdb_id": movie_id, "name": c["name"]})
    exec_many("""
        INSERT IGNORE INTO directors (film_tmdb_id, name)
        VALUES (:film_tmdb_id, :name)
    """, rows)

def upsert_genres(movie_id, genres):
    exec_many("""INSERT IGNORE INTO genre (id, name) VALUES (:id,:name)""",
              [{"id": g["id"], "name": g["name"]} for g in genres])
    exec_many("""INSERT IGNORE INTO film_genre (film_id, genre_id) VALUES (:f,:g)""",
              [{"f": movie_id, "g": g["id"]} for g in genres])

def ingest_one(tmdb_id: int):
    m = movie_details(tmdb_id)
    upsert_movie(m)
    upsert_directors(m["id"], m.get("credits", {}))
    upsert_genres(m["id"], m.get("genres", []))
    return {"ingested": m["id"], "title": m.get("title")}

def ingest_many(ids: list[int]):
    return [ingest_one(i) for i in ids]
