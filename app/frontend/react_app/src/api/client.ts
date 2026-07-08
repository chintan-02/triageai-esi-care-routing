import type { ApiErrorBody } from '@/types/api';

export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
  'http://localhost:8001';

export class ApiError extends Error {
  readonly status: number;
  readonly statusText: string;
  readonly details: unknown;

  constructor(message: string, response: Response, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = response.status;
    this.statusText = response.statusText;
    this.details = details;
  }
}

export interface ApiRequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
}

function joinUrl(path: string): string {
  const normalizedBase = API_BASE_URL.replace(/\/+$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

function isJsonResponse(response: Response): boolean {
  return response.headers.get('content-type')?.includes('application/json') ?? false;
}

function messageFromErrorBody(body: ApiErrorBody | string | unknown, fallback: string): string {
  if (typeof body === 'string' && body.trim()) return body;

  if (body && typeof body === 'object') {
    const payload = body as ApiErrorBody;
    if (typeof payload.message === 'string') return payload.message;
    if (typeof payload.error === 'string') return payload.error;
    if (typeof payload.detail === 'string') return payload.detail;
    if (Array.isArray(payload.detail)) return payload.detail.map(String).join(', ');
  }

  return fallback;
}

async function readErrorBody(response: Response): Promise<unknown> {
  if (isJsonResponse(response)) {
    try {
      return await response.json();
    } catch {
      return undefined;
    }
  }

  try {
    return await response.text();
  } catch {
    return undefined;
  }
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { body, headers, ...requestOptions } = options;
  const requestHeaders = new Headers(headers);

  let requestBody: BodyInit | undefined;
  if (body !== undefined) {
    if (body instanceof FormData || body instanceof Blob || typeof body === 'string') {
      requestBody = body;
    } else {
      requestHeaders.set('Content-Type', 'application/json');
      requestBody = JSON.stringify(body);
    }
  }

  const response = await fetch(joinUrl(path), {
    credentials: 'include',
    ...requestOptions,
    headers: requestHeaders,
    body: requestBody,
  });

  if (!response.ok) {
    const details = await readErrorBody(response);
    const fallback = `Request failed with ${response.status} ${response.statusText}`;
    throw new ApiError(messageFromErrorBody(details, fallback), response, details);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function apiBlobRequest(
  path: string,
  options: ApiRequestOptions = {},
): Promise<Blob> {
  const { body, headers, ...requestOptions } = options;
  const requestHeaders = new Headers(headers);

  let requestBody: BodyInit | undefined;
  if (body !== undefined) {
    if (body instanceof FormData || body instanceof Blob || typeof body === 'string') {
      requestBody = body;
    } else {
      requestHeaders.set('Content-Type', 'application/json');
      requestBody = JSON.stringify(body);
    }
  }

  const response = await fetch(joinUrl(path), {
    credentials: 'include',
    ...requestOptions,
    headers: requestHeaders,
    body: requestBody,
  });

  if (!response.ok) {
    const details = await readErrorBody(response);
    const fallback = `Request failed with ${response.status} ${response.statusText}`;
    throw new ApiError(messageFromErrorBody(details, fallback), response, details);
  }

  return response.blob();
}
