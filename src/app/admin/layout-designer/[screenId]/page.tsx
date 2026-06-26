"use client";

import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  MousePointer,
  Hand,
  Plus,
  Minus,
  RotateCcw,
  Trash2,
  Copy,
  LayoutGrid,
  Check,
  Eye,
  AlertTriangle,
  Info,
  TrendingUp,
  X,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import * as adminApi from "@/lib/api/admin";
import type { SeatDefinition, TheatreLayout, LayoutTemplate } from "@/types/admin";

type ToolType = "select" | "pan" | "seat-brush" | "aisle-brush";
type EditMode = "designer" | "audience";

interface HistoryState {
  seats: SeatDefinition[];
  rows: number;
  cols: number;
}

const SEAT_CATEGORIES = ["Normal", "Executive", "Premium"];
const SEAT_TYPES = [
  { value: "standard", label: "Standard", color: "bg-blue-600 border-blue-400" },
  { value: "wheelchair", label: "Wheelchair", color: "bg-cyan-600 border-cyan-400" },
  { value: "couple", label: "Couple Seat", color: "bg-pink-600 border-pink-400" },
  { value: "blocked", label: "Blocked", color: "bg-zinc-700 border-zinc-500" },
  { value: "maintenance", label: "Maintenance", color: "bg-amber-600 border-amber-400" },
  { value: "emergency", label: "Emergency Exit", color: "bg-red-700 border-red-500" },
];

export default function AdminLayoutDesignerPage() {
  const { screenId } = useParams();
  const router = useRouter();
  const { accessToken } = useAuth();

  // Core State
  const [layout, setLayout] = useState<TheatreLayout | null>(null);
  const [seats, setSeats] = useState<SeatDefinition[]>([]);
  const [rows, setRows] = useState(10);
  const [cols, setCols] = useState(15);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Editor configuration
  const [activeTool, setActiveTool] = useState<ToolType>("select");
  const [activeCategory, setActiveCategory] = useState("Normal");
  const [activeSeatType, setActiveSeatType] = useState("standard");
  const [editMode, setEditMode] = useState<EditMode>("designer");

  // Selection
  const [selectedIds, setSelectedIds] = useState<string[]>([]); // seat_code as unique identifier
  const [marqueeStart, setMarqueeStart] = useState<{ x: number; y: number } | null>(null);
  const [marqueeEnd, setMarqueeEnd] = useState<{ x: number; y: number } | null>(null);

  // Canvas Transform (Pan & Zoom)
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState({ x: 50, y: 50 });
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLDivElement>(null);

  // Undo / Redo History Stack
  const [history, setHistory] = useState<HistoryState[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Layout Versions & Comparison
  const [allVersions, setAllVersions] = useState<TheatreLayout[]>([]);
  const [compareTarget, setCompareTarget] = useState<TheatreLayout | null>(null);
  const [compareModalOpen, setCompareModalOpen] = useState(false);

  // Templates
  const [templates, setTemplates] = useState<LayoutTemplate[]>([]);
  const [selectedTemplateName, setSelectedTemplateName] = useState("STANDARD");
  const [targetCapacity, setTargetCapacity] = useState(150);



  // ─── Fetch Screen Layout ────────────────────────────────────────────────────
  const fetchLayoutData = useCallback(async () => {
    if (!accessToken || !screenId) return;
    setLoading(true);
    try {
      // Get all layouts for this screen to find published or drafts
      const allLayouts = await adminApi.getAllLayoutsForScreen(accessToken, Number(screenId));
      setAllVersions(allLayouts ?? []);

      // Expose templates
      const templateList = await adminApi.getLayoutTemplates(accessToken);
      setTemplates(templateList ?? []);

      // Find published layout, or fallback to the latest version
      const published = allLayouts?.find((l) => l.is_published) ?? allLayouts?.[0];
      if (published) {
        setLayout(published);
        setSeats(published.seats ?? []);
        setRows(published.rows ?? 10);
        setCols(published.cols ?? 15);

        // Reset history
        const initialState: HistoryState = {
          seats: published.seats ?? [],
          rows: published.rows ?? 10,
          cols: published.cols ?? 15,
        };
        setHistory([initialState]);
        setHistoryIndex(0);
      } else {
        // Generate a default preview standard layout
        const preview = await adminApi.previewLayout(accessToken, {
          total_seats: 120,
          template: "STANDARD",
        });
        if (preview) {
          setSeats(preview.seats);
          setRows(preview.rows);
          setCols(preview.cols);
          setHistory([{ seats: preview.seats, rows: preview.rows, cols: preview.cols }]);
          setHistoryIndex(0);
        }
      }
      setError(null);
    } catch {
      setError("Failed to load layout details.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, screenId]);

  useEffect(() => {
    fetchLayoutData();
  }, [fetchLayoutData]);

  // ─── History State Management ───────────────────────────────────────────────
  const pushState = useCallback((newSeats: SeatDefinition[], newRows = rows, newCols = cols) => {
    const updatedHistory = history.slice(0, historyIndex + 1);
    const nextState: HistoryState = { seats: newSeats, rows: newRows, cols: newCols };
    setHistory([...updatedHistory, nextState]);
    setHistoryIndex(updatedHistory.length);
    setSeats(newSeats);
    setRows(newRows);
    setCols(newCols);
  }, [history, historyIndex, rows, cols]);

  const handleDeleteSelected = useCallback(() => {
    if (selectedIds.length === 0) return;
    const updated = seats.map((s) => {
      if (selectedIds.includes(s.seat_code)) {
        return { ...s, seat_type: "blocked", is_active: false };
      }
      return s;
    });
    pushState(updated);
    setSelectedIds([]);
  }, [selectedIds, seats, pushState]);

  const handleUndo = useCallback(() => {
    if (historyIndex > 0) {
      const prevIndex = historyIndex - 1;
      setHistoryIndex(prevIndex);
      const state = history[prevIndex];
      setSeats(state.seats);
      setRows(state.rows);
      setCols(state.cols);
      setSelectedIds([]);
    }
  }, [history, historyIndex]);

  const handleRedo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const nextIndex = historyIndex + 1;
      setHistoryIndex(nextIndex);
      const state = history[nextIndex];
      setSeats(state.seats);
      setRows(state.rows);
      setCols(state.cols);
      setSelectedIds([]);
    }
  }, [history, historyIndex]);

  // Keyboard Event Listeners for Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) {
          handleRedo();
        } else {
          handleUndo();
        }
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
        e.preventDefault();
        handleRedo();
      }
      if (e.key === "Delete" || e.key === "Backspace") {
        handleDeleteSelected();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleUndo, handleRedo, handleDeleteSelected]);

  // ─── Visual Calculations & Spacings ─────────────────────────────────────────
  // Spacing offsets for coordinates positioning
  const seatSize = 36;
  const gapSize = 14;

  const canvasWidth = useMemo(() => {
    return cols * (seatSize + gapSize) + 200;
  }, [cols]);

  const canvasHeight = useMemo(() => {
    return rows * (seatSize + gapSize) + 250;
  }, [rows]);

  // Get seat color by type & category
  const getSeatColor = (seat: SeatDefinition) => {
    if (seat.seat_type === "blocked") return "bg-zinc-700 border-zinc-600 text-zinc-500";
    if (seat.seat_type === "maintenance") return "bg-amber-600 border-amber-500 text-amber-900";
    if (seat.seat_type === "emergency") return "bg-red-700 border-red-500 text-red-100";
    if (seat.seat_type === "wheelchair") return "bg-cyan-600 border-cyan-500 text-cyan-100";
    if (seat.seat_type === "couple") return "bg-pink-600 border-pink-500 text-pink-100";

    switch (seat.category) {
      case "Premium":
        return "bg-rose-600 border-rose-500 text-rose-100";
      case "Executive":
        return "bg-amber-500 border-amber-400 text-amber-950";
      default:
        return "bg-slate-700 border-slate-600 text-slate-200";
    }
  };

  // Distance from screen calculation (0 = closest, rows = furthest)
  const getScreenDistance = (seat: SeatDefinition) => {
    return `${seat.position_y} rows away`;
  };

  // ─── Brushes and Canvas Interactivity ───────────────────────────────────────
  const handleCanvasMouseDown = (e: React.MouseEvent) => {
    if (activeTool === "pan" || e.button === 1 || e.button === 2) {
      setIsPanning(true);
      panStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
      return;
    }

    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left - pan.x) / scale;
    const y = (e.clientY - rect.top - pan.y) / scale;

    if (activeTool === "select") {
      setMarqueeStart({ x, y });
      setMarqueeEnd({ x, y });
      if (!e.ctrlKey) {
        setSelectedIds([]);
      }
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent) => {
    if (isPanning) {
      setPan({
        x: e.clientX - panStart.current.x,
        y: e.clientY - panStart.current.y,
      });
      return;
    }

    if (marqueeStart && activeTool === "select") {
      if (!canvasRef.current) return;
      const rect = canvasRef.current.getBoundingClientRect();
      const x = (e.clientX - rect.left - pan.x) / scale;
      const y = (e.clientY - rect.top - pan.y) / scale;
      setMarqueeEnd({ x, y });
    }
  };

  const handleCanvasMouseUp = () => {
    setIsPanning(false);

    if (marqueeStart && marqueeEnd) {
      const x1 = Math.min(marqueeStart.x, marqueeEnd.x);
      const x2 = Math.max(marqueeStart.x, marqueeEnd.x);
      const y1 = Math.min(marqueeStart.y, marqueeEnd.y);
      const y2 = Math.max(marqueeStart.y, marqueeEnd.y);

      // Select seats within marquee box
      const newlySelected: string[] = [];
      seats.forEach((seat) => {
        const sx = seat.position_x * (seatSize + gapSize) + 50 + seatSize / 2;
        const sy = seat.position_y * (seatSize + gapSize) + 150 + seatSize / 2;
        if (sx >= x1 && sx <= x2 && sy >= y1 && sy <= y2) {
          newlySelected.push(seat.seat_code);
        }
      });

      setSelectedIds((prev) => {
        const next = [...prev];
        newlySelected.forEach((id) => {
          if (!next.includes(id)) next.push(id);
        });
        return next;
      });
    }

    setMarqueeStart(null);
    setMarqueeEnd(null);
  };

  const handleSeatClick = (seat: SeatDefinition, e: React.MouseEvent) => {
    e.stopPropagation();
    if (activeTool === "select") {
      if (e.ctrlKey) {
        setSelectedIds((prev) =>
          prev.includes(seat.seat_code) ? prev.filter((id) => id !== seat.seat_code) : [...prev, seat.seat_code]
        );
      } else {
        setSelectedIds([seat.seat_code]);
      }
    } else if (activeTool === "seat-brush") {
      // Toggle active status or apply brush category/type
      const updated = seats.map((s) => {
        if (s.seat_code === seat.seat_code) {
          return {
            ...s,
            category: activeCategory,
            seat_type: activeSeatType,
            is_active: activeSeatType !== "blocked",
          };
        }
        return s;
      });
      pushState(updated);
    } else if (activeTool === "aisle-brush") {
      // Convert to blocked (creates an aisle representation)
      const updated = seats.map((s) => {
        if (s.seat_code === seat.seat_code) {
          return { ...s, seat_type: "blocked", is_active: false };
        }
        return s;
      });
      pushState(updated);
    }
  };

  // ─── Actions & Editing operations ───────────────────────────────────────────

  const handleDuplicateSelected = () => {
    if (selectedIds.length === 0) return;
    // Duplicate selected seats by placing them 1 row further down
    const duplicates: SeatDefinition[] = [];
    selectedIds.forEach((code) => {
      const seat = seats.find((s) => s.seat_code === code);
      if (seat) {
        const nextY = Math.min(seat.position_y + 1, rows - 1);
        const codeNum = seat.seat_number + 50; // shift code
        const newCode = `${seat.row_label}${codeNum}`;
        duplicates.push({
          ...seat,
          seat_code: newCode,
          seat_number: codeNum,
          position_y: nextY,
        });
      }
    });

    // Merge without conflicts
    const updated = [...seats];
    duplicates.forEach((dup) => {
      const idx = updated.findIndex(
        (s) => s.position_x === dup.position_x && s.position_y === dup.position_y
      );
      if (idx !== -1) {
        updated[idx] = dup;
      } else {
        updated.push(dup);
      }
    });
    pushState(updated);
  };

  const handleBulkUpdate = (updates: Partial<SeatDefinition>) => {
    if (selectedIds.length === 0) return;
    const updated = seats.map((s) => {
      if (selectedIds.includes(s.seat_code)) {
        return { ...s, ...updates };
      }
      return s;
    });
    pushState(updated);
  };

  // Template instantiation
  const handleApplyTemplate = async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      const preview = await adminApi.previewLayout(accessToken, {
        total_seats: targetCapacity,
        template: selectedTemplateName,
      });
      if (preview) {
        setSeats(preview.seats);
        setRows(preview.rows);
        setCols(preview.cols);
        pushState(preview.seats, preview.rows, preview.cols);
        setSelectedIds([]);
      }
    } catch {
      setError("Failed to apply layout template");
    } finally {
      setLoading(false);
    }
  };

  // ─── Validation ─────────────────────────────────────────────────────────────
  const validations = useMemo(() => {
    const errors: string[] = [];
    const duplicates = new Set<string>();
    const positions = new Set<string>();

    seats.forEach((s) => {
      if (!s.is_active && s.seat_type === "blocked") return;

      // Duplicate Code Check
      if (duplicates.has(s.seat_code)) {
        errors.push(`Duplicate seat code found: "${s.seat_code}"`);
      }
      duplicates.add(s.seat_code);

      // Overlap Position Check
      const posKey = `${s.position_x},${s.position_y}`;
      if (positions.has(posKey)) {
        errors.push(`Multiple active seats overlap at coordinate (${s.position_x}, ${s.position_y})`);
      }
      positions.add(posKey);

      // Missing Number check
      if (!s.seat_number || isNaN(s.seat_number)) {
        errors.push(`Seat at grid (${s.position_x}, ${s.position_y}) is missing a valid seat number`);
      }
    });

    // Check pricing hierarchy: Premium closest to top (farthest from screen/closest to maximum y)
    // screen at position_y = 0. Premium seats should have position_y >= Normal seats
    const normalMaxY = Math.max(...seats.filter((s) => s.category === "Normal").map((s) => s.position_y), -1);
    const premiumMinY = Math.min(...seats.filter((s) => s.category === "Premium").map((s) => s.position_y), 999);
    if (premiumMinY < normalMaxY && premiumMinY !== 999 && normalMaxY !== -1) {
      errors.push("Pricing Zone Warning: Premium seats placed closer to screen than Normal seats");
    }

    return errors;
  }, [seats]);

  // ─── Statistics & Revenue Estimator ─────────────────────────────────────────
  const stats = useMemo(() => {
    const active = seats.filter((s) => s.is_active);
    const counts = {
      total: active.length,
      normal: active.filter((s) => s.category === "Normal").length,
      executive: active.filter((s) => s.category === "Executive").length,
      premium: active.filter((s) => s.category === "Premium").length,
      wheelchair: active.filter((s) => s.seat_type === "wheelchair").length,
      couple: active.filter((s) => s.seat_type === "couple").length,
      blocked: seats.filter((s) => s.seat_type === "blocked").length,
    };

    // Revenue Projection Potential (illustrative prices: Normal 250, Executive 400, Premium 600)
    const revenue = counts.normal * 250 + counts.executive * 400 + counts.premium * 600;

    return { counts, revenue };
  }, [seats]);

  // ─── Save & Publish Flows ───────────────────────────────────────────────────
  const handleSaveDraft = async () => {
    if (!accessToken || !screenId) return;
    setSaving(true);
    try {
      const payload = {
        screen_id: Number(screenId),
        layout_name: layout?.layout_name ?? "Designer Seating Plan",
        layout_type: selectedTemplateName,
        seats,
        rows,
        cols,
      };
      await adminApi.saveLayout(accessToken, payload);
      setSuccess("Layout draft saved successfully!");
      fetchLayoutData();
      setTimeout(() => setSuccess(null), 3000);
    } catch {
      setError("Failed to save layout draft");
    } finally {
      setSaving(false);
    }
  };

  const handlePublishLayout = async () => {
    if (!accessToken || !layout?.id) return;
    if (validations.length > 0) {
      setError("Cannot publish layout with active validation errors");
      return;
    }
    setSaving(true);
    try {
      await adminApi.publishLayout(accessToken, layout.id);
      setSuccess("Layout plan published successfully!");
      fetchLayoutData();
      setTimeout(() => setSuccess(null), 3000);
    } catch {
      setError("Failed to publish layout");
    } finally {
      setSaving(false);
    }
  };

  // Zooming
  const zoomIn = () => setScale((s) => Math.min(s + 0.1, 2.5));
  const zoomOut = () => setScale((s) => Math.max(s - 0.1, 0.4));
  const resetZoom = () => {
    setScale(1);
    setPan({ x: 50, y: 50 });
  };

  // Version Rolback
  const handleRollback = async (versionNum: number) => {
    if (!accessToken || !screenId) return;
    setLoading(true);
    try {
      await adminApi.rollbackLayoutVersion(accessToken, Number(screenId), { version: versionNum });
      setSuccess(`Rolled back to version ${versionNum}`);
      fetchLayoutData();
      setTimeout(() => setSuccess(null), 3000);
    } catch {
      setError("Failed to rollback layout version");
    } finally {
      setLoading(false);
    }
  };

  const currentSelection = useMemo(() => {
    return seats.filter((s) => selectedIds.includes(s.seat_code));
  }, [seats, selectedIds]);

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] border border-white/[0.06] bg-[hsl(222,84%,3.5%)] rounded-xl overflow-hidden shadow-2xl relative">
      {loading && (
        <div className="absolute inset-0 z-[70] flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
        </div>
      )}
      {/* Editor Header Bar */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-white/[0.06] bg-[hsl(222,84%,4.9%)]">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-red-600/10 p-2 text-red-500">
            <LayoutGrid className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-zinc-100">
              Theatre Seating Designer: {layout?.layout_name ?? "Draft Plan"}
            </h1>
            <p className="text-[11px] text-zinc-500">
              Screen #{screenId} • Version {layout?.version ?? 1} • {layout?.is_published ? "Published" : "Draft"}
            </p>
          </div>
        </div>

        {/* Edit / Customer View Mode tabs */}
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg bg-white/[0.03] border border-white/[0.06] p-1">
            <button
              onClick={() => setEditMode("designer")}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg transition-colors ${
                editMode === "designer" ? "bg-red-600 text-white shadow-md" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <MousePointer className="h-3.5 w-3.5" />
              Designer View
            </button>
            <button
              onClick={() => setEditMode("audience")}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg transition-colors ${
                editMode === "audience" ? "bg-red-600 text-white shadow-md" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Eye className="h-3.5 w-3.5" />
              Audience View
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSaveDraft}
              disabled={saving || isReadOnly}
              className="px-3.5 py-1.5 rounded-lg border border-white/[0.08] text-xs font-bold text-zinc-300 bg-white/[0.01] hover:bg-white/[0.04] disabled:opacity-50 transition-colors"
            >
              Save Draft
            </button>
            <button
              onClick={handlePublishLayout}
              disabled={saving || isReadOnly}
              className="px-3.5 py-1.5 rounded-lg bg-red-600 text-xs font-bold text-white shadow-lg shadow-red-600/20 hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              Publish
            </button>
            <button
              onClick={() => router.back()}
              className="px-3.5 py-1.5 rounded-lg border border-white/[0.08] text-xs font-bold text-zinc-400 hover:text-zinc-200"
            >
              Exit
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border-b border-red-500/20 text-red-400 text-xs px-6 py-2.5 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {success && (
        <div className="bg-emerald-500/10 border-b border-emerald-500/20 text-emerald-400 text-xs px-6 py-2.5 flex items-center justify-between">
          <span>{success}</span>
          <button onClick={() => setSuccess(null)} className="hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Main Workspace Panels */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Toolbar / Template panel */}
        {editMode === "designer" && (
          <aside className="w-64 border-r border-white/[0.06] bg-[hsl(222,84%,4.5%)] p-4 flex flex-col gap-5 overflow-y-auto">
            {/* Design Templates */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Design Template</h3>
              <div className="space-y-2">
                <select
                  value={selectedTemplateName}
                  onChange={(e) => setSelectedTemplateName(e.target.value)}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-zinc-300 outline-none focus:border-red-500/30"
                >
                  {templates.length > 0 ? (
                    templates.map((tpl) => (
                      <option key={tpl.name} value={tpl.name}>
                        {tpl.description || `${tpl.name} Template`}
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="STANDARD">Standard Template</option>
                      <option value="IMAX">IMAX Multiplex</option>
                      <option value="VIP">VIP Gold Lounge</option>
                      <option value="RECLINER">Luxury Recliners</option>
                    </>
                  )}
                  <option value="CUSTOM">Custom Dimensions</option>
                </select>
                <div>
                  <label className="block text-[10px] text-zinc-500 mb-1">Target Capacity</label>
                  <input
                    type="number"
                    value={targetCapacity}
                    onChange={(e) => setTargetCapacity(Number(e.target.value))}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs text-zinc-300 outline-none focus:border-red-500/30"
                  />
                </div>
                <button
                  onClick={handleApplyTemplate}
                  className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 text-xs font-semibold transition-colors"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  Generate Template
                </button>
              </div>
            </div>

            {/* Editor Brushes */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Brush Settings</h3>

              <div>
                <label className="block text-[10px] text-zinc-500 mb-1">Brush Category</label>
                <select
                  value={activeCategory}
                  onChange={(e) => setActiveCategory(e.target.value)}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-zinc-300 outline-none focus:border-red-500/30"
                >
                  {SEAT_CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-zinc-500 mb-1">Brush Seat Type</label>
                <select
                  value={activeSeatType}
                  onChange={(e) => setActiveSeatType(e.target.value)}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-zinc-300 outline-none focus:border-red-500/30"
                >
                  {SEAT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Versions List */}
            <div className="space-y-3 mt-auto">
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Version History</h3>
              <div className="space-y-1.5 max-h-[160px] overflow-y-auto">
                {allVersions.map((v) => (
                  <div
                    key={v.id}
                    className={`flex items-center justify-between rounded-lg p-2 border ${
                      v.id === layout?.id
                        ? "border-red-500/20 bg-red-500/5 text-red-400"
                        : "border-white/[0.04] bg-white/[0.01] text-zinc-400"
                    } text-xs`}
                  >
                    <div>
                      <span className="font-semibold block">v{v.version} - {v.layout_name}</span>
                      <span className="text-[10px] text-zinc-500">
                        {v.is_published ? "Active" : "Draft"}
                      </span>
                    </div>
                    {v.id !== layout?.id && (
                      <button
                        onClick={() => handleRollback(v.version)}
                        className="text-[10px] hover:text-red-400 underline"
                      >
                        Restore
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <button
                onClick={() => setCompareModalOpen(true)}
                className="w-full text-center py-2 border border-white/[0.08] hover:bg-white/[0.04] text-xs font-semibold rounded-lg text-zinc-400 hover:text-zinc-200 transition-colors"
              >
                Compare Versions
              </button>
            </div>
          </aside>
        )}

        {/* Center Designer Workspace Canvas */}
        <main className="flex-1 bg-[hsl(222,84%,2.5%)] overflow-hidden relative flex flex-col select-none">
          {/* Editor Action floating Toolbar */}
          {editMode === "designer" && (
            <div className="absolute top-4 left-4 z-20 flex flex-col gap-1 p-1 rounded-xl border border-white/[0.06] bg-[hsl(222,84%,5.5%)]/90 backdrop-blur-md shadow-2xl">
              <button
                onClick={() => setActiveTool("select")}
                title="Select Tool"
                className={`p-2 rounded-lg transition-colors ${
                  activeTool === "select" ? "bg-red-600 text-white" : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
                }`}
              >
                <MousePointer className="h-4 w-4" />
              </button>
              <button
                onClick={() => setActiveTool("pan")}
                title="Pan Canvas Tool"
                className={`p-2 rounded-lg transition-colors ${
                  activeTool === "pan" ? "bg-red-600 text-white" : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
                }`}
              >
                <Hand className="h-4 w-4" />
              </button>
              <button
                onClick={() => setActiveTool("seat-brush")}
                title="Seat brush tool (Click to place/paint)"
                className={`p-2 rounded-lg transition-colors ${
                  activeTool === "seat-brush" ? "bg-red-600 text-white" : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
                }`}
              >
                <Plus className="h-4 w-4" />
              </button>
              <button
                onClick={() => setActiveTool("aisle-brush")}
                title="Aisle brush (Click to erase/block)"
                className={`p-2 rounded-lg transition-colors ${
                  activeTool === "aisle-brush" ? "bg-red-600 text-white" : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
                }`}
              >
                <Minus className="h-4 w-4" />
              </button>
              <div className="h-px bg-white/[0.06] my-1" />
              <button
                onClick={handleDuplicateSelected}
                disabled={selectedIds.length === 0}
                title="Duplicate Selected (Ctrl+D)"
                className="p-2 rounded-lg text-zinc-400 hover:bg-white/5 hover:text-zinc-200 disabled:opacity-30"
              >
                <Copy className="h-4 w-4" />
              </button>
              <button
                onClick={handleDeleteSelected}
                disabled={selectedIds.length === 0}
                title="Delete Selected"
                className="p-2 rounded-lg text-zinc-400 hover:bg-red-500/10 hover:text-red-400 disabled:opacity-30"
              >
                <Trash2 className="h-4 w-4" />
              </button>
              <div className="h-px bg-white/[0.06] my-1" />
              <button onClick={zoomIn} title="Zoom In" className="p-2 rounded-lg text-zinc-400 hover:bg-white/5 hover:text-zinc-200">
                <Plus className="h-4 w-4" />
              </button>
              <button onClick={zoomOut} title="Zoom Out" className="p-2 rounded-lg text-zinc-400 hover:bg-white/5 hover:text-zinc-200">
                <Minus className="h-4 w-4" />
              </button>
              <button onClick={resetZoom} title="Reset View" className="p-2 rounded-lg text-zinc-400 hover:bg-white/5 hover:text-zinc-200">
                <RotateCcw className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Canvas Area */}
          <div
            ref={canvasRef}
            onMouseDown={handleCanvasMouseDown}
            onMouseMove={handleCanvasMouseMove}
            onMouseUp={handleCanvasMouseUp}
            className={`w-full h-full relative outline-none overflow-hidden ${
              activeTool === "pan" || isPanning ? "cursor-grab active:cursor-grabbing" : "cursor-default"
            }`}
          >
            {/* Visual Canvas Elements */}
            <div
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
                transformOrigin: "0 0",
              }}
              className="absolute transition-transform duration-75 ease-out"
            >
              {/* SCREEN Graphic */}
              <div className="absolute top-10 left-1/2 -translate-x-1/2 flex flex-col items-center">
                <div className="w-[300px] h-[6px] rounded-full bg-cyan-400/40 shadow-[0_0_12px_rgba(34,211,238,0.3)]" />
                <span className="text-[10px] text-zinc-600 mt-2 uppercase tracking-widest font-extrabold">Screen</span>
              </div>

              {/* Seats container */}
              <div
                style={{ width: `${canvasWidth}px`, height: `${canvasHeight}px` }}
                className="relative"
              >
                {seats.map((seat) => {
                  const x = seat.position_x * (seatSize + gapSize) + 50;
                  const y = seat.position_y * (seatSize + gapSize) + 150;
                  const isSelected = selectedIds.includes(seat.seat_code);

                  return (
                    <button
                      key={seat.seat_code}
                      onClick={(e) => handleSeatClick(seat, e)}
                      style={{
                        position: "absolute",
                        left: `${x}px`,
                        top: `${y}px`,
                        width: `${seatSize}px`,
                        height: `${seatSize}px`,
                      }}
                      className={`
                        rounded-lg border-2 flex items-center justify-center text-[10px] font-bold select-none cursor-pointer transition-all
                        ${getSeatColor(seat)}
                        ${
                          isSelected
                            ? "ring-2 ring-red-500 scale-105 border-white shadow-lg"
                            : "hover:scale-105"
                        }
                      `}
                    >
                      {seat.seat_type !== "blocked" && seat.seat_code}
                    </button>
                  );
                })}

                {/* Draw Selection Marquee Overlay */}
                {marqueeStart && marqueeEnd && (
                  <div
                    style={{
                      position: "absolute",
                      left: `${Math.min(marqueeStart.x, marqueeEnd.x)}px`,
                      top: `${Math.min(marqueeStart.y, marqueeEnd.y)}px`,
                      width: `${Math.abs(marqueeStart.x - marqueeEnd.x)}px`,
                      height: `${Math.abs(marqueeStart.y - marqueeEnd.y)}px`,
                    }}
                    className="border border-red-500 bg-red-500/10 pointer-events-none rounded"
                  />
                )}
              </div>
            </div>
          </div>
        </main>

        {/* Right Properties Panel */}
        {editMode === "designer" && (
          <aside className="w-80 border-l border-white/[0.06] bg-[hsl(222,84%,4.5%)] p-5 flex flex-col gap-6 overflow-y-auto">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-3">
                Selected Properties ({selectedIds.length})
              </h3>

              {currentSelection.length === 0 ? (
                <div className="rounded-lg border border-white/[0.04] bg-white/[0.01] p-6 text-center">
                  <Info className="h-10 w-10 text-zinc-600 mx-auto mb-2" />
                  <p className="text-zinc-500 text-xs">Select one or more seats on the canvas to configure properties</p>
                </div>
              ) : currentSelection.length === 1 ? (
                // Single Selection details
                <div className="space-y-4 text-xs">
                  <div>
                    <label className="text-zinc-500 block mb-1">Seat Code</label>
                    <input
                      type="text"
                      value={currentSelection[0].seat_code}
                      onChange={(e) => handleBulkUpdate({ seat_code: e.target.value.toUpperCase() })}
                      className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-zinc-300 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-zinc-500 block mb-1">Row label</label>
                      <input
                        type="text"
                        value={currentSelection[0].row_label}
                        onChange={(e) => handleBulkUpdate({ row_label: e.target.value.toUpperCase() })}
                        className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-zinc-300 outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-zinc-500 block mb-1">Seat Number</label>
                      <input
                        type="number"
                        value={currentSelection[0].seat_number}
                        onChange={(e) => handleBulkUpdate({ seat_number: Number(e.target.value) })}
                        className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-zinc-300 outline-none"
                      />
                    </div>
                  </div>
                  <div>
                    <span className="text-zinc-500 block">Screen Distance</span>
                    <span className="text-zinc-300 block mt-1">{getScreenDistance(currentSelection[0])}</span>
                  </div>
                  <div>
                    <label className="text-zinc-500 block mb-1">Category</label>
                    <select
                      value={currentSelection[0].category}
                      onChange={(e) => handleBulkUpdate({ category: e.target.value })}
                      className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-zinc-300 outline-none"
                    >
                      {SEAT_CATEGORIES.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-zinc-500 block mb-1">Seat Type</label>
                    <select
                      value={currentSelection[0].seat_type}
                      onChange={(e) =>
                        handleBulkUpdate({
                          seat_type: e.target.value,
                          is_active: e.target.value !== "blocked",
                        })
                      }
                      className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-zinc-300 outline-none"
                    >
                      {SEAT_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              ) : (
                // Bulk Selection details
                <div className="space-y-4 text-xs">
                  <div>
                    <label className="text-zinc-500 block mb-1">Update Category</label>
                    <select
                      onChange={(e) => handleBulkUpdate({ category: e.target.value })}
                      defaultValue=""
                      className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-zinc-300 outline-none"
                    >
                      <option value="" disabled>Choose category...</option>
                      {SEAT_CATEGORIES.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-zinc-500 block mb-1">Update Seat Type</label>
                    <select
                      onChange={(e) =>
                        handleBulkUpdate({
                          seat_type: e.target.value,
                          is_active: e.target.value !== "blocked",
                        })
                      }
                      defaultValue=""
                      className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-zinc-300 outline-none"
                    >
                      <option value="" disabled>Choose type...</option>
                      {SEAT_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* Validation Panel */}
            <div className="border-t border-white/[0.06] pt-4 flex-1 flex flex-col min-h-0">
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-3 flex items-center justify-between">
                Layout Validations
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                    validations.length > 0 ? "bg-red-500/10 text-red-400" : "bg-emerald-500/10 text-emerald-400"
                  }`}
                >
                  {validations.length === 0 ? "Valid" : `${validations.length} Errors`}
                </span>
              </h3>

              <div className="flex-1 overflow-y-auto space-y-2 max-h-[220px]">
                {validations.length === 0 ? (
                  <div className="flex items-center gap-2 rounded-lg bg-emerald-500/5 p-3 text-xs text-emerald-400 border border-emerald-500/10">
                    <Check className="h-4 w-4 shrink-0" />
                    No layout configuration errors.
                  </div>
                ) : (
                  validations.map((err, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 rounded-lg bg-red-500/5 p-3 text-xs text-red-400 border border-red-500/10"
                    >
                      <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                      <span>{err}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </aside>
        )}
      </div>

      {/* Bottom Status / Stats & Revenue Bar */}
      <footer className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between px-6 py-3 bg-[hsl(222,84%,4.9%)] border-t border-white/[0.06] text-xs text-zinc-400">
        <div className="flex flex-wrap items-center gap-6">
          <div>
            Total Capacity: <span className="font-bold text-zinc-200">{stats.counts.total} seats</span>
          </div>
          <div>
            Normal: <span className="font-bold text-zinc-200">{stats.counts.normal}</span>
          </div>
          <div>
            Executive: <span className="font-bold text-zinc-200">{stats.counts.executive}</span>
          </div>
          <div>
            Premium: <span className="font-bold text-zinc-200">{stats.counts.premium}</span>
          </div>
          <div>
            Special: <span className="font-bold text-zinc-200">{stats.counts.wheelchair + stats.counts.couple}</span>
          </div>
        </div>

        <div className="flex items-center gap-4 border-l border-white/[0.08] pl-4">
          <div className="flex items-center gap-1">
            <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
            Potential Revenue:
          </div>
          <span className="font-extrabold text-sm text-emerald-400">
            {new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(
              stats.revenue
            )}
          </span>
        </div>
      </footer>

      {/* Version Comparison Modal Dialog */}
      {compareModalOpen && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl rounded-xl border border-white/[0.06] bg-[hsl(222,84%,5.5%)] p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-zinc-100">Compare Seating Layout Versions</h2>
              <button onClick={() => setCompareModalOpen(false)} className="text-zinc-500 hover:text-zinc-300">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-zinc-500 block mb-1">Compare Target Version</label>
                  <select
                    onChange={(e) => setCompareTarget(allVersions.find((v) => v.id === Number(e.target.value)) ?? null)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-300"
                  >
                    <option value="">Select version...</option>
                    {allVersions.map((v) => (
                      <option key={v.id} value={v.id}>
                        v{v.version} - {v.layout_name} ({v.is_published ? "Published" : "Draft"})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {compareTarget && (
                <div className="grid grid-cols-2 gap-6 border-t border-white/[0.06] pt-6">
                  {/* Left Column: Current design */}
                  <div className="space-y-4 text-xs">
                    <h3 className="font-bold text-zinc-200 uppercase tracking-wider text-[11px] border-b border-white/[0.04] pb-2">
                      Current Designer Layout
                    </h3>
                    <div className="grid grid-cols-2 gap-2 text-zinc-400">
                      <span>Total Capacity</span>
                      <span className="font-bold text-zinc-200 text-right">{stats.counts.total}</span>

                      <span>Normal Seats</span>
                      <span className="font-bold text-zinc-200 text-right">{stats.counts.normal}</span>

                      <span>Executive Seats</span>
                      <span className="font-bold text-zinc-200 text-right">{stats.counts.executive}</span>

                      <span>Premium Seats</span>
                      <span className="font-bold text-zinc-200 text-right">{stats.counts.premium}</span>

                      <span>Blocked Seats</span>
                      <span className="font-bold text-zinc-200 text-right">{stats.counts.blocked}</span>
                    </div>
                  </div>

                  {/* Right Column: Compare Target layout */}
                  <div className="space-y-4 text-xs">
                    <h3 className="font-bold text-red-400 uppercase tracking-wider text-[11px] border-b border-white/[0.04] pb-2">
                      Version {compareTarget.version} - {compareTarget.layout_name}
                    </h3>
                    <div className="grid grid-cols-2 gap-2 text-zinc-400">
                      <span>Total Capacity</span>
                      <span className="font-bold text-zinc-200 text-right">{compareTarget.total_seats}</span>

                      <span>Normal Seats</span>
                      <span className="font-bold text-zinc-200 text-right">
                        {compareTarget.seats.filter((s) => s.category === "Normal" && s.is_active).length}
                      </span>

                      <span>Executive Seats</span>
                      <span className="font-bold text-zinc-200 text-right">
                        {compareTarget.seats.filter((s) => s.category === "Executive" && s.is_active).length}
                      </span>

                      <span>Premium Seats</span>
                      <span className="font-bold text-zinc-200 text-right">
                        {compareTarget.seats.filter((s) => s.category === "Premium" && s.is_active).length}
                      </span>

                      <span>Blocked Seats</span>
                      <span className="font-bold text-zinc-200 text-right">
                        {compareTarget.seats.filter((s) => s.seat_type === "blocked").length}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setCompareModalOpen(false)}
                className="rounded-lg border border-white/[0.08] px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04] transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Staff / View-only check helper
const isReadOnly = false;
