const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function searchMovies(query) {
  const res = await fetch(`${API_BASE}/tmdb/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error("Erreur recherche TMDb");
  return res.json();
}

export async function ingestAndAdd(query) {
  const res = await fetch(`${API_BASE}/ingest/search_and_add?q=${encodeURIComponent(query)}`, { method: "POST" });
  if (!res.ok) throw new Error(`Erreur ingestion film (HTTP ${res.status})`);
  const json = await res.json();

  // Façonner le payload attendu par App.jsx => data.movie.title
  const id =
    json?.id ??
    json?.ingested?.ingested ??
    json?.selected?.id ??
    null;

  const title =
    json?.title ??
    json?.ingested?.title ??
    json?.selected?.title ??
    "";

  if (!id) {
    console.error("Payload ingestion inattendu:", json);
    throw new Error("Erreur ingestion film (payload)");
  }

  return { ok: true, movie: { id, title } };
}

export async function getRecommendations(seedIds, k = 5) {
  const res = await fetch(`${API_BASE}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed_ids: seedIds, k }),
  });
  if (!res.ok) throw new Error("Erreur recommandations");
  const json = await res.json();

  // Normaliser -> App.jsx lit data.recommendations
  const items = (json?.results ?? json?.recommendations ?? []).map((r) => {
    // si l'API a déjà une URL complète, on la garde; sinon on préfixe côté UI
    const p = r?.poster_path;
    const poster =
      typeof p === "string" && p.startsWith("http")
        ? p
        : p || null;
    return { ...r, poster_path: poster };
  });

  return { recommendations: items };
}

export async function refreshCache() {
  // Endpoint correct côté backend
  const res = await fetch(`${API_BASE}/refresh`, { method: "POST" });
  if (!res.ok) throw new Error("Erreur refresh cache");
  return res.json();
}
