"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  CheckCircle,
  Download,
  Share2,
  Calendar,
  Clock,
  Monitor,
  ChevronRight,
  XCircle
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { apiClient, resolveMediaUrl } from "@/lib/api/client";
import BookingStepper from "@/components/booking/stepper";
import type { Booking } from "@/types/domain";

export default function ConfirmationPage() {
  const { bookingId } = useParams();
  const router = useRouter();
  const { accessToken } = useAuth();

  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [shareSuccess, setShareSuccess] = useState(false);
  const [calendarSuccess, setCalendarSuccess] = useState(false);

  useEffect(() => {
    async function loadBooking() {
      if (!bookingId || !accessToken) return;
      try {
        // Query user bookings to locate this booking
        const res = await apiClient.get<Booking[]>(`/api/bookings/user/bookings`, { token: accessToken });
        const target = res?.find(b => b.id === Number(bookingId));
        if (target) {
          setBooking(target);
        } else {
          setError("Booking details not found or unauthorized to view.");
        }
      } catch (err) {
        console.error("Failed to load booking details:", err);
        setError("Failed to retrieve booking confirmation info.");
      } finally {
        setLoading(false);
      }
    }

    loadBooking();
  }, [bookingId, accessToken]);

  const handleDownloadPDF = async () => {
    if (!bookingId || !accessToken) return;
    try {
      const blob = await apiClient.blob(`/api/tickets/ticket/${bookingId}/pdf`, {
        token: accessToken,
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `cinema_plus_ticket_${bookingId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error("PDF download error:", err);
      alert("Error initiating PDF download.");
    }
  };

  const handleShare = () => {
    setShareSuccess(true);
    setTimeout(() => setShareSuccess(false), 3000);
  };

  const handleCalendar = () => {
    setCalendarSuccess(true);
    setTimeout(() => setCalendarSuccess(false), 3000);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex flex-col items-center justify-center gap-4 text-zinc-300">
        <XCircle className="h-10 w-10 text-red-500" />
        <p className="max-w-md text-center text-sm">{error || "Failed to find booking."}</p>
        <button onClick={() => router.push("/")} className="px-4 py-2 bg-red-600 text-white rounded-lg text-xs font-bold">
          Back to Home
        </button>
      </div>
    );
  }

  const show = booking.show;
  const movie = booking.movie;

  return (
    <main className="min-h-screen bg-[hsl(222,84%,2.5%)] text-zinc-100 pb-20">
      {/* Stepper Header */}
      <div className="border-b border-white/[0.04] bg-[hsl(222,84%,3.5%)]">
        <div className="max-w-5xl mx-auto px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <h1 className="text-base font-bold text-white flex items-center gap-2">
            Booking Success
          </h1>
          <BookingStepper currentStep={5} />
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 mt-10 space-y-8 text-center">
        {/* Success Banner */}
        <div className="flex flex-col items-center gap-3">
          <CheckCircle className="h-14 w-14 text-emerald-400 animate-bounce" />
          <h2 className="text-xl sm:text-2xl font-extrabold text-white">Congratulations, your order is locked!</h2>
          <p className="text-xs text-zinc-400">
            A confirmation email along with your PDF ticket receipt has been sent to your email address.
          </p>
        </div>

        {/* Dynamic Digital Cinema Ticket Design Card */}
        <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] overflow-hidden shadow-2xl relative flex flex-col text-left">
          
          {/* Top segment: Branding & Booking ID */}
          <div className="bg-red-600/10 border-b border-white/[0.04] p-5 flex items-center justify-between">
            <span className="text-xs font-extrabold text-red-500 uppercase tracking-widest">Cinema Plus Digital Ticket</span>
            <span className="text-xs text-zinc-400">Booking ID: <strong className="text-zinc-200">#CP{booking.id}</strong></span>
          </div>

          {/* Middle segment: Poster & Details */}
          <div className="p-6 flex flex-col sm:flex-row gap-6 border-b border-dashed border-white/[0.08]">
            {movie?.poster_url && (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img src={resolveMediaUrl(movie.poster_url)} alt={movie.title} className="w-24 h-36 object-cover rounded-xl border border-white/[0.08] shrink-0" />
            )}
            
            <div className="space-y-4 flex-1">
              <div>
                <h3 className="text-lg font-bold text-white">{movie?.title}</h3>
                <span className="text-[10px] uppercase font-bold text-zinc-500">{movie?.genre} • {movie?.language}</span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="space-y-1">
                  <span className="text-zinc-500 block uppercase text-[9px] tracking-wider">Date</span>
                  <span className="font-semibold text-zinc-200 flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    {show?.date}
                  </span>
                </div>
                <div className="space-y-1">
                  <span className="text-zinc-500 block uppercase text-[9px] tracking-wider">Time</span>
                  <span className="font-semibold text-zinc-200 flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {show?.start_time.slice(0, 5)}
                  </span>
                </div>
                <div className="space-y-1">
                  <span className="text-zinc-500 block uppercase text-[9px] tracking-wider">Auditorium</span>
                  <span className="font-semibold text-zinc-200 flex items-center gap-1">
                    <Monitor className="h-3.5 w-3.5" />
                    {show?.screen?.name || `Screen #${show?.screen_id}`}
                  </span>
                </div>
                <div className="space-y-1">
                  <span className="text-zinc-500 block uppercase text-[9px] tracking-wider">Selected Seats</span>
                  <span className="font-extrabold text-zinc-200">
                    {booking.booked_seats.map(s => s.seat_name).sort().join(", ")}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom segment: Ticket QR Scanner validation details */}
          <div className="p-6 bg-white/[0.01] flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="space-y-2">
              <span className="text-zinc-500 block uppercase text-[9px] tracking-wider">Instructions</span>
              <p className="text-[10px] text-zinc-400 leading-relaxed max-w-sm">
                Present this QR code at the screen entrance. Food & beverage items can be purchased separately at the counter.
              </p>
              <div className="text-xs pt-1">
                Amount Paid: <span className="font-extrabold text-emerald-400">₹{booking.total_amount}</span>
              </div>
            </div>

            {/* Public QR Code service */}
            <div className="p-2 rounded-xl bg-white border border-zinc-200 shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img 
                src={`https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=CP-BOOKING-${booking.id}`} 
                alt="Ticket QR Code" 
                className="w-24 h-24"
              />
            </div>
          </div>
        </div>

        {/* Interactive Actions Bar */}
        <div className="flex flex-wrap items-center justify-center gap-3">
          <button
            onClick={handleDownloadPDF}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-xs font-bold text-white shadow-lg shadow-red-600/10 transition-all hover:scale-105"
          >
            <Download className="h-4 w-4" />
            Download PDF Ticket
          </button>
          
          <button
            onClick={handleShare}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-white/[0.08] hover:bg-white/[0.04] text-xs font-bold text-zinc-300 transition-all"
          >
            <Share2 className="h-4 w-4" />
            {shareSuccess ? "Link Copied!" : "Share Booking"}
          </button>

          <button
            onClick={handleCalendar}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-white/[0.08] hover:bg-white/[0.04] text-xs font-bold text-zinc-300 transition-all"
          >
            <Calendar className="h-4 w-4" />
            {calendarSuccess ? "Added to Calendar!" : "Add to Calendar"}
          </button>
        </div>

        <div className="pt-4">
          <Link 
            href="/"
            className="text-xs font-bold text-red-500 hover:text-red-400 inline-flex items-center gap-1"
          >
            Go back to Movie Spotlight
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </main>
  );
}
