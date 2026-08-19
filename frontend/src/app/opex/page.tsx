'use client';

import React, { useEffect, useState } from 'react';
import { useFilters } from '@/context/FilterContext';
import { api } from '@/lib/api';
import { 
  Building2, 
  Target, 
  Briefcase, 
  Layers
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
  Cell 
} from 'recharts';

const OPEX_COLORS = ['#c084fc', '#a855f7', '#7e22ce', '#e9d5ff', '#9333ea'];

export default function OpExPage() {
  const { filters } = useFilters();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await api.getOpEx(filters);
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

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-sky-500/20 border-t-sky-500 rounded-full animate-spin" />
          <p className="text-sm text-slate-400 font-medium">Loading operating expenses & budget targets...</p>
        </div>
      </div>
    );
  }

  const functionBreakdown = data?.function_breakdown || [];
  const budgetRecords = data?.budget_records || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 tracking-tight">Operating Expenses & Budget Targets</h1>
        <p className="text-sm text-slate-400 mt-1">
          Benchmark departmental overhead (SG&A, Operations, Sales, Marketing) and compare corporate performance against `Fact_Budget` targets.
        </p>
      </div>

      {/* OpEx Breakdown Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Horizontal Bar: Function Expense */}
        <div className="glass-panel p-6">
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="h-4 w-4 text-purple-400" />
            <div>
              <h2 className="text-base font-bold text-slate-100">Operating Expenses by Function</h2>
              <p className="text-xs text-slate-400">Total departmental overhead for selected period</p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={functionBreakdown} layout="vertical" margin={{ top: 10, right: 10, left: 30, bottom: 0 }}>
                <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="Expense_Function" stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(val: any) => [formatCurrency(Number(val)), 'Total Expense']}
                />
                <Bar dataKey="Total_Expense" name="Expense" fill="#a855f7" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Donut Chart: Expense Share */}
        <div className="glass-panel p-6">
          <div className="flex items-center gap-2 mb-4">
            <Layers className="h-4 w-4 text-indigo-400" />
            <div>
              <h2 className="text-base font-bold text-slate-100">Expense Distribution Share</h2>
              <p className="text-xs text-slate-400">Proportional function breakdown</p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={functionBreakdown}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="Total_Expense"
                  nameKey="Expense_Function"
                >
                  {functionBreakdown.map((_: any, i: number) => (
                    <Cell key={`cell-${i}`} fill={OPEX_COLORS[i % OPEX_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(val: any) => [formatCurrency(Number(val)), 'Amount']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="flex justify-around mt-2 pt-3 border-t border-slate-800">
            {functionBreakdown.map((f: any, i: number) => (
              <div key={f.Expense_Function} className="text-center">
                <div className="flex items-center justify-center gap-1.5 text-xs text-slate-400">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: OPEX_COLORS[i % OPEX_COLORS.length] }} />
                  <span>{f.Expense_Function}</span>
                </div>
                <div className="text-xs font-semibold text-slate-200 mt-0.5">{formatCurrency(f.Total_Expense)}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Budget vs Actuals Chart */}
      <div className="glass-panel p-6">
        <div className="flex items-center gap-2 mb-4">
          <Target className="h-4 w-4 text-sky-400" />
          <div>
            <h2 className="text-base font-bold text-slate-100">Management Budget Targets by Profit Center</h2>
            <p className="text-xs text-slate-400">Budgeted Revenue vs. Management Forecast Revenue vs. Target Profit</p>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={budgetRecords} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <XAxis dataKey="Profit_Center_Name" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(val: any) => [formatCurrency(Number(val)), '']}
              />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />
              <Bar dataKey="Total_Budget_Revenue" name="Budgeted Revenue" fill="#38bdf8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Total_Forecast_Revenue" name="Management Forecast" fill="#818cf8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Total_Budget_Profit" name="Target Budget Profit" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Profit Center Table */}
      <div className="glass-panel p-6">
        <div className="flex items-center gap-2 mb-4">
          <Briefcase className="h-4 w-4 text-emerald-400" />
          <div>
            <h2 className="text-base font-bold text-slate-100">Profit Center Benchmark Table</h2>
            <p className="text-xs text-slate-400">Detailed financial benchmarks across operational business units</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-slate-400 border-b border-slate-800">
              <tr>
                <th className="pb-2.5 font-semibold">Profit Center</th>
                <th className="pb-2.5 font-semibold">Business Unit</th>
                <th className="pb-2.5 font-semibold text-right">Budget Revenue</th>
                <th className="pb-2.5 font-semibold text-right">Forecast Revenue</th>
                <th className="pb-2.5 font-semibold text-right">Budget Cost</th>
                <th className="pb-2.5 font-semibold text-right">Target Profit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {budgetRecords.map((b: any) => (
                <tr key={b.Profit_Center} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 font-medium text-slate-200">{b.Profit_Center_Name}</td>
                  <td className="py-2.5 text-slate-400">{b.Business_Unit}</td>
                  <td className="py-2.5 text-right font-semibold text-sky-400">{formatCurrency(b.Total_Budget_Revenue)}</td>
                  <td className="py-2.5 text-right text-indigo-300">{formatCurrency(b.Total_Forecast_Revenue)}</td>
                  <td className="py-2.5 text-right text-rose-400">{formatCurrency(b.Total_Budget_Cost)}</td>
                  <td className="py-2.5 text-right font-bold text-emerald-400">{formatCurrency(b.Total_Budget_Profit)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
