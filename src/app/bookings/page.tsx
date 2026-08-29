"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Search, 
  Film, 
  Calendar, 
  Clock, 
  MapPin, 
  ArrowUpDown, 
  Download, 
  QrCode, 
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Monitor
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { bookingsApi } from "@/lib/api/bookings";
import { resolveMediaUrl } from "@/lib/api/client";
import type { Booking } from "@/types/domain";

export default function BookingsHistoryPage() {
  const { accessToken, isAuthenticated, isHydrated } = useAuth();
  const router = useRouter();

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "confirmed" | "cancelled">("all");
  const [sortField, setSortField] = useState<"date" | "amount">("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 6;

  // Selected booking for QR Preview modal
  const [previewBooking, setPreviewBooking] = useState<Booking | null>(null);

  useEffect(() => {
    if (isHydrated && !isAuthenticated) {
      router.push("/login?redirect=/bookings");
    }
  }, [isAuthenticated, isHydrated, router]);

  useEffect(() => {
    if (!isAuthenticated || !accessToken) return;

    async function loadBookings() {
      try {
        const data = await bookingsApi.userBookings(accessToken as string);
        setBookings(data ?? []);
      } catch (err) {
        console.error("Failed to load user bookings history", err);
      } finally {
        setLoading(false);
      }
    }
    loadBookings();
  }, [accessToken, isAuthenticated]);

  const handleDownloadPdf = async (bookingId: number, movieTitle: string) => {
    if (!accessToken) return;
    try {
      const blob = await bookingsApi.ticketPdf(accessToken, bookingId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ticket-${movieTitle.toLowerCase().replace(/\s+/g, "-")}-${bookingId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download ticket PDF", err);
      alert("Failed to download PDF ticket. Please try again later.");
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

  // Sort & Filter
  const filteredBookings = bookings
    .filter((b) => {
      const matchesSearch = 
        b.movie?.title.toLowerCase().includes(search.toLowerCase()) ||
        b.id.toString().includes(search) ||
        b.show?.screen?.name?.toLowerCase().includes(search.toLowerCase());

      const matchesStatus =
        statusFilter === "all" || b.status === statusFilter;

      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      if (sortField === "date") {
        const dateA = a.show?.date ? new Date(a.show.date).getTime() : new Date(a.booking_date).getTime();
        const dateB = b.show?.date ? new Date(b.show.date).getTime() : new Date(b.booking_date).getTime();
        return sortOrder === "desc" ? dateB - dateA : dateA - dateB;
      } else {
        return sortOrder === "desc" ? b.total_amount - a.total_amount : a.total_amount - b.total_amount;
      }
    });

  // Paginated bookings
  const totalPages = Math.max(1, Math.ceil(filteredBookings.length / itemsPerPage));
  const paginatedBookings = filteredBookings.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const toggleSort = (field: "date" | "amount") => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
    setCurrentPage(1);
  };

  return (
    <main className="min-h-screen bg-[hsl(222,84%,2.5%)] text-zinc-100 pb-20">
      <div className="max-w-6xl mx-auto px-6 py-12 space-y-8">
        
        {/* Title */}
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-white/[0.04] pb-6">
          <div className="space-y-1">
            <h1 className="text-3xl font-extrabold text-white tracking-tight">Booking History</h1>
            <p className="text-xs text-zinc-400 font-medium">Search, filter, and retrieve all your movie tickets and receipt copies.</p>
          </div>
          <Link
            href="/dashboard"
            className="self-start text-xs font-bold text-red-400 hover:text-red-300 flex items-center gap-0.5"
          >
            <ChevronLeft className="h-4 w-4" />
            Dashboard
          </Link>
        </div>

        {/* Filters Panel */}
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-white/[0.02] border border-white/[0.06] p-4 rounded-2xl">
          {/* Search */}
          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              placeholder="Search by Movie or booking ID..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full rounded-xl border border-white/[0.08] bg-zinc-900/30 py-2.5 pl-9 pr-4 text-xs text-white placeholder-zinc-600 focus:border-red-500/30 outline-none"
            />
          </div>

          {/* Controls */}
          <div className="flex flex-wrap items-center gap-4 w-full md:w-auto">
            {/* Status Select */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-zinc-500">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as "all" | "confirmed" | "cancelled");
                  setCurrentPage(1);
                }}
                className="rounded-lg border border-white/[0.08] bg-zinc-900 py-2 px-3 text-xs text-white focus:outline-none"
              >
                <option value="all">All Bookings</option>
                <option value="confirmed">Confirmed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            {/* Sorting Toggles */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => toggleSort("date")}
                className={`flex items-center gap-1 px-3 py-2 rounded-lg border text-xs font-semibold transition-colors ${
                  sortField === "date" ? "bg-red-600/10 border-red-500/30 text-red-400" : "border-white/[0.06] text-zinc-400 hover:text-zinc-200"
                }`}
              >
                Date
                <ArrowUpDown className="h-3 w-3" />
              </button>
              <button
                onClick={() => toggleSort("amount")}
                className={`flex items-center gap-1 px-3 py-2 rounded-lg border text-xs font-semibold transition-colors ${
                  sortField === "amount" ? "bg-red-600/10 border-red-500/30 text-red-400" : "border-white/[0.06] text-zinc-400 hover:text-zinc-200"
                }`}
              >
                Amount
                <ArrowUpDown className="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>

        {/* Listings Grid */}
        {paginatedBookings.length === 0 ? (
          <div className="rounded-2xl border border-white/[0.04] bg-white/[0.01] p-16 text-center space-y-3">
            <Film className="mx-auto h-12 w-12 text-zinc-700" />
            <p className="text-zinc-500 text-sm">No ticket bookings match your parameters.</p>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2">
            {paginatedBookings.map((booking) => (
              <div 
                key={booking.id}
                className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 flex flex-col justify-between gap-5 hover:border-red-500/20 transition-all shadow-md relative group"
              >
                {/* Header info */}
                <div className="flex gap-4">
                  {/* Poster */}
                  <div className="aspect-[2/3] w-24 rounded-xl bg-zinc-900 border border-white/[0.06] overflow-hidden shrink-0">
                    {booking.movie?.poster_url ? (
                      /* eslint-disable-next-line @next/next/no-img-element */
                      <img src={resolveMediaUrl(booking.movie.poster_url)} alt={booking.movie.title} className="w-full h-full object-cover group-hover:scale-102 transition-transform" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-zinc-700">
                        <Film className="h-8 w-8" />
                      </div>
                    )}
                  </div>

                  {/* Booking details */}
                  <div className="space-y-1.5 flex-grow min-w-0">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <span className="text-[10px] text-zinc-500 font-mono">ID: cp-{booking.id}</span>
                      <span className={`px-2 py-0.5 rounded text-[9px] font-extrabold uppercase ${
                        booking.status === "confirmed" 
                          ? "bg-green-500/10 border border-green-500/20 text-green-400" 
                          : "bg-red-500/10 border border-red-500/20 text-red-400"
                      }`}>
                        {booking.status}
                      </span>
                    </div>

                    <h3 className="font-extrabold text-base text-zinc-100 group-hover:text-red-400 transition-colors line-clamp-1">
                      {booking.movie?.title}
                    </h3>

                    <div className="space-y-1 text-xs text-zinc-400 font-medium">
                      <p className="flex items-center gap-1.5">
                        <Calendar className="h-4 w-4 text-zinc-600 shrink-0" />
                        {booking.show?.date ? new Date(booking.show.date).toLocaleDateString("en-US", { weekday: "short", day: "numeric", month: "short" }) : "N/A"}
                      </p>
                      <p className="flex items-center gap-1.5">
                        <Clock className="h-4 w-4 text-zinc-600 shrink-0" />
                        {booking.show?.start_time ? booking.show.start_time.slice(0, 5) : "N/A"}
                      </p>
                      <p className="flex items-center gap-1.5">
                        <Monitor className="h-4 w-4 text-zinc-600 shrink-0" />
                        {booking.show?.screen?.name || "Standard Screen"}
                      </p>
                      <p className="flex items-center gap-1.5">
                        <MapPin className="h-4 w-4 text-zinc-600 shrink-0" />
                        Seats: <span className="font-bold text-zinc-300">{booking.booked_seats?.map(s => s.seat_name).join(", ")}</span>
                      </p>
                    </div>
                  </div>
                </div>

                {/* Footer buttons */}
                <div className="flex items-center justify-between border-t border-white/[0.04] pt-4 mt-auto">
                  <span className="text-sm font-black text-zinc-200">
                    ${booking.total_amount.toFixed(2)}
                  </span>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPreviewBooking(booking)}
                      className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] text-zinc-400 hover:text-white transition-colors"
                      title="Preview QR Code"
                    >
                      <QrCode className="h-4 w-4" />
                    </button>
                    {booking.status === "confirmed" && (
                      <button
                        onClick={() => handleDownloadPdf(booking.id, booking.movie?.title)}
                        className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] text-zinc-400 hover:text-white transition-colors"
                        title="Download PDF E-Ticket"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                    )}
                    <Link
                      href={`/bookings/${booking.id}`}
                      className="px-3.5 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs flex items-center gap-1"
                    >
                      Details
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                </div>

              </div>
            ))}
          </div>
        )}

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-4 pt-6">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-xl border border-white/[0.06] bg-white/[0.01] text-zinc-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <span className="text-xs font-bold text-zinc-400">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-xl border border-white/[0.06] bg-white/[0.01] text-zinc-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        )}

      </div>

      {/* QR Code Preview Modal */}
      {previewBooking && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-zinc-950 border border-white/[0.12] rounded-3xl p-6 max-w-sm w-full text-center space-y-5 relative shadow-2xl">
            <button
              onClick={() => setPreviewBooking(null)}
              className="absolute top-4 right-4 text-zinc-500 hover:text-zinc-300 text-sm font-bold"
            >
              ✕
            </button>
            <div className="space-y-1">
              <span className="inline-flex rounded bg-red-500/10 border border-red-500/20 px-2 py-0.5 text-[9px] font-bold text-red-400 uppercase">
                Digital Boarding Pass
              </span>
              <h3 className="font-extrabold text-lg text-white line-clamp-1">{previewBooking.movie?.title}</h3>
              <p className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">
                Seats: {previewBooking.booked_seats?.map(s => s.seat_name).join(", ")}
              </p>
            </div>

            {/* QR box */}
            <div className="h-44 w-44 bg-white rounded-2xl mx-auto flex items-center justify-center p-3 shadow-inner">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img 
                src={`https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=CinemaPlus_Booking_${previewBooking.id}`}
                alt="QR Code Ticket"
                className="h-full w-full object-contain"
              />
            </div>

            <div className="space-y-1 text-xs text-zinc-500 font-medium">
              <p>Booking ID: cp-{previewBooking.id}</p>
              <p>Show date: {previewBooking.show?.date ? new Date(previewBooking.show.date).toLocaleDateString() : "N/A"}</p>
              <p className="text-[10px] text-red-400">Scan this QR barcode at the screen entrance.</p>
            </div>

            <button
              onClick={() => {
                handleDownloadPdf(previewBooking.id, previewBooking.movie?.title);
                setPreviewBooking(null);
              }}
              className="w-full py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-lg"
            >
              <Download className="h-4 w-4" />
              Download PDF E-Ticket
            </button>
          </div>
        </div>
      )}

    </main>
  );
}
