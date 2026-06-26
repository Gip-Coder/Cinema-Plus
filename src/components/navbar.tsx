"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Film, User as UserIcon, LogOut, ChevronDown, LayoutDashboard, Ticket, Search } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { GlobalSearch } from "@/components/global-search";

export function Navbar() {
  const router = useRouter();
  const { isAuthenticated, role, user, logout, isHydrated } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  // Close dropdown when clicking outside
  useEffect(() => {
    const closeDropdown = () => setDropdownOpen(false);
    if (dropdownOpen) {
      window.addEventListener("click", closeDropdown);
    }
    return () => window.removeEventListener("click", closeDropdown);
  }, [dropdownOpen]);

  // Global Ctrl+K keyboard shortcut
  useEffect(() => {
    const handleShortcut = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, []);

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4 md:px-8 max-w-7xl mx-auto">
        {/* Logo */}
        <Link href={isAuthenticated && role === "admin" ? "/admin" : "/"} className="flex items-center gap-2 font-bold select-none cursor-pointer">
          <Film className="h-6 w-6 text-red-600" />
          <span className="text-xl font-extrabold tracking-[0.25em] bg-gradient-to-r from-red-600 to-red-400 bg-clip-text text-transparent uppercase">
            Cinema Plus
          </span>
        </Link>

        {/* Search Trigger Button */}
        <button
          onClick={() => setSearchOpen(true)}
          className="hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-white/[0.08] bg-white/[0.02] text-xs font-semibold text-zinc-500 hover:bg-white/[0.04] transition-colors ml-auto mr-4 cursor-pointer"
        >
          <Search className="h-3.5 w-3.5" />
          <span>Search...</span>
          <span className="text-[9px] bg-zinc-800 border border-white/[0.08] px-1.5 py-0.5 rounded text-zinc-500 font-mono">
            Ctrl+K
          </span>
        </button>

        {/* Navigation Links */}
        <nav className="flex items-center gap-6">
          {!isAuthenticated || role !== "admin" ? (
            <Link href="/" className="text-sm font-medium transition-colors hover:text-red-500">
              Movies
            </Link>
          ) : null}

          {isHydrated && isAuthenticated ? (
            <>
              {role === "admin" ? (
                <Link href="/admin" className="text-sm font-medium transition-colors hover:text-red-500 flex items-center gap-1">
                  <LayoutDashboard className="h-4 w-4" />
                  Dashboard
                </Link>
              ) : (
                <Link href="/bookings" className="text-sm font-medium transition-colors hover:text-red-500 flex items-center gap-1">
                  <Ticket className="h-4 w-4" />
                  My Bookings
                </Link>
              )}

              {/* User Dropdown */}
              <div className="relative">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setDropdownOpen(!dropdownOpen);
                  }}
                  className="flex items-center gap-2 rounded-full border border-border px-3 py-1.5 text-sm font-medium hover:bg-accent/50 transition-colors"
                >
                  <UserIcon className="h-4 w-4" />
                  <span className="max-w-[100px] truncate">{user?.username ?? "Account"}</span>
                  <ChevronDown className="h-4 w-4 opacity-50" />
                </button>

                {dropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 rounded-md border border-border bg-popover p-1 text-popover-foreground shadow-md animate-in fade-in slide-in-from-top-1">
                    {role !== "admin" && (
                      <>
                        <Link
                          href="/dashboard"
                          className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
                        >
                          <LayoutDashboard className="h-4 w-4" />
                          My Dashboard
                        </Link>
                        <Link
                          href="/profile"
                          className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
                        >
                          <UserIcon className="h-4 w-4" />
                          My Profile
                        </Link>
                        <Link
                          href="/bookings"
                          className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
                        >
                          <Ticket className="h-4 w-4" />
                          My Bookings
                        </Link>
                      </>
                    )}
                    <button
                      onClick={handleLogout}
                      className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm text-destructive hover:bg-destructive/10 hover:text-destructive transition-colors text-left"
                    >
                      <LogOut className="h-4 w-4" />
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            isHydrated && (
              <Link
                href="/login"
                className="inline-flex h-9 items-center justify-center rounded-full bg-red-600 px-6 text-sm font-bold text-white transition-colors hover:bg-red-700 active:scale-95"
              >
                Login
              </Link>
            )
          )}
        </nav>
      </div>
      <GlobalSearch isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </header>
  );
}
