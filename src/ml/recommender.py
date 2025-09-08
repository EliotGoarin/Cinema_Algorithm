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
    echo=False
)

# ----- Charger les films avec réalisateurs et genres -----
def load_movies():
    # Films + réalisateur
    films_df = pd.read_sql("""
        SELECT f.tmdb_id AS film_tmdb_id, f.title, d.name AS director
        FROM film f
        LEFT JOIN directors d ON f.tmdb_id = d.film_tmdb_id
    """, engine)

    # Genres concaténés (si tu as une table genre / film_genre)
    try:
        genres_df = pd.read_sql("""
            SELECT fg.film_id, GROUP_CONCAT(g.name SEPARATOR ',') AS genres
            FROM film_genre fg
            JOIN genre g ON fg.genre_id = g.id
            GROUP BY fg.film_id
        """, engine)
        df = films_df.merge(genres_df, left_on='film_tmdb_id', right_on='film_id', how='left')
    except Exception:
        df = films_df
        df['genres'] = ''  # si pas de genres

    df = df.fillna('')  # valeurs manquantes remplacées par chaîne vide
    return df

# ----- Charger et encoder -----
df_movies = load_movies()
print("Nombre de films chargés :", len(df_movies))
print(df_movies.head())

# Remplacer les valeurs vides par 'Unknown' pour l'encodage
df_movies['director'].replace('', 'Unknown', inplace=True)
df_movies['genres'].replace('', 'Unknown', inplace=True)

# Encoder director et genres séparément
df_encoded_director = pd.get_dummies(df_movies['director'], prefix='director')
df_encoded_genres = df_movies['genres'].str.get_dummies(sep=',')
df_encoded = pd.concat([df_encoded_director, df_encoded_genres], axis=1)

# Vérification
if df_encoded.empty:
    raise ValueError("df_encoded est vide ! Vérifie la base de données et load_movies()")

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
def get_recommendations(film_titles):
    """
    film_titles: liste des titres de films (ex: ["Inception", "Avatar"])
    Retourne dictionnaire {"recommendations": [titres]} ou {"error": msg}
    """
    # Vérifier que les titres existent
    valid_titles = df_movies['title'].tolist()
    unknown_titles = [t for t in film_titles if t not in valid_titles]
    if unknown_titles:
        return {"error": f"Film(s) inconnu(s) : {unknown_titles}"}

    # Récupérer le tmdb_id du premier film préféré
    first_title = film_titles[0]
    first_tmdb_id = df_movies[df_movies['title'] == first_title]['film_tmdb_id'].values[0]

    # Encoder le premier film préféré
    fav_encoded = df_encoded[df_movies['film_tmdb_id'] == first_tmdb_id]
    distances, indices = model.kneighbors(fav_encoded)

    # Récupérer les titres recommandés
    recommended_titles = df_movies.iloc[indices.flatten()]['title'].tolist()

    # Exclure les films d'entrée
    recommended_titles = [t for t in recommended_titles if t not in film_titles]

    return {"recommendations": recommended_titles}

