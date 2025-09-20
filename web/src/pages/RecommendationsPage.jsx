import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { postRecommend, getMovieDetails } from "../api/client.js";
import MovieCard from "../components/MovieCard.jsx";

export default function RecommendationsPage() {
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [movie, setMovie] = useState(null);
  const [reco, setReco] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let on = true;
    (async () => {
      setLoading(true); setError("");
      try {
        const m = await getMovieDetails(id);
        if (on) setMovie(m);

        const data = await postRecommend([Number(id)], 12);
        if (on) setReco(Array.isArray(data.recommendations) ? data.recommendations : []);
      } catch (e) {
        if (on) setError(e?.message || "Erreur de recommandations");
      } finally {
        if (on) setLoading(false);
      }
    })();
    return () => { on = false; };
  }, [id]);

  if (loading) return <div style={{ padding: 16 }}>Recherche de recommandations…</div>;
  if (error) return <div style={{ padding: 16, color: "#ff6b6b" }}>{error}</div>;

  const title = movie?.title || movie?.original_title || `Film #${id}`;

  return (
    <div className="panel">
      <Link to={`/film/${id}`} className="backlink">← Retour au film</Link>
      <h2 className="section-title">Recommandations pour « {title} »</h2>
      <div className="grid">
        {reco.map(m => <MovieCard key={m.id} movie={m} />)}
      </div>
    </div>
  );
}
