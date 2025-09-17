// src/pages/RecommendationsPage.jsx
import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getRecommendations, getMovieDetails } from "../api/client.js";
import MovieCard from "../components/MovieCard.jsx";

export default function RecommendationsPage() {
  const { id } = useParams();
  const [seed, setSeed] = useState(null);
  const [recs, setRecs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let on = true;
    async function load() {
      setLoading(true); setError(""); setRecs([]); setSeed(null);
      try {
        // Charger le film de référence (pour l'afficher en haut)
        const seedMovie = await getMovieDetails(id);
        if (on) setSeed(seedMovie);

        // Charger les recommandations
        const data = await getRecommendations(id);
        const list = Array.isArray(data) ? data : (data.results || data.recommendations || []);

        // Nettoyage : enlever doublons + enlever le film seed
        const seen = new Set([Number(id)]);
        const unique = [];
        for (const m of list || []) {
          const mid = Number(m.id || m.tmdb_id || m.tmdbId);
          if (!mid || seen.has(mid)) continue;
          seen.add(mid);
          unique.push(m);
        }

        if (on) setRecs(unique);
      } catch (err) {
        if (on) setError(err.message || "Erreur de chargement");
      } finally {
        if (on) setLoading(false);
      }
    }
    load();
    return () => { on = false; };
  }, [id]);

  return (
    <div style={{maxWidth:1000, margin:"0 auto", padding:16}}>
      <Link to={`/film/${id}`} style={{display:"inline-block", marginBottom:12}}>← Retour au film</Link>
      <h1>Recommandations</h1>
      {seed && (
        <p style={{marginTop:4, color:"#6b7280"}}>
          Basées sur : <strong>{seed.title || seed.original_title}</strong>
        </p>
      )}

      {loading && <p>Chargement…</p>}
      {error && <p style={{color:"#b91c1c"}}>{error}</p>}
      {!loading && !error && recs.length === 0 && <p>Aucune recommandation trouvée.</p>}

      <div style={{
        marginTop:16,
        display:"grid",
        gridTemplateColumns:"repeat(auto-fill, minmax(160px, 1fr))",
        gap:12
      }}>
        {recs.map((m) => <MovieCard key={m.id || m.tmdb_id} movie={m} />)}
      </div>
    </div>
  );
}
