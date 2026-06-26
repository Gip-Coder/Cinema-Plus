"use client";

import React, { useMemo, useState, useRef } from "react";
import { 
  Plus, 
  Minus, 
  RotateCcw, 
  Sparkles,
  Accessibility,
  Eye
} from "lucide-react";
import type { SeatDefinition } from "@/types/domain";

interface SeatMapProps {
  seats: SeatDefinition[];
  rows: number;
  cols: number;
  bookedSeats: string[];      // seat_codes
  reservedSeats: string[];    // seat_codes
  selectedSeats: string[];    // seat_codes
  onSeatSelect: (seatCode: string) => void;
  pricingBySeat: (seat: SeatDefinition) => number;
}



export default function SeatMap({
  seats,
  rows,
  cols,
  bookedSeats,
  reservedSeats,
  selectedSeats,
  onSeatSelect,
  pricingBySeat,
}: SeatMapProps) {
  const [scale, setScale] = useState(0.85);
  const [pan, setPan] = useState({ x: 40, y: 30 });
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0 });

  // Hover seat info state
  const [hoveredSeat, setHoveredSeat] = useState<SeatDefinition | null>(null);
  const [hoverPos, setHoverPos] = useState({ x: 0, y: 0 });

  // Recommendations state
  const [recommendQty, setRecommendQty] = useState(2);

  const seatSize = 34;
  const gapSize = 12;

  const canvasWidth = useMemo(() => cols * (seatSize + gapSize) + 120, [cols]);
  const canvasHeight = useMemo(() => rows * (seatSize + gapSize) + 200, [rows]);

  // Determine viewing quality estimate
  const getViewQuality = (y: number, x: number) => {
    const centerCol = cols / 2;
    const colDistance = Math.abs(x - centerCol);
    
    if (y <= 1) {
      return { label: "Fair (Near Screen)", color: "text-amber-400", description: "Close view of screen, neck angle required." };
    }
    if (colDistance > cols * 0.35) {
      return { label: "Good (Side Angle)", color: "text-blue-400", description: "Side view perspective, clear line of sight." };
    }
    if (y >= 3 && y <= 6) {
      return { label: "Excellent (Prime Center)", color: "text-emerald-400", description: "Ideal viewing sweet spot and acoustic focus." };
    }
    return { label: "Great (Panoramic)", color: "text-cyan-400", description: "Wide field of view from the back rows." };
  };

  // Get seat colors according to booking state and categories
  const getSeatStyles = (seat: SeatDefinition) => {
    if (!seat.is_active || seat.seat_type === "blocked") {
      return "bg-zinc-950 border-zinc-900 text-zinc-800 cursor-not-allowed opacity-20 pointer-events-none";
    }
    if (seat.seat_type === "maintenance") {
      return "bg-amber-600/30 border-amber-600/60 text-amber-500 cursor-not-allowed";
    }
    if (seat.seat_type === "emergency") {
      return "bg-red-700/20 border-red-700/60 text-red-500 cursor-not-allowed";
    }
    
    const code = seat.seat_code;
    const isBooked = bookedSeats.includes(code);
    const isReserved = reservedSeats.includes(code);
    const isSelected = selectedSeats.includes(code);

    if (isBooked) {
      return "bg-zinc-800 border-zinc-700 text-zinc-500 cursor-not-allowed";
    }
    if (isReserved) {
      return "bg-amber-500/20 border-amber-500/60 text-amber-400 cursor-not-allowed";
    }
    if (isSelected) {
      return "bg-red-600 border-white text-white shadow-lg ring-2 ring-red-500/50 scale-105";
    }

    // Available seat styling by category
    if (seat.seat_type === "wheelchair") {
      return "bg-cyan-950/40 border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/20 hover:scale-105";
    }
    if (seat.seat_type === "couple") {
      return "bg-pink-950/40 border-pink-500/50 text-pink-400 hover:bg-pink-500/20 hover:scale-105";
    }

    switch (seat.category) {
      case "Premium":
        return "bg-rose-950/40 border-rose-500/50 text-rose-400 hover:bg-rose-500/20 hover:scale-105";
      case "Executive":
        return "bg-amber-950/40 border-amber-500/50 text-amber-400 hover:bg-amber-500/20 hover:scale-105";
      default:
        return "bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-800 hover:scale-105";
    }
  };

  // Panning controls
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 1 || e.button === 2 || e.altKey) {
      setIsPanning(true);
      panStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
      e.preventDefault();
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isPanning) {
      setPan({
        x: e.clientX - panStart.current.x,
        y: e.clientY - panStart.current.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const zoomIn = () => setScale((s) => Math.min(s + 0.1, 2.0));
  const zoomOut = () => setScale((s) => Math.max(s - 0.1, 0.4));
  const resetView = () => {
    setScale(0.85);
    setPan({ x: 40, y: 30 });
  };

  // Intelligent Seat Recommendation Engine
  const recommendSeats = () => {
    // Filter out taken or inactive seats
    const available = seats.filter(
      (s) =>
        s.is_active &&
        s.seat_type !== "blocked" &&
        s.seat_type !== "maintenance" &&
        s.seat_type !== "emergency" &&
        !bookedSeats.includes(s.seat_code) &&
        !reservedSeats.includes(s.seat_code)
    );

    if (available.length === 0) return;

    // Group seats by row
    const rowsMap: Record<number, SeatDefinition[]> = {};
    available.forEach((s) => {
      if (!rowsMap[s.position_y]) rowsMap[s.position_y] = [];
      rowsMap[s.position_y].push(s);
    });

    // Score rows: prefer rows y = 3,4,5,6 (center prime)
    let bestSelection: SeatDefinition[] = [];
    let bestScore = -1000;

    Object.entries(rowsMap).forEach(([yStr, rowSeats]) => {
      const y = Number(yStr);
      // Sort row seats by col X coordinate ascending
      rowSeats.sort((a, b) => a.position_x - b.position_x);

      // Find all contiguous groups of recommendQty
      for (let i = 0; i <= rowSeats.length - recommendQty; i++) {
        const candidateGroup = rowSeats.slice(i, i + recommendQty);
        
        // Verify they are contiguous on X layout positions
        let isContiguous = true;
        for (let j = 0; j < candidateGroup.length - 1; j++) {
          if (candidateGroup[j + 1].position_x !== candidateGroup[j].position_x + 1) {
            isContiguous = false;
            break;
          }
        }

        if (isContiguous) {
          // Calculate score based on center proximity & category
          const avgX = candidateGroup.reduce((acc, s) => acc + s.position_x, 0) / recommendQty;
          const distFromCenter = Math.abs(avgX - cols / 2);
          
          let rowMultiplier = 10;
          if (y >= 3 && y <= 6) rowMultiplier = 50; // sweet spot
          else if (y >= 7) rowMultiplier = 35;      // rear panoramic
          else rowMultiplier = 20;

          // score formula
          const score = rowMultiplier * 10 - distFromCenter * 5;
          if (score > bestScore) {
            bestScore = score;
            bestSelection = candidateGroup;
          }
        }
      }
    });

    // If no contiguous seats found, fallback to scoring individual best seats
    if (bestSelection.length === 0) {
      // Sort available seats by view quality score
      const sorted = [...available].sort((a, b) => {
        const scoreA = (a.position_y >= 3 && a.position_y <= 6 ? 100 : 50) - Math.abs(a.position_x - cols / 2);
        const scoreB = (b.position_y >= 3 && b.position_y <= 6 ? 100 : 50) - Math.abs(b.position_x - cols / 2);
        return scoreB - scoreA;
      });
      bestSelection = sorted.slice(0, recommendQty);
    }

    // Select the recommended seats
    bestSelection.forEach((s) => {
      if (!selectedSeats.includes(s.seat_code)) {
        onSeatSelect(s.seat_code);
      }
    });
  };

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Smart recommendation bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-white/[0.06] bg-[hsl(222,84%,4.9%)] shadow-md">
        <div className="flex items-center gap-2 text-zinc-300 text-xs">
          <Sparkles className="h-4 w-4 text-amber-400" />
          <span className="font-semibold">Seat Recommendations:</span>
          <span>Suggest best seating groups for:</span>
          <select 
            value={recommendQty}
            onChange={(e) => setRecommendQty(Number(e.target.value))}
            className="rounded border border-white/[0.1] bg-white/[0.05] text-zinc-200 outline-none px-2 py-0.5 text-xs focus:border-red-500"
          >
            <option value={1}>1 Guest</option>
            <option value={2}>2 Guests</option>
            <option value={3}>3 Guests</option>
            <option value={4}>4 Guests</option>
          </select>
        </div>
        <button
          onClick={recommendSeats}
          className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg bg-amber-500 text-xs font-bold text-slate-950 hover:bg-amber-400 transition-all hover:scale-105 active:scale-95"
        >
          Recommend Seats
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-5">
        {/* Map Workspace */}
        <div className="flex-1 relative border border-white/[0.06] rounded-xl bg-[hsl(222,84%,2%)] overflow-hidden h-[450px] select-none shadow-inner">
          {/* Zoom pan controls */}
          <div className="absolute bottom-4 left-4 z-20 flex gap-1 p-1 rounded-lg border border-white/[0.08] bg-[hsl(222,84%,5.5%)]/95 shadow-md">
            <button onClick={zoomIn} title="Zoom In" className="p-1.5 rounded text-zinc-400 hover:bg-white/5 hover:text-zinc-100"><Plus className="h-4 w-4" /></button>
            <button onClick={zoomOut} title="Zoom Out" className="p-1.5 rounded text-zinc-400 hover:bg-white/5 hover:text-zinc-100"><Minus className="h-4 w-4" /></button>
            <button onClick={resetView} title="Reset View" className="p-1.5 rounded text-zinc-400 hover:bg-white/5 hover:text-zinc-100"><RotateCcw className="h-4 w-4" /></button>
          </div>

          {/* Minimap Viewport Indicator */}
          <div className="absolute top-4 right-4 z-20 p-2 rounded-xl border border-white/[0.06] bg-[hsl(222,84%,4.9%)]/90 backdrop-blur-sm w-36 shadow-lg">
            <span className="text-[9px] uppercase tracking-wider font-extrabold text-zinc-500 block mb-1">Layout Minimap</span>
            <div className="h-20 bg-black/40 rounded border border-white/[0.04] relative overflow-hidden">
              {/* Seating outline representation */}
              <div className="absolute inset-2 grid gap-[1px]" style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
                {seats.map((s, idx) => (
                  <div 
                    key={idx} 
                    className={`h-[3px] rounded-[1px] ${
                      bookedSeats.includes(s.seat_code) 
                        ? "bg-zinc-700" 
                        : selectedSeats.includes(s.seat_code) 
                        ? "bg-red-500" 
                        : "bg-zinc-500/20"
                    }`} 
                  />
                ))}
              </div>
              {/* Viewport Box */}
              <div 
                className="absolute border border-red-500/60 bg-red-500/5 rounded pointer-events-none transition-all"
                style={{
                  left: `${Math.max(0, Math.min(60, 45 - pan.x * 0.05))}px`,
                  top: `${Math.max(0, Math.min(40, 30 - pan.y * 0.05))}px`,
                  width: `${Math.min(100, 120 / scale * 0.2)}px`,
                  height: `${Math.min(60, 80 / scale * 0.2)}px`,
                }}
              />
            </div>
          </div>

          {/* Seating Canvas Wrapper */}
          <div
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            className={`w-full h-full relative overflow-hidden outline-none ${
              isPanning ? "cursor-grabbing" : "cursor-grab"
            }`}
          >
            <div
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
                transformOrigin: "0 0",
              }}
              className="absolute transition-transform duration-75 ease-out"
            >
              {/* Screen graphic */}
              <div className="absolute top-8 left-1/2 -translate-x-1/2 flex flex-col items-center">
                <div className="w-[280px] h-[5px] rounded-full bg-red-500/40 shadow-[0_0_12px_rgba(239,68,68,0.3)]" />
                <span className="text-[9px] text-zinc-600 mt-2 uppercase tracking-widest font-extrabold">Cinema Screen Front</span>
              </div>

              {/* Seating Grid */}
              <div
                style={{ width: `${canvasWidth}px`, height: `${canvasHeight}px` }}
                className="relative"
              >
                {seats.map((seat) => {
                  if (!seat.is_active || seat.seat_type === "blocked") return null;
                  
                  const x = seat.position_x * (seatSize + gapSize) + 50;
                  const y = seat.position_y * (seatSize + gapSize) + 120;

                  return (
                    <button
                      key={seat.seat_code}
                      onClick={() => onSeatSelect(seat.seat_code)}
                      onMouseEnter={() => {
                        setHoveredSeat(seat);
                        setHoverPos({ x: x + seatSize + 10, y: y - 20 });
                      }}
                      onMouseLeave={() => setHoveredSeat(null)}
                      style={{
                        position: "absolute",
                        left: `${x}px`,
                        top: `${y}px`,
                        width: `${seatSize}px`,
                        height: `${seatSize}px`,
                      }}
                      className={`
                        rounded-lg border-2 flex items-center justify-center text-[10px] font-extrabold select-none cursor-pointer transition-all
                        ${getSeatStyles(seat)}
                      `}
                    >
                      {seat.seat_code}
                    </button>
                  );
                })}

                {/* Seating Hover Info Card */}
                {hoveredSeat && (
                  <div
                    style={{
                      position: "absolute",
                      left: `${hoverPos.x}px`,
                      top: `${hoverPos.y}px`,
                    }}
                    className="z-30 w-52 p-3.5 rounded-xl border border-white/[0.08] bg-[hsl(222,84%,5.5%)]/95 backdrop-blur-md shadow-2xl flex flex-col gap-2 pointer-events-none text-left"
                  >
                    <div className="flex items-center justify-between border-b border-white/[0.04] pb-1.5">
                      <span className="text-xs font-bold text-zinc-200">Seat {hoveredSeat.seat_code}</span>
                      <span className="text-[10px] uppercase font-extrabold px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300">
                        {hoveredSeat.category}
                      </span>
                    </div>

                    <div className="space-y-1.5 text-[11px] text-zinc-400">
                      <div className="flex items-center justify-between">
                        <span>Seat Type:</span>
                        <span className="capitalize font-semibold text-zinc-300">{hoveredSeat.seat_type}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Price:</span>
                        <span className="font-extrabold text-emerald-400">₹{pricingBySeat(hoveredSeat)}</span>
                      </div>
                      <div className="flex items-start gap-1 border-t border-white/[0.04] pt-1.5">
                        <Eye className="h-3.5 w-3.5 text-zinc-500 shrink-0 mt-0.5" />
                        <div>
                          <div className={`font-bold ${getViewQuality(hoveredSeat.position_y, hoveredSeat.position_x).color}`}>
                            {getViewQuality(hoveredSeat.position_y, hoveredSeat.position_x).label}
                          </div>
                          <p className="text-[9px] text-zinc-500 leading-normal mt-0.5">
                            {getViewQuality(hoveredSeat.position_y, hoveredSeat.position_x).description}
                          </p>
                        </div>
                      </div>
                      {hoveredSeat.seat_type === "wheelchair" && (
                        <div className="flex items-center gap-1.5 rounded bg-cyan-950/20 text-cyan-400 p-1 mt-1">
                          <Accessibility className="h-3.5 w-3.5" />
                          <span>Wheelchair Accessible</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Legend Sidebar Panel */}
        <div className="w-full lg:w-60 flex flex-col gap-4 p-4 rounded-xl border border-white/[0.06] bg-[hsl(222,84%,4.5%)]">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Seat Categories</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 rounded border-2 border-rose-500 bg-rose-950/40" />
                Premium
              </span>
              <span className="font-semibold text-rose-400">Farthest (Best View)</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 rounded border-2 border-amber-500 bg-amber-950/40" />
                Executive
              </span>
              <span className="font-semibold text-amber-400">Middle Rows</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 rounded border-2 border-slate-700 bg-slate-900" />
                Normal
              </span>
              <span className="font-semibold text-slate-400">Closest Rows</span>
            </div>
          </div>

          <div className="h-px bg-white/[0.06] my-1" />

          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Physical seat states</h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 rounded border-2 border-slate-700 bg-slate-900" />
              Available
            </span>
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 rounded border-2 border-zinc-700 bg-zinc-800" />
              Booked
            </span>
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 rounded border-2 border-amber-500 bg-amber-500/20" />
              Reserved
            </span>
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 rounded border-2 border-red-500 bg-red-600" />
              Selected
            </span>
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 rounded border-2 border-cyan-500 bg-cyan-950/40" />
              Wheelchair
            </span>
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 rounded border-2 border-pink-500 bg-pink-950/40" />
              Couple Seat
            </span>
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 rounded border-2 border-amber-600 bg-amber-600/30" />
              Maintenance
            </span>
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 rounded border-2 border-red-700 bg-red-700/20" />
              Exit Path
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
