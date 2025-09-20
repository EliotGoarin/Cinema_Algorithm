import { useEffect, useMemo, useState } from "react";
import { useParams, Link, useSearchParams } from "react-router-dom";
import { postRecommend, getMovieDetails } from "../api/client.js";
import MovieCard from "../components/MovieCard.jsx";

const K_CHOICES = [4, 8, 12, 20, 50];

export default function RecommendationsPage() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialK = useMemo(() => {
    // priorité à l’URL, sinon mémoire locale, sinon 12
    const urlK = Number(searchParams.get("k"));
    if (Number.isInteger(urlK) && urlK > 0) return urlK;
    const saved = Number(localStorage.getItem("reco_k") || "");
    return Number.isInteger(saved) && saved > 0 ? saved : 12;
  }, [searchParams]);

  const [k, setK] = useState(initialK);
  const [loading, setLoading] = useState(true);
  const [movie, setMovie] = useState(null);
  const [reco, setReco] = useState([]);
  const [error, setError] = useState("");

  // recharge les recos quand id ou k changent
  useEffect(() => {
    let on = true;
    (async () => {
      setLoading(true); setError("");
      try {
        const m = await getMovieDetails(id);
        if (on) setMovie(m);

        const data = await postRecommend([Number(id)], k);
        if (on) setReco(Array.isArray(data.recommendations) ? data.recommendations : []);
      } catch (e) {
        if (on) setError(e?.message || "Erreur de recommandations");
      } finally {
        if (on) setLoading(false);
      }
    })();
    return () => { on = false; };
  }, [id, k]);

  // garde l’URL et le localStorage synchronisés
  useEffect(() => {
    const sp = new URLSearchParams(searchParams);
    sp.set("k", String(k));
    setSearchParams(sp, { replace: true });
    localStorage.setItem("reco_k", String(k));
  }, [k]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) return <div style={{ padding: 16 }}>Recherche de recommandations…</div>;
  if (error) return <div style={{ padding: 16, color: "#ff6b6b" }}>{error}</div>;

  const title = movie?.title || movie?.original_title || `Film #${id}`;

  return (
    <div className="panel">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px" }}>
        <Link to={`/film/${id}`} className="backlink">← Retour au film</Link>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <label htmlFor="kselect" style={{ color: "var(--muted)", fontSize: 14 }}>Nombre de recommandations</label>
          <select
            id="kselect"
            value={k}
            onChange={(e) => setK(Number(e.target.value))}
            className="input"
            style={{ width: 120, padding: "10px 12px" }}
          >
            {K_CHOICES.map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
      </div>

      <h2 className="section-title">Recommandations pour « {title} »</h2>
      <div className="grid">
        {reco.map(m => <MovieCard key={m.id} movie={m} />)}
      </div>
    </div>
  );
}
