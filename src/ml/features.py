import pandas as pd
from sqlalchemy import text

from src.core.db import engine

def load_catalog() -> pd.DataFrame:
    with engine.begin() as conn:
        films_df = pd.read_sql(
            """
            SELECT
              f.tmdb_id AS film_tmdb_id,
              f.title,
              f.poster_path,
              COALESCE(d.name,'') AS director
            FROM film f
            LEFT JOIN directors d ON f.tmdb_id = d.film_tmdb_id
            """,
            conn,
        )
        genres_df = pd.read_sql(
            """
            SELECT fg.film_id AS film_tmdb_id, GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ',') AS genres
            FROM film_genre fg
            JOIN genre g ON g.id = fg.genre_id
            GROUP BY fg.film_id
            """,
            conn,
        )

    if films_df.empty:
        return pd.DataFrame(columns=["film_tmdb_id", "title", "poster_path", "director", "genres"])

    df = films_df.merge(genres_df, on="film_tmdb_id", how="left")
    df = df.fillna("")
    df.loc[:, "director"] = df["director"].replace("", "Unknown")
    df.loc[:, "genres"] = df["genres"].replace("", "Unknown")
    return df

def build_feature_matrix(df_movies: pd.DataFrame) -> pd.DataFrame:
    enc_dir = pd.get_dummies(df_movies["director"], prefix="director")
    enc_gen = df_movies["genres"].str.get_dummies(sep=",")
    X = pd.concat([enc_dir, enc_gen], axis=1)
    X.index = df_movies["film_tmdb_id"].astype(int).values
    return X
