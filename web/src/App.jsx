import { Routes, Route, Link } from "react-router-dom";
import HomePage from "./pages/HomePage.jsx";
import MoviePage from "./pages/MoviePage.jsx";
import RecommendationsPage from "./pages/RecommendationsPage.jsx";

function Frame({ children }) {
  return (
    <div className="container">
      <header className="header">
        <Link to="/" className="brand">
          <div className="brand-badge" />
          <h1 className="brand-title">Movie Algorithm</h1>
        </Link>
        <nav>
          <a className="btn ghost" href="https://www.themoviedb.org/" target="_blank">TMDb</a>
        </nav>
      </header>
      {children}
      <footer style={{ marginTop: 28, color: "var(--muted)" }}>
        © {new Date().getFullYear()} — Movie Algorithm
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Frame><HomePage /></Frame>} />
      <Route path="/film/:id" element={<Frame><MoviePage /></Frame>} />
      <Route path="/film/:id/recommandations" element={<Frame><RecommendationsPage /></Frame>} />
      <Route path="*" element={<Frame><div>Page introuvable — <Link to="/" className="backlink">Retour</Link></div></Frame>} />
    </Routes>
  );
}
