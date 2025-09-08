import requests
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

# Charger clé API et DB
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(DB_URL)

# Exemple : récupérer les films populaires TMDb
url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=fr-FR&page=1"
response = requests.get(url).json()
movies = response['results']

# Préparer dataframe
data = []
for m in movies:
    data.append({
        "id": m['id'],
        "title": m['title'],
        "year": m['release_date'][:4] if m['release_date'] else None
    })

df = pd.DataFrame(data)
df.to_sql("film", engine, if_exists="replace", index=False)
print("Films insérés dans la DB !")
