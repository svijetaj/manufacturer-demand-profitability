'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { 
  BookOpen, 
  Database, 
  Cpu, 
  Layers, 
  Code2, 
  Terminal, 
  CheckCircle2,
  Sparkles
} from 'lucide-react';

export default function DocsPage() {
  const [activeTab, setActiveTab] = useState('architecture');
  const [ragData, setRagData] = useState<any>(null);
  const [schemaData, setSchemaData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDocs() {
      setLoading(true);
      try {
        const [rag, schema] = await Promise.all([
          api.getRagMetadata(),
          api.getRagSchema()
        ]);
        setRagData(rag);
        setSchemaData(schema);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadDocs();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 tracking-tight flex items-center gap-2.5">
          <BookOpen className="h-6 w-6 text-sky-400" />
          System Blueprint & RAG Knowledge Documentation
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Technical specifications, physical cost equations, DuckDB semantic schema, and RAG-ready REST metadata.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        {[
          { id: 'architecture', label: 'Architecture & Engine', icon: Cpu },
          { id: 'formulas', label: 'Financial Formulas', icon: Layers },
          { id: 'rag', label: 'RAG Metadata Endpoints', icon: Sparkles },
          { id: 'schema', label: 'Database Schema', icon: Database },
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Architecture */}
      {activeTab === 'architecture' && (
        <div className="space-y-6">
          <div className="glass-panel p-6">
            <h2 className="text-base font-bold text-slate-100 mb-2">Decoupled Next.js + FastAPI + DuckDB Architecture</h2>
            <p className="text-xs text-slate-300 leading-relaxed mb-4">
              The platform pairs an ultra-fast embedded columnar analytics engine (**DuckDB**) with a typed **FastAPI REST backend** and an interactive **Next.js React frontend**.
            </p>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed overflow-x-auto">
              {`Next.js 15 (React 19 / TypeScript / Recharts / TailwindCSS)
         ▲
         │ (HTTP REST / JSON API via port 8000)
         ▼
FastAPI Backend (Python 3.14 / Pydantic v2 / Uvicorn)
  ├─ LightGBM Quantile Decision Trees (P10 / P50 / P90 Volume Bounds)
  ├─ Scikit-Learn Multi-Layer Perceptron (Deep MLP Neural Net)
  ├─ Linear CVP Break-Even & Profit Trajectory Engines
  └─ DuckDB In-Process Analytical OLAP Engine (finance.duckdb)
       ├─ vw_line_margin (Line-level sales, freight, and margins)
       ├─ vw_margin_waterfall (Rollup waterfall stages)
       └─ vw_sku_net_margin_by_basis (Overhead allocation comparisons)`}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="glass-panel p-5">
              <div className="text-xs font-bold text-sky-400 uppercase tracking-wider mb-1">DuckDB Analytics</div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Executes complex joins, window functions, and multi-dimensional group-bys across tens of thousands of rows in sub-15ms.
              </p>
            </div>
            <div className="glass-panel p-5">
              <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">Dual AI Engines</div>
              <p className="text-xs text-slate-300 leading-relaxed">
                LightGBM quantile regression trees capture discrete tabular thresholds; Deep MLPs provide continuous neural forecasting.
              </p>
            </div>
            <div className="glass-panel p-5">
              <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-1">RAG-Ready Design</div>
              <p className="text-xs text-slate-300 leading-relaxed">
                All business semantics and schemas are exposed via `/api/rag/metadata` for immediate LLM agent grounding.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Financial Formulas */}
      {activeTab === 'formulas' && (
        <div className="glass-panel p-6 space-y-4">
          <h2 className="text-base font-bold text-slate-100 mb-2">Standardized ANSI SQL Semantic Formulas</h2>
          
          <div className="space-y-3">
            {ragData?.accounting_formulas && Object.entries(ragData.accounting_formulas).map(([key, formula]) => (
              <div key={key} className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                <span className="text-xs font-semibold text-sky-300 uppercase tracking-wider">{key.replace(/_/g, ' ')}</span>
                <code className="text-xs font-mono text-emerald-400 bg-slate-950 px-2.5 py-1 rounded border border-slate-800/80">
                  {String(formula)}
                </code>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: RAG Metadata */}
      {activeTab === 'rag' && (
        <div className="space-y-6">
          <div className="glass-panel p-6">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="h-4 w-4 text-purple-400" />
              <h2 className="text-base font-bold text-slate-100">Live RAG System Metadata Payload (`/api/rag/metadata`)</h2>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              This structured JSON payload is consumed by LLMs, Vector DBs, or Retrieval-Augmented Generation agents to ground AI responses with audit-grade financial facts.
            </p>
            <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 max-h-96 overflow-y-auto">
              {JSON.stringify(ragData, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Tab 4: Database Schema */}
      {activeTab === 'schema' && (
        <div className="space-y-6">
          <div className="glass-panel p-6">
            <h2 className="text-base font-bold text-slate-100 mb-4">DuckDB Tables & Semantic Views (`finance.duckdb`)</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {schemaData?.tables_and_views?.map((t: any) => (
                <div key={t.table_name} className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold text-slate-200">{t.table_name}</span>
                    <span className="text-[10px] block text-slate-500 font-mono">schema: main</span>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                    t.table_type === 'VIEW' ? 'bg-indigo-500/20 text-indigo-300' : 'bg-emerald-500/20 text-emerald-300'
                  }`}>
                    {t.table_type}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
