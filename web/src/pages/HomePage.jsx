import { useState } from "react";
import { searchMovies } from "../api/client.js";
import MovieCard from "../components/MovieCard.jsx";
import AutoMasonry from "../components/AutoMasonry.jsx";

export default function HomePage() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  async function doSearch() {
    const term = q.trim();
    if (!term) {
      setError("Entrez un titre (au moins 1 caractère).");
      setResults([]);
      setHasSearched(false);
      return;
    }
    setHasSearched(true);
    setLoading(true);
    setError("");
    try {
      const data = await searchMovies(term, 1);
      setResults(Array.isArray(data.results) ? data.results : []);
    } catch (e) {
      setError(e.message || "Search error");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    doSearch();
  }

  return (
    <>
      <section className="panel hero-compact hero-center">
        <h1 className="hero-title">Ton prochain film préféré t'attend</h1>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Recherche par titre, et découvre des idées adaptées à tes goûts.
        </p>

        <form
          onSubmit={handleSubmit}
          style={{
            display: "grid",
            gridTemplateColumns: "1fr auto",
            gap: 12,
            width: "min(800px, 100%)",
            margin: "10px auto 0"
          }}
        >
          <input
            className="input"
            style={{ padding: "18px 18px" }}
            value={q}
            onChange={(e)=>setQ(e.target.value)}
            placeholder="Cherchez un film..."
          />
          <button
            type="submit"
            className="btn"
            disabled={loading || q.trim().length === 0}
            style={{ padding: "16px 20px", opacity: (loading || q.trim().length===0) ? .8 : 1 }}
          >
            {loading ? "…" : "Rechercher"}
          </button>
        </form>

        {error && <div style={{ color: "#ff6b6b", marginTop: 10 }}>{error}</div>}
      </section>

      {!hasSearched && (
        <section style={{ marginTop: 16 }}>
          <AutoMasonry limit={220} />
        </section>
      )}

      {hasSearched && (
        <section className="panel" style={{ marginTop: 16 }}>
          <h2 className="section-title">Résultats</h2>
          <div className="grid" style={{ paddingTop: 0 }}>
            {results.map(m => <MovieCard key={m.id} movie={m} />)}
            {(!results || results.length === 0) && !loading && !error && (
              <div style={{ padding: "0 16px 16px", color: "var(--muted)" }}>
                Aucun résultat{q.trim() ? ` pour « ${q.trim()} »` : ""}.
              </div>
            )}
          </div>
        </section>
      )}
    </>
  );
}
