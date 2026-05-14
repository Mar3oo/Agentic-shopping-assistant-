const BACKEND_BASE_URL = (import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const TIMEOUT_MS = 120_000;

export type ApiLanguage = 'en' | 'ar';

type RequestOptions = {
  json?: unknown;
  params?: Record<string, string | number | boolean | null | undefined>;
};

export class ApiClientError extends Error {
  status?: number;
  payload?: unknown;

  constructor(message: string, status?: number, payload?: unknown) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.payload = payload;
  }
}

async function parseJsonResponse(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    throw new ApiClientError('Backend returned invalid JSON.', res.status);
  }
}

function errorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') return fallback;
  const body = payload as Record<string, unknown>;
  const detail = body.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (detail && typeof detail === 'object') {
    const detailObj = detail as Record<string, unknown>;
    if (typeof detailObj.message === 'string' && detailObj.message.trim()) return detailObj.message;
    if (typeof detailObj.detail === 'string' && detailObj.detail.trim()) return detailObj.detail;
  }
  if (typeof body.message === 'string' && body.message.trim()) return body.message;
  if (typeof body.error === 'string' && body.error.trim()) return body.error;
  return fallback;
}

async function _request<T = Record<string, unknown>>(
  method: string,
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  let url = `${BACKEND_BASE_URL}${path}`;
  if (options.params) {
    const q = new URLSearchParams(
      Object.fromEntries(
        Object.entries(options.params)
          .filter(([, v]) => v !== undefined && v !== null)
          .map(([k, v]) => [k, String(v)])
      )
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

    if (!res.ok) {
      const payload = await parseJsonResponse(res);
      throw new ApiClientError(
        errorMessage(payload, `Request failed with status ${res.status}.`),
        res.status,
        payload
      );
    }

    const data = await parseJsonResponse(res);
    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      throw new ApiClientError('Unexpected response shape.', res.status, data);
    }

    const body = data as Record<string, unknown>;
    if (typeof body.status === 'string' && body.status !== 'success' && body.status !== 'ok') {
      throw new ApiClientError(errorMessage(body, 'Backend request failed.'), res.status, body);
    }

    return data as T;
  } catch (e) {
    if (e instanceof ApiClientError) throw e;
    if ((e as Error).name === 'AbortError') {
      throw new ApiClientError('Backend request timed out.');
    }
    throw new ApiClientError(`Could not connect to backend: ${(e as Error).message}`);
  } finally {
    clearTimeout(timer);
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
export const startRecommendation = (user_id: string, message: string, language: ApiLanguage = 'en') =>
  _request('POST', '/recommendation/start', { json: { user_id, message, language } });
export const chatRecommendation = (user_id: string, session_id: string, message: string, language: ApiLanguage = 'en') =>
  _request('POST', '/recommendation/chat', { json: { user_id, session_id, message, language } });

// Comparison
export const startComparison = (user_id: string, message: string, language: ApiLanguage = 'en') =>
  _request('POST', '/comparison/start', { json: { user_id, message, language } });
export const chatComparison = (user_id: string, session_id: string, message: string, language: ApiLanguage = 'en') =>
  _request('POST', '/comparison/chat', { json: { user_id, session_id, message, language } });

// Review
export const startReview = (user_id: string, message: string, language: ApiLanguage = 'en') =>
  _request('POST', '/review/start', { json: { user_id, message, language } });
export const chatReview = (user_id: string, session_id: string, message: string, language: ApiLanguage = 'en') =>
  _request('POST', '/review/chat', { json: { user_id, session_id, message, language } });

// Search
export const search = (user_id: string, message: string, language: ApiLanguage = 'en') =>
  _request('POST', '/search/', { json: { user_id, message, language } });

// Sessions
export const getSessions = (user_id: string, limit = 20) =>
  _request('GET', '/sessions/', { params: { user_id, limit } });
export const getSession = (session_id: string, user_id: string) =>
  _request('GET', `/sessions/${session_id}`, { params: { user_id } });
export const getSessionMessages = (session_id: string, user_id: string, limit = 50) =>
  _request('GET', `/sessions/${session_id}/messages`, { params: { user_id, limit } });
