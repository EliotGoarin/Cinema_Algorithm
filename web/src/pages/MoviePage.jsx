import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getMovieDetails } from "../api/client.js";

export default function MoviePage() {
  const { id } = useParams();
  const [movie, setMovie] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let on = true;
    (async () => {
      setLoading(true); setError("");
      try {
        const m = await getMovieDetails(id);
        if (on) setMovie(m);
      } catch (e) {
        if (on) setError(e.message || "Erreur de chargement");
      } finally {
        if (on) setLoading(false);
      }
    })();
    return () => { on = false; };
  }, [id]);

  if (loading) return <div style={{ padding: 16 }}>Chargement…</div>;
  if (error) return <div style={{ padding: 16, color: "#ff6b6b" }}>{error}</div>;
  if (!movie) return <div style={{ padding: 16 }}>Film introuvable.</div>;

  const title = movie.title || movie.original_title || `Film #${id}`;
  const poster = movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : null;

  return (
    <div className="panel">
      <Link to="/" className="backlink">← Retour</Link>

      <div className="hero">
        <div className="poster">
          {poster ? <img src={poster} alt={title} style={{ width:"100%", display:"block" }} /> : null}
        </div>
        <div className="meta">
          <h1 style={{ margin: "0 0 6px" }}>{title}</h1>
          {movie.release_date && <p>Sortie : {movie.release_date}</p>}
          {movie.genres && (
            <p>Genres : {Array.isArray(movie.genres) ? movie.genres.map(g => g?.name || g).filter(Boolean).join(", ") : String(movie.genres)}</p>
          )}
          {movie.overview && <p style={{ lineHeight: 1.6, color:"#cbd5e1" }}>{movie.overview}</p>}

          <Link to={`/film/${id}/recommandations`} className="btn" style={{ display:"inline-block", marginTop: 8 }}>
            Voir les recommandations
          </Link>
        </div>
      </div>

      <div className="hr" />
    </div>
  );
}
