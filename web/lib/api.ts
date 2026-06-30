import type {
  AnswerResponse,
  Dashboard,
  ExampleChip,
  HealthInfo,
  QueryResult,
  SavedQuestion,
  SchemaTable,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function extractMessage(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (detail && typeof detail === "object" && "message" in detail) {
      return String((detail as { message: unknown }).message);
    }
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      "Can't reach the API. Is the backend running on " + BASE + "?",
      0,
    );
  }

  if (res.status === 204) return undefined as T;

  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    /* non-JSON response */
  }

  if (!res.ok) {
    throw new ApiError(
      extractMessage(body, `Request failed (${res.status}).`),
      res.status,
    );
  }
  return body as T;
}

export const api = {
  health: () => request<HealthInfo>("/health"),
  examples: () => request<ExampleChip[]>("/api/examples"),
  ask: (question: string) =>
    request<AnswerResponse>("/api/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  schema: () => request<SchemaTable[]>("/api/schema"),
  dashboard: () => request<Dashboard>("/api/dashboard"),
  savedQuestions: () => request<SavedQuestion[]>("/api/saved-questions"),
  saveQuestion: (payload: {
    title: string;
    question_text: string;
    generated_sql: string;
    chart_type: string;
    chart_config: { x: string | null; y: string[]; series?: string | null };
    summary: string | null;
  }) =>
    request<SavedQuestion>("/api/saved-questions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  runSaved: (id: number) =>
    request<QueryResult>(`/api/saved-questions/${id}/run`, { method: "POST" }),
  setPin: (id: number, pinned: boolean) =>
    request<SavedQuestion>(`/api/saved-questions/${id}/pin`, {
      method: "POST",
      body: JSON.stringify({ pinned }),
    }),
  deleteSaved: (id: number) =>
    request<void>(`/api/saved-questions/${id}`, { method: "DELETE" }),
};
