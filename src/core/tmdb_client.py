import os, requests
from dotenv import load_dotenv
load_dotenv()

import time, requests, os
from functools import lru_cache

API = "https://api.themoviedb.org/3"
KEY = os.getenv("TMDB_API_KEY")

def _get(path, params=None, tries=3):
    params = {"api_key": KEY, "language": "fr-FR", **(params or {})}
    for i in range(tries):
        r = requests.get(f"{API}{path}", params=params, timeout=15)
        if r.status_code == 429:
            time.sleep(1.5 * (i+1)); continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("TMDb rate-limited")

@lru_cache(maxsize=2048)
def movie_details(movie_id:int):
    return _get(f"/movie/{movie_id}", params={"append_to_response":"credits"})


TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE = "https://api.themoviedb.org/3"

def tmdb_get(path: str, **params):
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY manquant")
    params["api_key"] = TMDB_API_KEY
    r = requests.get(f"{BASE}{path}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def movie_details(tmdb_id: int, language="fr-FR"):
    return tmdb_get(f"/movie/{tmdb_id}", language=language, append_to_response="credits")

def search_movie(query: str, language="fr-FR", page=1):
    return tmdb_get("/search/movie", query=query, language=language, page=page)
