from sklearn.neighbors import NearestNeighbors
import pandas as pd

# Exemple minimal de dataframe fictive pour tester le prototype
df = pd.DataFrame({
    "id": [1, 2, 3],
    "director": ["A", "B", "A"],
    "genre": ["Action", "Comédie", "Action"]
})

# Encodage simple
df_encoded = pd.get_dummies(df[["director", "genre"]])

# Modèle k-NN
model = NearestNeighbors(n_neighbors=2, metric='cosine')
model.fit(df_encoded)

# Fonction à appeler depuis l'API
def get_recommendations(film_ids):
    """
    film_ids: liste des IDs de films préférés de l'utilisateur
    Retourne les indices des films recommandés (exemple minimal)
    """
    fav_encoded = df_encoded.iloc[[0]]  # Prototype : on prend toujours le premier film
    distances, indices = model.kneighbors(fav_encoded)
    # Pour l'instant, on renvoie les indices
    return indices.flatten().tolist()
