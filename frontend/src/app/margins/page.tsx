'use client';

import React, { useEffect, useState } from 'react';
import { useFilters } from '@/context/FilterContext';
import { api } from '@/lib/api';
import { 
  DollarSign, 
  Scale, 
  PieChart as PieIcon, 
  Target, 
  ListTree,
  AlertTriangle
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  PieChart, 
  Pie, 
  Cell, 
  ScatterChart, 
  Scatter 
} from 'recharts';

const PIE_COLORS = ['#f87171', '#fb923c', '#60a5fa'];

export default function MarginsPage() {
  const { filters } = useFilters();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await api.getMargins(filters);
        setData(res);
      } catch (err) {
        console.error(err);
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
          <p className="text-sm text-slate-400 font-medium">Deconstructing financial waterfall & overhead pools...</p>
        </div>
      </div>
    );
  }

  const waterfallItems = data?.waterfall_items || [];
  const overheadSens = data?.overhead_sensitivity || [];
  const costShares = data?.cost_shares || [];
  const customerMatrix = data?.customer_matrix || [];
  const skuMargins = data?.sku_margins || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 tracking-tight">Financial Margins & Waterfall</h1>
        <p className="text-sm text-slate-400 mt-1">
          Deconstruct pocket contribution margins, evaluate human-in-the-loop overhead absorption methods, and pinpoint customer rebate traps.
        </p>
      </div>

      {/* Waterfall Breakdown Chart */}
      <div className="glass-panel p-6">
        <div className="flex items-center gap-2 mb-4">
          <DollarSign className="h-4 w-4 text-sky-400" />
          <div>
            <h2 className="text-base font-bold text-slate-100">Financial Waterfall Breakdown (Gross Sales to Contribution Margin)</h2>
            <p className="text-xs text-slate-400">Step-by-step margin erosion and direct cost absorption</p>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={waterfallItems} margin={{ top: 20, right: 10, left: 10, bottom: 20 }}>
              <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} interval={0} angle={-25} textAnchor="end" />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(val: any) => [formatCurrency(Number(val)), 'Amount']}
              />
              <Bar 
                dataKey="amount" 
                radius={[4, 4, 0, 0]}
              >
                {waterfallItems.map((entry: any, index: number) => {
                  const color = entry.type === 'total' ? '#38bdf8' : (entry.amount < 0 ? '#ef4444' : '#10b981');
                  return <Cell key={`cell-${index}`} fill={color} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Overhead Allocation Sensitivity Section */}
      <div className="glass-panel p-6 border-l-4 border-l-amber-500">
        <div className="flex items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Scale className="h-4 w-4 text-amber-400" />
              Human-in-the-Loop Overhead Allocation Sensitivity
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Plant overhead is maintained unallocated in `Fact_Overhead_Pool`. Comparing <strong>Units Produced Basis</strong> vs. <strong>Machine Hours Basis</strong> reveals true cost reality.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-4">
          <div className="lg:col-span-8 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={overheadSens} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <XAxis dataKey="Product_Category" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(val: any) => [`${Number(val).toFixed(1)}%`, '']}
                />
                <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="net_margin_units_basis" name="Units Produced Basis (%)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="net_margin_hours_basis" name="Machine Hours Basis (%)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="lg:col-span-4 bg-slate-900/60 p-4 rounded-xl border border-slate-800 flex flex-col justify-center space-y-3">
            <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold">
              <AlertTriangle className="h-4 w-4" />
              Executive Key Insight
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Product categories like <strong>Cutlery</strong> and <strong>Hot Cups</strong> require disproportionately longer machine tooling cycles per dollar of revenue.
            </p>
            <p className="text-xs text-slate-400 leading-relaxed">
              Switching from units to machine runtime hours exposes negative pocket margins on low-turnover SKUs.
            </p>
          </div>
        </div>
      </div>

      {/* Direct Cost Shares & Customer Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Direct Cost Driver Shares */}
        <div className="glass-panel p-6">
          <div className="flex items-center gap-2 mb-4">
            <PieIcon className="h-4 w-4 text-rose-400" />
            <div>
              <h2 className="text-base font-bold text-slate-100">Direct Production Cost Shares</h2>
              <p className="text-xs text-slate-400">Material vs. Direct Labor vs. Outbound Delivery Freight</p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={costShares}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                  nameKey="name"
                >
                  {costShares.map((_: any, i: number) => (
                    <Cell key={`cell-${i}`} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(val: any) => [formatCurrency(Number(val)), 'Cost']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="flex justify-around mt-2 pt-3 border-t border-slate-800">
            {costShares.map((c: any, i: number) => (
              <div key={c.name} className="text-center">
                <div className="flex items-center justify-center gap-1.5 text-xs text-slate-400">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS[i] }} />
                  <span>{c.name}</span>
                </div>
                <div className="text-sm font-semibold text-slate-200 mt-0.5">{formatCurrency(c.value)}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Customer Rebate Trap Matrix */}
        <div className="glass-panel p-6">
          <div className="flex items-center gap-2 mb-4">
            <Target className="h-4 w-4 text-emerald-400" />
            <div>
              <h2 className="text-base font-bold text-slate-100">Customer Profitability Matrix (Rebate Trap)</h2>
              <p className="text-xs text-slate-400">Volume vs Pocket Contribution Margin %</p>
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
                <XAxis 
                  type="number" 
                  dataKey="Total_Units" 
                  name="Volume" 
                  stroke="#64748b" 
                  fontSize={11} 
                  tickLine={false} 
                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} 
                />
                <YAxis 
                  type="number" 
                  dataKey="Pocket_Margin_Pct" 
                  name="Pocket Margin" 
                  unit="%" 
                  stroke="#64748b" 
                  fontSize={11} 
                  tickLine={false} 
                />
                <Tooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(val: any, name: any) => [name === 'Pocket Margin' ? `${Number(val).toFixed(1)}%` : formatNumber(Number(val)), name]}
                />
                <Scatter name="Customers" data={customerMatrix} fill="#10b981" opacity={0.7} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Detailed SKU Table */}
      <div className="glass-panel p-6">
        <div className="flex items-center gap-2 mb-4">
          <ListTree className="h-4 w-4 text-sky-400" />
          <div>
            <h2 className="text-base font-bold text-slate-100">SKU & Category Margin Summary</h2>
            <p className="text-xs text-slate-400">Granular line item unit economics</p>
          </div>
        </div>

        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left text-xs">
            <thead className="text-slate-400 border-b border-slate-800 sticky top-0 bg-[#0f172a]">
              <tr>
                <th className="py-2.5 font-semibold">Product SKU</th>
                <th className="py-2.5 font-semibold">Category</th>
                <th className="py-2.5 font-semibold text-right">Units</th>
                <th className="py-2.5 font-semibold text-right">Net Revenue</th>
                <th className="py-2.5 font-semibold text-right">Direct COGS</th>
                <th className="py-2.5 font-semibold text-right">Gross Profit</th>
                <th className="py-2.5 font-semibold text-right">Gross Margin</th>
                <th className="py-2.5 font-semibold text-right">Contribution</th>
                <th className="py-2.5 font-semibold text-right">Pocket Margin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {skuMargins.map((s: any) => (
                <tr key={s.Product_Name} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 font-medium text-slate-200">{s.Product_Name}</td>
                  <td className="py-2.5 text-slate-400">{s.Product_Category}</td>
                  <td className="py-2.5 text-right text-slate-300">{formatNumber(s.Units_Sold)}</td>
                  <td className="py-2.5 text-right font-semibold text-sky-400">{formatCurrency(s.Net_Revenue)}</td>
                  <td className="py-2.5 text-right text-rose-400">{formatCurrency(s.Direct_COGS)}</td>
                  <td className="py-2.5 text-right text-emerald-400">{formatCurrency(s.Gross_Profit)}</td>
                  <td className="py-2.5 text-right text-slate-300 font-medium">{Number(s.Gross_Margin_Pct).toFixed(1)}%</td>
                  <td className="py-2.5 text-right text-amber-400 font-semibold">{formatCurrency(s.Contribution_Margin)}</td>
                  <td className="py-2.5 text-right font-bold text-emerald-400">{Number(s.Pocket_Margin_Pct).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
