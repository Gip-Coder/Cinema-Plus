import { apiClient } from "@/lib/api/client";
import { apiRoutes } from "@/lib/api/routes";
import type { Booking, BookedSeat, PriceCalculation } from "@/types/domain";

export interface BookingCreate {
  movie_id: number;
  seats: Array<Pick<BookedSeat, "category" | "seat_name" | "show_id">>;
  show_id?: number | null;
  total_amount: number;
}

export const bookingsApi = {
  seatStatuses(showId: number) {
    return apiClient.get<Record<string, unknown>>(apiRoutes.bookings.seats(showId));
  },
  create(token: string, payload: BookingCreate) {
    return apiClient.post<Booking, BookingCreate>(apiRoutes.bookings.book, payload, { token });
  },
  userBookings(token: string) {
    return apiClient.get<Booking[]>(apiRoutes.bookings.userBookings, { token });
  },
  priceCalculation(showId: number, category: string) {
    return apiClient.get<PriceCalculation>(apiRoutes.bookings.priceCalculation, {
      query: { category, show_id: showId },
    });
  },
  ticketPdf(token: string, bookingId: number) {
    return apiClient.blob(apiRoutes.tickets.pdf(bookingId), { token });
  },
};
