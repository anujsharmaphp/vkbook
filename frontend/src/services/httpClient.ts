import { useAuthStore } from "../features/auth/store";
import type { ApiErrorBody, TokenResponse } from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  status: number;
  code: string;
  requestId: string | null;
  details: unknown;

  constructor(status: number, code: string, message: string, requestId: string | null, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
    this.details = details;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
  query?: Record<string, string | undefined>;
}

function buildUrl(path: string, query?: Record<string, string | undefined>): string {
  const url = new URL(API_BASE.replace(/\/$/, "") + path, window.location.origin);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) url.searchParams.set(key, value);
    }
  }
  return url.toString();
}

async function parseErrorBody(response: Response): Promise<ApiErrorBody["error"]> {
  try {
    const body = (await response.json()) as ApiErrorBody;
    if (body?.error) return body.error;
  } catch {
    /* fall through */
  }
  return { code: "UNKNOWN_ERROR", message: response.statusText || "Request failed", request_id: null };
}

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const { refreshToken, setAccessToken, logout } = useAuthStore.getState();
  if (!refreshToken) return null;

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const response = await fetch(buildUrl("/auth/refresh"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!response.ok) {
          logout();
          return null;
        }
        const tokens = (await response.json()) as TokenResponse;
        setAccessToken(tokens.access_token);
        return tokens.access_token;
      } catch {
        logout();
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true, query } = options;

  const doFetch = async (): Promise<Response> => {
    const headers: Record<string, string> = {};
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (auth) {
      const token = useAuthStore.getState().accessToken;
      if (token) headers["Authorization"] = `Bearer ${token}`;
    }
    return fetch(buildUrl(path, query), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  };

  let response = await doFetch();

  if (response.status === 401 && auth && useAuthStore.getState().refreshToken) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      response = await doFetch();
    }
  }

  if (!response.ok) {
    const error = await parseErrorBody(response);
    throw new ApiError(response.status, error.code, error.message, error.request_id, error.details);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function wsBaseUrl(): string {
  const withoutApiV1 = API_BASE.replace(/\/api\/v1\/?$/, "");
  return withoutApiV1.replace(/^http/, "ws");
}
