# src/services/tmdb_simple_reco.py
from __future__ import annotations
import os, time
import requests
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv  # pip install python-dotenv
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"
LANG = os.getenv("TMDB_LANG", "fr-FR")
REGION = os.getenv("TMDB_REGION", "FR")

def _tmdb_get(path: str, params: dict | None = None) -> dict:
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY manquant")
    params = dict(params or {})
    headers = None
    if TMDB_API_KEY.startswith("ey"):  # token v4
        headers = {"Authorization": f"Bearer {TMDB_API_KEY}"}
    else:  # clé v3
        params["api_key"] = TMDB_API_KEY
    params.setdefault("language", LANG)
    r = requests.get(f"{TMDB_BASE}{path}", params=params, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()

def _movie_details_and_credits(tmdb_id: int) -> dict:
    return _tmdb_get(f"/movie/{tmdb_id}", {"append_to_response": "credits"})

def _similar_movies(tmdb_id: int, pages: int = 1) -> List[dict]:
    out = []
    for p in range(1, pages + 1):
        data = _tmdb_get(f"/movie/{tmdb_id}/similar", {"page": p, "region": REGION})
        out.extend(data.get("results", []))
        time.sleep(0.05)
    return out

def _discover_candidates(with_cast: List[int], with_crew: List[int], with_genres: List[int]) -> List[dict]:
    # On fait quelques appels discover “OR” (TMDb traite les ids séparés par virgules comme OR)
    results = []
    if with_cast:
        data = _tmdb_get("/discover/movie", {
            "with_cast": ",".join(str(i) for i in with_cast[:6]),
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "page": 1, "region": REGION
        })
        results.extend(data.get("results", []))
        time.sleep(0.05)
    if with_crew:
        data = _tmdb_get("/discover/movie", {
            "with_crew": ",".join(str(i) for i in with_crew[:4]),
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "page": 1, "region": REGION
        })
        results.extend(data.get("results", []))
        time.sleep(0.05)
    if with_genres:
        data = _tmdb_get("/discover/movie", {
            "with_genres": ",".join(str(i) for i in with_genres[:6]),
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "page": 1, "region": REGION
        })
        results.extend(data.get("results", []))
    return results

def _collect_seed_features(seed_ids: List[int]) -> Tuple[set, set, set, Dict[int, dict]]:
    cast_ids, crew_dir_ids, genre_ids = set(), set(), set()
    seed_meta: Dict[int, dict] = {}
    for sid in seed_ids:
        d = _movie_details_and_credits(sid)
        seed_meta[sid] = d
        # genres
        for g in d.get("genres", []) or []:
            if g.get("id"): genre_ids.add(int(g["id"]))
        # crew -> director ids
        for c in (d.get("credits", {}).get("crew") or []):
            if c.get("job") == "Director" and c.get("id"):
                crew_dir_ids.add(int(c["id"]))
        # cast (top 6)
        cast = sorted((d.get("credits", {}).get("cast") or []), key=lambda x: x.get("order", 999))[:6]
        for a in cast:
            if a.get("id"): cast_ids.add(int(a["id"]))
        time.sleep(0.05)
    return cast_ids, crew_dir_ids, genre_ids, seed_meta

def _score_candidate(c: dict, seed_feats: Tuple[set, set, set, Dict[int, dict]]) -> Tuple[float, str]:
    cast_ids, crew_dir_ids, genre_ids, _ = seed_feats
    # Features du candidat (en récupérant crédits si nécessaire pour meilleure raison)
    cand_cast_ids, cand_dir_ids, cand_gen_ids = set(), set(), set()
    # Les résultats discover/similar n'ont pas toujours genres détaillés ⇒ on essaie d'éviter un appel de plus,
    # mais pour une bonne raison on peut appeler les détails UNE fois si besoin.
    genres = c.get("genre_ids") or []
    for gid in genres:
        cand_gen_ids.add(int(gid))
    # On fetch crédits d’un coup si on n’a pas assez de signal
    need_details = True
    if cand_gen_ids & genre_ids:
        need_details = False
    if need_details:
        try:
            det = _movie_details_and_credits(int(c["id"]))
            for g in det.get("genres", []) or []:
                cand_gen_ids.add(int(g["id"]))
            for cr in (det.get("credits", {}).get("crew") or []):
                if cr.get("job") == "Director" and cr.get("id"):
                    cand_dir_ids.add(int(cr["id"]))
            cast = sorted((det.get("credits", {}).get("cast") or []), key=lambda x: x.get("order", 999))[:6]
            for a in cast:
                if a.get("id"): cand_cast_ids.add(int(a["id"]))
        except Exception:
            pass

    # Overlaps
    n_dir = len(cand_dir_ids & crew_dir_ids)
    n_cast = len(cand_cast_ids & cast_ids)
    n_gen = len(cand_gen_ids & genre_ids)
    pop = float(c.get("popularity") or 0.0)

    # Score pondéré simple
    score = 3.0 * n_dir + 2.0 * n_cast + 1.0 * n_gen + (pop / 100.0)

    # Raison courte (priorité: dir > cast > genres)
    reason = "Proximité de style et thématiques"
    if n_dir > 0:
        # on n’a pas les noms ici; pour afficher un nom, on refait un petit lookup via credits si pas déjà fait
        if not cand_dir_ids:
            try:
                det = _movie_details_and_credits(int(c["id"]))
                cand_dir_ids = {int(cr["id"]) for cr in det.get("credits", {}).get("crew") or [] if cr.get("job")=="Director" and cr.get("id")}
            except Exception:
                pass
        reason = "Même réalisateur"
    elif n_cast >= 2:
        reason = "Acteurs en commun"
    elif n_cast == 1:
        reason = "Acteur en commun"
    elif n_gen > 0:
        reason = "Genres proches"

    return score, reason

def recommend_simple(seed_ids: List[int], k: int = 12) -> List[Dict[str, Any]]:
    if not seed_ids:
        return []
    cast_ids, crew_dir_ids, genre_ids, seed_meta = _collect_seed_features(seed_ids)

    # Candidats = union (similar) + discover
    candidates = {}
    for sid in seed_ids:
        for c in _similar_movies(sid, pages=1):
            candidates[c["id"]] = c
    disc = _discover_candidates(list(cast_ids), list(crew_dir_ids), list(genre_ids))
    for c in disc:
        candidates[c["id"]] = c

    # Score & raison
    scored: List[Tuple[float, dict, str]] = []
    feats = (cast_ids, crew_dir_ids, genre_ids, seed_meta)
    for cid, c in candidates.items():
        if int(cid) in seed_ids:
            continue
        s, reason = _score_candidate(c, feats)
        scored.append((s, c, reason))

    # Trier & formatter
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for s, c, reason in scored[:k]:
        out.append({
            "tmdb_id": c["id"],
            "title": c.get("title") or c.get("original_title") or "(sans titre)",
            "poster_path": c.get("poster_path"),
            "overview": (c.get("overview") or "")[:360].strip(),
            "reason": reason,
            "score": round(float(s), 4),
        })
    return out
