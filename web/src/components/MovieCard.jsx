// web/src/components/MovieCard.jsx
import React from "react";
import "./tooltip.css";

export default function MovieCard({
  movie,
  posterBaseUrl = "https://image.tmdb.org/t/p/w342",
}) {
  const { tmdb_id, title, poster_path, reason, overview } = movie;
  const posterUrl = poster_path
    ? (poster_path.startsWith("http") ? poster_path : `${posterBaseUrl}${poster_path}`)
    : "/placeholder.png";

  const safeOverview = (overview || "").trim();
  const safeReason = (reason || "").trim();

  return (
    <div className="movie-card tooltip" data-testid={`movie-${tmdb_id}`}>
      <img className="movie-poster" src={posterUrl} alt={title} loading="lazy" />
      <div className="movie-title" title={title}>{title}</div>

      {/* Tooltip au survol */}
      <div
        className="tooltip-content"
        role="tooltip"
        aria-label={`${safeReason ? safeReason + ". " : ""}${safeOverview}`}
      >
        {safeReason && <strong className="tooltip-reason">{safeReason}</strong>}
        <div className="tooltip-overview">
          {safeOverview || "Pas de description disponible."}
        </div>
      </div>
    </div>
  );
}
