/**
 * Typed API Client for FastAPI backend.
 */

const DEFAULT_PROD_API = 'https://meridian-finance-api.onrender.com';
const API_BASE = 
  process.env.NEXT_PUBLIC_API_URL || 
  (typeof window !== 'undefined' && !window.location.hostname.includes('localhost')
    ? DEFAULT_PROD_API
    : 'http://localhost:8000');

export interface FilterParams {
  startDate?: string;
  endDate?: string;
  categories?: string[];
  segments?: string[];
  regions?: string[];
}

function buildQueryString(params?: FilterParams & Record<string, any>): string {
  if (!params) return '';
  const searchParams = new URLSearchParams();

  if (params.startDate) searchParams.append('start_date', params.startDate);
  if (params.endDate) searchParams.append('end_date', params.endDate);
  if (params.categories) params.categories.forEach(c => searchParams.append('categories', c));
  if (params.segments) params.segments.forEach(s => searchParams.append('segments', s));
  if (params.regions) params.regions.forEach(r => searchParams.append('regions', r));

  // Add any extra scalar params
  Object.keys(params).forEach(key => {
    if (!['startDate', 'endDate', 'categories', 'segments', 'regions'].includes(key) && params[key] !== undefined) {
      searchParams.append(key, String(params[key]));
    }
  });

  const str = searchParams.toString();
  return str ? `?${str}` : '';
}

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

export const api = {
  getFilters: () => fetchApi<any>('/api/filters'),
  getOverview: (filters?: FilterParams) => fetchApi<any>(`/api/overview${buildQueryString(filters)}`),
  getDemand: (filters?: FilterParams, granularity: string = 'Monthly') => 
    fetchApi<any>(`/api/demand${buildQueryString({ ...filters, granularity })}`),
  getMargins: (filters?: FilterParams) => fetchApi<any>(`/api/margins${buildQueryString(filters)}`),
  getOpEx: (filters?: FilterParams) => fetchApi<any>(`/api/opex${buildQueryString(filters)}`),
  predictDemand: (payload: any) => fetchApi<any>('/api/predict/demand', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  predictProfitability: (payload: any) => fetchApi<any>('/api/predict/profitability', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  getRagMetadata: () => fetchApi<any>('/api/rag/metadata'),
  getRagSchema: () => fetchApi<any>('/api/rag/schema'),
  getVariancePeriods: () => fetchApi<any>('/api/variance/periods'),
  getVariance: (periodA?: string, periodB?: string, filters?: FilterParams) => 
    fetchApi<any>(`/api/variance${buildQueryString({ ...filters, period_a: periodA, period_b: periodB })}`),
  getAnomalySummary: () => fetchApi<any>('/api/anomaly/summary'),
  getAnomalyItems: (category?: string, severity?: string) => 
    fetchApi<any>(`/api/anomaly/items${buildQueryString({ category, severity })}`),
};
