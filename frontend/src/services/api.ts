const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000";


export type JobStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";


export interface HealthResponse {
  status: string;
  service: string;
}


export interface RunTestRequest {
  page_url: string;
  objective: string;
  headless: boolean;
}


export interface JobCreatedResponse {
  job_id: string;
  status: JobStatus;
  status_url: string;
}


export interface JobResultSummary {
  total_runs: number;
  passed_runs: number;
  failed_runs: number;
  bug_reports: number;
  run_ids: string[];
}


export interface TestJob {
  job_id: string;
  status: JobStatus;
  page_url: string;
  objective: string;
  headless: boolean;
  result: JobResultSummary | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}


export interface JobListResponse {
  count: number;
  jobs: TestJob[];
}


export interface StoredTestStep {
  step_number: number;
  description: string;
  status: string;
  error: string | null;
  screenshot: string | null;
}


export interface StoredDiagnostics {
  console_errors: unknown[];
  page_errors: unknown[];
  failed_requests: unknown[];
  http_errors: unknown[];
}


export interface StoredTestRun {
  run_id: string;
  job_id: string;
  test_name: string;
  objective: string;
  status: string;
  error: string | null;
  created_at: string;
  steps: StoredTestStep[];
  diagnostics: StoredDiagnostics;
  bug_report: unknown | null;
}


export interface JobRunsResponse {
  job_id: string;
  count: number;
  runs: StoredTestRun[];
}


export interface JobDeletedResponse {
  job_id: string;
  message: string;
}


interface ApiErrorResponse {
  detail?: string;
}


async function getErrorMessage(
  response: Response,
): Promise<string> {
  try {
    const errorData =
      (await response.json()) as ApiErrorResponse;

    if (errorData.detail) {
      return errorData.detail;
    }
  } catch {
    // The response did not contain valid JSON.
  }

  return `Request failed with status ${response.status}.`;
}


export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(
    `${API_BASE_URL}/health`,
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<HealthResponse>;
}


export async function submitTest(
  payload: RunTestRequest,
): Promise<JobCreatedResponse> {
  const response = await fetch(
    `${API_BASE_URL}/tests/run`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<JobCreatedResponse>;
}


export async function getJob(
  jobId: string,
): Promise<TestJob> {
  const response = await fetch(
    `${API_BASE_URL}/tests/jobs/${jobId}`,
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<TestJob>;
}


export async function listJobs(
  limit = 20,
  status?: JobStatus,
): Promise<JobListResponse> {
  const searchParameters = new URLSearchParams({
    limit: String(limit),
  });

  if (status) {
    searchParameters.set(
      "status",
      status,
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/tests/jobs?${searchParameters.toString()}`,
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<JobListResponse>;
}


export async function getJobRuns(
  jobId: string,
): Promise<JobRunsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/tests/jobs/${jobId}/runs`,
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<JobRunsResponse>;
}


export async function cancelJob(
  jobId: string,
): Promise<TestJob> {
  const response = await fetch(
    `${API_BASE_URL}/tests/jobs/${jobId}/cancel`,
    {
      method: "POST",
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<TestJob>;
}


export async function deleteJob(
  jobId: string,
): Promise<JobDeletedResponse> {
  const response = await fetch(
    `${API_BASE_URL}/tests/jobs/${jobId}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<JobDeletedResponse>;
}


export function getRunScreenshotUrl(
  runId: string,
  screenshotPath: string,
): string {
  const normalizedPath =
    screenshotPath.replaceAll("\\", "/");

  const filename =
    normalizedPath.split("/").pop();

  if (!filename) {
    return "";
  }

  return (
    `${API_BASE_URL}/tests/runs/` +
    `${encodeURIComponent(runId)}/screenshots/` +
    `${encodeURIComponent(filename)}`
  );
}