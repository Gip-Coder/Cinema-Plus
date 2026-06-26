"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ChevronLeft, 
  Download, 
  QrCode, 
  Sparkles, 
  ShieldAlert,
  Search
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { bookingsApi } from "@/lib/api/bookings";
import type { Booking } from "@/types/domain";

export default function TicketCenterPage() {
  const { accessToken, isAuthenticated, isHydrated } = useAuth();
  const router = useRouter();

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (isHydrated && !isAuthenticated) {
      router.push("/login?redirect=/tickets");
    }
  }, [isAuthenticated, isHydrated, router]);

  useEffect(() => {
    if (!isAuthenticated || !accessToken) return;

    async function loadTickets() {
      try {
        const data = await bookingsApi.userBookings(accessToken as string);
        setBookings(data ?? []);
      } catch (err) {
        console.error("Failed to load tickets", err);
      } finally {
        setLoading(false);
      }
    }
    loadTickets();
  }, [accessToken, isAuthenticated]);

  const handleDownloadPdf = async (bookingId: number, movieTitle: string) => {
    if (!accessToken) return;
    try {
      const blob = await bookingsApi.ticketPdf(accessToken as string, bookingId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ticket-${movieTitle.toLowerCase().replace(/\s+/g, "-")}-${bookingId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download PDF ticket", err);
      alert("Failed to download PDF ticket. Please try again.");
    }
  };

  if (!isHydrated || loading) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  // Split bookings into active and history
  const activeBookings = bookings.filter(b => {
    if (b.status === "cancelled") return false;
    const showDate = b.show?.date ? new Date(b.show.date) : new Date(b.booking_date);
    return showDate >= new Date(new Date().setHours(0,0,0,0));
  });

  const historyBookings = bookings.filter(b => {
    const showDate = b.show?.date ? new Date(b.show.date) : new Date(b.booking_date);
    return b.status === "cancelled" || showDate < new Date(new Date().setHours(0,0,0,0));
  });

  // Filtered by Search Query
  const filteredActive = activeBookings.filter(b => 
    b.movie?.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    b.id.toString().includes(searchQuery)
  );

  const filteredHistory = historyBookings.filter(b => 
    b.movie?.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    b.id.toString().includes(searchQuery)
  );

  return (
    <main className="min-h-screen bg-[hsl(222,84%,2.5%)] text-zinc-100 pb-20">
      <div className="max-w-5xl mx-auto px-6 py-12 space-y-8">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-white/[0.04] pb-6">
          <div className="space-y-1">
            <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <QrCode className="h-8 w-8 text-red-600" />
              Digital Ticket Center
            </h1>
            <p className="text-xs text-zinc-400 font-medium">Quick access boarding passes with printable receipt copies.</p>
          </div>
          <Link
            href="/dashboard"
            className="self-start text-xs font-bold text-red-400 hover:text-red-300 flex items-center gap-0.5"
          >
            <ChevronLeft className="h-4 w-4" />
            Dashboard
          </Link>
        </div>

        {/* Search bar */}
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <input
            type="text"
            placeholder="Search tickets by Movie..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-white/[0.08] bg-zinc-900/30 py-2.5 pl-9 pr-4 text-xs text-white placeholder-zinc-600 focus:border-red-500/30 outline-none"
          />
        </div>

        {/* Active Passes Section */}
        <div className="space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1">
            <Sparkles className="h-4 w-4 text-red-500" />
            Active Boarding Passes ({filteredActive.length})
          </h2>

          {filteredActive.length === 0 ? (
            <div className="rounded-2xl border border-white/[0.04] bg-white/[0.01] p-12 text-center text-zinc-500 text-xs">
              No active boarding passes ready. Past or cancelled tickets can be retrieved in History below.
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {filteredActive.map((booking) => (
                <div 
                  key={booking.id}
                  className="rounded-3xl border border-white/[0.12] bg-zinc-950 p-5 text-center space-y-5 shadow-2xl relative overflow-hidden group hover:border-red-500/30 transition-all duration-300"
                >
                  {/* Decorative Ticket cuts */}
                  <div className="absolute top-1/2 -left-3 h-5 w-5 rounded-full bg-[hsl(222,84%,2.5%)] -translate-y-1/2 border-r border-white/[0.06]" />
                  <div className="absolute top-1/2 -right-3 h-5 w-5 rounded-full bg-[hsl(222,84%,2.5%)] -translate-y-1/2 border-l border-white/[0.06]" />

                  {/* Movie Info */}
                  <div className="space-y-0.5">
                    <span className="inline-flex rounded bg-red-500/10 border border-red-500/20 px-2 py-0.5 text-[8px] font-bold text-red-400 uppercase">
                      {booking.show?.screen?.name || "Premium screen"}
                    </span>
                    <h3 className="font-extrabold text-sm text-white truncate group-hover:text-red-400 transition-colors">{booking.movie?.title}</h3>
                    <p className="text-[9px] text-zinc-500 font-mono">booking-id: cp-{booking.id}</p>
                  </div>

                  {/* QR Box */}
                  <div className="h-36 w-36 bg-white rounded-xl mx-auto flex items-center justify-center p-2.5 shadow-inner">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img 
                      src={`https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=CinemaPlus_Booking_${booking.id}`}
                      alt="QR Code"
                      className="h-full w-full object-contain"
                    />
                  </div>

                  {/* Show Information */}
                  <div className="space-y-2 text-[11px] text-zinc-400 font-medium text-left border-t border-dashed border-white/[0.12] pt-3.5">
                    <div className="flex justify-between">
                      <span className="text-zinc-600">Date:</span>
                      <span className="font-bold text-zinc-200">
                        {booking.show?.date ? new Date(booking.show.date).toLocaleDateString() : "N/A"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-600">Time:</span>
                      <span className="font-bold text-zinc-200">
                        {booking.show?.start_time ? booking.show.start_time.slice(0, 5) : "N/A"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-600">Seats:</span>
                      <span className="font-bold text-zinc-200 truncate max-w-[120px]">
                        {booking.booked_seats?.map(s => s.seat_name).join(", ")}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDownloadPdf(booking.id, booking.movie?.title)}
                    className="w-full py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs flex items-center justify-center gap-1 shadow-md"
                  >
                    <Download className="h-3.5 w-3.5" />
                    Download PDF E-Ticket
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Booking History Section */}
        <div className="space-y-4 border-t border-white/[0.04] pt-8">
          <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1">
            <ShieldAlert className="h-4 w-4 text-zinc-600" />
            Past & Cancelled Tickets ({filteredHistory.length})
          </h2>

          {filteredHistory.length === 0 ? (
            <p className="text-xs text-zinc-500 pl-1">No ticket history available.</p>
          ) : (
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.01] overflow-hidden">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/[0.06] bg-white/[0.02] text-zinc-500 font-bold uppercase text-[10px]">
                    <th className="p-4">Movie</th>
                    <th className="p-4">Date</th>
                    <th className="p-4">Seats</th>
                    <th className="p-4">Price</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04] text-zinc-300 font-medium">
                  {filteredHistory.map((booking) => (
                    <tr key={booking.id} className="hover:bg-white/[0.01]">
                      <td className="p-4 font-bold text-white">{booking.movie?.title}</td>
                      <td className="p-4">
                        {booking.show?.date ? new Date(booking.show.date).toLocaleDateString() : new Date(booking.booking_date).toLocaleDateString()}
                      </td>
                      <td className="p-4 font-mono">{booking.booked_seats?.map(s => s.seat_name).join(", ")}</td>
                      <td className="p-4 font-bold">${booking.total_amount.toFixed(2)}</td>
                      <td className="p-4">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase ${
                          booking.status === "cancelled" ? "bg-red-500/10 text-red-400" : "bg-zinc-800 text-zinc-400"
                        }`}>
                          {booking.status}
                        </span>
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <Link 
                          href={`/bookings/${booking.id}`}
                          className="text-[10px] font-bold text-red-400 hover:underline"
                        >
                          View Receipt
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </main>
  );
}
