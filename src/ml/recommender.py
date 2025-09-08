# src/ml/recommender.py

import mysql.connector  # nécessaire pour SQLAlchemy sur Windows
from sqlalchemy import create_engine
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import requests

# ----- CONFIGURATION -----
DB_USER = "root"
DB_PASS = "Ademolili0806!"
DB_HOST = "localhost"
DB_NAME = "movies"

TMDB_API_KEY = "TA_CLEF_API"  # Remplace par ta clé TMDb

# ----- Connexion MySQL -----
engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}",
    echo=False  # mettre True si tu veux voir les requêtes SQL
)

# ----- Charger les films avec réalisateurs et genres -----
def load_movies():
    # Films + réalisateur
    films_df = pd.read_sql("""
        SELECT f.id, f.tmdb_id, f.title, f.year, d.name AS director
        FROM film f
        LEFT JOIN director d ON f.director_id = d.id
    """, engine)

    # Genres concaténés
    genres_df = pd.read_sql("""
        SELECT fg.film_id, GROUP_CONCAT(g.name SEPARATOR ',') AS genres
        FROM film_genre fg
        JOIN genre g ON fg.genre_id = g.id
        GROUP BY fg.film_id
    """, engine)

    df = films_df.merge(genres_df, left_on='id', right_on='film_id', how='left')
    df = df.fillna('')  # valeurs manquantes remplacées par chaîne vide
    return df

# ----- Charger et encoder -----
df_movies = load_movies()
df_encoded = pd.get_dummies(df_movies[['director', 'genres']])

# ----- Créer le modèle k-NN -----
model = NearestNeighbors(n_neighbors=5, metric='cosine')
model.fit(df_encoded)

# ----- Récupérer titre + poster depuis TMDb -----
def get_film_info(tmdb_id):
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_API_KEY}&language=fr-FR"
    resp = requests.get(url)
    if resp.status_code != 200:
        return {"title": "Inconnu", "poster_path": None}
    data = resp.json()
    poster_url = f"https://image.tmdb.org/t/p/w200{data.get('poster_path')}" if data.get('poster_path') else None
    return {"title": data.get("title"), "poster_path": poster_url}

# ----- Fonction principale -----
def get_recommendations(film_ids):
    """
    film_ids: liste des IDs internes de la base (colonne id)
    Retourne dictionnaire {"recommendations": [tmdb_ids]} ou {"error": msg}
    """
    # Vérifier que les IDs existent
    valid_ids = df_movies['id'].tolist()
    unknown_ids = [f for f in film_ids if f not in valid_ids]
    if unknown_ids:
        return {"error": f"Film(s) inconnu(s) : {unknown_ids}"}

    # Encoder le premier film préféré (prototype simple)
    fav_encoded = df_encoded[df_movies['id'] == film_ids[0]]
    distances, indices = model.kneighbors(fav_encoded)

    recommended_tmdb_ids = df_movies.iloc[indices.flatten()]['tmdb_id'].tolist()
    return {"recommendations": recommended_tmdb_ids}
