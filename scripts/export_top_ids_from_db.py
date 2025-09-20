# scripts/export_top_ids_from_db.py
import os, json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()  # lit .env si présent à la racine

DB_URL = os.getenv("DB_URL")
assert DB_URL, "DB_URL manquant (ex: mysql+mysqlconnector://user:pass@host/db)"

TABLE   = os.getenv("CATALOG_TABLE", "films")
ID_COL  = os.getenv("CATALOG_ID_COL", "tmdb_id")
SCORE_COL = os.getenv("CATALOG_SCORE_COL", "avg_rating")
OUT_PATH  = os.getenv("TOP_RATED_IDS_PATH", "data/top_ids.json")

engine = create_engine(DB_URL, pool_pre_ping=True)
with engine.connect() as conn:
    rows = conn.execute(
        text(f"""
            SELECT {ID_COL} AS id, {SCORE_COL} AS s
            FROM {TABLE}
            WHERE {ID_COL} IS NOT NULL AND {SCORE_COL} IS NOT NULL
            ORDER BY {SCORE_COL} DESC
            LIMIT 400
        """)
    ).fetchall()

data = []
for r in rows:
    try:
        mid = int(r[0]); sc = float(r[1])
        data.append({"id": mid, "score": sc})
    except Exception:
        pass

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print(f"Écrit {len(data)} entrées dans {OUT_PATH}")
