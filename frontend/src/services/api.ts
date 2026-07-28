const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000";


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
  status: "queued" | "running";
  status_url: string;
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