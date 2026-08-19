'use client';

import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
  icon?: LucideIcon;
  subtitle?: string;
  accentColor?: string;
}

export default function KPICard({
  title,
  value,
  delta,
  deltaType = 'neutral',
  icon: Icon,
  subtitle,
  accentColor = 'text-sky-400',
}: KPICardProps) {
  const getDeltaBadgeClass = () => {
    switch (deltaType) {
      case 'positive':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'negative':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="glass-panel glass-panel-hover p-5 relative overflow-hidden group">
      {/* Decorative gradient blur in background */}
      <div className="absolute -right-8 -top-8 w-24 h-24 bg-sky-500/5 rounded-full blur-2xl group-hover:bg-sky-500/10 transition-colors pointer-events-none" />

      <div className="flex items-center justify-between gap-3 mb-2.5">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</span>
        {Icon && (
          <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/50">
            <Icon className={`h-4 w-4 ${accentColor}`} />
          </div>
        )}
      </div>

      <div className="flex items-baseline justify-between gap-2 mt-1">
        <div className="text-2xl font-bold text-slate-100 tracking-tight">{value}</div>
        {delta && (
          <span className={`text-xs px-2 py-0.5 rounded-md font-semibold border ${getDeltaBadgeClass()}`}>
            {delta}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="text-xs text-slate-400 mt-2 font-medium">{subtitle}</p>
      )}
    </div>
  );
}
