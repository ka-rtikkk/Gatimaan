'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import {
  Train, LayoutDashboard, Wrench, Calendar, CalendarDays,
  CalendarRange, BarChart3, Map, Upload, LogOut, ShieldCheck
} from 'lucide-react';

const NAV = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Overview' },
  { href: '/dashboard/tasks', icon: Wrench, label: 'Maintenance Tasks' },
  { href: '/dashboard/planner', icon: Calendar, label: 'Block Planner' },
  { href: '/dashboard/weekly', icon: CalendarDays, label: 'Weekly Plan' },
  { href: '/dashboard/monthly', icon: CalendarRange, label: 'Monthly Plan' },
  { href: '/dashboard/analytics', icon: BarChart3, label: 'Analytics' },
  { href: '/dashboard/corridors', icon: Map, label: 'Corridors' },
  { href: '/dashboard/import', icon: Upload, label: 'Data Sources' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-[#eef2f7] border-r border-slate-200 flex flex-col z-40">
      {/* Logo */}
      <div className="p-5 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="bg-red-600 p-2 rounded-lg">
            <Train className="w-5 h-5 text-slate-900" />
          </div>
          <div>
            <h1 className="font-black text-lg tracking-widest text-slate-900">GATIMAAN</h1>
            <p className="text-[9px] text-slate-500 tracking-widest uppercase">Block Planning</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = pathname === href || (href !== '/dashboard' && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                active
                  ? 'bg-red-600/20 text-red-400 border border-red-600/30'
                  : 'text-slate-500 hover:text-slate-900 hover:bg-white'
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="p-4 border-t border-slate-200">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 bg-blue-600/30 border border-blue-600/50 rounded-full flex items-center justify-center">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
            <p className="text-xs text-slate-500">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 text-slate-500 hover:text-red-400 hover:bg-red-50 rounded-lg text-xs transition"
        >
          <LogOut className="w-3.5 h-3.5" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
