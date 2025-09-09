const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function searchMovies(query) {
  const res = await fetch(`${API_BASE}/tmdb/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error("Erreur recherche TMDb");
  return res.json();
}

export async function ingestAndAdd(query) {
  const res = await fetch(`${API_BASE}/ingest/search_and_add?q=${encodeURIComponent(query)}`, { method: "POST" });
  if (!res.ok) throw new Error("Erreur ingestion film");
  return res.json();
}

export async function getRecommendations(seedIds, k = 5) {
  const res = await fetch(`${API_BASE}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed_ids: seedIds, k }),
  });
  if (!res.ok) throw new Error("Erreur recommandations");
  return res.json();
}

export async function refreshCache() {
  const res = await fetch(`${API_BASE}/admin/refresh_cache`, { method: "POST" });
  if (!res.ok) throw new Error("Erreur refresh cache");
  return res.json();
}
