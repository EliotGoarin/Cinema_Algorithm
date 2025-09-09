# src/ml/recommender.py

import os
import requests
import pandas as pd
from sqlalchemy import create_engine
from sklearn.neighbors import NearestNeighbors
from dotenv import load_dotenv

# ----- Charger .env -----
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
DB_URL = os.getenv("DB_URL")

if not TMDB_API_KEY or not DB_URL:
    raise ValueError("TMDB_API_KEY ou DB_URL manquant dans le fichier .env")

# ----- Connexion MySQL -----
engine = create_engine(DB_URL, echo=False)

# ----- Charger les films avec réalisateurs et genres -----
def load_movies() -> pd.DataFrame:
    films_df = pd.read_sql(
        """
        SELECT f.tmdb_id AS film_tmdb_id, f.title, d.name AS director
        FROM film f
        LEFT JOIN directors d ON f.tmdb_id = d.film_tmdb_id
        """,
        engine,
    )

    # Tenter de joindre les genres si les tables existent
    try:
        genres_df = pd.read_sql(
            """
            SELECT fg.film_id, GROUP_CONCAT(g.name SEPARATOR ',') AS genres
            FROM film_genre fg
            JOIN genre g ON fg.genre_id = g.id
            GROUP BY fg.film_id
            """,
            engine,
        )
        df = films_df.merge(
            genres_df, left_on="film_tmdb_id", right_on="film_id", how="left"
        )
    except Exception:
        df = films_df.copy()
        df["genres"] = ""

    # Nettoyage valeurs manquantes
    df = df.fillna("")
    # Remplacements sûrs (évite chained assignment)
    df.loc[:, "director"] = df["director"].replace("", "Unknown")
    df.loc[:, "genres"] = df["genres"].replace("", "Unknown")

    return df

# ----- Préparation données -----
df_movies = load_movies()
print(f"🎬 {len(df_movies)} films chargés")

# Encodage one-hot (réalisateur + genres)
df_encoded_director = pd.get_dummies(df_movies["director"], prefix="director")
df_encoded_genres = df_movies["genres"].str.get_dummies(sep=",")
df_encoded = pd.concat([df_encoded_director, df_encoded_genres], axis=1)

if df_encoded.empty:
    raise ValueError("df_encoded est vide ! Vérifie la base de données et la requête SQL.")

# ----- Modèle k-NN -----
# n_neighbors = k + 1 (pour pouvoir exclure le seed et garder k résultats)
DEFAULT_K = 5
n_neighbors = min(len(df_encoded), DEFAULT_K + 1)
model = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
model.fit(df_encoded)

# ----- Infos film via TMDb -----
def get_film_info(tmdb_id: int) -> dict:
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {"api_key": TMDB_API_KEY, "language": "fr-FR"}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
    except Exception:
        return {"title": "Inconnu", "poster_path": None}

    data = resp.json()
    poster_url = (
        f"https://image.tmdb.org/t/p/w200{data.get('poster_path')}"
        if data.get("poster_path")
        else None
    )
    return {"title": data.get("title", "Inconnu"), "poster_path": poster_url}

# ----- Fonction principale -----
def get_recommendations(film_titles: list[str], k: int = DEFAULT_K) -> dict:
    """
    film_titles: liste de titres (ex: ["Inception", "Avatar"])
    k: nombre de recommandations souhaité
    Retourne {"recommendations": [{"title":..., "poster_path":...}, ...]} ou {"error": "..."}
    """
    if not film_titles:
        return {"error": "Aucun titre fourni."}

    valid_titles = set(df_movies["title"].tolist())
    unknown_titles = [t for t in film_titles if t not in valid_titles]
    if unknown_titles:
        return {"error": f"Film(s) inconnu(s) : {unknown_titles}"}

    # Seed = premier titre fourni (simple et robuste)
    first_title = film_titles[0]
    seed_row = df_movies[df_movies["title"] == first_title]
    if seed_row.empty:
        return {"error": f"Titre introuvable: {first_title}"}

    first_tmdb_id = int(seed_row["film_tmdb_id"].values[0])

    fav_encoded = df_encoded[df_movies["film_tmdb_id"] == first_tmdb_id]
    if fav_encoded.empty:
        return {"error": f"Aucune feature pour le film seed: {first_title}"}

    distances, indices = model.kneighbors(fav_encoded)

    # Indices correspondants aux films recommandés (inclut le seed → on l'exclut)
    idx_list = indices.flatten().tolist()
    titles_list = df_movies.iloc[idx_list]["title"].tolist()
    ids_list = df_movies.iloc[idx_list]["film_tmdb_id"].tolist()

    # Exclure les films d'entrée (seed inclus) et limiter à k résultats
    recs = []
    seen = set(titles_list[:0])  # no-op, laissé pour clarté
    for tmdb_id, title in zip(ids_list, titles_list):
        if title in film_titles:
            continue  # exclusion stricte des entrées
        info = get_film_info(int(tmdb_id))
        recs.append(info)
        if len(recs) >= k:
            break

    return {"recommendations": recs}

# Petit test manuel (décommente si tu veux tester rapidement)
# if __name__ == "__main__":
#     print(get_recommendations(["Inception"], k=5))
