import {
  type FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  getHealth,
  getJob,
  listJobs,
  submitTest,
  type HealthResponse,
  type JobCreatedResponse,
  type TestJob,
} from "./services/api";

import "./App.css";


const DEFAULT_PAGE_URL =
  "file:///C:/Users/hp/Desktop/TestPilotAI/samples/locator_demo.html";

const DEFAULT_OBJECTIVE =
  "Test the login form and verify that signing in displays the welcome message.";


function formatDate(
  value: string,
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}


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

  const [currentJob, setCurrentJob] =
    useState<TestJob | null>(null);

  const [pollingError, setPollingError] =
    useState<string | null>(null);

  const [jobs, setJobs] =
    useState<TestJob[]>([]);

  const [isLoadingJobs, setIsLoadingJobs] =
    useState(false);

  const [historyError, setHistoryError] =
    useState<string | null>(null);


  const loadJobs = useCallback(
    async (): Promise<void> => {
      setIsLoadingJobs(true);
      setHistoryError(null);

      try {
        const response = await listJobs(20);

        setJobs(response.jobs);
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Could not load job history.";

        setHistoryError(message);
      } finally {
        setIsLoadingJobs(false);
      }
    },
    [],
  );


  useEffect(() => {
    async function checkBackend(): Promise<void> {
      try {
        const response = await getHealth();

        setHealth(response);
        setHealthError(null);
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Could not connect to the backend.";

        setHealth(null);
        setHealthError(message);
      }
    }

    void checkBackend();
  }, []);


  useEffect(() => {
    void loadJobs();
  }, [loadJobs]);


  useEffect(() => {
    const activeJobId = submittedJob?.job_id;

    if (!activeJobId) {
      return;
    }

    let stopped = false;
    let timeoutId: number | undefined;

    async function pollJob(
      jobId: string,
    ): Promise<void> {
      try {
        const job = await getJob(jobId);

        if (stopped) {
          return;
        }

        setCurrentJob(job);
        setPollingError(null);

        const isStillProcessing =
          job.status === "queued" ||
          job.status === "running";

        if (isStillProcessing) {
          timeoutId = window.setTimeout(
            () => {
              void pollJob(jobId);
            },
            2000,
          );
        } else {
          void loadJobs();
        }
      } catch (error) {
        if (stopped) {
          return;
        }

        const message =
          error instanceof Error
            ? error.message
            : "Could not retrieve the job status.";

        setPollingError(message);

        timeoutId = window.setTimeout(
          () => {
            void pollJob(jobId);
          },
          3000,
        );
      }
    }

    void pollJob(activeJobId);

    return () => {
      stopped = true;

      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [
    submittedJob?.job_id,
    loadJobs,
  ]);


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    setIsSubmitting(true);
    setSubmissionError(null);
    setSubmittedJob(null);
    setCurrentJob(null);
    setPollingError(null);

    try {
      const response = await submitTest({
        page_url: pageUrl.trim(),
        objective: objective.trim(),
        headless,
      });

      setSubmittedJob(response);

      void loadJobs();
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


  function handleSelectJob(
    job: TestJob,
  ): void {
    setCurrentJob(job);

    setSubmittedJob({
      job_id: job.job_id,
      status: job.status,
      status_url: `/tests/jobs/${job.job_id}`,
    });

    setPollingError(null);
    setSubmissionError(null);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }


  const backendConnected = health !== null;

  const liveJobStatus =
    currentJob?.status ??
    submittedJob?.status ??
    null;


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
              <strong>
                Run browser headlessly
              </strong>

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
            SELECTED JOB
          </p>

          {!submittedJob && (
            <div className="empty-state">
              <div className="empty-icon">
                ↗
              </div>

              <h3>No job selected</h3>

              <p>
                Submit a new job or open one from the
                history section below.
              </p>
            </div>
          )}

          {submittedJob && (
            <div className="job-card">
              <div className="job-card-header">
                <div>
                  <span
                    className={`job-status ${
                      liveJobStatus ?? ""
                    }`}
                  >
                    <span className="status-dot" />

                    {liveJobStatus}
                  </span>

                  <h3>
                    {liveJobStatus === "completed"
                      ? "Test completed"
                      : liveJobStatus === "failed"
                        ? "Test failed"
                        : liveJobStatus === "cancelled"
                          ? "Test cancelled"
                          : "Test in progress"}
                  </h3>
                </div>

                {(liveJobStatus === "queued" ||
                  liveJobStatus === "running") && (
                  <span className="live-indicator">
                    LIVE
                  </span>
                )}
              </div>

              <dl className="job-details">
                <div>
                  <dt>Job ID</dt>
                  <dd>{submittedJob.job_id}</dd>
                </div>

                {currentJob && (
                  <>
                    <div>
                      <dt>Website</dt>
                      <dd>{currentJob.page_url}</dd>
                    </div>

                    <div>
                      <dt>Objective</dt>
                      <dd>{currentJob.objective}</dd>
                    </div>
                  </>
                )}
              </dl>

              {(liveJobStatus === "queued" ||
                liveJobStatus === "running") && (
                <div className="processing-state">
                  <span className="spinner" />

                  <div>
                    <strong>
                      {liveJobStatus === "queued"
                        ? "Waiting for worker"
                        : "Running automated test"}
                    </strong>

                    <p>
                      Status updates automatically every
                      two seconds.
                    </p>
                  </div>
                </div>
              )}

              {liveJobStatus === "completed" &&
                currentJob?.result && (
                  <div className="result-summary">
                    <div>
                      <strong>
                        {currentJob.result.total_runs}
                      </strong>
                      <span>Total runs</span>
                    </div>

                    <div>
                      <strong>
                        {currentJob.result.passed_runs}
                      </strong>
                      <span>Passed</span>
                    </div>

                    <div>
                      <strong>
                        {currentJob.result.failed_runs}
                      </strong>
                      <span>Failed</span>
                    </div>

                    <div>
                      <strong>
                        {currentJob.result.bug_reports}
                      </strong>
                      <span>Bug reports</span>
                    </div>
                  </div>
                )}

              {liveJobStatus === "completed" &&
                !currentJob?.result && (
                  <div className="job-note">
                    The test completed, but no result
                    summary was returned.
                  </div>
                )}

              {liveJobStatus === "failed" && (
                <div className="job-error">
                  <strong>Execution failed</strong>

                  <p>
                    {currentJob?.error ??
                      "The test job failed without an error message."}
                  </p>
                </div>
              )}

              {liveJobStatus === "cancelled" && (
                <div className="job-note">
                  This test was cancelled before execution.
                </div>
              )}

              {pollingError && (
                <div className="job-error polling-error">
                  <strong>Status update failed</strong>
                  <p>{pollingError}</p>
                </div>
              )}
            </div>
          )}
        </aside>
      </section>

      <section className="history-section">
        <div className="history-header">
          <div>
            <p className="section-label">
              JOB HISTORY
            </p>

            <h2>Recent test jobs</h2>

            <p>
              These jobs are loaded from the SQLite
              database.
            </p>
          </div>

          <button
            className="history-refresh"
            type="button"
            onClick={() => {
              void loadJobs();
            }}
            disabled={isLoadingJobs}
          >
            {isLoadingJobs
              ? "Refreshing..."
              : "Refresh history"}
          </button>
        </div>

        {historyError && (
          <div className="history-message history-error">
            {historyError}
          </div>
        )}

        {isLoadingJobs && jobs.length === 0 && (
          <div className="history-message">
            Loading saved jobs...
          </div>
        )}

        {!isLoadingJobs &&
          !historyError &&
          jobs.length === 0 && (
            <div className="history-empty">
              <h3>No saved jobs yet</h3>

              <p>
                Submit your first automated test to create
                a job record.
              </p>
            </div>
          )}

        {jobs.length > 0 && (
          <div className="history-list">
            {jobs.map((job) => {
              const isSelected =
                submittedJob?.job_id === job.job_id;

              return (
                <article
                  className={
                    isSelected
                      ? "history-card selected"
                      : "history-card"
                  }
                  key={job.job_id}
                >
                  <div className="history-card-top">
                    <span
                      className={`history-status ${job.status}`}
                    >
                      <span />

                      {job.status}
                    </span>

                    <time dateTime={job.created_at}>
                      {formatDate(job.created_at)}
                    </time>
                  </div>

                  <h3>{job.objective}</h3>

                  <p className="history-url">
                    {job.page_url}
                  </p>

                  <div className="history-card-footer">
                    <code>{job.job_id}</code>

                    <button
                      className="history-open"
                      type="button"
                      onClick={() => {
                        handleSelectJob(job);
                      }}
                    >
                      {isSelected
                        ? "Selected"
                        : "Open job"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}


export default App;