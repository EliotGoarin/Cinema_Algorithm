import { useState } from "react";
import { searchMovies, ingestAndAdd, getRecommendations, refreshCache } from "./apiClient";

function App() {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  async function handleSearch() {
    setLoading(true);
    try {
      const data = await searchMovies(query);
      setSearchResults(data.results || []);
    } catch (err) {
      console.error(err);
      alert("Erreur recherche");
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd(title) {
    setLoading(true);
    try {
      const data = await ingestAndAdd(title);
      alert(`Film ajouté: ${data.movie.title}`);
    } catch (err) {
      console.error(err);
      alert("Erreur ingestion");
    } finally {
      setLoading(false);
    }
  }

  async function handleRecommend(seedId) {
    setLoading(true);
    try {
      const data = await getRecommendations([seedId], 5);
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error(err);
      alert("Erreur reco");
    } finally {
      setLoading(false);
    }
  }

  async function handleRefreshCache() {
    try {
      await refreshCache();
      alert("Cache rafraîchi !");
    } catch (err) {
      console.error(err);
      alert("Erreur refresh cache");
    }
  }

  return (
    <div style={{ padding: "20px" }}>
      <h1>🎬 Cinema Algorithm</h1>

      <div>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Rechercher un film..." />
        <button onClick={handleSearch}>Chercher</button>
        <button onClick={handleRefreshCache}>Rafraîchir cache</button>
      </div>

      {loading && <p>Chargement...</p>}

      <h2>Résultats</h2>
      <ul>
        {searchResults.map((m) => (
          <li key={m.id}>
            {m.title} ({m.release_date})
            <button onClick={() => handleAdd(m.title)}>Ajouter</button>
            <button onClick={() => handleRecommend(m.id)}>Recommander</button>
          </li>
        ))}
      </ul>

      <h2>Recommandations</h2>
      <ul>
        {recommendations.map((r) => (
          <li key={r.tmdb_id}>
            {r.title}
            {r.poster_path && <img src={`https://image.tmdb.org/t/p/w200${r.poster_path}`} alt={r.title} />}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
