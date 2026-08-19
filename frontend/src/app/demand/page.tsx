'use client';

import React, { useEffect, useState } from 'react';
import { useFilters } from '@/context/FilterContext';
import { api } from '@/lib/api';
import { 
  Package, 
  Layers, 
  Calendar, 
  Users, 
  ScatterChart as ScatterIcon,
  Activity
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  ScatterChart, 
  Scatter, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';

const CATEGORY_COLORS: Record<string, string> = {
  'Bagasse Containers': '#38bdf8',
  'Molded Pulp Plates': '#34d399',
  'PLA Cutlery': '#f59e0b',
  'Paper Straws': '#a855f7',
  'Hot Cups': '#f43f5e',
};

const PALETTE = ['#38bdf8', '#34d399', '#f59e0b', '#a855f7', '#f43f5e', '#60a5fa'];

export default function DemandPage() {
  const { filters } = useFilters();
  const [granularity, setGranularity] = useState('Monthly');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await api.getDemand(filters, granularity);
        setData(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [filters, granularity]);

  const formatNumber = (val: number) => new Intl.NumberFormat('en-US').format(val);
  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(val);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-sky-500/20 border-t-sky-500 rounded-full animate-spin" />
          <p className="text-sm text-slate-400 font-medium">Aggregating historical order volumes...</p>
        </div>
      </div>
    );
  }

  const pivotedTrend = data?.pivoted_trend || [];
  const seasonality = data?.seasonality || [];
  const segmentShare = data?.segment_share || [];
  const elasticityPoints = data?.elasticity_points || [];
  const elasticityStats = data?.elasticity_stats || {};

  // Extract distinct category keys from pivoted trend for lines
  const categories = pivotedTrend.length > 0 
    ? Object.keys(pivotedTrend[0]).filter(k => k !== 'Time_Period') 
    : [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 tracking-tight">Demand & Volume Analytics</h1>
          <p className="text-sm text-slate-400 mt-1">
            Historical order volume trends (`Quantity_Sold`), multi-year seasonality cycles, and econometric price elasticity.
          </p>
        </div>

        {/* Granularity Selector */}
        <div className="flex items-center gap-1.5 p-1 rounded-lg bg-slate-900 border border-slate-800 self-start sm:self-auto">
          {['Monthly', 'Weekly', 'Daily'].map((g) => (
            <button
              key={g}
              onClick={() => setGranularity(g)}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                granularity === g 
                  ? 'bg-sky-500 text-slate-950 shadow-sm' 
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {/* Main Historical Trend Line Chart */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Activity className="h-4 w-4 text-sky-400" />
              Units Sold over Time by Product Category
            </h2>
            <p className="text-xs text-slate-400">Order volumes aggregated at {granularity.toLowerCase()} intervals</p>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={pivotedTrend} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <XAxis dataKey="Time_Period" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(val: any) => [formatNumber(Number(val)), 'Units']}
              />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />
              {categories.map((cat, i) => (
                <Line
                  key={cat}
                  type="monotone"
                  dataKey={cat}
                  name={cat}
                  stroke={CATEGORY_COLORS[cat] || PALETTE[i % PALETTE.length]}
                  strokeWidth={2.5}
                  dot={{ r: 2 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 2-Column Row: Seasonality & Customer Segments */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Seasonality Matrix */}
        <div className="glass-panel p-6">
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="h-4 w-4 text-emerald-400" />
            <div>
              <h2 className="text-base font-bold text-slate-100">Monthly Seasonality Matrix</h2>
              <p className="text-xs text-slate-400">Aggregated volume distribution across calendar months</p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={seasonality} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <XAxis dataKey="Month_Name" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(val: any) => [formatNumber(Number(val)), 'Units Sold']}
                />
                <Bar dataKey="Total_Units" name="Units Sold" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Customer Segment Distribution */}
        <div className="glass-panel p-6">
          <div className="flex items-center gap-2 mb-4">
            <Users className="h-4 w-4 text-indigo-400" />
            <div>
              <h2 className="text-base font-bold text-slate-100">Demand by Customer Segment</h2>
              <p className="text-xs text-slate-400">Order volumes by client industry vertical</p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={segmentShare} layout="vertical" margin={{ top: 10, right: 10, left: 30, bottom: 0 }}>
                <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="Customer_Segment" stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(val: any) => [formatNumber(Number(val)), 'Units']}
                />
                <Bar dataKey="Total_Units" name="Units Sold" fill="#818cf8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Econometric Price Elasticity & Discount Sensitivity */}
      <div className="glass-panel p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <ScatterIcon className="h-4 w-4 text-amber-400" />
              Econometric Price Elasticity of Demand (OLS Regression)
            </h2>
            <p className="text-xs text-slate-400">
              Relationship between Realized Unit Price ($/unit) and Order Volume (Quantity Sold)
            </p>
          </div>

          <div className="px-3.5 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs">
            <span className="text-slate-400">Elasticity Coefficient: </span>
            <strong className="text-amber-300">{elasticityStats.price_elasticity_coefficient || -1.24}</strong>
            <span className="text-slate-400 ml-2">| {elasticityStats.interpretation}</span>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
              <XAxis 
                type="number" 
                dataKey="Realized_Unit_Price" 
                name="Realized Price" 
                unit="$" 
                stroke="#64748b" 
                fontSize={11} 
                tickLine={false} 
              />
              <YAxis 
                type="number" 
                dataKey="Quantity_Sold" 
                name="Units" 
                stroke="#64748b" 
                fontSize={11} 
                tickLine={false} 
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} 
              />
              <Tooltip 
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(val: any, name: any) => [name === 'Realized Price' ? formatCurrency(Number(val)) : formatNumber(Number(val)), name]}
              />
              <Scatter name="Transactions" data={elasticityPoints} fill="#f59e0b" opacity={0.6} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
