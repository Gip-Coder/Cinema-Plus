"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  AlertTriangle,
  Clock,
  CreditCard,
  Smartphone,
  Wallet,
  Building,
  User,
  ShieldCheck,
  CheckCircle,
  XCircle,
  HelpCircle
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { scheduleApi } from "@/lib/api/schedule";
import * as adminApi from "@/lib/api/admin";
import { reservationsApi } from "@/lib/api/reservations";
import { apiClient } from "@/lib/api/client";
import BookingStepper from "@/components/booking/stepper";
import type { Show, ReservationGroup, TheatreLayout, PriceCalculation } from "@/types/domain";

type PaymentMethod = "card" | "upi" | "netbanking" | "wallet" | "cash";
type SimStatus = "idle" | "verifying" | "cred_check" | "bank_wait" | "confirming" | "success" | "failure";

export default function CheckoutPage() {
  const { groupId } = useParams();
  const router = useRouter();
  const { accessToken } = useAuth();

  const [group, setGroup] = useState<ReservationGroup | null>(null);
  const [show, setShow] = useState<Show | null>(null);
  const [layout, setLayout] = useState<TheatreLayout | null>(null);
  const [prices, setPrices] = useState<Record<string, number>>({ Normal: 150, Executive: 220, Premium: 300 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Timer state
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes default (seconds)

  // Payment Sim States
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>("card");
  const [simStatus, setSimStatus] = useState<SimStatus>("idle");
  const [simStageText, setSimStageText] = useState("");
  const [cardName, setCardName] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [cardExpiry, setCardExpiry] = useState("");
  const [cardCVV, setCardCVV] = useState("");
  const [upiId, setUpiId] = useState("");


  // Fetch group data
  useEffect(() => {
    async function loadCheckoutData() {
      if (!groupId || !accessToken) return;
      setLoading(true);
      try {
        const groupData = await reservationsApi.detail(accessToken, Number(groupId));
        setGroup(groupData);

        if (groupData) {
          const showData = await scheduleApi.show(groupData.show_id);
          setShow(showData);

          if (showData) {
            const layoutData = await adminApi.getLayoutForScreen(accessToken, showData.screen_id);
            setLayout(layoutData);

            // Fetch dynamic pricing
            const categories = ["Normal", "Executive", "Premium"];
            const priceMap: Record<string, number> = { Normal: 150, Executive: 220, Premium: 300 };
            await Promise.all(
              categories.map(async (cat) => {
                try {
                  const priceRes = await apiClient.get<PriceCalculation>("/api/bookings/price-calculation", {
                    query: { show_id: showData.id, category: cat }
                  });
                  if (priceRes && priceRes.final_price) {
                    priceMap[cat] = priceRes.final_price;
                  }
                } catch {}
              })
            );
            setPrices(priceMap);
          }

          // Initial timer calculation
          const expiryTime = new Date(groupData.expires_at).getTime();
          const diff = Math.max(0, Math.floor((expiryTime - Date.now()) / 1000));
          setTimeLeft(diff);

          if (diff <= 0) {
            setError("This reservation group session has already expired.");
          }
        }
      } catch (err) {
        console.error("Failed to load checkout details:", err);
        setError("Failed to load reservation checkout details.");
      } finally {
        setLoading(false);
      }
    }

    loadCheckoutData();
  }, [groupId, accessToken]);

  // Tick countdown timer
  useEffect(() => {
    if (loading || error || simStatus === "success" || !group) return;

    const interval = setInterval(() => {
      const expiryTime = new Date(group.expires_at).getTime();
      const diff = Math.max(0, Math.floor((expiryTime - Date.now()) / 1000));
      setTimeLeft(diff);

      if (diff <= 0) {
        clearInterval(interval);
        setError("Your reservation session has expired. The seats have been released back.");
        localStorage.removeItem(`cinema_plus_active_reservation_${group.show_id}`);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [group, loading, error, simStatus]);

  // Subtotal and Fee Breakdown
  const fees = useMemo(() => {
    if (!group || !layout) return { subtotal: 0, gst: 0, convenience: 0, total: 0 };
    
    const subtotal = group.reserved_seats.reduce((acc, rs) => {
      const seat = layout.seats.find((s) => s.seat_code === rs.seat_id);
      if (seat) {
        return acc + (prices[seat.category] || 150);
      }
      return acc + 150;
    }, 0);

    const convenience = group.reserved_seats.length * 30; // ₹30 per seat
    const gst = Math.round(subtotal * 0.18); // 18% GST
    const total = subtotal + gst + convenience;

    return { subtotal, gst, convenience, total };
  }, [group, layout, prices]);

  // Run Payment Simulator Flow
  const runSimulator = async () => {
    if (!accessToken || !group) return;
    
    // Set simulator workflow status
    setSimStatus("verifying");
    setSimStageText("Contacting safe payment gateway...");
    
    const stages: { status: SimStatus; text: string; delay: number }[] = [
      { status: "cred_check", text: "Verifying secure payment credentials...", delay: 1500 },
      { status: "bank_wait", text: "Waiting for authorization from issuing bank...", delay: 1500 },
      { status: "confirming", text: "Verifying seat hold state and locking tickets...", delay: 1500 },
    ];

    for (const stage of stages) {
      await new Promise(resolve => setTimeout(resolve, stage.delay));
      setSimStatus(stage.status);
      setSimStageText(stage.text);
    }

    // Try backend booking confirmation
    try {
      const bookingRes = await reservationsApi.confirm(accessToken, group.id);
      if (bookingRes && bookingRes.id) {
        setSimStatus("success");
        // Clear recovery localStorage
        localStorage.removeItem(`cinema_plus_active_reservation_${group.show_id}`);
        // Wait and redirect
        setTimeout(() => {
          router.push(`/confirmation/${bookingRes.id}`);
        }, 1500);
      } else {
        setSimStatus("failure");
        setSimStageText("Failed to confirm booking. Seat release requested.");
      }
    } catch (err) {
      console.error("Payment authorization error:", err);
      setSimStatus("failure");
      setSimStageText("Bank transaction rejected. Double booking prevention locked.");
    }
  };

  const handleCancelPayment = async () => {
    if (!accessToken || !group) return;
    try {
      await reservationsApi.cancel(accessToken, group.id);
      localStorage.removeItem(`cinema_plus_active_reservation_${group.show_id}`);
      router.push(`/book/${group.show_id}`);
    } catch (err) {
      console.error("Failed to cancel reservation hold:", err);
    }
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // Percent progress remaining (max 600s / 10m)
  const timerPercent = Math.min(100, (timeLeft / 600) * 100);

  if (loading) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  if (error || timeLeft <= 0) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex flex-col items-center justify-center gap-4 text-zinc-300">
        <AlertTriangle className="h-10 w-10 text-red-500" />
        <p className="max-w-md text-center text-sm">{error || "Your reservation time expired."}</p>
        <button 
          onClick={() => router.push(group ? `/book/${group.show_id}` : "/")} 
          className="px-4 py-2 bg-red-600 text-white rounded-lg text-xs font-bold"
        >
          Return to Seat Selection
        </button>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[hsl(222,84%,2.5%)] text-zinc-100 pb-20">
      {/* Stepper Header */}
      <div className="border-b border-white/[0.04] bg-[hsl(222,84%,3.5%)]">
        <div className="max-w-5xl mx-auto px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <h1 className="text-base font-bold text-white flex items-center gap-2">
            Confirm Checkout Booking
          </h1>
          <BookingStepper currentStep={simStatus === "idle" ? 3 : 4} />
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 mt-8 grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left Column: Review Seating & Payment Options */}
        <div className="md:col-span-2 space-y-6">
          {/* Timer Card */}
          <div className="rounded-2xl border border-white/[0.06] bg-[hsl(222,84%,4%)] p-5 space-y-3 shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-zinc-400 flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-red-500" />
                Remaining Seat Release Time:
              </span>
              <span className={`text-base font-extrabold ${timeLeft < 120 ? "text-red-500 animate-pulse" : "text-amber-400"}`}>
                {formatTimer(timeLeft)}
              </span>
            </div>
            {/* Progress bar */}
            <div className="h-1.5 w-full bg-white/[0.04] rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-1000 ${timeLeft < 120 ? "bg-red-500" : "bg-red-600"}`}
                style={{ width: `${timerPercent}%` }}
              />
            </div>
          </div>

          {/* Payment Methods */}
          {simStatus === "idle" && (
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 space-y-6">
              <h2 className="text-sm font-bold text-white border-b border-white/[0.04] pb-3">Choose Payment Method</h2>
              
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {[
                  { id: "card", label: "Credit/Debit", icon: CreditCard },
                  { id: "upi", label: "UPI Apps", icon: Smartphone },
                  { id: "netbanking", label: "NetBanking", icon: Building },
                  { id: "wallet", label: "Wallets", icon: Wallet },
                  { id: "cash", label: "Cash Counter", icon: User },
                ].map((item) => {
                  const Icon = item.icon;
                  const isSel = selectedMethod === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setSelectedMethod(item.id as PaymentMethod)}
                      className={`
                        p-3 rounded-xl border flex flex-col items-center justify-center gap-2 text-center transition-all
                        ${isSel 
                          ? "bg-red-600/10 border-red-500 text-red-400 scale-105" 
                          : "bg-white/[0.01] border-white/[0.06] text-zinc-400 hover:border-white/[0.12] hover:text-zinc-200"
                        }
                      `}
                    >
                      <Icon className="h-5 w-5" />
                      <span className="text-[10px] font-bold">{item.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Form Input fields according to payment method */}
              <div className="bg-white/[0.01] border border-white/[0.04] p-5 rounded-xl space-y-4">
                {selectedMethod === "card" && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] text-zinc-500 uppercase font-extrabold mb-1">Cardholder Name</label>
                        <input
                          type="text"
                          placeholder="John Doe"
                          value={cardName}
                          onChange={(e) => setCardName(e.target.value)}
                          className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-zinc-300 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] text-zinc-500 uppercase font-extrabold mb-1">Card Number</label>
                        <input
                          type="text"
                          placeholder="4000 1234 5678 9010"
                          value={cardNumber}
                          onChange={(e) => setCardNumber(e.target.value)}
                          className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-zinc-300 outline-none"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] text-zinc-500 uppercase font-extrabold mb-1">Expiry Date</label>
                        <input
                          type="text"
                          placeholder="MM/YY"
                          value={cardExpiry}
                          onChange={(e) => setCardExpiry(e.target.value)}
                          className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-zinc-300 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] text-zinc-500 uppercase font-extrabold mb-1">CVV</label>
                        <input
                          type="password"
                          placeholder="***"
                          value={cardCVV}
                          onChange={(e) => setCardCVV(e.target.value)}
                          className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-zinc-300 outline-none"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {selectedMethod === "upi" && (
                  <div>
                    <label className="block text-[10px] text-zinc-500 uppercase font-extrabold mb-1">UPI Address (VPA)</label>
                    <input
                      type="text"
                      placeholder="username@okaxis"
                      value={upiId}
                      onChange={(e) => setUpiId(e.target.value)}
                      className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-zinc-300 outline-none"
                    />
                  </div>
                )}

                {selectedMethod === "netbanking" && (
                  <div className="text-xs text-zinc-400 flex items-center gap-2">
                    <HelpCircle className="h-4 w-4 text-zinc-500" />
                    You will be redirected to your bank portal securely upon continuing.
                  </div>
                )}

                {selectedMethod === "wallet" && (
                  <div className="text-xs text-zinc-400 flex items-center gap-2">
                    <HelpCircle className="h-4 w-4 text-zinc-500" />
                    Simulates secure linking of electronic mobile wallets.
                  </div>
                )}

                {selectedMethod === "cash" && (
                  <div className="text-xs text-zinc-400 flex items-center gap-2">
                    <HelpCircle className="h-4 w-4 text-zinc-500" />
                    Assumes ticket booking lock directly from the box office desk.
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between border-t border-white/[0.04] pt-4">
                <button
                  onClick={handleCancelPayment}
                  className="px-4 py-2 border border-white/[0.08] hover:bg-white/[0.04] text-xs font-bold text-zinc-400 rounded-lg"
                >
                  Cancel & Change Seats
                </button>
                <button
                  onClick={runSimulator}
                  className="px-6 py-2.5 bg-red-600 hover:bg-red-700 text-xs font-bold text-white shadow-lg shadow-red-600/20 rounded-lg flex items-center gap-2"
                >
                  <ShieldCheck className="h-4 w-4" />
                  Authorize simulated payment
                </button>
              </div>
            </div>
          )}

          {/* Payment processing stages UI */}
          {simStatus !== "idle" && (
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8 text-center flex flex-col items-center justify-center min-h-[300px] space-y-6">
              {simStatus !== "success" && simStatus !== "failure" ? (
                <>
                  <div className="h-10 w-10 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
                  <div className="space-y-2">
                    <h3 className="font-bold text-white text-sm">Payment Authorization Processing</h3>
                    <p className="text-xs text-zinc-500 max-w-sm">{simStageText}</p>
                  </div>
                </>
              ) : simStatus === "success" ? (
                <>
                  <CheckCircle className="h-12 w-12 text-emerald-400" />
                  <div className="space-y-2">
                    <h3 className="font-bold text-emerald-400 text-sm">Simulated Payment Approved!</h3>
                    <p className="text-xs text-zinc-500">Allocating tickets & issuing PDF receipt...</p>
                  </div>
                </>
              ) : (
                <>
                  <XCircle className="h-12 w-12 text-red-500" />
                  <div className="space-y-2">
                    <h3 className="font-bold text-red-400 text-sm">Simulated Authorization Failed</h3>
                    <p className="text-xs text-zinc-500">{simStageText}</p>
                  </div>
                  <button
                    onClick={() => setSimStatus("idle")}
                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-xs font-bold text-zinc-300 rounded-lg"
                  >
                    Retry Payment
                  </button>
                </>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Checkout Pricing Summary Card */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] overflow-hidden shadow-lg flex flex-col">
            {/* Spotlight Header Banner */}
            <div className="bg-red-600/10 border-b border-white/[0.04] p-5 flex gap-4">
              {show?.movie?.poster_url && (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={show.movie.poster_url} alt={show.movie.title} className="w-12 h-16 object-cover rounded-lg border border-white/[0.08]" />
              )}
              <div className="space-y-1 text-left">
                <span className="text-[9px] uppercase tracking-wider font-extrabold text-red-400">Spotlight Movie</span>
                <h2 className="font-bold text-sm text-zinc-100 line-clamp-1">{show?.movie?.title}</h2>
                <p className="text-[10px] text-zinc-500 font-semibold">{show?.movie?.genre}</p>
              </div>
            </div>

            {/* Summary Details list */}
            <div className="p-5 space-y-4 text-xs border-b border-white/[0.04]">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Show Date</span>
                  <span className="font-bold text-zinc-200">{show?.date}</span>
                </div>
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Showtime</span>
                  <span className="font-bold text-zinc-200">{show?.start_time.slice(0, 5)}</span>
                </div>
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Auditorium</span>
                  <span className="font-bold text-zinc-200">{show?.screen?.name}</span>
                </div>
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Selected Seats</span>
                  <span className="font-extrabold text-zinc-200">{group?.reserved_seats.map(s => s.seat_id).sort().join(", ")}</span>
                </div>
              </div>
            </div>

            {/* Price Calculations */}
            <div className="p-5 space-y-3 border-b border-white/[0.04] bg-white/[0.01]">
              <div className="flex items-center justify-between text-zinc-400 text-xs">
                <span>Subtotal ({group?.reserved_seats.length} tickets)</span>
                <span className="font-semibold text-zinc-200">₹{fees.subtotal}</span>
              </div>
              <div className="flex items-center justify-between text-zinc-400 text-xs">
                <span>Convenience Fee</span>
                <span className="font-semibold text-zinc-200">₹{fees.convenience}</span>
              </div>
              <div className="flex items-center justify-between text-zinc-400 text-xs">
                <span>Taxes (18% GST)</span>
                <span className="font-semibold text-zinc-200">₹{fees.gst}</span>
              </div>
            </div>

            {/* Grand Total */}
            <div className="p-5 flex items-center justify-between">
              <span className="text-xs font-bold text-zinc-300">Grand Total Payable</span>
              <span className="text-xl font-extrabold text-emerald-400">₹{fees.total}</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
