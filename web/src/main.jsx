import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";

function bootError(e) {
  const el = document.getElementById("root");
  if (el) {
    el.innerHTML = `<pre style="white-space:pre-wrap;color:#b91c1c;padding:16px">Boot error: ${String(
      e?.message || e
    )}</pre>`;
  }
  console.error("Boot error:", e);
}

try {
  ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </React.StrictMode>
  );
} catch (e) {
  bootError(e);
}
