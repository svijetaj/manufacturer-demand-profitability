'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  BarChart3, 
  Package, 
  DollarSign, 
  Building2, 
  Sparkles, 
  TrendingUp, 
  BookOpen, 
  Layers,
  Database,
  Calculator,
  ShieldAlert
} from 'lucide-react';

const NAV_ITEMS = [
  { href: '/', label: 'Executive Overview', icon: BarChart3 },
  { href: '/demand', label: 'Historical Demand', icon: Package },
  { href: '/margins', label: 'Financial Margins', icon: DollarSign },
  { href: '/opex', label: 'OpEx & Budget', icon: Building2 },
  { href: '/variance', label: 'Variance Explanation', icon: Calculator, badge: '5-Way' },
  { href: '/anomaly', label: 'Anomaly Detection', icon: ShieldAlert, badge: 'Quality' },
  { href: '/predict-demand', label: 'AI Demand Prediction', icon: Sparkles, badge: 'ML' },
  { href: '/predict-profit', label: 'Profit & CVP Model', icon: TrendingUp, badge: 'Linear' },
  { href: '/docs', label: 'System & RAG Docs', icon: BookOpen },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#0d1322] border-r border-[#1e293b] flex flex-col shrink-0 min-h-screen">
      {/* Brand Header */}
      <div className="p-6 border-b border-[#1e293b]">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <Layers className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-100 tracking-tight leading-tight">Meridian Corp</h1>
            <p className="text-xs text-sky-400 font-medium">Demand & Profitability</p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-5 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Analytics & Intelligence
        </div>
        {NAV_ITEMS.map(item => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`h-4 w-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                  item.badge === 'ML' ? 'bg-indigo-500/20 text-indigo-300' : 'bg-emerald-500/20 text-emerald-300'
                }`}>
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer System Badge */}
      <div className="p-4 border-t border-[#1e293b] bg-[#090d18]">
        <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg bg-slate-900/80 border border-slate-800">
          <Database className="h-4 w-4 text-emerald-400 shrink-0" />
          <div className="text-xs truncate">
            <p className="font-semibold text-slate-300">DuckDB Semantic</p>
            <p className="text-[11px] text-slate-500">FastAPI REST v2.0</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
