const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function tmdbSearch(q) {
  const r = await fetch(`${API_BASE}/tmdb/search?q=${encodeURIComponent(q)}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function ingestSearchAndAdd(q) {
  const r = await fetch(`${API_BASE}/ingest/search_and_add?q=${encodeURIComponent(q)}`, { method: "POST" });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function recommend(seedIds, k = 10) {
  const r = await fetch(`${API_BASE}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed_ids: seedIds, k })
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
