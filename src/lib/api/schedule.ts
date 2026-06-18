import { apiClient } from "@/lib/api/client";
import { apiRoutes } from "@/lib/api/routes";
import type { Screen, Show, Theatre } from "@/types/domain";

export type TheatreCreate = Omit<Theatre, "created_at" | "id" | "screens" | "updated_at">;
export type ScreenCreate = Omit<Screen, "created_at" | "id" | "updated_at">;
export type ShowCreate = Omit<Show, "id" | "movie" | "screen">;

export const scheduleApi = {
  theatres() {
    return apiClient.get<Theatre[]>(apiRoutes.schedule.theatres);
  },
  screens() {
    return apiClient.get<Screen[]>(apiRoutes.schedule.screens);
  },
  createTheatre(token: string, payload: TheatreCreate) {
    return apiClient.post<Theatre, TheatreCreate>(apiRoutes.schedule.theatres, payload, { token });
  },
  createScreen(token: string, theatreId: number, payload: Omit<ScreenCreate, "theatre_id">) {
    return apiClient.post<Screen, typeof payload>(apiRoutes.schedule.screens, payload, {
      query: { theatre_id: theatreId },
      token,
    });
  },
  createShow(token: string, payload: ShowCreate) {
    return apiClient.post<Show, ShowCreate>(apiRoutes.schedule.shows, payload, { token });
  },
  showsByMovie(movieId: number) {
    return apiClient.get<Show[]>(apiRoutes.schedule.showsByMovie(movieId));
  },
  allShows() {
    return apiClient.get<Show[]>(apiRoutes.schedule.allShows);
  },
  show(showId: number) {
    return apiClient.get<Show>(apiRoutes.schedule.show(showId));
  },
  deleteShow(token: string, showId: number) {
    return apiClient.delete<null>(apiRoutes.schedule.deleteShow(showId), { token });
  },
};
