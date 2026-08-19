'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, FilterParams } from '@/lib/api';

interface FilterContextType {
  filters: FilterParams;
  availableCategories: string[];
  availableSegments: string[];
  availableRegions: string[];
  dateBounds: { minDate: string; maxDate: string };
  setDateRange: (start: string, end: string) => void;
  toggleCategory: (category: string) => void;
  toggleSegment: (segment: string) => void;
  toggleRegion: (region: string) => void;
  resetFilters: () => void;
  isLoadingFilters: boolean;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export function FilterProvider({ children }: { children: React.ReactNode }) {
  const [filters, setFilters] = useState<FilterParams>({
    startDate: '',
    endDate: '',
    categories: [],
    segments: [],
    regions: [],
  });

  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [availableSegments, setAvailableSegments] = useState<string[]>([]);
  const [availableRegions, setAvailableRegions] = useState<string[]>([]);
  const [dateBounds, setDateBounds] = useState({ minDate: '', maxDate: '' });
  const [isLoadingFilters, setIsLoadingFilters] = useState(true);

  useEffect(() => {
    async function loadInitialFilters() {
      try {
        const data = await api.getFilters();
        if (data?.date_bounds) {
          setDateBounds({
            minDate: data.date_bounds.min_date,
            maxDate: data.date_bounds.max_date,
          });
          setFilters(prev => ({
            ...prev,
            startDate: data.date_bounds.min_date,
            endDate: data.date_bounds.max_date,
          }));
        }
        if (data?.categories) setAvailableCategories(data.categories);
        if (data?.segments) setAvailableSegments(data.segments);
        if (data?.regions) setAvailableRegions(data.regions);
      } catch (err) {
        console.error('Failed to load filter metadata:', err);
      } finally {
        setIsLoadingFilters(false);
      }
    }
    loadInitialFilters();
  }, []);

  const setDateRange = (start: string, end: string) => {
    setFilters(prev => ({ ...prev, startDate: start, endDate: end }));
  };

  const toggleCategory = (category: string) => {
    setFilters(prev => {
      const exists = prev.categories?.includes(category);
      const next = exists
        ? prev.categories?.filter(c => c !== category)
        : [...(prev.categories || []), category];
      return { ...prev, categories: next };
    });
  };

  const toggleSegment = (segment: string) => {
    setFilters(prev => {
      const exists = prev.segments?.includes(segment);
      const next = exists
        ? prev.segments?.filter(s => s !== segment)
        : [...(prev.segments || []), segment];
      return { ...prev, segments: next };
    });
  };

  const toggleRegion = (region: string) => {
    setFilters(prev => {
      const exists = prev.regions?.includes(region);
      const next = exists
        ? prev.regions?.filter(r => r !== region)
        : [...(prev.regions || []), region];
      return { ...prev, regions: next };
    });
  };

  const resetFilters = () => {
    setFilters({
      startDate: dateBounds.minDate,
      endDate: dateBounds.maxDate,
      categories: [],
      segments: [],
      regions: [],
    });
  };

  return (
    <FilterContext.Provider
      value={{
        filters,
        availableCategories,
        availableSegments,
        availableRegions,
        dateBounds,
        setDateRange,
        toggleCategory,
        toggleSegment,
        toggleRegion,
        resetFilters,
        isLoadingFilters,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
}

export function useFilters() {
  const context = useContext(FilterContext);
  if (!context) {
    throw new Error('useFilters must be used within a FilterProvider');
  }
  return context;
}
