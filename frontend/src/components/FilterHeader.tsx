'use client';

import React, { useState } from 'react';
import { useFilters } from '@/context/FilterContext';
import { Filter, Calendar, RotateCcw, ChevronDown, Check } from 'lucide-react';

export default function FilterHeader() {
  const {
    filters,
    availableCategories,
    availableSegments,
    availableRegions,
    setDateRange,
    toggleCategory,
    toggleSegment,
    toggleRegion,
    resetFilters,
  } = useFilters();

  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  const activeCount = 
    (filters.categories?.length || 0) +
    (filters.segments?.length || 0) +
    (filters.regions?.length || 0);

  return (
    <header className="bg-[#0b101d]/90 backdrop-blur-md border-b border-[#1e293b] px-6 py-3.5 sticky top-0 z-30 flex flex-wrap items-center justify-between gap-4">
      {/* Date Range Selection */}
      <div className="flex items-center gap-2.5">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-700 text-xs text-slate-100">
          <Calendar className="h-4 w-4 text-sky-400" />
          <span className="text-slate-200 font-semibold">Period:</span>
          <input
            type="date"
            value={filters.startDate || ''}
            onChange={(e) => setDateRange(e.target.value, filters.endDate || '')}
            className="bg-transparent border-0 text-slate-100 font-medium text-xs focus:ring-0 focus:outline-none cursor-pointer"
          />
          <span className="text-slate-400 font-semibold">to</span>
          <input
            type="date"
            value={filters.endDate || ''}
            onChange={(e) => setDateRange(filters.startDate || '', e.target.value)}
            className="bg-transparent border-0 text-slate-100 font-medium text-xs focus:ring-0 focus:outline-none cursor-pointer"
          />
        </div>
      </div>

      {/* Multi-Dimensional Filter Dropdowns */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Categories Dropdown */}
        <div className="relative">
          <button
            onClick={() => setOpenDropdown(openDropdown === 'cat' ? null : 'cat')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
              (filters.categories?.length || 0) > 0
                ? 'bg-sky-500/10 border-sky-500/30 text-sky-300'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
            }`}
          >
            <span>Category</span>
            {(filters.categories?.length || 0) > 0 && (
              <span className="h-4 w-4 rounded-full bg-sky-500 text-[10px] text-slate-950 font-bold flex items-center justify-center">
                {filters.categories?.length}
              </span>
            )}
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {openDropdown === 'cat' && (
            <div className="absolute left-0 mt-2 w-56 p-2 rounded-xl bg-[#0f172a] border border-slate-700 shadow-2xl z-50 space-y-1">
              <div className="text-[11px] font-semibold text-slate-400 px-2 py-1 uppercase">Filter Categories</div>
              {availableCategories.map(cat => {
                const checked = filters.categories?.includes(cat);
                return (
                  <button
                    key={cat}
                    onClick={() => toggleCategory(cat)}
                    className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs text-left text-slate-200 hover:bg-slate-800 transition-colors"
                  >
                    <span>{cat}</span>
                    {checked && <Check className="h-3.5 w-3.5 text-sky-400" />}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Customer Segment Dropdown */}
        <div className="relative">
          <button
            onClick={() => setOpenDropdown(openDropdown === 'seg' ? null : 'seg')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
              (filters.segments?.length || 0) > 0
                ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
            }`}
          >
            <span>Segment</span>
            {(filters.segments?.length || 0) > 0 && (
              <span className="h-4 w-4 rounded-full bg-indigo-500 text-[10px] text-white font-bold flex items-center justify-center">
                {filters.segments?.length}
              </span>
            )}
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {openDropdown === 'seg' && (
            <div className="absolute left-0 mt-2 w-56 p-2 rounded-xl bg-[#0f172a] border border-slate-700 shadow-2xl z-50 space-y-1">
              <div className="text-[11px] font-semibold text-slate-400 px-2 py-1 uppercase">Filter Segments</div>
              {availableSegments.map(seg => {
                const checked = filters.segments?.includes(seg);
                return (
                  <button
                    key={seg}
                    onClick={() => toggleSegment(seg)}
                    className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs text-left text-slate-200 hover:bg-slate-800 transition-colors"
                  >
                    <span>{seg}</span>
                    {checked && <Check className="h-3.5 w-3.5 text-indigo-400" />}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Sales Region Dropdown */}
        <div className="relative">
          <button
            onClick={() => setOpenDropdown(openDropdown === 'reg' ? null : 'reg')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
              (filters.regions?.length || 0) > 0
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
            }`}
          >
            <span>Region</span>
            {(filters.regions?.length || 0) > 0 && (
              <span className="h-4 w-4 rounded-full bg-emerald-500 text-[10px] text-slate-950 font-bold flex items-center justify-center">
                {filters.regions?.length}
              </span>
            )}
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {openDropdown === 'reg' && (
            <div className="absolute left-0 mt-2 w-56 p-2 rounded-xl bg-[#0f172a] border border-slate-700 shadow-2xl z-50 space-y-1">
              <div className="text-[11px] font-semibold text-slate-400 px-2 py-1 uppercase">Filter Regions</div>
              {availableRegions.map(reg => {
                const checked = filters.regions?.includes(reg);
                return (
                  <button
                    key={reg}
                    onClick={() => toggleRegion(reg)}
                    className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs text-left text-slate-200 hover:bg-slate-800 transition-colors"
                  >
                    <span>{reg}</span>
                    {checked && <Check className="h-3.5 w-3.5 text-emerald-400" />}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Reset Filters */}
        {activeCount > 0 && (
          <button
            onClick={resetFilters}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 text-xs font-medium transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Reset</span>
          </button>
        )}
      </div>
    </header>
  );
}
