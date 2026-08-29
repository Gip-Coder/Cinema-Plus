"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  ChevronLeft, 
  Film, 
  Calendar, 
  Download, 
  Copy, 
  Check, 
  AlertCircle,
  Printer
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { bookingsApi } from "@/lib/api/bookings";
import { resolveMediaUrl } from "@/lib/api/client";
import type { Booking } from "@/types/domain";

export default function BookingDetailPage() {
  const { bookingId } = useParams();
  const router = useRouter();
  const { accessToken, isAuthenticated, isHydrated } = useAuth();

  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isHydrated && !isAuthenticated) {
      router.push("/login?redirect=/bookings");
    }
  }, [isAuthenticated, isHydrated, router]);

  useEffect(() => {
    if (!isAuthenticated || !accessToken || !bookingId) return;

    async function loadBooking() {
      try {
        const idNum = Number(bookingId);
        const data = await bookingsApi.userBookings(accessToken as string);
        const found = data?.find(b => b.id === idNum) || null;
        
        if (found) {
          setBooking(found);
        } else {
          setError("Booking not found. Please double check the ID or listing.");
        }
      } catch (err) {
        console.error("Failed to load booking detail info", err);
        setError("Failed to retrieve booking information.");
      } finally {
        setLoading(false);
      }
    }
    loadBooking();
  }, [accessToken, isAuthenticated, bookingId]);

  const handleDownloadPdf = async () => {
    if (!accessToken || !booking) return;
    try {
      const blob = await bookingsApi.ticketPdf(accessToken, booking.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ticket-${booking.movie?.title.toLowerCase().replace(/\s+/g, "-")}-${booking.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download PDF", err);
      alert("Failed to download PDF ticket. Please try again later.");
    }
  };

  const handleShare = () => {
    if (!booking) return;
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    const text = `Cinema Plus Ticket: "${booking.movie.title}" - Seats: ${booking.booked_seats?.map(s => s.seat_name).join(", ")} on ${booking.show?.date || "N/A"} at ${booking.show?.start_time?.slice(0, 5) || "N/A"}. View details at ${origin}/bookings/${booking.id}`;
    
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  const handleAddToCalendar = () => {
    if (!booking) return;
    
    const showDate = booking.show?.date || new Date().toISOString().split('T')[0];
    const startTime = booking.show?.start_time || "12:00:00";
    
    // Simple google calendar link
    const startIso = `${showDate.replace(/-/g, '')}T${startTime.replace(/:/g, '')}Z`;
    // Add 2 hours for duration
    const endHour = parseInt(startTime.split(':')[0]) + 2;
    const endIso = `${showDate.replace(/-/g, '')}T${endHour < 10 ? '0' : ''}${endHour}${startTime.split(':')[1]}00Z`;

    const gCalUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent("Cinema Plus: " + booking.movie.title)}&dates=${startIso}/${endIso}&details=${encodeURIComponent("Enjoy your movie! Seats: " + booking.booked_seats?.map(s => s.seat_name).join(", "))}&location=${encodeURIComponent(booking.show?.screen?.name || "Premium Screen")}`;
    
    window.open(gCalUrl, '_blank');
  };

  if (!isHydrated || loading) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex flex-col items-center justify-center gap-4 text-zinc-300">
        <AlertCircle className="h-10 w-10 text-red-500" />
        <p>{error || "Booking not found"}</p>
        <button onClick={() => router.push("/bookings")} className="px-4 py-2 bg-red-600 text-white rounded-xl text-xs font-bold">
          Back to Bookings
        </button>
      </div>
    );
  }

  // Payment Breakdown
  const basePrice = booking.total_amount * 0.85;
  const bookingFee = booking.total_amount * 0.10;
  const taxes = booking.total_amount * 0.05;

  return (
    <main className="min-h-screen bg-[hsl(222,84%,2.5%)] text-zinc-100 pb-20">
      
      {/* Top action bar */}
      <section className="max-w-4xl mx-auto px-6 pt-8 flex items-center justify-between">
        <button
          onClick={() => router.push("/bookings")}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/[0.08] bg-black/40 text-xs font-bold text-zinc-300 hover:bg-white/[0.04] transition-colors"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to Bookings
        </button>
        
        <span className="text-xs text-zinc-500 font-mono">CP-ID: {booking.id}</span>
      </section>

      {/* Main Container */}
      <section className="max-w-4xl mx-auto px-6 mt-6 grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Left Column (2/3 width) - Movie info, Timeline, Seating */}
        <div className="md:col-span-2 space-y-6">
          
          {/* Movie spotlight info */}
          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 flex gap-4">
            {/* Poster */}
            <div className="aspect-[2/3] w-20 rounded-xl bg-zinc-900 border border-white/[0.06] overflow-hidden shrink-0">
              {booking.movie?.poster_url ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={resolveMediaUrl(booking.movie.poster_url)} alt={booking.movie.title} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-zinc-700">
                  <Film className="h-6 w-6" />
                </div>
              )}
            </div>

            {/* Details */}
            <div className="space-y-1">
              <span className="inline-flex rounded bg-red-500/10 border border-red-500/20 px-2 py-0.5 text-[9px] font-bold text-red-400 uppercase">
                Now Confirmed
              </span>
              <h2 className="font-extrabold text-lg text-white">{booking.movie?.title}</h2>
              <p className="text-xs text-zinc-400 font-medium capitalize">{booking.movie?.genre} • {booking.movie?.language}</p>
            </div>
          </div>

          {/* Stepper Timeline */}
          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Booking Timeline</h3>
            
            <div className="relative flex items-center justify-between pt-2">
              <div className="absolute left-4 right-4 top-1/2 -translate-y-1/2 h-0.5 bg-white/[0.06] -z-10" />
              <div className="absolute left-4 right-4 top-1/2 -translate-y-1/2 h-0.5 bg-red-600 -z-10" style={{ width: booking.status === "confirmed" ? "66%" : "100%" }} />

              {/* Step 1 */}
              <div className="flex flex-col items-center gap-1.5 text-center">
                <div className="h-8 w-8 rounded-full bg-red-600 text-white flex items-center justify-center text-xs font-bold shadow-md">
                  ✓
                </div>
                <span className="text-[10px] font-bold text-zinc-300">Reserved</span>
              </div>

              {/* Step 2 */}
              <div className="flex flex-col items-center gap-1.5 text-center">
                <div className="h-8 w-8 rounded-full bg-red-600 text-white flex items-center justify-center text-xs font-bold shadow-md">
                  ✓
                </div>
                <span className="text-[10px] font-bold text-zinc-300">Paid</span>
              </div>

              {/* Step 3 */}
              <div className="flex flex-col items-center gap-1.5 text-center">
                <div className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold shadow-md transition-all ${
                  booking.status === "confirmed" ? "bg-red-600 text-white" : "bg-white/[0.06] text-zinc-500 border border-white/[0.08]"
                }`}>
                  {booking.status === "confirmed" ? "✓" : "3"}
                </div>
                <span className="text-[10px] font-bold text-zinc-300">Ticket Ready</span>
              </div>

              {/* Step 4 */}
              <div className="flex flex-col items-center gap-1.5 text-center">
                <div className="h-8 w-8 rounded-full bg-white/[0.03] border border-white/[0.08] text-zinc-600 flex items-center justify-center text-xs font-bold">
                  4
                </div>
                <span className="text-[10px] font-bold text-zinc-500">Checked In</span>
              </div>
            </div>
          </div>

          {/* Seat Layout Preview */}
          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Screen View Layout</h3>
            
            {/* Visual preview box */}
            <div className="bg-zinc-950/60 rounded-xl p-6 border border-white/[0.03] space-y-8 flex flex-col items-center">
              
              {/* Screen curve */}
              <div className="w-full max-w-sm space-y-1.5 text-center">
                <div className="h-1.5 w-full bg-red-600/30 rounded-full shadow-[0_-2px_10px_rgba(220,38,38,0.2)]" />
                <span className="text-[9px] uppercase tracking-widest text-zinc-600 font-bold">Screen This Way</span>
              </div>

              {/* Simulated seating block */}
              <div className="flex flex-col gap-2.5">
                {["A", "B", "C", "D", "E"].map((rowLabel) => (
                  <div key={rowLabel} className="flex items-center gap-2">
                    <span className="text-[10px] text-zinc-600 font-bold w-4">{rowLabel}</span>
                    <div className="flex gap-2">
                      {[1, 2, 3, 4, 5, 6, 7, 8].map((colNum) => {
                        const seatName = `${rowLabel}${colNum}`;
                        const isBookedByUser = booking.booked_seats?.some(s => s.seat_name === seatName);
                        
                        return (
                          <div
                            key={colNum}
                            className={`h-4.5 w-4.5 sm:h-5 sm:w-5 rounded flex items-center justify-center text-[8px] font-extrabold select-none transition-all ${
                              isBookedByUser
                                ? "bg-red-600 text-white shadow-lg shadow-red-600/20 scale-110"
                                : "bg-white/[0.04] text-zinc-700 border border-white/[0.04]"
                            }`}
                          >
                            {colNum}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-4 text-[10px] font-semibold text-zinc-500">
                <div className="flex items-center gap-1.5">
                  <div className="h-3 w-3 rounded bg-red-600" />
                  <span>Your Seats</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="h-3 w-3 rounded bg-white/[0.04] border border-white/[0.04]" />
                  <span>Other Seats</span>
                </div>
              </div>

            </div>
          </div>

        </div>

        {/* Right Column (1/3 width) - Ticket Card & Receipt */}
        <div className="space-y-6">
          
          {/* Visual E-Ticket Card */}
          <div className="rounded-3xl border border-white/[0.12] bg-zinc-950 p-6 text-center space-y-6 shadow-2xl relative overflow-hidden">
            {/* Visual cuts on left/right for ticket look */}
            <div className="absolute top-1/2 -left-3 h-6 w-6 rounded-full bg-[hsl(222,84%,2.5%)] -translate-y-1/2" />
            <div className="absolute top-1/2 -right-3 h-6 w-6 rounded-full bg-[hsl(222,84%,2.5%)] -translate-y-1/2" />

            <div className="space-y-1">
              <span className="inline-flex rounded-full bg-red-600/10 border border-red-500/20 px-3.5 py-0.5 text-[9px] font-extrabold text-red-400 uppercase tracking-widest">
                Admission Ticket
              </span>
              <h3 className="font-extrabold text-base text-white truncate">{booking.movie?.title}</h3>
              <p className="text-[10px] text-zinc-500 font-mono">cp-id: {booking.id}</p>
            </div>

            {/* QR Barcode */}
            <div className="h-40 w-40 bg-white rounded-2xl mx-auto flex items-center justify-center p-3 shadow-inner">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=CinemaPlus_Booking_${booking.id}`}
                alt="QR Code"
                className="h-full w-full object-contain"
              />
            </div>

            <div className="space-y-3.5 text-xs border-t border-dashed border-white/[0.12] pt-4">
              <div className="grid grid-cols-2 gap-2 text-left">
                <div>
                  <span className="block text-[10px] text-zinc-500 font-semibold uppercase">Show Date</span>
                  <span className="font-bold text-zinc-200">
                    {booking.show?.date ? new Date(booking.show.date).toLocaleDateString() : "N/A"}
                  </span>
                </div>
                <div>
                  <span className="block text-[10px] text-zinc-500 font-semibold uppercase">Showtime</span>
                  <span className="font-bold text-zinc-200">
                    {booking.show?.start_time ? booking.show.start_time.slice(0, 5) : "N/A"}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-left">
                <div>
                  <span className="block text-[10px] text-zinc-500 font-semibold uppercase">Screen</span>
                  <span className="font-bold text-zinc-200">{booking.show?.screen?.name || "Screen 1"}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-zinc-500 font-semibold uppercase">Seats</span>
                  <span className="font-bold text-zinc-200 truncate block">
                    {booking.booked_seats?.map(s => s.seat_name).join(", ")}
                  </span>
                </div>
              </div>
            </div>

            {/* Ticket download actions */}
            <div className="space-y-2 pt-2">
              {booking.status === "confirmed" && (
                <button
                  onClick={handleDownloadPdf}
                  className="w-full py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-lg transition-all"
                >
                  <Download className="h-4 w-4" />
                  Download PDF Ticket
                </button>
              )}
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={handleAddToCalendar}
                  className="py-2 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04] text-zinc-300 hover:text-white font-bold text-[10px] flex items-center justify-center gap-1 transition-all"
                >
                  <Calendar className="h-3.5 w-3.5" />
                  Add to Calendar
                </button>
                <button
                  onClick={handleShare}
                  className="py-2 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04] text-zinc-300 hover:text-white font-bold text-[10px] flex items-center justify-center gap-1 transition-all"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? "Copied!" : "Share Details"}
                </button>
              </div>
            </div>

          </div>

          {/* Payment receipt card */}
          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Payment Summary</h3>
            
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-zinc-500">Base Fare:</span>
                <span className="text-zinc-300 font-semibold">${basePrice.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Convenience Charge:</span>
                <span className="text-zinc-300 font-semibold">${bookingFee.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Taxes:</span>
                <span className="text-zinc-300 font-semibold">${taxes.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t border-white/[0.04] pt-2.5 text-sm font-black">
                <span className="text-zinc-200">Total Paid:</span>
                <span className="text-red-500">${booking.total_amount.toFixed(2)}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 bg-white/[0.01] p-3 rounded-xl border border-white/[0.03] text-[10px] text-zinc-500">
              <Printer className="h-4 w-4 text-zinc-600 shrink-0" />
              <span>Paid via Simulated Credit Card. Need assistance? Contact support@cinemaplus.com</span>
            </div>
          </div>

        </div>

      </section>
    </main>
  );
}
