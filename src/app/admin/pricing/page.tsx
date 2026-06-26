"use client";

import { useEffect, useState, useCallback } from "react";
import {
  DollarSign,
  Save,
  Plus,
  Pencil,
  X,
  ToggleLeft,
  ToggleRight,
  ArrowDown,
  Monitor,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import * as adminApi from "@/lib/api/admin";
import type { SeatPricing, PricingRule, PricingRuleCreate, Theatre } from "@/types/admin";

// Pricing hierarchy: SCREEN → Normal → Executive → Premium
// Premium is farthest from screen and highest priced
const CATEGORY_ORDER = ["Normal", "Executive", "Premium"] as const;
const CATEGORY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  Normal: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/20" },
  Executive: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/20" },
  Premium: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/20" },
};

const RULE_TYPES = ["weekend", "holiday", "event", "surge", "time_based"] as const;

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(amount);
}

export default function AdminPricingPage() {
  const { accessToken } = useAuth();
  const [pricings, setPricings] = useState<SeatPricing[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [rules, setRules] = useState<PricingRule[]>([]);
  const [theatres, setTheatres] = useState<Theatre[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editPrice, setEditPrice] = useState("");
  const [saving, setSaving] = useState(false);

  // Rule modal
  const [ruleModal, setRuleModal] = useState(false);
  const [ruleName, setRuleName] = useState("");
  const [ruleType, setRuleType] = useState<string>("weekend");
  const [ruleMultiplier, setRuleMultiplier] = useState(1.5);
  const [rulePriority, setRulePriority] = useState(0);
  const [ruleStackable, setRuleStackable] = useState(true);
  const [ruleActive, setRuleActive] = useState(true);

  const fetchData = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      const [pricingData, theatresData] = await Promise.all([
        adminApi.getPricing(accessToken),
        adminApi.getTheatres(accessToken),
      ]);
      setPricings(pricingData ?? []);
      setTheatres(theatresData ?? []);
      setError(null);
    } catch {
      setError("Failed to load pricing data");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getTheatreName = (theatreId: number) =>
    theatres.find((t) => t.id === theatreId)?.name ?? `Theatre #${theatreId}`;

  const handleStartEdit = (pricing: SeatPricing) => {
    setEditingId(pricing.id);
    setEditPrice(String(pricing.base_price));
  };

  const handleSavePrice = async (id: number) => {
    if (!accessToken || !editPrice) return;
    setSaving(true);
    try {
      await adminApi.updatePricing(accessToken, id, { base_price: Number(editPrice) });
      setEditingId(null);
      fetchData();
    } catch {
      setError("Failed to update pricing");
    } finally {
      setSaving(false);
    }
  };

  const handleCreateRule = async () => {
    if (!accessToken || !ruleName.trim()) return;
    setSaving(true);
    try {
      const payload: PricingRuleCreate = {
        name: ruleName.trim(),
        rule_type: ruleType,
        multiplier: ruleMultiplier,
        priority: rulePriority,
        stackable: ruleStackable,
        is_active: ruleActive,
      };
      await adminApi.createPricingRule(accessToken, payload);
      setRuleModal(false);
      // Rules aren't loaded in the same endpoint but add it for display
      setRules((prev) => [...prev, { ...payload, id: Date.now(), created_at: new Date().toISOString() } as PricingRule]);
    } catch {
      setError("Failed to create pricing rule");
    } finally {
      setSaving(false);
    }
  };

  // Group pricing by theatre → category
  const grouped = pricings.reduce(
    (acc, p) => {
      const key = p.theatre_id;
      if (!acc[key]) acc[key] = [];
      acc[key].push(p);
      return acc;
    },
    {} as Record<number, SeatPricing[]>,
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Pricing</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Manage seat pricing by category. Hierarchy: Screen → Normal → Executive → Premium
          </p>
        </div>
        <button
          onClick={() => {
            setRuleModal(true);
            setRuleName("");
            setRuleType("weekend");
            setRuleMultiplier(1.5);
            setRulePriority(0);
            setRuleStackable(true);
            setRuleActive(true);
          }}
          className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-red-600/20 hover:bg-red-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Pricing Rule
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400">{error}</div>
      )}

      {/* Pricing Hierarchy Legend */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
        <div className="flex items-center gap-3 text-sm text-zinc-400 mb-3">
          <Monitor className="h-4 w-4 text-zinc-500" />
          <span className="font-medium text-zinc-300">Cinema Plus Pricing Hierarchy</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="rounded bg-zinc-800 px-2 py-1 text-zinc-300 font-mono">SCREEN</span>
          <ArrowDown className="h-3 w-3 text-zinc-600 rotate-[-90deg]" />
          <span className="rounded bg-blue-500/10 px-2 py-1 text-blue-400 font-medium">Normal</span>
          <ArrowDown className="h-3 w-3 text-zinc-600 rotate-[-90deg]" />
          <span className="rounded bg-amber-500/10 px-2 py-1 text-amber-400 font-medium">Executive</span>
          <ArrowDown className="h-3 w-3 text-zinc-600 rotate-[-90deg]" />
          <span className="rounded bg-purple-500/10 px-2 py-1 text-purple-400 font-medium">Premium</span>
          <span className="text-zinc-600 ml-2">(Farthest from screen, highest price)</span>
        </div>
      </div>

      {/* Pricing by Theatre */}
      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-xl border border-white/[0.06] bg-white/[0.02]" />
          ))}
        </div>
      ) : Object.keys(grouped).length === 0 ? (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-12 text-center">
          <DollarSign className="mx-auto h-12 w-12 text-zinc-600 mb-3" />
          <p className="text-zinc-500">No pricing data configured</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([theatreIdStr, theatrePricings]) => {
            const theatreId = Number(theatreIdStr);
            // Sort by hierarchy order
            const sorted = [...theatrePricings].sort(
              (a, b) =>
                CATEGORY_ORDER.indexOf(a.seat_category as typeof CATEGORY_ORDER[number]) -
                CATEGORY_ORDER.indexOf(b.seat_category as typeof CATEGORY_ORDER[number]),
            );

            return (
              <div
                key={theatreId}
                className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden"
              >
                <div className="border-b border-white/[0.06] px-5 py-3 bg-white/[0.01]">
                  <h3 className="font-semibold text-zinc-200">{getTheatreName(theatreId)}</h3>
                </div>
                <div className="grid gap-4 p-5 sm:grid-cols-3">
                  {sorted.map((pricing) => {
                    const colors = CATEGORY_COLORS[pricing.seat_category] ?? {
                      bg: "bg-zinc-500/10",
                      text: "text-zinc-400",
                      border: "border-zinc-500/20",
                    };
                    const isEditing = editingId === pricing.id;

                    return (
                      <div
                        key={pricing.id}
                        className={`rounded-xl border ${colors.border} ${colors.bg} p-4 transition-all hover:shadow-lg`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className={`text-sm font-bold ${colors.text}`}>
                            {pricing.seat_category}
                          </span>
                          {pricing.screen_id && (
                            <span className="text-[10px] text-zinc-500">Screen #{pricing.screen_id}</span>
                          )}
                        </div>

                        {isEditing ? (
                          <div className="flex items-center gap-2">
                            <input
                              type="number"
                              value={editPrice}
                              onChange={(e) => setEditPrice(e.target.value)}
                              min={1}
                              className="w-full rounded border border-white/[0.1] bg-white/[0.05] px-2 py-1.5 text-sm text-zinc-200 outline-none font-mono"
                            />
                            <button
                              onClick={() => handleSavePrice(pricing.id)}
                              disabled={saving}
                              className="rounded bg-emerald-600 p-1.5 text-white hover:bg-emerald-700 transition-colors"
                            >
                              <Save className="h-3.5 w-3.5" />
                            </button>
                            <button
                              onClick={() => setEditingId(null)}
                              className="rounded bg-zinc-700 p-1.5 text-zinc-300 hover:bg-zinc-600 transition-colors"
                            >
                              <X className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between">
                            <span className="text-xl font-bold text-zinc-100">
                              {formatCurrency(pricing.base_price)}
                            </span>
                            <button
                              onClick={() => handleStartEdit(pricing)}
                              className="rounded p-1.5 text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.06] transition-colors"
                            >
                              <Pencil className="h-4 w-4" />
                            </button>
                          </div>
                        )}

                        <p className="text-[10px] text-zinc-600 mt-2">{pricing.currency}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pricing Rule Modal */}
      {ruleModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-white/[0.06] bg-[hsl(222,84%,5.5%)] p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-zinc-100">Add Pricing Rule</h2>
              <button onClick={() => setRuleModal(false)} className="text-zinc-500 hover:text-zinc-300">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Rule Name *</label>
                <input
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  placeholder="Weekend Surge"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Type *</label>
                  <select
                    value={ruleType}
                    onChange={(e) => setRuleType(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  >
                    {RULE_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t.replace("_", " ")}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Multiplier *</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={ruleMultiplier}
                    onChange={(e) => setRuleMultiplier(Number(e.target.value))}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Priority</label>
                <input
                  type="number"
                  value={rulePriority}
                  onChange={(e) => setRulePriority(Number(e.target.value))}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                />
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <button onClick={() => setRuleStackable(!ruleStackable)} className="text-zinc-400 hover:text-zinc-200">
                    {ruleStackable ? <ToggleRight className="h-6 w-6 text-emerald-400" /> : <ToggleLeft className="h-6 w-6" />}
                  </button>
                  <span className="text-sm text-zinc-400">Stackable</span>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => setRuleActive(!ruleActive)} className="text-zinc-400 hover:text-zinc-200">
                    {ruleActive ? <ToggleRight className="h-6 w-6 text-emerald-400" /> : <ToggleLeft className="h-6 w-6" />}
                  </button>
                  <span className="text-sm text-zinc-400">Active</span>
                </div>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                onClick={() => setRuleModal(false)}
                className="rounded-lg border border-white/[0.08] px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateRule}
                disabled={saving || !ruleName.trim()}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {saving ? "Creating..." : "Create Rule"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
