/**
 * Lumine API Client — axios + JWT interceptor + auto-refresh.
 * SRS §7 NFR-02: access token 60min, refresh token 7 days.
 * SRS §6.6: 401 → call refresh → retry original request.
 * SRS §5 FR-04 / §15: mid-upload token expiry → pause → refresh → resume.
 *
 * staff_id is NEVER sent in any request body — always read from JWT on the backend.
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  MOCK_AUTH_RESPONSE,
  MOCK_REFRESH_RESPONSE,
  MOCK_TASKS,
  MOCK_UPLOAD_RESPONSE,
  MOCK_UPLOAD_HISTORY,
  MOCK_EVIDENCE_RESPONSE,
  MOCK_KPI_REPORT,
} from '../mock/mockData';

// ---------------------------------------------------------------------------
// DEV_MODE — set true to use mock data instead of real API.
// Real API calls are preserved — flip to false to connect to backend.
// ---------------------------------------------------------------------------

export const DEV_MODE = false;

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

const STORAGE_KEYS = {
  ACCESS_TOKEN: 'lumine_access_token',
  REFRESH_TOKEN: 'lumine_refresh_token',
} as const;

// ---------------------------------------------------------------------------
// Token storage helpers
// ---------------------------------------------------------------------------

export const tokenStorage = {
  async getAccessToken(): Promise<string | null> {
    return AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  },

  async getRefreshToken(): Promise<string | null> {
    return AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  },

  async setTokens(accessToken: string, refreshToken: string): Promise<void> {
    await Promise.all([
      AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, accessToken),
      AsyncStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken),
    ]);
  },

  async setAccessToken(accessToken: string): Promise<void> {
    await AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, accessToken);
  },

  async clearTokens(): Promise<void> {
    await Promise.all([
      AsyncStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN),
      AsyncStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN),
    ]);
  },
};

// ---------------------------------------------------------------------------
// Refresh logic — called by interceptor on 401
// ---------------------------------------------------------------------------

let _refreshPromise: Promise<string> | null = null;

/**
 * Exchange refresh token for a new access token.
 * Uses a shared promise to prevent multiple concurrent refresh calls
 * (e.g. mid-upload with multiple parallel requests all hitting 401 at once).
 */
async function refreshAccessToken(): Promise<string> {
  if (_refreshPromise) return _refreshPromise;

  _refreshPromise = (async () => {
    const refreshToken = await tokenStorage.getRefreshToken();
    if (!refreshToken) throw new Error('No refresh token — must log in.');

    const response = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, {
      refresh_token: refreshToken,
    });

    const newAccessToken: string = response.data.access_token;
    await tokenStorage.setAccessToken(newAccessToken);
    return newAccessToken;
  })().finally(() => {
    _refreshPromise = null;
  });

  return _refreshPromise;
}

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
});

// ---------------------------------------------------------------------------
// Mock adapter — intercepts all requests when DEV_MODE = true.
// Real axios interceptors below still run (request attaches token etc.)
// but the network call never fires — adapter short-circuits it.
// ---------------------------------------------------------------------------

function mockResponse(data: unknown, status = 200) {
  return { data, status, statusText: 'OK', headers: {}, config: {} as any };
}

if (DEV_MODE) {
  client.defaults.adapter = async (config) => {
    const url = config.url ?? '';
    const method = (config.method ?? 'get').toLowerCase();

    // Simulate 300ms network latency so loading states are visible
    await new Promise((r) => setTimeout(r, 300));

    // POST /api/v1/auth/login
    if (method === 'post' && url.includes('/auth/login')) {
      return mockResponse(MOCK_AUTH_RESPONSE);
    }

    // POST /api/v1/auth/refresh
    if (method === 'post' && url.includes('/auth/refresh')) {
      return mockResponse(MOCK_REFRESH_RESPONSE);
    }

    // GET /api/v1/tasks
    if (method === 'get' && url.includes('/tasks')) {
      return mockResponse(MOCK_TASKS);
    }

    // PATCH /api/v1/tasks/:id  — mark Done
    if (method === 'patch' && url.includes('/tasks/')) {
      const taskIdStr = url.split('/tasks/')[1];
      const taskId = parseInt(taskIdStr, 10);
      const found = MOCK_TASKS.find((t) => t.id === taskId);
      return mockResponse(found ? { ...found, status: 'Done' } : MOCK_TASKS[0]);
    }

    // POST /api/v1/evidence
    if (method === 'post' && url.includes('/evidence')) {
      return mockResponse(MOCK_EVIDENCE_RESPONSE);
    }

    // GET /api/v1/upload/history
    if (method === 'get' && url.includes('/upload/history')) {
      return mockResponse(MOCK_UPLOAD_HISTORY);
    }

    // POST /api/v1/upload
    if (method === 'post' && url.includes('/upload')) {
      return mockResponse(MOCK_UPLOAD_RESPONSE);
    }

    // GET /api/v1/reports/kpi
    if (method === 'get' && url.includes('/reports/kpi')) {
      return mockResponse(MOCK_KPI_REPORT);
    }

    // Fallback — return empty success so unknown routes don't crash
    return mockResponse({});
  };
}

// ---------------------------------------------------------------------------
// Request interceptor — attach access token to every request
// ---------------------------------------------------------------------------

client.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const token = await tokenStorage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Response interceptor — handle 401, refresh, retry
// SRS §7 NFR-02: 401 → refresh → retry original request transparently.
// If refresh fails → force logout.
// ---------------------------------------------------------------------------

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Only attempt refresh once per request — prevents infinite retry loops
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Auth endpoints must never trigger a refresh attempt
      if (originalRequest.url?.includes('/auth/')) {
        return Promise.reject(error);
      }
      originalRequest._retry = true;

      try {
        const newAccessToken = await refreshAccessToken();
        if (originalRequest.headers) {
          (originalRequest.headers as Record<string, string>).Authorization =
            `Bearer ${newAccessToken}`;
        } else {
          originalRequest.headers = { Authorization: `Bearer ${newAccessToken}` };
        }
        // Resume original request with new token (handles mid-upload pause/resume)
        return client(originalRequest);
      } catch {
        // Refresh failed — session expired, force logout
        await tokenStorage.clearTokens();
        // Emit a global logout event — AppNavigator listens and redirects to Login
        authEvents.emit('logout');
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------------
// Auth event emitter — decoupled logout signal to navigation layer
// ---------------------------------------------------------------------------

type AuthEventListener = () => void;

const authEvents = {
  _listeners: new Set<AuthEventListener>(),

  emit(event: 'logout'): void {
    if (event === 'logout') {
      this._listeners.forEach((fn) => fn());
    }
  },

  onLogout(fn: AuthEventListener): () => void {
    this._listeners.add(fn);
    return () => this._listeners.delete(fn); // returns unsubscribe function
  },
};

export { authEvents };
export default client;
