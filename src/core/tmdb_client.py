import os, requests
from dotenv import load_dotenv
load_dotenv()

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
