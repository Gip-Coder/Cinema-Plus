import type { ApiEnvelope, ApiProblem, HttpMethod, QueryParams, QueryValue } from "@/types/api";

const DEFAULT_API_BASE_URL = "http://localhost:8001";

export class ApiError extends Error {
  readonly status: number;
  readonly payload?: unknown;

  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export interface ApiRequestOptions<TBody = unknown> {
  body?: TBody;
  headers?: HeadersInit;
  method?: HttpMethod;
  query?: QueryParams;
  signal?: AbortSignal;
  token?: string | null;
  unwrap?: boolean;
}

function getApiBaseUrl() {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

function appendQuery(url: URL, query?: QueryParams) {
  if (!query) {
    return;
  }

  Object.entries(query).forEach(([key, value]) => {
    const values = Array.isArray(value) ? value : [value];
    values.forEach((item: QueryValue) => {
      if (item !== null && item !== undefined) {
        url.searchParams.append(key, String(item));
      }
    });
  });
}

function isApiEnvelope<TData>(payload: unknown): payload is ApiEnvelope<TData> {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "success" in payload &&
    "message" in payload &&
    "data" in payload
  );
}

function getErrorMessage(payload: unknown, fallback: string) {
  if (typeof payload === "object" && payload !== null) {
    const problem = payload as ApiProblem;
    return problem.detail ?? problem.message ?? fallback;
  }

  return fallback;
}

class ApiClient {
  async request<TData, TBody = unknown>(
    path: string,
    {
      body,
      headers,
      method = "GET",
      query,
      signal,
      token,
      unwrap = true,
    }: ApiRequestOptions<TBody> = {},
  ): Promise<TData> {
    const url = new URL(path, `${getApiBaseUrl()}/`);
    appendQuery(url, query);

    const requestHeaders = new Headers(headers);
    if (token) {
      requestHeaders.set("Authorization", `Bearer ${token}`);
    }

    const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
    const requestBody = body === undefined ? undefined : isFormData ? body : JSON.stringify(body);

    if (body !== undefined && !isFormData && !requestHeaders.has("Content-Type")) {
      requestHeaders.set("Content-Type", "application/json");
    }

    const response = await fetch(url, {
      body: requestBody as BodyInit | undefined,
      headers: requestHeaders,
      method,
      signal,
    });

    if (response.status === 204) {
      return undefined as TData;
    }

    const contentType = response.headers.get("content-type") ?? "";
    const payload = contentType.includes("application/json")
      ? ((await response.json()) as unknown)
      : await response.text();

    if (!response.ok) {
      throw new ApiError(getErrorMessage(payload, response.statusText), response.status, payload);
    }

    if (unwrap && isApiEnvelope<TData>(payload)) {
      return payload.data;
    }

    return payload as TData;
  }

  get<TData>(path: string, options?: Omit<ApiRequestOptions, "body" | "method">) {
    return this.request<TData>(path, { ...options, method: "GET" });
  }

  post<TData, TBody = unknown>(
    path: string,
    body?: TBody,
    options?: Omit<ApiRequestOptions<TBody>, "body" | "method">,
  ) {
    return this.request<TData, TBody>(path, { ...options, body, method: "POST" });
  }

  put<TData, TBody = unknown>(
    path: string,
    body?: TBody,
    options?: Omit<ApiRequestOptions<TBody>, "body" | "method">,
  ) {
    return this.request<TData, TBody>(path, { ...options, body, method: "PUT" });
  }

  delete<TData>(path: string, options?: Omit<ApiRequestOptions, "body" | "method">) {
    return this.request<TData>(path, { ...options, method: "DELETE" });
  }

  async blob(path: string, options: Omit<ApiRequestOptions, "body" | "method" | "unwrap"> = {}) {
    const url = new URL(path, `${getApiBaseUrl()}/`);
    appendQuery(url, options.query);

    const headers = new Headers(options.headers);
    if (options.token) {
      headers.set("Authorization", `Bearer ${options.token}`);
    }

    const response = await fetch(url, {
      headers,
      method: "GET",
      signal: options.signal,
    });

    if (!response.ok) {
      const payload = await response.text();
      throw new ApiError(payload || response.statusText, response.status, payload);
    }

    return response.blob();
  }
}

export const apiClient = new ApiClient();
