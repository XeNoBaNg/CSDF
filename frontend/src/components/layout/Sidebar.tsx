import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderArchive,
  PlusCircle,
  Activity,
  ShieldCheck,
  AudioLines,
  GitCompare,
} from 'lucide-react';

interface SidebarProps {
  apiStatus: 'healthy' | 'degraded' | 'offline' | 'checking';
}

export const Sidebar: React.FC<SidebarProps> = ({ apiStatus }) => {
  const navItems = [
    {
      to: '/',
      label: 'Dashboard',
      icon: LayoutDashboard,
      description: 'Overview & telemetry',
    },
    {
      to: '/cases',
      label: 'Investigations',
      icon: FolderArchive,
      description: 'Case registry & audit',
    },
    {
      to: '/cases/new',
      label: 'New Investigation',
      icon: PlusCircle,
      description: 'Register case & intake',
    },
    {
      to: '/compare',
      label: 'Cross-Comparison',
      icon: GitCompare,
      description: 'Audio & spectral diff',
    },
    {
      to: '/status',
      label: 'Diagnostics',
      icon: Activity,
      description: 'Subsystems & SHA-256',
    },
  ];

  return (
    <aside className="w-64 bg-slate-900/90 border-r border-slate-800 flex flex-col shrink-0 select-none">
      {/* Brand Header */}
      <div className="h-16 px-5 border-b border-slate-800 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-linear-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-md shadow-cyan-500/20">
          <AudioLines className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-100 tracking-tight text-base">AudioSleuth</span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded">
              v0.1
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-medium">Digital Audio Forensics</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          Forensic Workspace
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-xs'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <div className="flex flex-col">
                <span>{item.label}</span>
                <span className="text-[10px] text-slate-400 font-normal leading-tight">
                  {item.description}
                </span>
              </div>
            </NavLink>
          );
        })}
      </nav>

      {/* Forensic Lab & System Environment Footer */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/40 space-y-2">
        <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                apiStatus === 'healthy'
                  ? 'bg-emerald-400 shadow-xs shadow-emerald-400/50'
                  : apiStatus === 'degraded'
                  ? 'bg-amber-400 shadow-xs shadow-amber-400/50'
                  : apiStatus === 'checking'
                  ? 'bg-cyan-400 animate-pulse'
                  : 'bg-rose-500'
              }`}
            />
            <span className="text-xs text-slate-300 font-medium">
              {apiStatus === 'healthy'
                ? 'Backend Online'
                : apiStatus === 'degraded'
                ? 'Backend Degraded'
                : apiStatus === 'checking'
                ? 'Connecting...'
                : 'Backend Offline'}
            </span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">127.0.0.1</span>
        </div>

        <div className="px-2 py-1.5 text-[10px] text-slate-400 flex items-center justify-between">
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400/80" />
            Local-First / Offline
          </span>
          <span className="font-mono text-slate-400">PICT CSDF</span>
        </div>
      </div>
    </aside>
  );
};
