"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useState } from "react";
import {
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Clapperboard,
  DollarSign,
  Film,
  LayoutDashboard,
  LogOut,
  Menu,
  Monitor,
  Theater,
  Ticket,
  X,
  FileText,
  Activity,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

interface NavItem {
  label: string;
  href: string;
  icon: ReactNode;
  allowedRoles?: string[];
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/admin", icon: <LayoutDashboard className="h-5 w-5" /> },
  { label: "Movies", href: "/admin/movies", icon: <Clapperboard className="h-5 w-5" /> },
  { label: "Theatres", href: "/admin/theatres", icon: <Theater className="h-5 w-5" /> },
  { label: "Screens", href: "/admin/screens", icon: <Monitor className="h-5 w-5" /> },
  { label: "Shows", href: "/admin/shows", icon: <Ticket className="h-5 w-5" /> },
  { label: "Pricing", href: "/admin/pricing", icon: <DollarSign className="h-5 w-5" /> },
  { label: "Analytics", href: "/admin/analytics", icon: <BarChart3 className="h-5 w-5" />, allowedRoles: ["admin", "super_admin"] },
  { label: "Audit Logs", href: "/admin/audit", icon: <FileText className="h-5 w-5" />, allowedRoles: ["admin", "super_admin"] },
  { label: "System Health", href: "/admin/health", icon: <Activity className="h-5 w-5" />, allowedRoles: ["admin", "super_admin"] },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/admin") return pathname === "/admin";
  return pathname.startsWith(href);
}

export default function AdminLayout({ children }: Readonly<{ children: ReactNode }>) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, isHydrated, isAuthenticated, role } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  // Breadcrumbs from pathname
  const segments = pathname.split("/").filter(Boolean);
  const breadcrumbs = segments.map((seg, i) => ({
    label: seg.charAt(0).toUpperCase() + seg.slice(1),
    href: "/" + segments.slice(0, i + 1).join("/"),
  }));

  if (!isHydrated) {
    return (
      <div className="flex h-screen items-center justify-center bg-[hsl(222,84%,4.9%)]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-red-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[hsl(222,84%,3.5%)]">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 flex flex-col border-r border-white/[0.06]
          bg-[hsl(222,84%,4.9%)]/95 backdrop-blur-xl transition-all duration-300 ease-in-out
          lg:relative lg:translate-x-0
          ${collapsed ? "w-[72px]" : "w-64"}
          ${mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        {/* Brand */}
        <div className="flex h-16 items-center gap-3 border-b border-white/[0.06] px-4">
          <Film className="h-7 w-7 shrink-0 text-red-500" />
          {!collapsed && (
            <span className="text-lg font-extrabold tracking-widest bg-gradient-to-r from-red-500 to-orange-400 bg-clip-text text-transparent uppercase">
              Cinema+
            </span>
          )}
          {/* Mobile close */}
          <button
            className="ml-auto lg:hidden text-zinc-400 hover:text-white"
            onClick={() => setMobileOpen(false)}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
          {NAV_ITEMS.map((item) => {
            if (item.allowedRoles && (!role || !item.allowedRoles.includes(role))) {
              return null;
            }
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                title={collapsed ? item.label : undefined}
                className={`
                  group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium
                  transition-all duration-200
                  ${
                    active
                      ? "bg-red-500/10 text-red-400 shadow-[inset_0_0_0_1px_rgba(239,68,68,0.15)]"
                      : "text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-200"
                  }
                  ${collapsed ? "justify-center" : ""}
                `}
              >
                <span className={active ? "text-red-400" : "text-zinc-500 group-hover:text-zinc-300"}>
                  {item.icon}
                </span>
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* User card */}
        <div className="border-t border-white/[0.06] p-3">
          {!collapsed && isAuthenticated && (
            <div className="mb-2 rounded-lg bg-white/[0.03] p-3">
              <p className="text-sm font-semibold text-zinc-200 truncate">{user?.username ?? "Admin"}</p>
              <p className="text-xs text-zinc-500 truncate">{role ?? "admin"}</p>
            </div>
          )}
          <button
            onClick={handleLogout}
            title="Logout"
            className={`
              flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium
              text-zinc-400 transition-colors hover:bg-red-500/10 hover:text-red-400
              ${collapsed ? "justify-center" : ""}
            `}
          >
            <LogOut className="h-5 w-5" />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>

        {/* Collapse toggle (desktop only) */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden lg:flex absolute -right-3 top-20 h-6 w-6 items-center justify-center rounded-full border border-white/[0.08] bg-[hsl(222,84%,6%)] text-zinc-400 hover:text-white transition-colors"
        >
          {collapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
        </button>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-16 shrink-0 items-center gap-4 border-b border-white/[0.06] bg-[hsl(222,84%,4.9%)]/80 backdrop-blur-xl px-4 lg:px-6">
          {/* Mobile menu trigger */}
          <button
            className="lg:hidden text-zinc-400 hover:text-white"
            onClick={() => setMobileOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Breadcrumbs */}
          <nav className="flex items-center gap-1.5 text-sm">
            {breadcrumbs.map((crumb, i) => (
              <span key={crumb.href} className="flex items-center gap-1.5">
                {i > 0 && <span className="text-zinc-600">/</span>}
                {i === breadcrumbs.length - 1 ? (
                  <span className="text-zinc-200 font-medium">{crumb.label}</span>
                ) : (
                  <Link href={crumb.href} className="text-zinc-500 hover:text-zinc-300 transition-colors">
                    {crumb.label}
                  </Link>
                )}
              </span>
            ))}
          </nav>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
