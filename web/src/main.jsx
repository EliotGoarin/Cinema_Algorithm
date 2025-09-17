// src/main.jsx (ou src/index.jsx)
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter /* basename={import.meta.env.BASE_URL} si déployé en sous-chemin */>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
