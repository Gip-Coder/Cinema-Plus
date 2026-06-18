import { apiClient } from "@/lib/api/client";
import { apiRoutes } from "@/lib/api/routes";
import type { Booking, ReservationGroup } from "@/types/domain";

export interface ReservationCreate {
  seats: string[];
  show_id: number;
}

export const reservationsApi = {
  create(token: string, payload: ReservationCreate) {
    return apiClient.post<ReservationGroup, ReservationCreate>(apiRoutes.reservations.create, payload, {
      token,
    });
  },
  detail(token: string, groupId: number) {
    return apiClient.get<ReservationGroup>(apiRoutes.reservations.detail(groupId), { token });
  },
  cancel(token: string, groupId: number) {
    return apiClient.delete<null>(apiRoutes.reservations.cancel(groupId), { token });
  },
  confirm(token: string, groupId: number) {
    return apiClient.post<Booking>(apiRoutes.reservations.confirm(groupId), undefined, { token });
  },
  seatStatus(showId: number) {
    return apiClient.get<Record<string, unknown>>(apiRoutes.reservations.seatStatus(showId));
  },
};
