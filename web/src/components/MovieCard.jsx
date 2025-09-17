// src/components/MovieCard.jsx
import { Link } from "react-router-dom";

export default function MovieCard({ movie }) {
  const id = movie.id || movie.tmdb_id || movie.tmdbId;
  const title = movie.title || movie.original_title || "Titre inconnu";
  const poster = movie.poster_path
    ? `https://image.tmdb.org/t/p/w342${movie.poster_path}`
    : null;

  return (
    <Link to={`/film/${id}`} className="movie-card" style={{textDecoration:"none"}}>
      <div style={{
        border:"1px solid #e5e7eb",
        borderRadius:12,
        overflow:"hidden",
        display:"flex",
        flexDirection:"column",
        height:"100%",
        background:"#fff"
      }}>
        {poster ? (
          <img src={poster} alt={`Affiche de ${title}`} style={{width:"100%", aspectRatio:"2/3", objectFit:"cover"}} />
        ) : (
          <div style={{width:"100%", aspectRatio:"2/3", display:"grid", placeItems:"center", background:"#f3f4f6"}}>
            <span>Pas d’affiche</span>
          </div>
        )}
        <div style={{padding:12}}>
          <div style={{fontWeight:600, color:"#111827"}}>{title}</div>
          {movie.release_date && (
            <div style={{fontSize:12, color:"#6b7280"}}>{movie.release_date?.slice(0,4)}</div>
          )}
        </div>
      </div>
    </Link>
  );
}
