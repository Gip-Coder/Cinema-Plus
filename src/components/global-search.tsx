"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, Film, MapPin, Settings, ShieldAlert, Loader2, Sparkles } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { moviesApi } from "@/lib/api/movies";
import { scheduleApi } from "@/lib/api/schedule";
import type { Movie, Theatre } from "@/types/domain";

interface SearchItem {
  id: string;
  category: "Movies" | "Theatres" | "Admin Panel" | "Showtimes";
  title: string;
  subtitle?: string;
  url: string;
  icon: React.ReactNode;
}

export function GlobalSearch({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const router = useRouter();
  const { role, isAuthenticated } = useAuth();
  
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<SearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  
  const modalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load searchable index
  useEffect(() => {
    if (!isOpen) return;
    setQuery("");
    setSelectedIndex(0);
    setTimeout(() => inputRef.current?.focus(), 50);

    async function loadIndex() {
      setLoading(true);
      try {
        const [moviesData, theatresData] = await Promise.all([
          moviesApi.list().catch(() => [] as Movie[]),
          scheduleApi.theatres().catch(() => [] as Theatre[]),
        ]);

        const mappedItems: SearchItem[] = [];

        // Movies
        moviesData?.forEach(m => {
          mappedItems.push({
            id: `movie-${m.id}`,
            category: "Movies",
            title: m.title,
            subtitle: `${m.genre} • ${m.language}`,
            url: `/movies/${m.id}`,
            icon: <Film className="h-4 w-4 text-red-500" />
          });
        });

        // Theatres
        theatresData?.forEach(t => {
          mappedItems.push({
            id: `theatre-${t.id}`,
            category: "Theatres",
            title: t.name,
            subtitle: `${t.city || ""}, ${t.state || ""}`,
            url: `/`,
            icon: <MapPin className="h-4 w-4 text-emerald-500" />
          });
        });

        // Add Admin tools if authorized
        if (isAuthenticated && (role === "admin" || role === "super_admin")) {
          mappedItems.push(
            { id: "adm-dash", category: "Admin Panel", title: "Admin Console Dashboard", subtitle: "Operational metrics", url: "/admin", icon: <Settings className="h-4 w-4 text-purple-500" /> },
            { id: "adm-movies", category: "Admin Panel", title: "Manage Spotlight Movies Catalog", subtitle: "CRUD listing", url: "/admin/movies", icon: <Film className="h-4 w-4 text-purple-500" /> },
            { id: "adm-theatres", category: "Admin Panel", title: "Manage Cinema Theatres", subtitle: "Theatres list", url: "/admin/theatres", icon: <MapPin className="h-4 w-4 text-purple-500" /> },
            { id: "adm-pricing", category: "Admin Panel", title: "Seat Tier Pricing Configuration", subtitle: "Normal, Executive, Premium", url: "/admin/pricing", icon: <Settings className="h-4 w-4 text-purple-500" /> },
            { id: "adm-anal", category: "Admin Panel", title: "Executive Revenue Analytics", subtitle: "Revenue charts", url: "/admin/analytics", icon: <Sparkles className="h-4 w-4 text-purple-500" /> },
            { id: "adm-health", category: "Admin Panel", title: "System Operational Health Status", subtitle: "Database & latency logs", url: "/admin/health", icon: <ShieldAlert className="h-4 w-4 text-purple-500" /> },
            { id: "adm-audit", category: "Admin Panel", title: "System Administration Audit Trails", subtitle: "Changes log", url: "/admin/audit", icon: <ShieldAlert className="h-4 w-4 text-purple-500" /> }
          );
        }

        setItems(mappedItems);
      } catch (e) {
        console.error("Failed to load search index", e);
      } finally {
        setLoading(false);
      }
    }
    loadIndex();
  }, [isOpen, isAuthenticated, role]);

  // Click outside listener
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, onClose]);

  // Keyboard navigation inside search results
  const filtered = items.filter(item => 
    item.title.toLowerCase().includes(query.toLowerCase()) ||
    item.category.toLowerCase().includes(query.toLowerCase()) ||
    item.subtitle?.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (!isOpen) return;
      
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % Math.max(filtered.length, 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 + filtered.length) % Math.max(filtered.length, 1));
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          router.push(filtered[selectedIndex].url);
          onClose();
        }
      } else if (e.key === "Escape") {
        onClose();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filtered, selectedIndex, router, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-md flex items-start justify-center pt-24 px-4">
      <div 
        ref={modalRef}
        className="w-full max-w-xl rounded-3xl border border-white/[0.12] bg-zinc-950 shadow-2xl overflow-hidden flex flex-col max-h-[500px]"
        role="dialog"
        aria-modal="true"
        aria-label="Universal Search"
      >
        {/* Search input header */}
        <div className="relative border-b border-white/[0.08] p-4 flex items-center gap-3 bg-white/[0.01]">
          <Search className="h-5 w-5 text-zinc-500" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search movies, theatres, admin actions..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            className="w-full bg-transparent text-sm text-white outline-none placeholder-zinc-600"
            aria-label="Search field"
          />
          <span className="text-[10px] bg-zinc-800 border border-white/[0.08] px-2 py-0.5 rounded text-zinc-500 select-none">
            ESC
          </span>
        </div>

        {/* Search results list */}
        <div className="flex-grow overflow-y-auto p-2.5 space-y-1">
          {loading ? (
            <div className="py-12 flex items-center justify-center gap-2 text-zinc-500 text-xs">
              <Loader2 className="h-4 w-4 animate-spin text-red-500" />
              <span>Building search index...</span>
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-12 text-center text-zinc-600 text-xs">
              No matching records found. Try typing &apos;movies&apos; or &apos;theatre&apos;.
            </div>
          ) : (
            filtered.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    router.push(item.url);
                    onClose();
                  }}
                  className={`w-full flex items-center justify-between p-3 rounded-xl text-left transition-all border ${
                    isSelected 
                      ? "bg-red-600/10 border-red-500/30 text-white" 
                      : "bg-transparent border-transparent text-zinc-400 hover:bg-white/[0.02]"
                  }`}
                  aria-selected={isSelected}
                  role="option"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className="shrink-0">{item.icon}</div>
                    <div className="min-w-0">
                      <span className="text-xs font-bold block truncate">{item.title}</span>
                      {item.subtitle && (
                        <span className="text-[10px] text-zinc-500 font-semibold truncate block mt-0.5">
                          {item.subtitle}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className={`text-[9px] uppercase font-black px-2 py-0.5 rounded ${
                    isSelected ? "bg-red-600 text-white" : "bg-white/[0.04] text-zinc-500"
                  }`}>
                    {item.category}
                  </span>
                </button>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="border-t border-white/[0.06] p-3 text-[10px] text-zinc-600 flex justify-between bg-white/[0.005]">
          <span>Use arrow keys <span className="font-mono">↑↓</span> to navigate</span>
          <span>Press <span className="font-mono">Enter</span> to select</span>
        </div>
      </div>
    </div>
  );
}
