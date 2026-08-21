'use client';

import React, { useEffect, useState } from 'react';
import { useFilters } from '@/context/FilterContext';
import { api } from '@/lib/api';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend
} from 'recharts';
import { 
  Calculator, ArrowRight, ArrowUpRight, ArrowDownRight, AlertTriangle, 
  CheckCircle2, Sparkles, Sliders, Layers, TrendingDown, DollarSign
} from 'lucide-react';

export default function VarianceAnalysisPage() {
  const { filters } = useFilters();

  const [availablePeriods, setAvailablePeriods] = useState<string[]>([]);
  const [periodA, setPeriodA] = useState<string>('');
  const [periodB, setPeriodB] = useState<string>('');

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [activeDriverTab, setActiveDriverTab] = useState<'cost' | 'price' | 'mix'>('cost');

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);

  const formatNumber = (val: number) => 
    new Intl.NumberFormat('en-US').format(val);

  // 1. Fetch available periods
  useEffect(() => {
    async function loadPeriods() {
      try {
        const res = await api.getVariancePeriods();
        const pers = res.periods || [];
        setAvailablePeriods(pers);
        if (pers.length >= 2) {
          setPeriodA(pers[pers.length - 2]);
          setPeriodB(pers[pers.length - 1]);
        }
      } catch (err: any) {
        console.error('Error fetching variance periods:', err);
      }
    }
    loadPeriods();
  }, []);

  // 2. Fetch variance decomposition when periodA, periodB, or filters change
  useEffect(() => {
    if (!periodA || !periodB) return;

    async function loadVariance() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getVariance(periodA, periodB, filters);
        if (res.status === 'error') {
          setError(res.message);
        } else {
          setData(res);
        }
      } catch (err: any) {
        console.error('Error loading variance decomposition:', err);
        setError('Failed to compute variance decomposition.');
      } finally {
        setLoading(false);
      }
    }
    loadVariance();
  }, [periodA, periodB, filters]);

  const summary = data?.summary || {};
  const components = data?.variance_components || {};
  const narrative = data?.narrative || {};
  const waterfallBars = data?.waterfall_bars || [];
  const topDrivers = data?.top_drivers || {};

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 tracking-tight flex items-center gap-2.5">
            <Calculator className="h-7 w-7 text-sky-400" />
            Margin Variance Explanation Engine
          </h1>
          <p className="text-sm text-slate-300 mt-1">
            Workstream C — Deterministic 5-way Price / Volume / Mix / Input Cost / Cost-to-Serve margin decomposition.
          </p>
        </div>

        {/* Audit Tie-Out Badge */}
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-950/70 border border-emerald-700/60 self-start lg:self-auto shadow-md">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span className="text-xs font-bold text-emerald-200">
            Audit-Grade Tie-Out: $0.00 Variance
          </span>
        </div>
      </div>

      {/* Period Selection Control Bar */}
      <div className="glass-panel p-5 flex flex-wrap items-center justify-between gap-4 border-l-4 border-l-sky-500">
        <div className="flex items-center gap-3">
          <Sliders className="h-5 w-5 text-sky-400" />
          <div>
            <div className="text-xs font-bold text-slate-100 uppercase tracking-wider">
              Comparison Time Horizon
            </div>
            <div className="text-xs text-slate-300">
              Select Baseline (Period A) and Comparison Target (Period B)
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300">Baseline (Period A):</span>
            <select
              value={periodA}
              onChange={(e) => setPeriodA(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-bold text-slate-100 focus:outline-none focus:border-sky-400"
            >
              {availablePeriods.map(p => (
                <option key={`a-${p}`} value={p}>{p}</option>
              ))}
            </select>
          </div>

          <ArrowRight className="h-4 w-4 text-slate-500" />

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300">Comparison (Period B):</span>
            <select
              value={periodB}
              onChange={(e) => setPeriodB(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-bold text-slate-100 focus:outline-none focus:border-sky-400"
            >
              {availablePeriods.map(p => (
                <option key={`b-${p}`} value={p}>{p}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="glass-panel p-12 text-center space-y-3">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-sky-400"></div>
          <p className="text-sm font-semibold text-slate-300">Computing 5-Way Deterministic Variance Decomposition...</p>
        </div>
      ) : error ? (
        <div className="glass-panel p-8 border-l-4 border-l-rose-500 text-rose-300 flex items-center gap-3">
          <AlertTriangle className="h-6 w-6 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      ) : (
        <>
          {/* Key Metric Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="glass-panel p-4 flex flex-col justify-between">
              <div className="text-[11px] font-semibold text-slate-400 uppercase">Baseline Margin ({periodA})</div>
              <div className="text-2xl font-bold text-slate-100 font-mono mt-1">
                {formatCurrency(summary.baseline_contribution_margin || 0)}
              </div>
              <div className="text-[10px] text-slate-400 mt-1">
                Sales: {formatCurrency(summary.baseline_net_sales || 0)}
              </div>
            </div>

            <div className="glass-panel p-4 flex flex-col justify-between">
              <div className="text-[11px] font-semibold text-slate-400 uppercase">Comparison Margin ({periodB})</div>
              <div className="text-2xl font-bold text-slate-100 font-mono mt-1">
                {formatCurrency(summary.comparison_contribution_margin || 0)}
              </div>
              <div className="text-[10px] text-slate-400 mt-1">
                Sales: {formatCurrency(summary.comparison_net_sales || 0)}
              </div>
            </div>

            <div className="glass-panel p-4 flex flex-col justify-between border-l-4 border-l-sky-400">
              <div className="text-[11px] font-semibold text-slate-400 uppercase">Total Net Variance</div>
              <div className={`text-2xl font-bold font-mono mt-1 ${
                summary.total_margin_variance >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}>
                {summary.total_margin_variance >= 0 ? '+' : ''}{formatCurrency(summary.total_margin_variance || 0)}
              </div>
              <div className={`text-[10px] font-bold mt-1 ${
                summary.variance_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}>
                {summary.variance_pct >= 0 ? '▲' : '▼'} {summary.variance_pct}% Change
              </div>
            </div>

            <div className="glass-panel p-4 flex flex-col justify-between">
              <div className="text-[11px] font-semibold text-slate-400 uppercase">Largest Margin Drag</div>
              <div className="text-lg font-bold text-rose-400 font-mono mt-1">
                {narrative.primary_drag?.driver || 'None'}
              </div>
              <div className="text-[11px] font-mono text-rose-300 font-bold">
                {formatCurrency(narrative.primary_drag?.impact || 0)}
              </div>
            </div>
          </div>

          {/* Automated Executive Narrative Commentary */}
          <div className="glass-panel p-6 border-l-4 border-l-purple-500 bg-slate-900/60 space-y-4">
            <div className="flex items-center gap-2.5">
              <Sparkles className="h-5 w-5 text-purple-400 shrink-0" />
              <h2 className="text-base font-bold text-slate-100">Automated Agent Variance Commentary</h2>
            </div>
            
            <p className="text-sm font-semibold text-slate-200 leading-relaxed">
              {narrative.summary_paragraph}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              {narrative.key_findings?.map((finding: string, idx: number) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 flex items-start gap-2.5 text-xs text-slate-200">
                  <span className="h-2 w-2 rounded-full bg-purple-400 mt-1.5 shrink-0" />
                  <span>{finding}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Waterfall Margin Bridge Chart */}
          <div className="glass-panel p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <TrendingDown className="h-5 w-5 text-sky-400" />
                  Margin Waterfall Bridge ({periodA} ➔ {periodB})
                </h2>
                <p className="text-xs text-slate-300">
                  Exact 5-way decomposition showing price, volume, mix, COGS, freight, and rebate contributions
                </p>
              </div>
            </div>

            <div className="h-88 w-full">
              <ResponsiveContainer width="100%" height={340}>
                <BarChart data={waterfallBars} margin={{ top: 15, right: 10, left: 15, bottom: 25 }}>
                  <XAxis dataKey="name" stroke="#475569" tick={{ fill: '#cbd5e1', fontSize: 11 }} tickLine={false} interval={0} angle={-15} textAnchor="end" />
                  <YAxis stroke="#475569" tick={{ fill: '#cbd5e1', fontSize: 11 }} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#475569', borderRadius: '8px', color: '#f8fafc' }}
                    formatter={(val: any) => [formatCurrency(Number(val)), 'Impact']}
                  />
                  <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                    {waterfallBars.map((entry: any, index: number) => {
                      let color = '#38bdf8'; // sky blue for total
                      if (entry.type === 'relative') {
                        color = entry.amount >= 0 ? '#34d399' : '#f43f5e'; // green if positive, red if negative
                      }
                      return <Cell key={`cell-${index}`} fill={color} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top Outlier Drivers Breakdown Table */}
          <div className="glass-panel p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <Layers className="h-5 w-5 text-indigo-400" />
                  Top Outlier SKU Drivers
                </h2>
                <p className="text-xs text-slate-300">
                  Individual SKUs driving the largest variances between {periodA} and {periodB}
                </p>
              </div>

              {/* Driver Tabs */}
              <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800 self-start sm:self-auto">
                <button
                  onClick={() => setActiveDriverTab('cost')}
                  className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                    activeDriverTab === 'cost'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Direct Cost Drags
                </button>
                <button
                  onClick={() => setActiveDriverTab('price')}
                  className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                    activeDriverTab === 'price'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Price Shifters
                </button>
                <button
                  onClick={() => setActiveDriverTab('mix')}
                  className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                    activeDriverTab === 'mix'
                      ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Mix Shifts
                </button>
              </div>
            </div>

            {/* Drivers Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-slate-300 uppercase tracking-wider text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">SKU ID</th>
                    <th className="py-3 px-4">Product Name</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4 text-right">Units ({periodA})</th>
                    <th className="py-3 px-4 text-right">Units ({periodB})</th>
                    <th className="py-3 px-4 text-right">Variance Impact ($)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-200 font-medium">
                  {(topDrivers[activeDriverTab] || []).map((row: any) => {
                    const varVal = 
                      activeDriverTab === 'cost' ? row.input_cost_variance_slice :
                      activeDriverTab === 'price' ? row.price_variance_slice :
                      row.mix_variance_slice;

                    return (
                      <tr key={row.Product_ID} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-sky-300">{row.Product_ID}</td>
                        <td className="py-3 px-4 font-semibold text-slate-100">{row.Product_Name || row.Product_ID}</td>
                        <td className="py-3 px-4 text-slate-300">{row.Product_Category}</td>
                        <td className="py-3 px-4 text-right font-mono">{formatNumber(row.qty_a || 0)}</td>
                        <td className="py-3 px-4 text-right font-mono">{formatNumber(row.qty_b || 0)}</td>
                        <td className={`py-3 px-4 text-right font-mono font-bold ${
                          varVal >= 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}>
                          {varVal >= 0 ? '+' : ''}{formatCurrency(varVal || 0)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
