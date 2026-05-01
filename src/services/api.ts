const BACKEND_BASE_URL = (import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const TIMEOUT_MS = 120_000;

export class ApiClientError extends Error {}

async function _request<T = Record<string, unknown>>(
  method: string,
  path: string,
  options: { json?: unknown; params?: Record<string, string | number> } = {}
): Promise<T> {
  let url = `${BACKEND_BASE_URL}${path}`;
  if (options.params) {
    const q = new URLSearchParams(
      Object.fromEntries(Object.entries(options.params).map(([k, v]) => [k, String(v)]))
    );
    url += `?${q}`;
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method,
      headers: options.json ? { 'Content-Type': 'application/json' } : {},
      body: options.json ? JSON.stringify(options.json) : undefined,
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) {
      let msg = `Request failed with status ${res.status}.`;
      try {
        const payload = await res.json();
        if (typeof payload?.detail === 'string') msg = payload.detail;
        else if (typeof payload?.message === 'string') msg = payload.message;
      } catch { /* ignore */ }
      throw new ApiClientError(msg);
    }
    const data = await res.json();
    if (typeof data !== 'object' || Array.isArray(data)) throw new ApiClientError('Unexpected response shape.');
    return data as T;
  } catch (e) {
    clearTimeout(timer);
    if (e instanceof ApiClientError) throw e;
    throw new ApiClientError(`Could not connect to backend: ${(e as Error).message}`);
  }
}

// Auth
export const createGuestUser = () => _request('POST', '/users/guest');
export const register = (email: string, password: string, display_name?: string) =>
  _request('POST', '/auth/register', { json: { email, password, display_name } });
export const login = (email: string, password: string) =>
  _request('POST', '/auth/login', { json: { email, password } });
export const getCurrentUser = (user_id: string) =>
  _request('GET', '/auth/me', { params: { user_id } });

// Recommendation
export const startRecommendation = (user_id: string, message: string) =>
  _request('POST', '/recommendation/start', { json: { user_id, message } });
export const chatRecommendation = (user_id: string, session_id: string, message: string) =>
  _request('POST', '/recommendation/chat', { json: { user_id, session_id, message } });

// Comparison
export const startComparison = (user_id: string, message: string) =>
  _request('POST', '/comparison/start', { json: { user_id, message } });
export const chatComparison = (user_id: string, session_id: string, message: string) =>
  _request('POST', '/comparison/chat', { json: { user_id, session_id, message } });

// Review
export const startReview = (user_id: string, message: string) =>
  _request('POST', '/review/start', { json: { user_id, message } });
export const chatReview = (user_id: string, session_id: string, message: string) =>
  _request('POST', '/review/chat', { json: { user_id, session_id, message } });

// Search
export const search = (user_id: string, message: string) =>
  _request('POST', '/search/', { json: { user_id, message } });

// Sessions
export const getSessions = (user_id: string, limit = 20) =>
  _request('GET', '/sessions/', { params: { user_id, limit } });
export const getSession = (session_id: string, user_id: string) =>
  _request('GET', `/sessions/${session_id}`, { params: { user_id } });
export const getSessionMessages = (session_id: string, user_id: string, limit = 50) =>
  _request('GET', `/sessions/${session_id}/messages`, { params: { user_id, limit } });
