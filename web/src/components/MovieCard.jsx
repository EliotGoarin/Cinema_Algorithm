// web/src/components/MovieCard.jsx
import React from "react";
import "./tooltip.css";

export default function MovieCard({ movie, posterBaseUrl }) {
  const { tmdb_id, title, poster_path, reason, overview } = movie;
  const posterUrl = poster_path ? `${posterBaseUrl}${poster_path}` : "/placeholder.png";

  return (
    <div className="movie-card tooltip" data-testid={`movie-${tmdb_id}`}>
      <img className="movie-poster" src={posterUrl} alt={title} loading="lazy" />
      <div className="movie-title">{title}</div>

      <div className="tooltip-content" role="tooltip" aria-label={`${reason}. ${overview}`}>
        {reason ? <strong className="tooltip-reason">{reason}</strong> : null}
        {overview ? <div className="tooltip-overview">{overview}</div> : <div className="tooltip-overview">Pas de description disponible.</div>}
      </div>
    </div>
  );
}
