'use client';

import React, { useEffect, useState } from 'react';
import { useFilters } from '@/context/FilterContext';
import { api } from '@/lib/api';
import KPICard from '@/components/KPICard';
import { 
  TrendingUp, 
  Scale, 
  Sliders, 
  ShieldAlert, 
  Target, 
  DollarSign,
  Activity
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  ReferenceLine 
} from 'recharts';

export default function PredictProfitPage() {
  const { filters } = useFilters();
  const [horizon, setHorizon] = useState(6);
  const [matInflation, setMatInflation] = useState(0);
  const [laborShift, setLaborShift] = useState(0);
  const [overheadBasis, setOverheadBasis] = useState('Units Produced');

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadProfitForecast() {
      setLoading(true);
      try {
        const res = await api.predictProfitability({
          horizon_months: horizon,
          material_inflation_pct: matInflation,
          labor_shift_pct: laborShift,
          overhead_basis: overheadBasis,
          price_delta_pct: 0,
          demand_shock_pct: 0,
          categories: filters.categories,
          segments: filters.segments,
          regions: filters.regions,
        });
        setData(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadProfitForecast();
  }, [horizon, matInflation, laborShift, overheadBasis, filters]);

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);

  const formatNumber = (val: number) => 
    new Intl.NumberFormat('en-US').format(val);

  const summary = data?.summary || {};
  const cvp = data?.cvp_break_even || {};
  const cvpCurvePoints = data?.cvp_curve_points || [];
  const timeline = data?.monthly_profit_timeline || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 tracking-tight flex items-center gap-2.5">
          <TrendingUp className="h-6 w-6 text-emerald-400" />
          Linear Profitability & CVP Break-Even Modeling
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Predict future net margins using economic linear formulations: Revenue R(Q) = P &times; Q, Total Cost TC(Q) = v &times; Q + F, and Break-Even Volume Q* = F / (P - v).
        </p>
      </div>

      {/* CVP KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <KPICard
          title="Break-Even Volume (Q*)"
          value={`${formatNumber(cvp.break_even_units || 0)} Units`}
          subtitle={`Requires ${formatCurrency(cvp.break_even_revenue || 0)} in Sales`}
          icon={Target}
          accentColor="text-sky-400"
        />
        <KPICard
          title="Margin of Safety"
          value={`${Number(cvp.margin_of_safety_pct || 0).toFixed(1)}%`}
          delta={`${formatNumber(cvp.margin_of_safety_units || 0)} Units buffer`}
          deltaType={Number(cvp.margin_of_safety_pct) > 15 ? 'positive' : 'negative'}
          subtitle="Downside demand protection"
          icon={ShieldAlert}
          accentColor="text-emerald-400"
        />
        <KPICard
          title="Forecasted Net Profit"
          value={formatCurrency(summary.forecast_net_profit || 0)}
          delta={`${Number(summary.net_margin_pct || 0).toFixed(1)}% Net Margin`}
          deltaType={Number(summary.forecast_net_profit) > 0 ? 'positive' : 'negative'}
          subtitle={`vs Baseline: ${summary.delta_profit_pct > 0 ? `+${summary.delta_profit_pct}%` : `${summary.delta_profit_pct}%`}`}
          icon={DollarSign}
          accentColor="text-amber-400"
        />
        <KPICard
          title="Unit Contribution (P - v)"
          value={`$${Number(cvp.cm_per_unit || 0).toFixed(3)} / unit`}
          subtitle={`${Number(cvp.cm_ratio_pct || 0).toFixed(1)}% Contribution Ratio`}
          icon={Scale}
          accentColor="text-indigo-400"
        />
      </div>

      {/* Simulation Controls Panel */}
      <div className="glass-panel p-6">
        <div className="flex items-center gap-2 mb-6">
          <Sliders className="h-4 w-4 text-emerald-400" />
          <h2 className="text-base font-bold text-slate-100">Cost Inflation & Operational Levers</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Horizon */}
          <div>
            <div className="flex justify-between text-xs font-semibold mb-2">
              <span className="text-slate-300">Horizon:</span>
              <span className="text-sky-400">Next {horizon} Months</span>
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {[3, 6, 9].map(h => (
                <button
                  key={h}
                  onClick={() => setHorizon(h)}
                  className={`py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                    horizon === h
                      ? 'bg-sky-500/20 border-sky-500/40 text-sky-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  {h}M
                </button>
              ))}
            </div>
          </div>

          {/* Raw Material Price Shift */}
          <div>
            <div className="flex justify-between text-xs font-semibold mb-2">
              <span className="text-slate-300">Raw Material Shift:</span>
              <span className={matInflation > 0 ? 'text-rose-400' : matInflation < 0 ? 'text-emerald-400' : 'text-slate-400'}>
                {matInflation > 0 ? `+${matInflation}%` : `${matInflation}%`}
              </span>
            </div>
            <input
              type="range"
              min={-20}
              max={20}
              step={1}
              value={matInflation}
              onChange={(e) => setMatInflation(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-rose-500"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>-20% Deflation</span>
              <span>+20% Spike</span>
            </div>
          </div>

          {/* Plant Labor Wage Shift */}
          <div>
            <div className="flex justify-between text-xs font-semibold mb-2">
              <span className="text-slate-300">Plant Labor Wage:</span>
              <span className={laborShift > 0 ? 'text-rose-400' : laborShift < 0 ? 'text-emerald-400' : 'text-slate-400'}>
                {laborShift > 0 ? `+${laborShift}%` : `${laborShift}%`}
              </span>
            </div>
            <input
              type="range"
              min={-15}
              max={15}
              step={1}
              value={laborShift}
              onChange={(e) => setLaborShift(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>-15% Wage Cut</span>
              <span>+15% Overtime</span>
            </div>
          </div>

          {/* Overhead Allocation Basis Switcher */}
          <div>
            <div className="text-xs font-semibold text-slate-300 mb-2">Overhead Absorption:</div>
            <div className="grid grid-cols-2 gap-1.5">
              <button
                onClick={() => setOverheadBasis('Units Produced')}
                className={`py-1.5 px-2 text-[11px] font-semibold rounded-lg border transition-all text-center ${
                  overheadBasis === 'Units Produced'
                    ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                Units Basis
              </button>
              <button
                onClick={() => setOverheadBasis('Machine Runtime Hours')}
                className={`py-1.5 px-2 text-[11px] font-semibold rounded-lg border transition-all text-center ${
                  overheadBasis === 'Machine Runtime Hours'
                    ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                Hours Basis
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive CVP Break-Even Graph */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Activity className="h-4 w-4 text-emerald-400" />
              Cost-Volume-Profit (CVP) Break-Even Analysis Curves
            </h2>
            <p className="text-xs text-slate-400">
              Visualizing Total Revenue $R(Q)$, Total Cost $TC(Q) = vQ + F$, and Net Profit $\Pi(Q)$
            </p>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={cvpCurvePoints} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <XAxis dataKey="units" stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(val: any) => [formatCurrency(Number(val)), '']}
              />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />
              {/* Reference Break-Even Line */}
              {cvp.break_even_units > 0 && (
                <ReferenceLine x={cvp.break_even_units} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Break-Even Q*', fill: '#f59e0b', fontSize: 10, position: 'top' }} />
              )}
              <Line type="monotone" dataKey="revenue" name="Total Revenue R(Q)" stroke="#38bdf8" strokeWidth={2.5} dot={false} />
              <Line type="monotone" dataKey="total_cost" name="Total Cost TC(Q)" stroke="#ef4444" strokeWidth={2.5} dot={false} />
              <Line type="monotone" dataKey="fixed_cost" name="Fixed Overhead F" stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
              <Line type="monotone" dataKey="net_profit" name="Net Profit Π(Q)" stroke="#10b981" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monthly Net Profit Forecast Timeline */}
      <div className="glass-panel p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-4 w-4 text-sky-400" />
          <div>
            <h2 className="text-base font-bold text-slate-100">Forward Monthly Net Profit Trajectory</h2>
            <p className="text-xs text-slate-400">Projected Net Sales and Net Profit after absorbing all fixed plant overhead</p>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={timeline} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <XAxis dataKey="period" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(val: any) => [formatCurrency(Number(val)), '']}
              />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />
              <Bar dataKey="Net_Sales" name="Net Revenue" fill="#0284c7" radius={[4, 4, 0, 0]} opacity={0.8} />
              <Bar dataKey="Allocated_Overhead" name="Fixed Overhead" fill="#f43f5e" radius={[4, 4, 0, 0]} opacity={0.6} />
              <Bar dataKey="Net_Profit" name="Net Profit" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
