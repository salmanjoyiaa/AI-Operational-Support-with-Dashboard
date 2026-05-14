import { BarChart3, BookOpen, Gauge, Inbox, Settings, ShieldCheck } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: Gauge },
  { to: "/tickets", label: "Inbox", icon: Inbox },
  { to: "/knowledge-base", label: "Knowledge Base", icon: BookOpen },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: Settings }
];

export function Layout() {
  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-slate-200 bg-gradient-to-b from-white to-slate-50 lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-slate-100 px-6">
          <div className="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-cyan-700 to-slate-900 text-white">
            <ShieldCheck className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-900">AI Support Ops</p>
            <p className="text-xs text-slate-500">Human review enforced</p>
          </div>
        </div>
        <nav className="space-y-1 px-3 py-5">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded px-3 py-2.5 text-sm font-medium ${
                  isActive ? "bg-slate-950 text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
                }`
              }
            >
              <item.icon className="h-4 w-4" aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-10 border-b border-slate-100 bg-white/80 backdrop-blur-sm">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3 lg:hidden">
              <ShieldCheck className="h-6 w-6 text-slate-900" aria-hidden="true" />
              <span className="font-semibold text-slate-900">AI Support Ops</span>
            </div>
            <div className="hidden text-sm font-medium text-slate-500 lg:block">Support command center</div>
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs text-slate-500">Signed in as</span>
                <span className="text-sm font-semibold text-slate-900">Product Demo</span>
              </div>
              <div className="flex items-center gap-2 rounded border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-sm font-semibold text-emerald-700">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                Review gate active
              </div>
            </div>
          </div>
        </header>
        <main className="px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
