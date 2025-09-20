const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function jsonOrThrow(res, label) {
  if (!res.ok) {
    const txt = await res.text().catch(() => res.statusText);
    throw new Error(`${label} failed: ${txt}`);
  }
  return res.json();
}

export async function searchMovies(q, page = 1) {
  const r = await fetch(`${BASE}/tmdb/search?q=${encodeURIComponent(q)}&page=${page}`);
  return jsonOrThrow(r, "Search");
}

export async function getMovieDetails(id) {
  const r = await fetch(`${BASE}/tmdb/details?id=${encodeURIComponent(id)}`);
  return jsonOrThrow(r, "Details");
}

export async function postRecommend(seedIds, k = 12) {
  const r = await fetch(`${BASE}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed_ids: seedIds.map(Number), k })
  });
  return jsonOrThrow(r, "Recommend");
}
