from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from src.ml.recommender import get_recommendations

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>Movie Recommender API</title>
        </head>
        <body>
            <h1>Bienvenue sur l'API Movie Recommender</h1>
            <p>Entrez les IDs de vos films préférés (séparés par des virgules) :</p>
            <form action="/recommendations/" method="get">
                <input type="text" name="films" placeholder="Inception, Avatar ..." />
                <input type="submit" value="Voir recommandations" />
            </form>
        </body>
    </html>
    """

@app.get("/recommendations/", response_class=HTMLResponse)
def recommendations(films: str = ""):
    if not films.strip():
        return """..."""  # message d'erreur identique

    # Split en titres
    film_titles = [f.strip() for f in films.split(",")]

    result = get_recommendations(film_titles)

    if "error" in result:
        return f"""..."""  # message d'erreur identique

    # Créer le HTML avec les titres
    html_recs = "<ul>" + "".join(f"<li>{title}</li>" for title in result["recommendations"]) + "</ul>"

    return f"""
    <html>
        <body>
            <h1>Films recommandés :</h1>
            {html_recs}
            <p><a href="/">Retour à l'accueil</a></p>
        </body>
    </html>
    """

