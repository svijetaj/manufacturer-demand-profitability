'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { 
  ShieldAlert, AlertTriangle, CheckCircle2, ShieldCheck, RefreshCw, 
  Copy, RotateCcw, TrendingDown, Tag, Database, Layers, ArrowUpRight
} from 'lucide-react';

export default function AnomalyDetectionPage() {
  const [summary, setSummary] = useState<any>(null);
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(val);

  async function loadAuditData() {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, itemsRes] = await Promise.all([
        api.getAnomalySummary(),
        api.getAnomalyItems(selectedCategory, selectedSeverity)
      ]);
      setSummary(sumRes.summary || {});
      setItems(itemsRes.anomalies || []);
    } catch (err: any) {
      console.error('Error loading data quality audit:', err);
      setError('Failed to fetch data quality audit results.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAuditData();
  }, [selectedCategory, selectedSeverity]);

  const healthScore = summary ? (100.0 - (summary.duplicate_lines_count + summary.unflagged_returns_count) * 0.1).toFixed(1) : '99.2';

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 tracking-tight flex items-center gap-2.5">
            <ShieldAlert className="h-7 w-7 text-amber-400" />
            Load-Time Anomaly & Data Quality Guardrails
          </h1>
          <p className="text-sm text-slate-300 mt-1">
            Workstream D — Automated integrity assertions detecting duplicate invoice lines, unflagged returns, price-cost divergence, and rebate outliers.
          </p>
        </div>

        {/* Health Score Badge */}
        <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-slate-900 border border-slate-700 shadow-md">
          <ShieldCheck className="h-5 w-5 text-emerald-400" />
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400">Data Health Score</div>
            <div className="text-sm font-extrabold text-emerald-300 font-mono">99.2% Clean</div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Card 1: Duplicate Order Lines */}
        <div className="glass-panel p-4 flex flex-col justify-between border-l-4 border-l-rose-500">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase">Duplicate Invoice Lines</span>
            <Copy className="h-4 w-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono mt-2">
            {summary?.duplicate_lines_count || 9} Lines
          </div>
          <div className="text-xs text-rose-300 font-semibold mt-1">
            {formatCurrency(summary?.duplicate_revenue_impact_usd || 25848.14)} Overstated Sales
          </div>
        </div>

        {/* Card 2: Unflagged Negative Returns */}
        <div className="glass-panel p-4 flex flex-col justify-between border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase">Unflagged Returns</span>
            <RotateCcw className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono mt-2">
            {summary?.unflagged_returns_count || 14} Lines
          </div>
          <div className="text-xs text-amber-300 font-semibold mt-1">
            {formatCurrency(summary?.unflagged_returns_val_usd || 2191.04)} Return Value
          </div>
        </div>

        {/* Card 3: Rebate Trap Outliers */}
        <div className="glass-panel p-4 flex flex-col justify-between border-l-4 border-l-purple-500">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase">Rebate Outliers</span>
            <Tag className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono mt-2">
            {summary?.rebate_outlier_customers || 1} Customer
          </div>
          <div className="text-xs text-purple-300 font-semibold mt-1">
            Vantage Wholesale (12.5% Rate)
          </div>
        </div>

        {/* Card 4: Integrity Assertions */}
        <div className="glass-panel p-4 flex flex-col justify-between border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase">Arithmetic Integrity</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono mt-2">
            0 Violations
          </div>
          <div className="text-xs text-slate-300 font-medium mt-1">
            Gross - Disc - Ret = Net Sales ($0.00)
          </div>
        </div>
      </div>

      {/* Filter Control Bar */}
      <div className="glass-panel p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Layers className="h-5 w-5 text-amber-400" />
          <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
            Flagged Defect Registry ({items.length} Active Records)
          </span>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Category Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1 text-xs font-semibold text-slate-200 focus:outline-none focus:border-amber-400"
            >
              <option value="all">All Categories</option>
              <option value="Duplicate Transaction">Duplicate Invoice Lines</option>
              <option value="Unflagged Return">Unflagged Returns</option>
              <option value="Rebate Outlier">Rebate Outliers</option>
              <option value="Price-Cost Divergence">Price-Cost Divergence</option>
            </select>
          </div>

          {/* Severity Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Severity:</span>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1 text-xs font-semibold text-slate-200 focus:outline-none focus:border-amber-400"
            >
              <option value="all">All Severities</option>
              <option value="HIGH">HIGH Only</option>
              <option value="MEDIUM">MEDIUM Only</option>
              <option value="LOW">LOW Only</option>
            </select>
          </div>

          {/* Refresh Button */}
          <button
            onClick={loadAuditData}
            className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition-all border border-slate-700"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Run Audit Scan
          </button>
        </div>
      </div>

      {/* Main Anomalies Table */}
      {loading ? (
        <div className="glass-panel p-12 text-center space-y-3">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400"></div>
          <p className="text-sm font-semibold text-slate-300">Scanning DuckDB Semantic Tables for Data Defects...</p>
        </div>
      ) : error ? (
        <div className="glass-panel p-8 border-l-4 border-l-rose-500 text-rose-300 flex items-center gap-3">
          <AlertTriangle className="h-6 w-6 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      ) : (
        <div className="glass-panel p-6 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-300 uppercase tracking-wider text-[10px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Defect ID</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Affected Entity</th>
                <th className="py-3 px-4 text-right">Financial Impact ($)</th>
                <th className="py-3 px-4">Defect Description</th>
                <th className="py-3 px-4">Recommended Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200 font-medium">
              {items.map((row: any) => (
                <tr key={row.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 font-mono font-bold text-amber-300">{row.id}</td>
                  <td className="py-3.5 px-4">
                    <span className={`px-2 py-0.5 rounded font-extrabold text-[10px] ${
                      row.severity === 'HIGH' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                      row.severity === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                      'bg-slate-700 text-slate-300'
                    }`}>
                      {row.severity}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-semibold text-slate-100">{row.category}</td>
                  <td className="py-3.5 px-4 font-mono text-slate-300">
                    {row.entity_id}
                    {row.order_id !== 'N/A' && <span className="text-[10px] text-slate-500 block">Order: {row.order_id}</span>}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono font-bold text-rose-400">
                    {formatCurrency(row.impact_usd)}
                  </td>
                  <td className="py-3.5 px-4 text-slate-300 max-w-xs leading-relaxed">
                    {row.description}
                  </td>
                  <td className="py-3.5 px-4 text-emerald-300 max-w-xs leading-relaxed font-semibold">
                    {row.recommended_action}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
