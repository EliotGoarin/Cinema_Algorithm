// src/pages/MoviePage.jsx
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
    async function load() {
      setLoading(true); setError("");
      try {
        const data = await getMovieDetails(id);
        if (on) setMovie(data);
      } catch (err) {
        if (on) setError(err.message || "Erreur de chargement");
      } finally {
        if (on) setLoading(false);
      }
    }
    load();
    return () => { on = false; };
  }, [id]);

  if (loading) return <div style={{padding:16}}>Chargement…</div>;
  if (error) return <div style={{padding:16, color:"#b91c1c"}}>{error}</div>;
  if (!movie) return <div style={{padding:16}}>Film introuvable.</div>;

  const title = movie.title || movie.original_title || "Titre inconnu";
  const poster = movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : null;

  return (
    <div style={{maxWidth:1000, margin:"0 auto", padding:16}}>
      <Link to="/" style={{display:"inline-block", marginBottom:12}}>← Retour</Link>
      <div style={{display:"grid", gridTemplateColumns:"180px 1fr", gap:16}}>
        {poster ? (
          <img src={poster} alt={`Affiche de ${title}`} style={{width:180, borderRadius:12}}/>
        ) : (
          <div style={{width:180, aspectRatio:"2/3", background:"#f3f4f6", borderRadius:12, display:"grid", placeItems:"center"}}>Pas d’affiche</div>
        )}

        <div>
          <h1 style={{marginTop:0}}>{title}</h1>
          {movie.release_date && <p>Sortie : {movie.release_date}</p>}
          {movie.genres && (
            <p>Genres : {Array.isArray(movie.genres)
              ? movie.genres.map(g=>g.name || g).join(", ")
              : String(movie.genres)}
            </p>
          )}
          {movie.director && <p>Réalisateur : {movie.director}</p>}
          {movie.cast && movie.cast.length > 0 && (
            <p>Acteurs : {movie.cast.slice(0,5).join(", ")}{movie.cast.length>5?"…":""}</p>
          )}
          {movie.overview && <p style={{marginTop:12, lineHeight:1.5}}>{movie.overview}</p>}

          <Link
            to={`/film/${id}/recommandations`}
            style={{display:"inline-block", marginTop:16, padding:"10px 16px", borderRadius:8, border:"1px solid #111827", background:"#111827", color:"#fff"}}
          >
            Recommander
          </Link>
        </div>
      </div>
    </div>
  );
}
