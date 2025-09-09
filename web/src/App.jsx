import { useState } from "react";
import { tmdbSearch, ingestSearchAndAdd, recommend } from "./apiClient";

export default function App() {
  const [q, setQ] = useState("Inception");
  const [seed, setSeed] = useState("27205");
  const [log, setLog] = useState("");
  const [recs, setRecs] = useState([]);

  const onSearch = async () => {
    setLog("Recherche en cours...");
    try { setLog(JSON.stringify(await tmdbSearch(q), null, 2)); }
    catch (e) { setLog("Erreur: " + e.message); }
  };

  const onAdd = async () => {
    setLog("Ajout en cours...");
    try { setLog(JSON.stringify(await ingestSearchAndAdd(q), null, 2)); }
    catch (e) { setLog("Erreur: " + e.message); }
  };

  const onReco = async () => {
    const ids = seed.split(",").map(s => parseInt(s, 10)).filter(Boolean);
    try { setRecs((await recommend(ids, 10)).recommendations || []); }
    catch (e) { setLog("Erreur: " + e.message); }
  };

  return (
    <div style={{ padding: 16, fontFamily: "sans-serif" }}>
      <h2>🎬 Ingestion TMDB</h2>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher un film..." style={{ marginRight: 8, padding: 4 }}/>
      <button onClick={onSearch}>Rechercher</button>
      <button onClick={onAdd} style={{ marginLeft: 8 }}>Chercher + Ajouter</button>
      <pre style={{ whiteSpace: "pre-wrap", background: "#f5f5f5", padding: 8, marginTop: 8 }}>{log}</pre>

      <h2 style={{ marginTop: 24 }}>⭐ Recommandations</h2>
      <input value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="tmdb_id, ex: 27205" style={{ marginRight: 8, padding: 4 }}/>
      <button onClick={onReco}>Recommander</button>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, 140px)", gap: 12, marginTop: 12 }}>
        {recs.map(r => (
          <div key={r.tmdb_id} style={{ border: "1px solid #ddd", padding: 8 }}>
            {r.poster_path && <img src={r.poster_path} alt="" style={{ width: "100%", height: "auto" }} />}
            <div style={{ fontSize: 12, marginTop: 6 }}>{r.title}</div>
            <div style={{ color: "#888", fontSize: 11 }}>#{r.tmdb_id}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
