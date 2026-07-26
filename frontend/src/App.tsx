import { useEffect, useState } from "react";

import {
  getHealth,
  type HealthResponse,
} from "./services/api";

import "./App.css";


function App() {
  const [health, setHealth] =
    useState<HealthResponse | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await getHealth();

        setHealth(response);
        setError(null);
      } catch (requestError) {
        const message =
          requestError instanceof Error
            ? requestError.message
            : "Could not connect to TestPilot API.";

        setError(message);
      }
    }

    void checkBackend();
  }, []);

  return (
    <main className="app">
      <section className="card">
        <p className="eyebrow">TESTPILOT AI</p>

        <h1>AI-powered web testing</h1>

        <p>
          Generate tests, run them with Playwright,
          and inspect structured bug reports.
        </p>

        {health && (
          <div className="status success">
            <span className="status-dot" />

            {health.service} API is connected
          </div>
        )}

        {!health && !error && (
          <div className="status">
            Checking backend connection...
          </div>
        )}

        {error && (
          <div className="status error">
            Backend connection failed: {error}
          </div>
        )}
      </section>
    </main>
  );
}

export default App;