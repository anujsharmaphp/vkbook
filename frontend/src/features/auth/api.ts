import { apiRequest } from "../../services/httpClient";
import type { TokenResponse, UserRead } from "../../types/api";

export function register(payload: { email: string; password: string; display_name: string }) {
  return apiRequest<UserRead>("/auth/register", { method: "POST", body: payload, auth: false });
}

export function login(payload: { email: string; password: string }) {
  return apiRequest<TokenResponse>("/auth/login", { method: "POST", body: payload, auth: false });
}

export function fetchMe() {
  return apiRequest<UserRead>("/auth/me");
}
