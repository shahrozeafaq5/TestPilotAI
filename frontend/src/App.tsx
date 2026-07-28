import {
  type FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  cancelJob,
  deleteJob,
  getHealth,
  getJob,
  getJobRuns,
  getRunScreenshotUrl,
  listJobs,
  submitTest,
  type HealthResponse,
  type JobCreatedResponse,
  type StoredDiagnostics,
  type StoredTestRun,
  type TestJob,
} from "./services/api";

import "./App.css";


const DEFAULT_PAGE_URL =
  "file:///C:/Users/hp/Desktop/TestPilotAI/samples/locator_demo.html";

const DEFAULT_OBJECTIVE =
  "Test the login form and verify that signing in displays the welcome message.";


type JobAction =
  | "cancel"
  | "delete"
  | null;


function formatDate(
  value: string,
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}


function formatDiagnosticItem(
  value: unknown,
): string {
  if (typeof value === "string") {
    return value;
  }

  const serializedValue =
    JSON.stringify(value, null, 2);

  return serializedValue ?? String(value);
}


function getDiagnosticCount(
  diagnostics: StoredDiagnostics,
): number {
  return (
    diagnostics.console_errors.length +
    diagnostics.page_errors.length +
    diagnostics.failed_requests.length +
    diagnostics.http_errors.length
  );
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

  const [runs, setRuns] =
    useState<StoredTestRun[]>([]);

  const [isLoadingRuns, setIsLoadingRuns] =
    useState(false);

  const [runsError, setRunsError] =
    useState<string | null>(null);

  const [activeJobAction, setActiveJobAction] =
    useState<JobAction>(null);

  const [jobActionError, setJobActionError] =
    useState<string | null>(null);

  const [jobActionMessage, setJobActionMessage] =
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


  useEffect(() => {
    const selectedJobId =
      currentJob?.job_id ??
      submittedJob?.job_id;

    const selectedJobStatus =
      currentJob?.status ??
      submittedJob?.status;

    if (
      !selectedJobId ||
      selectedJobStatus !== "completed"
    ) {
      setRuns([]);
      setRunsError(null);
      setIsLoadingRuns(false);

      return;
    }

    let stopped = false;

    async function loadRuns(
      jobId: string,
    ): Promise<void> {
      setIsLoadingRuns(true);
      setRunsError(null);

      try {
        const response =
          await getJobRuns(jobId);

        if (stopped) {
          return;
        }

        setRuns(response.runs);
      } catch (error) {
        if (stopped) {
          return;
        }

        const message =
          error instanceof Error
            ? error.message
            : "Could not load test run details.";

        setRuns([]);
        setRunsError(message);
      } finally {
        if (!stopped) {
          setIsLoadingRuns(false);
        }
      }
    }

    void loadRuns(selectedJobId);

    return () => {
      stopped = true;
    };
  }, [
    currentJob?.job_id,
    currentJob?.status,
    submittedJob?.job_id,
    submittedJob?.status,
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
    setRuns([]);
    setRunsError(null);
    setJobActionError(null);
    setJobActionMessage(null);

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
    setRuns([]);
    setRunsError(null);
    setJobActionError(null);
    setJobActionMessage(null);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }


  const selectedJobId =
    currentJob?.job_id ??
    submittedJob?.job_id ??
    null;


  async function handleCancelJob(): Promise<void> {
    if (!selectedJobId) {
      return;
    }

    setActiveJobAction("cancel");
    setJobActionError(null);
    setJobActionMessage(null);

    try {
      const cancelledJob =
        await cancelJob(selectedJobId);

      setCurrentJob(cancelledJob);

      setSubmittedJob((previousJob) => {
        if (!previousJob) {
          return {
            job_id: cancelledJob.job_id,
            status: cancelledJob.status,
            status_url:
              `/tests/jobs/${cancelledJob.job_id}`,
          };
        }

        return {
          ...previousJob,
          status: cancelledJob.status,
        };
      });

      setJobActionMessage(
        "The queued job was cancelled.",
      );

      await loadJobs();
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "The job could not be cancelled.";

      setJobActionError(message);
    } finally {
      setActiveJobAction(null);
    }
  }


  async function handleDeleteJob(): Promise<void> {
    if (!selectedJobId) {
      return;
    }

    const confirmed = window.confirm(
      "Delete this job and all of its stored runs, steps, diagnostics and bug reports?",
    );

    if (!confirmed) {
      return;
    }

    setActiveJobAction("delete");
    setJobActionError(null);
    setJobActionMessage(null);

    try {
      await deleteJob(selectedJobId);

      setJobs((existingJobs) =>
        existingJobs.filter(
          (job) =>
            job.job_id !== selectedJobId,
        ),
      );

      setSubmittedJob(null);
      setCurrentJob(null);
      setRuns([]);
      setRunsError(null);
      setPollingError(null);

      await loadJobs();
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "The job could not be deleted.";

      setJobActionError(message);
    } finally {
      setActiveJobAction(null);
    }
  }


  const backendConnected = health !== null;

  const liveJobStatus =
    currentJob?.status ??
    submittedJob?.status ??
    null;

  const canDeleteSelectedJob =
    liveJobStatus === "completed" ||
    liveJobStatus === "failed" ||
    liveJobStatus === "cancelled";


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

              {jobActionError && (
                <div className="job-error action-message">
                  <strong>Job action failed</strong>

                  <p>{jobActionError}</p>
                </div>
              )}

              {jobActionMessage && (
                <div className="job-action-success">
                  {jobActionMessage}
                </div>
              )}

              <div className="job-actions">
                {liveJobStatus === "queued" && (
                  <button
                    className="cancel-job-button"
                    type="button"
                    onClick={() => {
                      void handleCancelJob();
                    }}
                    disabled={
                      activeJobAction !== null
                    }
                  >
                    {activeJobAction === "cancel"
                      ? "Cancelling..."
                      : "Cancel queued job"}
                  </button>
                )}

                {canDeleteSelectedJob && (
                  <button
                    className="delete-job-button"
                    type="button"
                    onClick={() => {
                      void handleDeleteJob();
                    }}
                    disabled={
                      activeJobAction !== null
                    }
                  >
                    {activeJobAction === "delete"
                      ? "Deleting..."
                      : "Delete job"}
                  </button>
                )}
              </div>
            </div>
          )}
        </aside>
      </section>

      {submittedJob &&
        liveJobStatus === "completed" && (
          <section className="runs-section">
            <div className="runs-header">
              <div>
                <p className="section-label">
                  RUN DETAILS
                </p>

                <h2>Executed test cases</h2>

                <p>
                  Steps, diagnostics, screenshots and
                  generated bug reports for this job.
                </p>
              </div>

              {!isLoadingRuns && (
                <span className="run-count">
                  {runs.length}{" "}
                  {runs.length === 1
                    ? "run"
                    : "runs"}
                </span>
              )}
            </div>

            {isLoadingRuns && (
              <div className="runs-message">
                <span className="spinner" />

                Loading detailed run results...
              </div>
            )}

            {runsError && (
              <div className="runs-message runs-error">
                {runsError}
              </div>
            )}

            {!isLoadingRuns &&
              !runsError &&
              runs.length === 0 && (
                <div className="runs-message">
                  This job completed, but no detailed test
                  runs were stored.
                </div>
              )}

            {runs.length > 0 && (
              <div className="runs-list">
                {runs.map((run) => {
                  const diagnosticCount =
                    getDiagnosticCount(
                      run.diagnostics,
                    );

                  return (
                    <article
                      className="run-card"
                      key={run.run_id}
                    >
                      <header className="run-card-header">
                        <div>
                          <span
                            className={`run-status ${run.status}`}
                          >
                            <span />

                            {run.status}
                          </span>

                          <h3>{run.test_name}</h3>

                          <p>{run.objective}</p>
                        </div>

                        <div className="run-meta">
                          <code>{run.run_id}</code>

                          <time
                            dateTime={run.created_at}
                          >
                            {formatDate(
                              run.created_at,
                            )}
                          </time>
                        </div>
                      </header>

                      {run.error && (
                        <div className="run-error">
                          <strong>Run error</strong>

                          <p>{run.error}</p>
                        </div>
                      )}

                      <div className="run-subsection">
                        <div className="run-subsection-heading">
                          <h4>Executed steps</h4>

                          <span>
                            {run.steps.length}
                          </span>
                        </div>

                        {run.steps.length === 0 && (
                          <p className="section-empty">
                            No steps were stored for this
                            run.
                          </p>
                        )}

                        {run.steps.length > 0 && (
                          <div className="steps-list">
                            {run.steps.map((step) => {
                              const screenshotUrl =
                                step.screenshot
                                  ? getRunScreenshotUrl(
                                      run.run_id,
                                      step.screenshot,
                                    )
                                  : "";

                              return (
                                <div
                                  className="step-card"
                                  key={
                                    `${run.run_id}-` +
                                    `${step.step_number}`
                                  }
                                >
                                  <div className="step-number">
                                    {step.step_number}
                                  </div>

                                  <div className="step-content">
                                    <div className="step-heading">
                                      <strong>
                                        {step.description}
                                      </strong>

                                      <span
                                        className={`step-status ${step.status}`}
                                      >
                                        {step.status}
                                      </span>
                                    </div>

                                    {step.error && (
                                      <p className="step-error">
                                        {step.error}
                                      </p>
                                    )}

                                    {step.screenshot &&
                                      screenshotUrl && (
                                        <div className="screenshot-card">
                                          <a
                                            href={
                                              screenshotUrl
                                            }
                                            target="_blank"
                                            rel="noreferrer"
                                          >
                                            <img
                                              src={
                                                screenshotUrl
                                              }
                                              alt={
                                                `Screenshot for ` +
                                                `step ${step.step_number}`
                                              }
                                              loading="lazy"
                                            />
                                          </a>

                                          <div className="screenshot-footer">
                                            <span>
                                              Step screenshot
                                            </span>

                                            <a
                                              href={
                                                screenshotUrl
                                              }
                                              target="_blank"
                                              rel="noreferrer"
                                            >
                                              Open full image
                                            </a>
                                          </div>
                                        </div>
                                      )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>

                      <div className="run-subsection">
                        <div className="run-subsection-heading">
                          <h4>Diagnostics</h4>

                          <span>
                            {diagnosticCount}
                          </span>
                        </div>

                        {diagnosticCount === 0 && (
                          <div className="diagnostics-clear">
                            No console, page, network or
                            HTTP errors were captured.
                          </div>
                        )}

                        {run.diagnostics.console_errors
                          .length > 0 && (
                          <div className="diagnostic-group">
                            <h5>Console errors</h5>

                            {run.diagnostics.console_errors.map(
                              (item, index) => (
                                <pre
                                  key={
                                    `console-${index}`
                                  }
                                >
                                  {formatDiagnosticItem(
                                    item,
                                  )}
                                </pre>
                              ),
                            )}
                          </div>
                        )}

                        {run.diagnostics.page_errors
                          .length > 0 && (
                          <div className="diagnostic-group">
                            <h5>Page errors</h5>

                            {run.diagnostics.page_errors.map(
                              (item, index) => (
                                <pre
                                  key={`page-${index}`}
                                >
                                  {formatDiagnosticItem(
                                    item,
                                  )}
                                </pre>
                              ),
                            )}
                          </div>
                        )}

                        {run.diagnostics.failed_requests
                          .length > 0 && (
                          <div className="diagnostic-group">
                            <h5>Failed requests</h5>

                            {run.diagnostics.failed_requests.map(
                              (item, index) => (
                                <pre
                                  key={
                                    `request-${index}`
                                  }
                                >
                                  {formatDiagnosticItem(
                                    item,
                                  )}
                                </pre>
                              ),
                            )}
                          </div>
                        )}

                        {run.diagnostics.http_errors
                          .length > 0 && (
                          <div className="diagnostic-group">
                            <h5>HTTP errors</h5>

                            {run.diagnostics.http_errors.map(
                              (item, index) => (
                                <pre
                                  key={`http-${index}`}
                                >
                                  {formatDiagnosticItem(
                                    item,
                                  )}
                                </pre>
                              ),
                            )}
                          </div>
                        )}
                      </div>

                      <div className="run-subsection">
                        <div className="run-subsection-heading">
                          <h4>Bug report</h4>

                          <span>
                            {run.bug_report
                              ? "Generated"
                              : "None"}
                          </span>
                        </div>

                        {!run.bug_report && (
                          <p className="section-empty">
                            No bug report was generated
                            because this run passed without
                            relevant diagnostics.
                          </p>
                        )}

                        {Boolean(run.bug_report) && (
                          <pre className="bug-report">
                            {formatDiagnosticItem(
                              run.bug_report,
                            )}
                          </pre>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        )}

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

        {isLoadingJobs &&
          jobs.length === 0 && (
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
                submittedJob?.job_id ===
                job.job_id;

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

                    <time
                      dateTime={job.created_at}
                    >
                      {formatDate(
                        job.created_at,
                      )}
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