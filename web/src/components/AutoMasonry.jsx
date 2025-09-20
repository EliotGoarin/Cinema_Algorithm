import { useEffect, useMemo, useState } from "react";
import { getTopRated } from "../api/client.js";

function ratingBadgeClass(scorePct){
  const n = Math.round(scorePct || 0);
  if (n >= 85) return "badge";
  if (n >= 70) return "badge warn";
  return "badge low";
}

function splitColumns(arr, cols){
  const out = Array.from({ length: cols }, () => []);
  arr.forEach((item, i) => out[i % cols].push(item));
  return out;
}

function calcCols(w){
  if (w >= 1680) return 6;
  if (w >= 1360) return 5;
  if (w >= 1024) return 4;
  if (w >= 760)  return 3;
  return 2;
}

/** Mur d’affiches auto-défilant — source: /catalog/top-rated */
export default function AutoMasonry({ limit = 160 }) {
  const [movies, setMovies] = useState([]);
  const [cols, setCols] = useState(() =>
    typeof window !== "undefined" ? calcCols(window.innerWidth) : 4
  );
  const [error, setError] = useState("");

  useEffect(() => {
    let on = true;
    (async () => {
      setError("");
      try {
        const data = await getTopRated(limit);
        // garde uniquement ceux qui ont un poster
        const list = (data.results || []).filter(m => m.poster_path);
        if (on) {
          setMovies(list);
          if (list.length === 0) {
            setError("Aucune donnée locale ‘mieux notés’. Vérifiez votre DB/JSON.");
          }
        }
      } catch (e) {
        if (on) setError(e?.message || "Chargement des mieux notés impossible.");
      }
    })();
    return () => { on = false; };
  }, [limit]);

  useEffect(() => {
    function onResize(){ setCols(calcCols(window.innerWidth)); }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const columns = useMemo(() => splitColumns(movies, cols), [movies, cols]);

  if (error) {
    return (
      <div className="panel" style={{ padding: 16, textAlign: "center" }}>
        {error}
      </div>
    );
  }

  return (
    <div className="masonry-hero">
      <div className="rail" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
        {columns.map((col, idx) => {
          const dur = 48 + (idx * 6);
          const stack = [...col, ...col]; // duplication pour loop infini
          return (
            <div key={idx} className="rail-col" style={{ ["--dur"]: `${dur}s` }}>
              {stack.map((m, i) => {
                const poster = `https://image.tmdb.org/t/p/w342${m.poster_path}`;
                const hasLocal = Number.isFinite(m?.local_score); // ← badge seulement si score local
                const badgeVal = hasLocal ? Math.round(m.local_score) : null;

                return (
                  <a key={`${m.id}-${i}`} className="rail-card" href={`/film/${m.id}`} title={m.title}>
                    <img className="rail-poster" src={poster} alt={m.title} loading="lazy" />
                    {hasLocal && (
                      <span
                        className={ratingBadgeClass(badgeVal)}
                        title={`Score local: ${badgeVal}/100`}
                      >
                        {badgeVal}
                      </span>
                    )}
                  </a>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
