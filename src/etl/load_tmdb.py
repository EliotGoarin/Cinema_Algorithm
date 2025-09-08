import requests
import mysql.connector
import time

# ----- CONFIGURATION -----
API_KEY = "94156e9cc0b3e52fedd6d061f16e97c9"  # Remplace par ta clé TMDb
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ademolili0806!",
    "database": "movies"
}
# -------------------------

# Connexion MySQL
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

def insert_unique(table, tmdb_id, name):
    """Insérer si n'existe pas déjà, retourne l'ID interne"""
    cursor.execute(f"SELECT id FROM {table} WHERE tmdb_id=%s", (tmdb_id,))
    res = cursor.fetchone()
    if res:
        return res[0]
    cursor.execute(f"INSERT INTO {table} (tmdb_id, name) VALUES (%s, %s)", (tmdb_id, name))
    conn.commit()
    return cursor.lastrowid

def insert_film(film_data, director_id):
    """Insérer un film si pas déjà présent"""
    cursor.execute("SELECT id FROM film WHERE tmdb_id=%s", (film_data['id'],))
    res = cursor.fetchone()
    if res:
        return res[0]
    year = int(film_data.get('release_date', '0000-00-00')[:4] or 0)
    decade = f"{year//10*10}s" if year else None
    cursor.execute(
        "INSERT INTO film (tmdb_id, title, year, decade, director_id) VALUES (%s,%s,%s,%s,%s)",
        (film_data['id'], film_data['title'], year, decade, director_id)
    )
    conn.commit()
    return cursor.lastrowid

def insert_film_actor(film_id, actor_id, order):
    cursor.execute("INSERT IGNORE INTO film_actor (film_id, actor_id, cast_order) VALUES (%s,%s,%s)",
                   (film_id, actor_id, order))
    conn.commit()

def insert_film_genre(film_id, genre_id):
    cursor.execute("INSERT IGNORE INTO film_genre (film_id, genre_id) VALUES (%s,%s)", (film_id, genre_id))
    conn.commit()

# ----- Récupération des films populaires -----
URL_POPULAR = f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=fr-FR&page="

for page in range(1, 3):  # Exemple : 2 pages de films populaires
    response = requests.get(URL_POPULAR + str(page))
    data = response.json()
    for film in data['results']:
        # Récupérer les détails du film
        film_id = film['id']
        details = requests.get(f"https://api.themoviedb.org/3/movie/{film_id}?api_key={API_KEY}&language=fr-FR").json()
        
        # Récupérer le réalisateur
        credits = requests.get(f"https://api.themoviedb.org/3/movie/{film_id}/credits?api_key={API_KEY}").json()
        director_id = None
        for crew in credits.get("crew", []):
            if crew['job'] == "Director":
                director_id = insert_unique("director", crew['id'], crew['name'])
                break

        # Insérer le film
        film_db_id = insert_film(details, director_id)

        # Insérer acteurs principaux (top 5)
        for order, actor in enumerate(credits.get("cast", [])[:5]):
            actor_id = insert_unique("actor", actor['id'], actor['name'])
            insert_film_actor(film_db_id, actor_id, order)

        # Insérer genres
        for genre in details.get("genres", []):
            genre_id = insert_unique("genre", genre['id'], genre['name'])
            insert_film_genre(film_db_id, genre_id)

        time.sleep(0.2)  # éviter d’être bloqué par TMDb

cursor.close()
conn.close()
print("Import TMDb terminé !")
