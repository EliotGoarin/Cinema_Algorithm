# 🎬 Cinema Algorithm

**Cinema Algorithm** est un moteur de recommandation de films basé sur le contenu.  
Il combine les données de **The Movie Database (TMDb)** avec un pipeline d’ingestion, un backend **FastAPI** et un client **React** pour offrir une expérience complète : recherche de films, sélection de favoris et recommandations personnalisées.

---
<img width="1883" height="863" alt="image" src="https://github.com/user-attachments/assets/bfd1b171-a2c0-4d97-8276-aa73b5b833b9" />
---



## 🚀 Fonctionnalités

- **Recherche de films** via l’API TMDb  
- **Sélection de films de référence** par l’utilisateur (1 à 5 films)  
- **Recommandations personnalisées** (k-Nearest Neighbors sur genres, acteurs, réalisateurs)  
- **Explication des recommandations** (partage de réalisateur, acteurs, genres)  
- **Backend REST** (FastAPI)  
- **Frontend React** simple et extensible  
- **Base SQL** avec migrations Alembic pour la persistance  
- **Cache/rafraîchissement** des recommandations pour de meilleures performances  

---

## 🛠️ Stack technique

- **Backend** : [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/), [Alembic](https://alembic.sqlalchemy.org/), [scikit-learn](https://scikit-learn.org/)  
- **Base de données** : MySQL (ou PostgreSQL compatible)  
- **Data source** : [TMDb API](https://developer.themoviedb.org/)  
- **Frontend** : [React](https://react.dev/) + Fetch API  
- **Déploiement** : Uvicorn, Docker (optionnel), Railway/Render pour la base/API, Vercel/Netlify pour le front  

---

## ⚙️ Installation & setup

### 1. Cloner le repo

git clone https://github.com/EliotGoarin/Cinema_Algorithm.git
cd Cinema_Algorithm
### 2. Créer un environnement virtuel et installer les dépendances

python -m venv .venv
source .venv/bin/activate    # Linux/Mac
.venv\Scripts\activate       # Windows

pip install -r requirements.txt
### 3. Configurer l’environnement
Copier le fichier .env.example → .env et remplir :

TMDB_API_KEY=ta_clef_tmdb
DB_URL=mysql+mysqlconnector://user:password@localhost/movies
ALLOW_ORIGINS=http://localhost:5173
### 4. Initialiser la base de données

alembic upgrade head
### 5. Lancer l’API

uvicorn src.api.app:app --reload
→ API disponible sur http://localhost:8000

### 6. Lancer le frontend

cd web
npm install
npm run dev
→ Frontend dispo sur http://localhost:5173

### 🔌 Endpoints principaux
GET /healthz → ping de santé

GET /tmdb/search?query=Inception → recherche TMDb

POST /recommend
Exemple payload :
{
  "seed_ids": [27205, 157336],
  "k": 10
}
→ renvoie les 10 films les plus proches

POST /admin/refresh_cache → reconstruit l’index k-NN

POST /admin/ingest_movie/{tmdb_id} → insère un film en base

### 📦 Déploiement
Base SQL : Railway, Render ou Supabase

Backend : Docker + Uvicorn/Gunicorn sur Railway/Render/Heroku

Frontend : Vercel ou Netlify

CI/CD : GitHub Actions (tests, lint, migrations)

### 📈 Roadmap
 Améliorer l’UI (sélection de films, cartes avec affiches, explications)

 Gestion utilisateurs (profils, historique)

 Pondération dynamique (curseurs acteurs/réalisateurs/genres)

 Tests unitaires & intégration continue

 Déploiement full cloud (DB + API + Front)

### 🤝 Contribution
Fork le projet

Crée une branche feature : git checkout -b feat/ma-fonctionnalite

Commit tes modifs : git commit -m "feat: ajout X"

Push : git push origin feat/ma-fonctionnalite

Ouvre une Pull Request

### 📜 Licence
Ce projet est sous licence Apache 2.0.

### 🙏 Remerciements
TMDb pour leur API

L’écosystème open-source Python & React

