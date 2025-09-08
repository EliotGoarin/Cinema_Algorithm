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
                <input type="text" name="films" placeholder="Ex: 1,2,3" />
                <input type="submit" value="Voir recommandations" />
            </form>
        </body>
    </html>
    """

@app.get("/recommendations/", response_class=HTMLResponse)
def recommendations(films: str = ""):
    if not films.strip():
        return """
        <html>
            <body>
                <h1>Erreur : aucun film renseigné !</h1>
                <p>Veuillez entrer au moins un ID de film.</p>
                <p><a href="/">Retour à l'accueil</a></p>
            </body>
        </html>
        """

    try:
        film_ids = [int(f) for f in films.split(",")]
    except ValueError:
        return """
        <html>
            <body>
                <h1>Erreur : format incorrect !</h1>
                <p>Veuillez entrer des IDs de films séparés par des virgules (ex: 1,2,3).</p>
                <p><a href="/">Retour à l'accueil</a></p>
            </body>
        </html>
        """

    result = get_recommendations(film_ids)

    if "error" in result:
        return f"""
        <html>
            <body>
                <h1>Erreur : {result['error']}</h1>
                <p><a href="/">Retour à l'accueil</a></p>
            </body>
        </html>
        """

    html_recs = "<ul>" + "".join(f"<li>Film ID: {r}</li>" for r in result["recommendations"]) + "</ul>"

    return f"""
    <html>
        <body>
            <h1>Films recommandés :</h1>
            {html_recs}
            <p><a href="/">Retour à l'accueil</a></p>
        </body>
    </html>
    """
