// src/pages/SearchPage.jsx
import { useState } from "react";
import MovieCard from "../components/MovieCard.jsx";
import { searchMovies } from "../api/client.js";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    if (!q.trim()) return;
    setLoading(true);
    setError("");
    setResults([]);
    try {
      const data = await searchMovies(q.trim());
      const list = Array.isArray(data) ? data : (data.results || []);
      setResults(list);
    } catch (err) {
      setError(err?.message || "Erreur de recherche");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: 16 }}>
      <h1>Recherche de films</h1>
      <form onSubmit={onSubmit} style={{ display: "flex", gap: 8 }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Ex: Matrix"
          style={{ flex: 1 }}
        />
        <button type="submit" disabled={loading}>Chercher</button>
      </form>

      {loading && <p style={{ marginTop: 16 }}>Chargement…</p>}
      {error && <p style={{ marginTop: 16, color: "#b91c1c" }}>{error}</p>}

      <div
        style={{
          marginTop: 16,
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
          gap: 12,
        }}
      >
        {results.map((m) => (
          <MovieCard key={m.id || m.tmdb_id || m.tmdbId} movie={m} />
        ))}
      </div>
    </div>
  );
}
