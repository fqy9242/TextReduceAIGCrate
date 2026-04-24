import axios, { type InternalAxiosRequestConfig } from "axios";
import type { TokenResponse } from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
const ACCESS_TOKEN_KEY = "aigc_access_token";
const REFRESH_TOKEN_KEY = "aigc_refresh_token";

export const tokenStore = {
  getAccessToken(): string {
    return localStorage.getItem(ACCESS_TOKEN_KEY) ?? "";
  },
  getRefreshToken(): string {
    return localStorage.getItem(REFRESH_TOKEN_KEY) ?? "";
  },
  setTokens(tokens: TokenResponse): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  },
  clear(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (!error.response || error.response.status !== 401 || originalRequest?._retry) {
      return Promise.reject(error);
    }

    const refreshToken = tokenStore.getRefreshToken();
    if (!refreshToken) {
      tokenStore.clear();
      return Promise.reject(error);
    }

    try {
      originalRequest._retry = true;
      const refreshResp = await axios.post<TokenResponse>(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      });
      tokenStore.setTokens(refreshResp.data);
      originalRequest.headers.Authorization = `Bearer ${refreshResp.data.access_token}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      tokenStore.clear();
      return Promise.reject(refreshError);
    }
  },
);
