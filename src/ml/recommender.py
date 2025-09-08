import pandas as pd
from sklearn.neighbors import NearestNeighbors

# Exemple de dataframe de films
df = pd.DataFrame({
    "id": [1, 2, 3],
    "title": ["Film A", "Film B", "Film C"],
    "director": ["A", "B", "A"],
    "genre": ["Action", "Comédie", "Action"]
})

# Encodage simple pour k-NN
df_encoded = pd.get_dummies(df[["director", "genre"]])

# Modèle k-NN
model = NearestNeighbors(n_neighbors=2, metric='cosine')
model.fit(df_encoded)

def get_recommendations(film_ids):
    """
    film_ids: liste des IDs de films préférés de l'utilisateur
    Retourne un dictionnaire avec les recommandations ou un message d'erreur
    """
    # Vérifier si les films existent
    valid_ids = df['id'].tolist()
    unknown_ids = [f for f in film_ids if f not in valid_ids]
    if unknown_ids:
        return {"error": f"Film(s) inconnu(s) : {unknown_ids}"}

    # Prototype minimal : on prend toujours le premier film pour k-NN
    fav_encoded = df_encoded.iloc[[0]]
    distances, indices = model.kneighbors(fav_encoded)
    
    # Renvoyer les IDs des films recommandés
    recommended_ids = df.iloc[indices.flatten()]["id"].tolist()
    return {"recommendations": recommended_ids}
