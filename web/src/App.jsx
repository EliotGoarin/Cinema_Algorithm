import { useState } from "react";
import {
  searchMovies,
  ingestAndAdd,
  getRecommendations,
  refreshCache,
} from "./apiClient";

// Utilitaire pour normaliser les posters (API peut renvoyer URL complète ou juste le path)
const posterUrl = (p) => {
  if (!p) return null;
  return typeof p === "string" && p.startsWith("http")
    ? p
    : `https://image.tmdb.org/t/p/w200${p}`;
};

export default function App() {
  // Recherche
  const [query, setQuery] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [results, setResults] = useState([]);

  // Seeds (films choisis par l'utilisateur)
  const [seeds, setSeeds] = useState([]); // [{ id, title }]
  const [k, setK] = useState(10);

  // Recommandations
  const [recoLoading, setRecoLoading] = useState(false);
  const [recoError, setRecoError] = useState("");
  const [recommendations, setRecommendations] = useState([]);

  // Actions
  const onSearch = async (e) => {
    e?.preventDefault?.();
    setSearchError("");
    setSearchLoading(true);
    try {
      if (!query.trim()) {
        setResults([]);
        return;
      }
      const data = await searchMovies(query.trim());
      setResults(Array.isArray(data?.results) ? data.results : []);
    } catch (err) {
      console.error(err);
      setSearchError("Erreur lors de la recherche TMDb.");
    } finally {
      setSearchLoading(false);
    }
  };

  const onIngest = async (title) => {
    try {
      const data = await ingestAndAdd(title);
      // On alerte succès (pour remplacer l'ancienne pop-up d'erreur)
      alert(`Film ingéré: ${data.movie.title} (id: ${data.movie.id})`);
    } catch (err) {
      console.error(err);
      alert("Erreur ingestion");
    }
  };

  const addSeed = (movie) => {
    if (!movie || !movie.id) return;
    setSeeds((prev) => {
      if (prev.some((m) => m.id === movie.id)) return prev;
      return [...prev, { id: movie.id, title: movie.title ?? "(sans titre)" }];
    });
  };

  const removeSeed = (id) => {
    setSeeds((prev) => prev.filter((m) => m.id !== id));
  };

  const onRecommend = async () => {
    setRecoError("");
    setRecoLoading(true);
    try {
      if (seeds.length === 0) {
        setRecommendations([]);
        return;
      }
      const ids = seeds.map((s) => s.id);
      const data = await getRecommendations(ids, Number(k) || 10);
      const recs = Array.isArray(data?.recommendations) ? data.recommendations : [];
      setRecommendations(recs);
      // Sanity check: ne pas contenir les seeds
      const seedSet = new Set(ids);
      const overlaps = recs.filter((r) => seedSet.has(r.tmdb_id));
      if (overlaps.length > 0) {
        console.warn("Ces résultats contiennent au moins un seed (ne devrait pas arriver):", overlaps);
      }
    } catch (err) {
      console.error(err);
      setRecoError("Erreur lors de la récupération des recommandations.");
    } finally {
      setRecoLoading(false);
    }
  };

  const onRefreshCache = async () => {
    try {
      await refreshCache();
      alert("Cache du modèle reconstruit.");
    } catch (err) {
      console.error(err);
      alert("Erreur lors du refresh du cache.");
    }
  };

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={{ margin: 0 }}>🎬 Movie Recommender (dev)</h1>
        <div style={styles.headerActions}>
          <button onClick={onRefreshCache} style={styles.buttonSecondary}>
            Rafraîchir cache modèle
          </button>
        </div>
      </header>

      {/* Bloc Recherche */}
      <section style={styles.section}>
        <h2 style={styles.h2}>Recherche TMDb</h2>
        <form onSubmit={onSearch} style={styles.formRow}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Titre du film (ex: Matrix)"
            style={styles.input}
          />
          <button type="submit" disabled={searchLoading} style={styles.button}>
            {searchLoading ? "Recherche..." : "Rechercher"}
          </button>
          <button
            type="button"
            onClick={() => onIngest(query.trim())}
            disabled={!query.trim()}
            style={styles.buttonSecondary}
            title="Ingestion rapide : ingère le premier résultat TMDb pour cette requête"
          >
            Ingérer (par recherche)
          </button>
        </form>
        {searchError && <p style={styles.error}>{searchError}</p>}

        {results.length > 0 && (
          <div style={styles.grid}>
            {results.map((m) => {
              const img = posterUrl(m.poster_path);
              const year = (m.release_date || "").slice(0, 4);
              return (
                <div key={m.id} style={styles.card}>
                  {img ? (
                    <img src={img} alt={m.title} style={styles.poster} />
                  ) : (
                    <div style={styles.posterPlaceholder}>No image</div>
                  )}
                  <div style={styles.cardBody}>
                    <div style={styles.titleLine}>
                      <strong>{m.title || "(sans titre)"}</strong>
                      {year ? <span style={styles.year}> {year}</span> : null}
                    </div>
                    <div style={styles.rowBtns}>
                      <button onClick={() => addSeed(m)} style={styles.buttonSmall}>
                        Sélectionner
                      </button>
                      <button onClick={() => onIngest(m.title || "")} style={styles.buttonSmallGhost}>
                        Ingérer ce film
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Bloc Seeds */}
      <section style={styles.section}>
        <h2 style={styles.h2}>Films sélectionnés (seeds)</h2>
        {seeds.length === 0 ? (
          <p style={styles.muted}>Aucun seed sélectionné.</p>
        ) : (
          <ul style={styles.seedList}>
            {seeds.map((s) => (
              <li key={s.id} style={styles.seedItem}>
                <span>{s.title}</span>
                <button onClick={() => removeSeed(s.id)} style={styles.removeBtn}>
                  Retirer
                </button>
              </li>
            ))}
          </ul>
        )}
        <div style={styles.formRow}>
          <label>
            k&nbsp;
            <input
              type="number"
              min={1}
              max={50}
              value={k}
              onChange={(e) => setK(e.target.value)}
              style={styles.kInput}
            />
          </label>
          <button onClick={onRecommend} disabled={recoLoading || seeds.length === 0} style={styles.button}>
            {recoLoading ? "Calcul..." : "Recommander"}
          </button>
        </div>
        {recoError && <p style={styles.error}>{recoError}</p>}
      </section>

      {/* Bloc Recommandations */}
      <section style={styles.section}>
        <h2 style={styles.h2}>Recommandations</h2>
        {recommendations.length === 0 ? (
          <p style={styles.muted}>Aucune recommandation à afficher.</p>
        ) : (
          <div style={styles.grid}>
            {recommendations.map((r) => {
              const img = posterUrl(r.poster_path);
              return (
                <div key={r.tmdb_id || r.id} style={styles.card}>
                  {img ? (
                    <img src={img} alt={r.title || r.tmdb_id} style={styles.poster} />
                  ) : (
                    <div style={styles.posterPlaceholder}>No image</div>
                  )}
                  <div style={styles.cardBody}>
                    <strong>{r.title || `(id: ${r.tmdb_id || r.id})`}</strong>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <footer style={styles.footer}>
        <small>API base: {import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000"}</small>
      </footer>
    </div>
  );
}

// Styles inline simples (tu pourras passer à Tailwind ensuite)
const styles = {
  page: {
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
    padding: "16px",
    background: "#0b0e14",
    color: "#e6e6e6",
    minHeight: "100vh",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "12px",
  },
  headerActions: { display: "flex", gap: 8 },
  section: { marginTop: 24 },
  h2: { margin: "8px 0 12px 0" },
  formRow: { display: "flex", gap: 8, alignItems: "center", marginBottom: 12, flexWrap: "wrap" },
  input: {
    padding: "8px 10px",
    borderRadius: 8,
    border: "1px solid #333",
    background: "#121826",
    color: "#e6e6e6",
    minWidth: 280,
  },
  kInput: {
    padding: "6px 8px",
    borderRadius: 8,
    border: "1px solid #333",
    background: "#121826",
    color: "#e6e6e6",
    width: 64,
  },
  button: {
    padding: "8px 12px",
    borderRadius: 10,
    border: "1px solid #2f6feb",
    background: "#2f6feb",
    color: "white",
    cursor: "pointer",
  },
  buttonSecondary: {
    padding: "8px 12px",
    borderRadius: 10,
    border: "1px solid #3b3b3b",
    background: "#1c2231",
    color: "#e6e6e6",
    cursor: "pointer",
  },
  buttonSmall: {
    padding: "6px 8px",
    borderRadius: 8,
    border: "1px solid #2f6feb",
    background: "#2f6feb",
    color: "white",
    cursor: "pointer",
    fontSize: 12,
  },
  buttonSmallGhost: {
    padding: "6px 8px",
    borderRadius: 8,
    border: "1px solid #3b3b3b",
    background: "transparent",
    color: "#e6e6e6",
    cursor: "pointer",
    fontSize: 12,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
    gap: 12,
  },
  card: {
    background: "#111827",
    border: "1px solid #1f2937",
    borderRadius: 12,
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
  },
  poster: { width: "100%", height: 270, objectFit: "cover", background: "#0f172a" },
  posterPlaceholder: {
    width: "100%",
    height: 270,
    display: "grid",
    placeItems: "center",
    background: "#0f172a",
    color: "#94a3b8",
    fontSize: 12,
  },
  cardBody: { padding: 10, display: "grid", gap: 8 },
  titleLine: { display: "flex", gap: 6, alignItems: "baseline", flexWrap: "wrap" },
  year: { color: "#9ca3af", fontSize: 13 },
  rowBtns: { display: "flex", gap: 8 },
  seedList: { listStyle: "none", padding: 0, margin: "6px 0 12px 0", display: "flex", gap: 8, flexWrap: "wrap" },
  seedItem: {
    display: "flex",
    gap: 8,
    alignItems: "center",
    background: "#111827",
    border: "1px solid #1f2937",
    borderRadius: 999,
    padding: "6px 10px",
  },
  removeBtn: {
    border: "none",
    background: "transparent",
    color: "#f87171",
    cursor: "pointer",
    fontSize: 12,
  },
  muted: { color: "#9ca3af" },
  error: { color: "#f87171" },
  footer: { marginTop: 32, color: "#9ca3af" },
};
