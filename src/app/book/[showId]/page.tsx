"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";

import { 
  ChevronLeft, 
  AlertTriangle,
  Clock
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { scheduleApi } from "@/lib/api/schedule";
import * as adminApi from "@/lib/api/admin";
import { reservationsApi } from "@/lib/api/reservations";
import { apiClient } from "@/lib/api/client";
import SeatMap from "@/components/booking/seat-map";
import BookingStepper from "@/components/booking/stepper";
import type { Show, SeatDefinition, TheatreLayout, PriceCalculation, ReservationGroup } from "@/types/domain";

export default function BookSeatsPage() {
  const { showId } = useParams();
  const router = useRouter();
  const { accessToken, isAuthenticated } = useAuth();

  // Core State
  const [show, setShow] = useState<Show | null>(null);
  const [layout, setLayout] = useState<TheatreLayout | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Seat States
  const [bookedSeats, setBookedSeats] = useState<string[]>([]);
  const [reservedSeats, setReservedSeats] = useState<string[]>([]);
  const [selectedSeats, setSelectedSeats] = useState<string[]>([]);

  // Dynamic Prices from Backend
  const [prices, setPrices] = useState<Record<string, number>>({
    Normal: 150,
    Executive: 220,
    Premium: 300,
  });

  // Local Reservation Recovery State
  const [recoveredReservation, setRecoveredReservation] = useState<ReservationGroup | null>(null);

  // Fetch seat statuses
  const fetchSeatStatuses = useCallback(async () => {
    if (!showId) return;
    try {
      const res = await reservationsApi.seatStatus(Number(showId));
      if (res) {
        // Safe cast response structure
        const data = res as unknown as { booked: string[]; reserved: string[] };
        setBookedSeats(data.booked || []);
        setReservedSeats(data.reserved || []);
      }
    } catch (err) {
      console.error("Failed to poll seat statuses:", err);
    }
  }, [showId]);

  // Initial Data Fetch
  useEffect(() => {
    async function loadData() {
      if (!showId) return;
      setLoading(true);
      try {
        const showData = await scheduleApi.show(Number(showId));
        setShow(showData);

        if (showData && showData.screen_id) {
          // Retrieve layout for screen
          const layoutData = await adminApi.getLayoutForScreen(accessToken || "", showData.screen_id);
          setLayout(layoutData);
          
          if (!layoutData) {
            setError("No published seating plan available for this screen room.");
            setLoading(false);
            return;
          }

          // Fetch dynamic pricing calculations from backend for category tiers
          const categories = ["Normal", "Executive", "Premium"];
          const priceMap: Record<string, number> = { Normal: 150, Executive: 220, Premium: 300 };
          
          await Promise.all(
            categories.map(async (cat) => {
              try {
                // Public pricing calculation route
                const priceRes = await apiClient.get<PriceCalculation>("/api/bookings/price-calculation", {
                  query: { show_id: Number(showId), category: cat }
                });
                if (priceRes && priceRes.final_price) {
                  priceMap[cat] = priceRes.final_price;
                }
              } catch (e) {
                console.error("Pricing fetch failed for category:", cat, e);
              }
            })
          );
          setPrices(priceMap);
        }

        // Retrieve initial status
        const statusRes = await reservationsApi.seatStatus(Number(showId));
        if (statusRes) {
          const data = statusRes as unknown as { booked: string[]; reserved: string[] };
          setBookedSeats(data.booked || []);
          setReservedSeats(data.reserved || []);
        }

        // Recovery check for active reservation from local storage
        const savedGroup = localStorage.getItem(`cinema_plus_active_reservation_${showId}`);
        if (savedGroup) {
          const parsed = JSON.parse(savedGroup) as ReservationGroup;
          const expiryTime = new Date(parsed.expires_at).getTime();
          const nowTime = Date.now();
          if (expiryTime > nowTime) {
            setRecoveredReservation(parsed);
            setSelectedSeats(parsed.reserved_seats.map(s => s.seat_id));
          } else {
            // Cleanup expired
            localStorage.removeItem(`cinema_plus_active_reservation_${showId}`);
          }
        }

        setError(null);
      } catch (err) {
        console.error("Error loading show seat selection:", err);
        setError("Failed to load show seating configuration details.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [showId, accessToken]);

  // Polling hook every 5 seconds
  useEffect(() => {
    if (loading || error) return;
    const interval = setInterval(fetchSeatStatuses, 5000);
    return () => clearInterval(interval);
  }, [fetchSeatStatuses, loading, error]);

  // Handle seat selection toggling
  const handleSeatSelect = (seatCode: string) => {
    // If seat is already booked or temporarily reserved by someone else
    if (bookedSeats.includes(seatCode) || (reservedSeats.includes(seatCode) && !selectedSeats.includes(seatCode))) {
      return;
    }

    setSelectedSeats((prev) => {
      if (prev.includes(seatCode)) {
        return prev.filter((code) => code !== seatCode);
      }
      return [...prev, seatCode];
    });
  };

  // Get seat price helper
  const getSeatPrice = useCallback((seat: SeatDefinition) => {
    return prices[seat.category] || 150;
  }, [prices]);

  // Subtotal calculation
  const subtotal = useMemo(() => {
    if (!layout) return 0;
    return selectedSeats.reduce((acc, code) => {
      const seat = layout.seats.find((s) => s.seat_code === code);
      if (seat) {
        return acc + getSeatPrice(seat);
      }
      return acc;
    }, 0);
  }, [selectedSeats, layout, getSeatPrice]);

  // Initiate reservation hold
  const handleProceed = async () => {
    if (!accessToken || !isAuthenticated) {
      router.push(`/login?redirect=/book/${showId}`);
      return;
    }
    if (selectedSeats.length === 0) return;

    setSaving(true);
    setError(null);
    try {
      // Call create reservation hold group
      const res = await reservationsApi.create(accessToken, {
        seats: selectedSeats,
        show_id: Number(showId),
      });

      if (res && res.id) {
        // Save in local storage for browser refresh recovery
        localStorage.setItem(`cinema_plus_active_reservation_${showId}`, JSON.stringify(res));
        // Redirect to checkout
        router.push(`/checkout/${res.id}`);
      } else {
        setError("Failed to create temporary seat lock session.");
      }
    } catch (err) {
      const errorObj = err as { status?: number; message?: string };
      // Capture conflicts (seat already reserved/booked)
      if (errorObj?.status === 409) {
        setError("One or more selected seats have already been locked by another customer. Please select different seats.");
        fetchSeatStatuses();
      } else {
        setError(errorObj?.message || "An unexpected error occurred while locking your seats.");
      }
    } finally {
      setSaving(false);
    }
  };

  // Release recovered reservation to start fresh
  const handleCancelRecovered = async () => {
    if (!accessToken || !recoveredReservation) return;
    try {
      await reservationsApi.cancel(accessToken, recoveredReservation.id);
      localStorage.removeItem(`cinema_plus_active_reservation_${showId}`);
      setRecoveredReservation(null);
      setSelectedSeats([]);
      fetchSeatStatuses();
    } catch (err) {
      console.error("Failed to cancel recovered hold:", err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  if (error && !layout) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex flex-col items-center justify-center gap-4 text-zinc-300">
        <AlertTriangle className="h-10 w-10 text-red-500" />
        <p className="max-w-md text-center text-sm">{error}</p>
        <button onClick={() => router.back()} className="px-4 py-2 bg-zinc-800 text-zinc-300 rounded-lg text-xs font-bold">
          Go Back
        </button>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[hsl(222,84%,2.5%)] text-zinc-100 pb-24">
      {/* Stepper Header */}
      <div className="border-b border-white/[0.04] bg-[hsl(222,84%,3.5%)]">
        <div className="max-w-5xl mx-auto px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => router.back()}
              className="rounded-lg border border-white/[0.08] p-2 text-zinc-400 hover:text-zinc-200"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <div>
              <h1 className="text-base font-bold text-white flex items-center gap-2">
                {show?.movie?.title}
              </h1>
              <p className="text-[11px] text-zinc-500 font-semibold">
                Showtime: {show?.start_time.slice(0, 5)} • {show?.date}
              </p>
            </div>
          </div>
          <BookingStepper currentStep={2} />
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 mt-8 space-y-6">
        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400 flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Recovered Reservation Alert Banner */}
        {recoveredReservation && (
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex gap-2">
              <Clock className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
              <div>
                <span className="text-sm font-bold text-amber-400 block">Active Seating Lock Recovered!</span>
                <span className="text-xs text-zinc-400">
                  You have an active lock on seats: {selectedSeats.join(", ")}. Resume checkout before expiry.
                </span>
              </div>
            </div>
            <div className="flex gap-2 shrink-0">
              <button 
                onClick={handleCancelRecovered}
                className="px-3.5 py-1.5 rounded-lg border border-white/[0.08] hover:bg-white/[0.04] text-xs font-bold text-zinc-400"
              >
                Release Lock
              </button>
              <button 
                onClick={() => router.push(`/checkout/${recoveredReservation.id}`)}
                className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-xs font-bold text-slate-950 shadow-lg shadow-amber-500/10"
              >
                Resume Checkout
              </button>
            </div>
          </div>
        )}

        {/* 2D Canvas Seat Map */}
        {layout && (
          <SeatMap
            seats={layout.seats}
            rows={layout.rows}
            cols={layout.cols}
            bookedSeats={bookedSeats}
            reservedSeats={reservedSeats}
            selectedSeats={selectedSeats}
            onSeatSelect={handleSeatSelect}
            pricingBySeat={getSeatPrice}
          />
        )}
      </div>

      {/* Floating Action Reservation Control Bar */}
      {selectedSeats.length > 0 && !recoveredReservation && (
        <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-white/[0.06] bg-[hsl(222,84%,5.5%)]/95 backdrop-blur-md py-4 shadow-2xl">
          <div className="max-w-5xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex flex-col text-left">
              <span className="text-[10px] uppercase tracking-wider font-extrabold text-zinc-500">
                Selected seats ({selectedSeats.length})
              </span>
              <span className="text-sm font-bold text-white truncate max-w-[280px]">
                {selectedSeats.sort().join(", ")}
              </span>
            </div>

            <div className="flex items-center gap-6">
              <div className="flex flex-col text-right">
                <span className="text-[10px] uppercase tracking-wider font-extrabold text-zinc-500">
                  Estimated Subtotal
                </span>
                <span className="text-lg font-extrabold text-emerald-400">
                  ₹{subtotal}
                </span>
              </div>

              <button
                onClick={handleProceed}
                disabled={saving}
                className="px-6 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-xs font-bold text-white shadow-lg shadow-red-600/20 disabled:opacity-50 transition-all hover:scale-105 active:scale-95"
              >
                {saving ? "Locking Seats..." : "Confirm & Proceed"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
