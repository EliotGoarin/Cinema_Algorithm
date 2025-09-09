import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise RuntimeError("DB_URL manquant dans .env")
engine = create_engine(DB_URL, echo=False, pool_pre_ping=True)

def exec_many(sql: str, rows: list[dict]):
    if not rows: return
    with engine.begin() as conn:
        conn.execute(text(sql), rows)
