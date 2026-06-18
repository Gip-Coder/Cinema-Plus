export type QueryValue = string | number | boolean | null | undefined;

export type QueryParams = Record<string, QueryValue | QueryValue[]>;

export interface ApiEnvelope<TData> {
  success: boolean;
  message: string;
  data: TData;
}

export interface ApiProblem {
  detail?: string;
  message?: string;
  errors?: unknown;
}

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
