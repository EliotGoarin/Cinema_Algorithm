// web/src/api/client.js
const API_BASE = import.meta.env?.VITE_API_URL || "http://localhost:8000";

async function http(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    let text = "";
    try { text = await res.text(); } catch {}
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

// Recherche de films (GET /tmdb/search)
export const searchMovies = (q, page = 1) =>
  http(`/tmdb/search?q=${encodeURIComponent(q)}&page=${page}`);

// Détails d’un film (GET /tmdb/details)
export const getMovieDetails = (id) =>
  http(`/tmdb/details?id=${encodeURIComponent(id)}`);

// Recommandations (POST /recommend)
export const getRecommendations = (id, k = 12) =>
  http(`/recommend`, {
    method: "POST",
    body: JSON.stringify({ seed_ids: [Number(id)], k }),
  });
