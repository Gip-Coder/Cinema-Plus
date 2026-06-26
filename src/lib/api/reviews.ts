import { apiClient } from "@/lib/api/client";
import { apiRoutes } from "@/lib/api/routes";
import type { Review } from "@/types/domain";

export interface ReviewCreate {
  comment: string;
  movie_id: number;
  rating: number;
}

export const reviewsApi = {
  create(token: string, payload: ReviewCreate) {
    return apiClient.post<Review, ReviewCreate>(apiRoutes.reviews.create, payload, { token });
  },
  byMovie(movieId: number) {
    return apiClient.get<Review[]>(apiRoutes.reviews.byMovie(movieId));
  },
  all(token: string) {
    return apiClient.get<Review[]>(apiRoutes.reviews.all, { token });
  },
  remove(token: string, reviewId: number) {
    return apiClient.delete<null>(apiRoutes.reviews.delete(reviewId), { token });
  },
  update(token: string, reviewId: number, payload: ReviewCreate) {
    return apiClient.put<Review, ReviewCreate>(apiRoutes.reviews.update(reviewId), payload, { token });
  },
};
