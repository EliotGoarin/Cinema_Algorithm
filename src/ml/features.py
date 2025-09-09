import pandas as pd
from src.core.db import engine

def load_catalog() -> pd.DataFrame:
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
        engine,
    )

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
        df = films_df.merge(genres_df, left_on="film_tmdb_id", right_on="film_id", how="left")
    except Exception:
        df = films_df.copy()
        df["genres"] = ""

    df = df.fillna("")
    df.loc[:, "director"] = df["director"].replace("", "Unknown")
    df.loc[:, "genres"]   = df["genres"].replace("", "Unknown")
    return df

def build_feature_matrix(df_movies: pd.DataFrame) -> pd.DataFrame:
    enc_dir = pd.get_dummies(df_movies["director"], prefix="director")
    enc_gen = df_movies["genres"].str.get_dummies(sep=",")
    X = pd.concat([enc_dir, enc_gen], axis=1)
    X.index = df_movies["film_tmdb_id"].values
    return X
