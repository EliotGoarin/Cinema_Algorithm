from fastapi import FastAPI
from src.ml.recommender import get_recommendations

app = FastAPI()

@app.get("/recommendations/")
def recommendations(films: str):
    # films = "1,2,3"
    film_ids = [int(f) for f in films.split(",")]
    recs = get_recommendations(film_ids)  # appel de ton moteur ML
    return {"recommendations": recs}
