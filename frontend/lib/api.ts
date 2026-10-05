"use client";

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const ACCESS_TOKEN_KEY = "holdit_access_token";
const REFRESH_TOKEN_KEY = "holdit_refresh_token";

type RetryableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean };

const safeGetItem = (key: string): string | null => {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
};

const safeSetItem = (key: string, value: string): void => {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.setItem(key, value);
  } catch {
    // Ignore storage write failures and keep runtime stable.
  }
};

const safeRemoveItem = (key: string): void => {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.removeItem(key);
  } catch {
    // Ignore storage removal failures and keep runtime stable.
  }
};

const getAccessToken = () =>
  safeGetItem(ACCESS_TOKEN_KEY);

const getRefreshToken = () =>
  safeGetItem(REFRESH_TOKEN_KEY);

const clearAuthStorage = () => {
  if (typeof window === "undefined") {
    return;
  }

  safeRemoveItem(ACCESS_TOKEN_KEY);
  safeRemoveItem(REFRESH_TOKEN_KEY);
  safeRemoveItem("holdit_user");
  window.dispatchEvent(new Event("holdit-auth-changed"));
};

const redirectToLogin = () => {
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
};

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      originalRequest.url?.includes("/auth/refresh")
    ) {
      return Promise.reject(error);
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearAuthStorage();
      redirectToLogin();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const refreshResponse = await axios.post(
        `${baseURL}/auth/refresh`,
        { refresh_token: refreshToken },
        { headers: { "Content-Type": "application/json" } },
      );

      const newAccessToken = refreshResponse.data?.data?.access_token as string | undefined;
      if (!newAccessToken) {
        throw new Error("Missing access token");
      }

      safeSetItem(ACCESS_TOKEN_KEY, newAccessToken);
      window.dispatchEvent(new Event("holdit-auth-changed"));
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

      return api(originalRequest);
    } catch (refreshError) {
      clearAuthStorage();
      redirectToLogin();
      return Promise.reject(refreshError);
    }
  },
);

export default api;
