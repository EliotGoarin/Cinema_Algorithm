// web/src/App.jsx
import React, { useState } from "react";
import MovieCard from "./components/MovieCard";

// Base URL de l'API (configurable via Vite : VITE_API_BASE)
const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

// Petit helper pour bâtir l'URL d'affiche TMDb au besoin
const TMDB_POSTER_BASE = "https://image.tmdb.org/t/p/w342";
const posterUrl = (path) =>
  path ? (path.startsWith("http") ? path : `${TMDB_POSTER_BASE}${path}`) : "";

// Normalise un film TMDb (search) en { tmdb_id, title, poster_path }
function normalizeTmdbMovie(m) {
  return {
    tmdb_id: m.tmdb_id ?? m.id,
    title: m.title ?? m.original_title ?? "(sans titre)",
    poster_path: m.poster_path ?? null,
  };
}

export default function App() {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");

  const [seeds, setSeeds] = useState([]); // [{tmdb_id,title,poster_path}]
  const [recommendations, setRecommendations] = useState([]);
  const [recLoading, setRecLoading] = useState(false);
  const [recError, setRecError] = useState("");

  // --- Actions ---

  async function handleSearch(e) {
    e?.preventDefault?.();
    setSearchError("");
    setSearchLoading(true);
    setSearchResults([]);
    try {
      const res = await fetch(`${API_BASE}/tmdb/search?q=${encodeURIComponent(query)}&page=1`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      const results = (json.results || []).map(normalizeTmdbMovie);
      setSearchResults(results);
    } catch (err) {
      console.error(err);
      setSearchError("Recherche impossible. Vérifie l'API et la clé TMDb.");
    } finally {
      setSearchLoading(false);
    }
  }

  function addSeed(m) {
    if (!m?.tmdb_id) return;
    if (seeds.find((s) => s.tmdb_id === m.tmdb_id)) return;
    if (seeds.length >= 5) return;
    setSeeds((prev) => [...prev, m]);
  }

  function removeSeed(id) {
    setSeeds((prev) => prev.filter((s) => s.tmdb_id !== id));
  }

  async function handleRecommend() {
    setRecError("");
    setRecLoading(true);
    setRecommendations([]);
    try {
      const body = { seed_ids: seeds.map((s) => s.tmdb_id), k: 12 };
      const res = await fetch(`${API_BASE}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      const json = await res.json();
      // On s'attend à { results: [...] } avec reason + overview dans chaque item
      setRecommendations(json.results || []);
    } catch (err) {
      console.error(err);
      setRecError("Recommandation impossible. Assure-toi d'avoir ingéré des films et rafraîchi l'index.");
    } finally {
      setRecLoading(false);
    }
  }

  // --- UI ---

  return (
    <div style={styles.page}>
      <h1 style={{ margin: 0 }}>🎬 Cinema Recommender</h1>
      <p style={{ marginTop: 8, color: "#666" }}>
        Cherche un film, ajoute-en jusqu'à 5 comme références, puis clique sur <strong>Recommander</strong>.
        Passe la souris sur chaque affiche recommandée pour voir <em>pourquoi</em> (reason) et la <em>description</em> (overview).
      </p>

      {/* Barre de recherche */}
      <form onSubmit={handleSearch} style={styles.searchRow}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ex: Matrix"
          style={styles.input}
        />
        <button type="submit" style={styles.button} disabled={searchLoading || !query.trim()}>
          {searchLoading ? "Recherche..." : "Rechercher"}
        </button>
      </form>

      {/* Résultats de recherche */}
      {searchError && <div style={styles.error}>{searchError}</div>}
      {searchResults.length > 0 && (
        <>
          <h2 style={styles.h2}>Résultats</h2>
          <div style={styles.grid}>
            {searchResults.map((m) => (
              <div key={m.tmdb_id} style={styles.card}>
                {posterUrl(m.poster_path) ? (
                  <img src={posterUrl(m.poster_path)} alt={m.title} style={styles.poster} />
                ) : (
                  <div style={styles.posterPlaceholder}>No image</div>
                )}
                <div style={styles.cardBody}>
                  <div style={styles.titleLine} title={m.title}>
                    {m.title}
                  </div>
                  <button
                    style={styles.smallBtn}
                    onClick={() => addSeed(m)}
                    disabled={!!seeds.find((s) => s.tmdb_id === m.tmdb_id) || seeds.length >= 5}
                  >
                    + Ajouter
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Seeds sélectionnés */}
      <h2 style={styles.h2}>
        Vos films de référence {seeds.length > 0 ? `(${seeds.length}/5)` : ""}
      </h2>
      {seeds.length === 0 ? (
        <div style={{ color: "#777", marginBottom: 12 }}>Ajoute au moins un film.</div>
      ) : (
        <div style={styles.seedsRow}>
          {seeds.map((s) => (
            <div key={s.tmdb_id} style={styles.seedChip}>
              {posterUrl(s.poster_path) ? (
                <img src={posterUrl(s.poster_path)} alt={s.title} style={styles.seedPoster} />
              ) : (
                <div style={styles.seedPosterFallback}>?</div>
              )}
              <span style={{ marginLeft: 8, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={s.title}>
                {s.title}
              </span>
              <button onClick={() => removeSeed(s.tmdb_id)} style={styles.chipX}>
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Action recommander */}
      <div style={{ marginTop: 8, marginBottom: 24 }}>
        <button
          style={styles.primaryBtn}
          onClick={handleRecommend}
          disabled={recLoading || seeds.length === 0}
        >
          {recLoading ? "Calcul..." : "Recommander"}
        </button>
      </div>

      {/* Recommandations */}
      {recError && <div style={styles.error}>{recError}</div>}
      <h2 style={styles.h2}>Recommandations</h2>
      {recommendations.length === 0 ? (
        <div style={{ color: "#777" }}>Aucune recommandation pour le moment.</div>
      ) : (
        <div style={styles.grid}>
          {recommendations.map((r) => (
            <MovieCard key={r.tmdb_id || r.id} movie={r} />
          ))}
        </div>
      )}

      <footer style={styles.footer}>
        <small>
          API&nbsp;: <code>{API_BASE}</code>
        </small>
      </footer>
    </div>
  );
}

// --- Styles inline simples (tu peux migrer en CSS/Tailwind) ---
const styles = {
  page: { padding: 24, fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif" },
  searchRow: { display: "flex", gap: 8, alignItems: "center", marginTop: 12 },
  input: {
    flex: 1,
    padding: "10px 12px",
    borderRadius: 10,
    border: "1px solid #ddd",
    fontSize: 16,
  },
  button: {
    padding: "10px 14px",
    borderRadius: 10,
    border: "1px solid #ddd",
    background: "#f5f5f5",
    cursor: "pointer",
  },
  primaryBtn: {
    padding: "12px 16px",
    borderRadius: 12,
    border: "none",
    background: "#111827",
    color: "#fff",
    cursor: "pointer",
    fontWeight: 600,
  },
  smallBtn: {
    padding: "6px 10px",
    borderRadius: 8,
    border: "1px solid #ddd",
    background: "#fff",
    cursor: "pointer",
    fontSize: 13,
  },
  h2: { marginTop: 24, marginBottom: 12 },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
    gap: 16,
  },
  card: {
    border: "1px solid #eee",
    borderRadius: 12,
    padding: 10,
    background: "#fff",
    boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
  },
  poster: { width: "100%", height: "auto", borderRadius: 10, display: "block" },
  posterPlaceholder: {
    width: "100%",
    aspectRatio: "2/3",
    borderRadius: 10,
    background: "#f0f0f0",
    color: "#999",
    display: "grid",
    placeItems: "center",
  },
  cardBody: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, marginTop: 8 },
  titleLine: {
    fontWeight: 600,
    fontSize: 14,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    flex: 1,
  },
  seedsRow: { display: "flex", flexWrap: "wrap", gap: 8 },
  seedChip: {
    display: "inline-flex",
    alignItems: "center",
    borderRadius: 999,
    background: "#f5f5f5",
    padding: "4px 8px 4px 4px",
  },
  seedPoster: { width: 28, height: 42, objectFit: "cover", borderRadius: 6 },
  seedPosterFallback: {
    width: 28,
    height: 42,
    borderRadius: 6,
    background: "#e5e5e5",
    display: "grid",
    placeItems: "center",
    color: "#888",
    fontWeight: 700,
  },
  chipX: {
    marginLeft: 8,
    border: "none",
    background: "transparent",
    fontSize: 14,
    cursor: "pointer",
    color: "#666",
  },
  error: {
    marginTop: 10,
    marginBottom: 8,
    padding: "10px 12px",
    borderRadius: 10,
    background: "#fee2e2",
    color: "#991b1b",
    border: "1px solid #fecaca",
  },
  footer: { marginTop: 40, color: "#888" },
};
