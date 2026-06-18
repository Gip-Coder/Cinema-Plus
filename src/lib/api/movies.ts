import { apiClient } from "@/lib/api/client";
import { apiRoutes } from "@/lib/api/routes";
import type { Movie, MovieCreate, MovieUpdate } from "@/types/domain";

export interface MovieSearchParams {
  genre?: string;
  language?: string;
  limit?: number;
  q?: string;
  skip?: number;
}

export const moviesApi = {
  list(params: Pick<MovieSearchParams, "limit" | "skip"> = {}) {
    return apiClient.get<Movie[]>(apiRoutes.movies.list, { query: params });
  },
  search(params: MovieSearchParams) {
    return apiClient.get<Movie[]>(apiRoutes.movies.search, { query: { ...params } });
  },
  detail(movieId: number) {
    return apiClient.get<Movie>(apiRoutes.movies.detail(movieId));
  },
  create(token: string, payload: MovieCreate) {
    return apiClient.post<Movie, MovieCreate>(apiRoutes.movies.list, payload, { token });
  },
  update(token: string, movieId: number, payload: MovieUpdate) {
    return apiClient.put<Movie, MovieUpdate>(apiRoutes.movies.detail(movieId), payload, { token });
  },
  remove(token: string, movieId: number) {
    return apiClient.delete<void>(apiRoutes.movies.detail(movieId), { token });
  },
  uploadPoster(token: string, payload: FormData | { poster_url: string }) {
    return apiClient.post<{ poster_url: string }, typeof payload>(apiRoutes.movies.uploadPoster, payload, {
      token,
    });
  },
};
