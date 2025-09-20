import { Link } from "react-router-dom";

export default function MovieCard({ movie }) {
  const poster = movie?.poster_path
    ? `https://image.tmdb.org/t/p/w342${movie.poster_path}`
    : null;

  return (
    <Link to={`/film/${movie.id}`} className="card" title={movie.title || "Film"}>
      {poster ? (
        <img className="card-img" src={poster} alt={movie.title} loading="lazy" />
      ) : (
        <div className="card-img" />
      )}
      <div className="card-body">
        <h3 className="card-title">{movie.title || "(Sans titre)"}</h3>
        <p className="card-meta">{movie.release_date || "Date inconnue"}</p>
      </div>
    </Link>
  );
}
