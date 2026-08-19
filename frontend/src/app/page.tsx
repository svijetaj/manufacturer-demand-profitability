'use client';

import React, { useEffect, useState } from 'react';
import { useFilters } from '@/context/FilterContext';
import { api } from '@/lib/api';
import KPICard from '@/components/KPICard';
import { 
  DollarSign, 
  TrendingUp, 
  Package, 
  Users, 
  Percent, 
  ShieldCheck,
  ShoppingBag,
  Award
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  ComposedChart, 
  Bar, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';

const COLORS = ['#38bdf8', '#818cf8', '#34d399', '#f472b6', '#fbbf24', '#a78bfa'];

export default function OverviewPage() {
  const { filters } = useFilters();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getOverview(filters);
        setData(res);
      } catch (err: any) {
        console.error(err);
        setError(err.message || 'Failed to load overview data.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [filters]);

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);

  const formatNumber = (val: number) => 
    new Intl.NumberFormat('en-US').format(val);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-sky-500/20 border-t-sky-500 rounded-full animate-spin" />
          <p className="text-sm text-slate-400 font-medium">Querying DuckDB semantic layer...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300">
        <h3 className="font-semibold text-base mb-1">Error Loading Data</h3>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  const kpis = data?.kpis || {};
  const monthlyTrend = data?.monthly_trend || [];
  const regionalShare = data?.regional_share || [];
  const topProducts = data?.top_products || [];
  const topCustomers = data?.top_customers || [];

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 tracking-tight">Executive Overview</h1>
        <p className="text-sm text-slate-400 mt-1">
          High-level corporate KPIs, realized revenue trends, and pocket contribution margins from the unified ANSI SQL semantic layer.
        </p>
      </div>

      {/* Primary KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <KPICard
          title="Gross Revenue"
          value={formatCurrency(kpis.Total_Gross_Sales || 0)}
          subtitle={`${formatNumber(kpis.Total_Units || 0)} Units Sold`}
          icon={DollarSign}
          accentColor="text-sky-400"
        />
        <KPICard
          title="Net Realized Sales"
          value={formatCurrency(kpis.Total_Net_Sales || 0)}
          subtitle={`${formatNumber(kpis.Total_Orders || 0)} Orders Processed`}
          icon={TrendingUp}
          accentColor="text-indigo-400"
        />
        <KPICard
          title="Gross Profit"
          value={formatCurrency(kpis.Total_Gross_Profit || 0)}
          delta={`${Number(kpis.Gross_Margin_Pct || 0).toFixed(1)}% Margin`}
          deltaType="positive"
          subtitle="Net of Direct Material & Labor"
          icon={Award}
          accentColor="text-emerald-400"
        />
        <KPICard
          title="Contribution Margin"
          value={formatCurrency(kpis.Total_Contribution_Margin || 0)}
          delta={`${Number(kpis.Pocket_Margin_Pct || 0).toFixed(1)}% Pocket`}
          deltaType="positive"
          subtitle="Net of Outbound Freight & Rebates"
          icon={ShieldCheck}
          accentColor="text-amber-400"
        />
      </div>

      {/* Charts Section: Monthly Trend & Regional Share */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Trend (2 cols) */}
        <div className="lg:col-span-2 glass-panel p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-base font-bold text-slate-100">Monthly Revenue & Margin Trajectory</h2>
              <p className="text-xs text-slate-400">Net Sales bar overlaid with Gross Profit & Contribution Margin lines</p>
            </div>
          </div>

          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={monthlyTrend} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <XAxis 
                  dataKey="Year_Month" 
                  stroke="#64748b" 
                  fontSize={11} 
                  tickLine={false} 
                />
                <YAxis 
                  stroke="#64748b" 
                  fontSize={11} 
                  tickLine={false}
                  tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} 
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(value: any) => [formatCurrency(Number(value)), '']}
                />
                <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="Net_Sales" name="Net Sales" fill="#0284c7" radius={[4, 4, 0, 0]} opacity={0.85} />
                <Line type="monotone" dataKey="Gross_Profit" name="Gross Profit" stroke="#10b981" strokeWidth={2.5} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="Contribution_Margin" name="Contribution Margin" stroke="#f59e0b" strokeWidth={2.5} strokeDasharray="4 4" dot={{ r: 3 }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Regional Share (1 col) */}
        <div className="glass-panel p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-100">Regional Revenue Share</h2>
            <p className="text-xs text-slate-400 mb-4">Geographic sales distribution</p>
            
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={regionalShare}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                    dataKey="Net_Sales"
                    nameKey="Sales_Region"
                  >
                    {regionalShare.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    formatter={(value: any) => [formatCurrency(Number(value)), 'Revenue']}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="space-y-2 mt-4 pt-4 border-t border-slate-800/80">
            {regionalShare.map((reg: any, i: number) => (
              <div key={reg.Sales_Region} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span className="text-slate-300 font-medium">{reg.Sales_Region}</span>
                </div>
                <span className="text-slate-200 font-semibold">{formatCurrency(reg.Net_Sales)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top 5 Products & Top 5 Customers Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <div className="glass-panel p-6">
          <div className="flex items-center gap-2 mb-4">
            <ShoppingBag className="h-4 w-4 text-sky-400" />
            <h2 className="text-base font-bold text-slate-100">Top 5 Products by Revenue</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="pb-2.5 font-semibold">Product SKU</th>
                  <th className="pb-2.5 font-semibold">Category</th>
                  <th className="pb-2.5 font-semibold text-right">Units</th>
                  <th className="pb-2.5 font-semibold text-right">Net Sales</th>
                  <th className="pb-2.5 font-semibold text-right">Margin %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {topProducts.map((p: any) => (
                  <tr key={p.Product_Name} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2.5 font-medium text-slate-200">{p.Product_Name}</td>
                    <td className="py-2.5 text-slate-400">{p.Product_Category}</td>
                    <td className="py-2.5 text-right text-slate-300">{formatNumber(p.Units_Sold)}</td>
                    <td className="py-2.5 text-right font-semibold text-sky-400">{formatCurrency(p.Net_Sales)}</td>
                    <td className="py-2.5 text-right text-emerald-400 font-medium">{Number(p.Gross_Margin_Pct).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Customers */}
        <div className="glass-panel p-6">
          <div className="flex items-center gap-2 mb-4">
            <Users className="h-4 w-4 text-indigo-400" />
            <h2 className="text-base font-bold text-slate-100">Top 5 Customer Accounts</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="pb-2.5 font-semibold">Account Name</th>
                  <th className="pb-2.5 font-semibold">Segment</th>
                  <th className="pb-2.5 font-semibold text-right">Net Revenue</th>
                  <th className="pb-2.5 font-semibold text-right">Contribution</th>
                  <th className="pb-2.5 font-semibold text-right">Pocket %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {topCustomers.map((c: any) => (
                  <tr key={c.Customer_Name} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2.5 font-medium text-slate-200">{c.Customer_Name}</td>
                    <td className="py-2.5 text-slate-400">{c.Customer_Segment}</td>
                    <td className="py-2.5 text-right font-semibold text-indigo-400">{formatCurrency(c.Net_Sales)}</td>
                    <td className="py-2.5 text-right text-slate-300">{formatCurrency(c.Contribution_Margin)}</td>
                    <td className="py-2.5 text-right text-amber-400 font-medium">{Number(c.Pocket_Margin_Pct).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
