// src/pages/NotFound.jsx
import { Link } from "react-router-dom";
export default function NotFound() {
  return (
    <div style={{maxWidth:700, margin:"0 auto", padding:16}}>
      <h1>Page introuvable</h1>
      <p>La page demandée n’existe pas.</p>
      <Link to="/">← Retour à l’accueil</Link>
    </div>
  );
}
