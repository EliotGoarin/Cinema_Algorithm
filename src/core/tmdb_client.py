import os
import time
from functools import lru_cache

import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://api.themoviedb.org/3"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
LANG = os.getenv("TMDB_LANG", "fr-FR")

class TMDBError(RuntimeError):
    pass

def _req(method: str, path: str, params: dict | None = None, tries: int = 3):
    if not TMDB_API_KEY:
        raise TMDBError("TMDB_API_KEY manquant dans l'environnement")
    params = {"api_key": TMDB_API_KEY, "language": LANG, **(params or {})}
    last = None
    for i in range(tries):
        r = requests.request(method, f"{BASE}{path}", params=params, timeout=20)
        if r.status_code == 429:  # rate limit
            time.sleep(1.5 * (i + 1))
            last = r
            continue
        if r.ok:
            return r.json()
        last = r
        time.sleep(0.2)
    raise TMDBError(f"TMDB {_req.__name__} échec {last.status_code if last else '??'}: {last.text if last else ''}")

def tmdb_get(path: str, **params):
    return _req("GET", path, params)

@lru_cache(maxsize=4096)
def movie_details(tmdb_id: int):
    return tmdb_get(f"/movie/{tmdb_id}", append_to_response="credits")

def search_movie(query: str, page: int = 1):
    return tmdb_get("/search/movie", query=query, page=page)

def popular(page: int = 1):
    return tmdb_get("/movie/popular", page=page)

def trending_day(page: int = 1):
    return tmdb_get("/trending/movie/day", page=page)

def similar_movies(tmdb_id: int, page: int = 1):
    return tmdb_get(f"/movie/{tmdb_id}/similar", page=page)

def popular_movies(page: int = 1):
    url = f"{BASE}/movie/popular"
    params = {"api_key": TMDB_API_KEY, "page": page, "language": LANG}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()