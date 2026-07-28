import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import {
  getHealth,
  submitTest,
  type HealthResponse,
  type JobCreatedResponse,
} from "./services/api";

import "./App.css";


const DEFAULT_PAGE_URL =
  "file:///C:/Users/hp/Desktop/TestPilotAI/samples/locator_demo.html";

const DEFAULT_OBJECTIVE =
  "Test the login form and verify that signing in displays the welcome message.";


function App() {
  const [health, setHealth] =
    useState<HealthResponse | null>(null);

  const [healthError, setHealthError] =
    useState<string | null>(null);

  const [pageUrl, setPageUrl] =
    useState(DEFAULT_PAGE_URL);

  const [objective, setObjective] =
    useState(DEFAULT_OBJECTIVE);

  const [headless, setHeadless] =
    useState(true);

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const [submissionError, setSubmissionError] =
    useState<string | null>(null);

  const [submittedJob, setSubmittedJob] =
    useState<JobCreatedResponse | null>(null);


  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await getHealth();

        setHealth(response);
        setHealthError(null);
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Could not connect to the backend.";

        setHealthError(message);
      }
    }

    void checkBackend();
  }, []);


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setIsSubmitting(true);
    setSubmissionError(null);
    setSubmittedJob(null);

    try {
      const response = await submitTest({
        page_url: pageUrl.trim(),
        objective: objective.trim(),
        headless,
      });

      setSubmittedJob(response);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "The test job could not be submitted.";

      setSubmissionError(message);
    } finally {
      setIsSubmitting(false);
    }
  }


  const backendConnected = health !== null;


  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">
            TP
          </span>

          <div>
            <strong>TestPilot AI</strong>
            <span>Autonomous web testing</span>
          </div>
        </div>

        <div
          className={
            backendConnected
              ? "connection connected"
              : "connection disconnected"
          }
        >
          <span className="connection-dot" />

          {backendConnected
            ? "API connected"
            : "API disconnected"}
        </div>
      </header>

      <section className="hero">
        <p className="eyebrow">
          AI-POWERED QUALITY ASSURANCE
        </p>

        <h1>
          Test a website from a single objective.
        </h1>

        <p className="hero-description">
          TestPilot inspects the page, generates a
          structured test plan, runs it with Playwright,
          captures diagnostics, and produces bug reports.
        </p>
      </section>

      <section className="workspace">
        <form
          className="test-form"
          onSubmit={handleSubmit}
        >
          <div className="form-heading">
            <div>
              <p className="section-label">
                NEW TEST
              </p>

              <h2>Submit a website test</h2>
            </div>

            <span className="step-badge">
              Step 1
            </span>
          </div>

          <label className="field">
            <span>Website URL</span>

            <input
              type="text"
              value={pageUrl}
              onChange={(event) =>
                setPageUrl(event.target.value)
              }
              placeholder="https://example.com/login"
              required
            />

            <small>
              Public URLs, localhost, or file URLs,
              depending on backend security settings.
            </small>
          </label>

          <label className="field">
            <span>Testing objective</span>

            <textarea
              value={objective}
              onChange={(event) =>
                setObjective(event.target.value)
              }
              placeholder="Describe what TestPilot should verify."
              rows={6}
              minLength={5}
              maxLength={1000}
              required
            />

            <div className="field-footer">
              <small>
                Be specific about the expected result.
              </small>

              <small>
                {objective.length}/1000
              </small>
            </div>
          </label>

          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={headless}
              onChange={(event) =>
                setHeadless(event.target.checked)
              }
            />

            <span className="checkbox-copy">
              <strong>Run browser headlessly</strong>

              <small>
                Chromium runs without opening a visible
                browser window.
              </small>
            </span>
          </label>

          <button
            className="submit-button"
            type="submit"
            disabled={
              isSubmitting ||
              !backendConnected ||
              !pageUrl.trim() ||
              objective.trim().length < 5
            }
          >
            {isSubmitting
              ? "Submitting test..."
              : "Start automated test"}
          </button>

          {!backendConnected && (
            <p className="inline-message error-message">
              Start the FastAPI backend before submitting
              a test.
            </p>
          )}

          {healthError && (
            <p className="inline-message error-message">
              {healthError}
            </p>
          )}

          {submissionError && (
            <p className="inline-message error-message">
              {submissionError}
            </p>
          )}
        </form>

        <aside className="result-panel">
          <p className="section-label">
            LATEST SUBMISSION
          </p>

          {!submittedJob && (
            <div className="empty-state">
              <div className="empty-icon">
                ↗
              </div>

              <h3>No job submitted yet</h3>

              <p>
                Submit the form to create a background
                testing job.
              </p>
            </div>
          )}

          {submittedJob && (
            <div className="job-card">
              <div className="job-card-header">
                <div>
                  <span className="job-status">
                    <span className="status-dot" />

                    {submittedJob.status}
                  </span>

                  <h3>Test job accepted</h3>
                </div>

                <span className="accepted-code">
                  202
                </span>
              </div>

              <dl className="job-details">
                <div>
                  <dt>Job ID</dt>
                  <dd>{submittedJob.job_id}</dd>
                </div>

                <div>
                  <dt>Status endpoint</dt>
                  <dd>{submittedJob.status_url}</dd>
                </div>
              </dl>

              <p className="job-note">
                The background worker is now processing
                this test. Live polling will be added in
                the next step.
              </p>
            </div>
          )}
        </aside>
      </section>
    </main>
  );
}


export default App;