// src/App.jsx
import { Routes, Route, Navigate } from "react-router-dom";
import SearchPage from "./pages/SearchPage.jsx";
import MoviePage from "./pages/MoviePage.jsx";
import RecommendationsPage from "./pages/RecommendationsPage.jsx";
import NotFound from "./pages/NotFound.jsx";

export default function App() {
  return (
    <div style={{minHeight:"100dvh", background:"#fafafa"}}>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/film/:id" element={<MoviePage />} />
        <Route path="/film/:id/recommandations" element={<RecommendationsPage />} />
        <Route path="/accueil" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
}
