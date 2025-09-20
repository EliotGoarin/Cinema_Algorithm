const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function jsonOrThrow(res, label) {
  const ct = res.headers.get("content-type") || "";
  const text = await res.text().catch(() => "");
  if (!res.ok) {
    let msg = text || res.statusText;
    if (res.status === 422) msg = "Entrez un titre (au moins 1 caractère).";
    if (ct.includes("application/json")) {
      try { msg = (JSON.parse(text).detail || msg); } catch {}
    }
    throw new Error(`${label} failed: ${msg}`);
  }
  return ct.includes("application/json") ? JSON.parse(text) : {};
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
    body: JSON.stringify({ seed_ids: seedIds.map(Number), k }),
  });
  return jsonOrThrow(r, "Recommend");
}
export async function getTopRated(limit = 160) {
  const r = await fetch(`${BASE}/catalog/top-rated?limit=${limit}`);
  return jsonOrThrow(r, "TopRated"); // {results:[{id,title,poster_path,..., local_score?}]}
}
