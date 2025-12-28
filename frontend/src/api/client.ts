const BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api';

export type HttpMethod = 'GET' | 'POST';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Request failed (${response.status}): ${message}`);
  }

  return response.json() as Promise<T>;
}

export function get<T>(path: string, signal?: AbortSignal) {
  return request<T>(path, { method: 'GET', signal });
}

export function post<T>(path: string, body: unknown, signal?: AbortSignal) {
  return request<T>(path, { method: 'POST', body: JSON.stringify(body), signal });
}
