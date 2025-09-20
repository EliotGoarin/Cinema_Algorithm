import { useState } from "react";
import { searchMovies } from "../api/client.js";
import MovieCard from "../components/MovieCard.jsx";

export default function HomePage() {
  const [q, setQ] = useState("matrix");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  async function doSearch() {
    setLoading(true); setError("");
    try {
      const data = await searchMovies(q, 1);
      setResults(Array.isArray(data.results) ? data.results : []);
    } catch (e) {
      setError(e.message || "Search error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <div className="input-row">
        <input className="input" value={q} onChange={(e)=>setQ(e.target.value)} placeholder="Chercher un film…" />
        <button className="btn" onClick={doSearch} disabled={loading}>
          {loading ? "…" : "Rechercher"}
        </button>
      </div>

      {error && <div style={{ color: "#ff6b6b", padding: "12px 16px" }}>{error}</div>}

      <h2 className="section-title">Résultats</h2>
      <div className="grid">
        {results.map(m => <MovieCard key={m.id} movie={m} />)}
      </div>
    </div>
  );
}
