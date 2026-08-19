import type { Metadata } from 'next';
import './globals.css';
import { FilterProvider } from '@/context/FilterContext';
import Sidebar from '@/components/Sidebar';
import FilterHeader from '@/components/FilterHeader';

export const metadata: Metadata = {
  title: 'Meridian Corp — Demand & Profitability Intelligence',
  description: 'Enterprise Demand Analytics, Waterfall Margins, LightGBM Forecasts, and Linear CVP Break-Even Intelligence Platform.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080c14] text-slate-100 min-h-screen flex antialiased selection:bg-sky-500/30 selection:text-sky-200">
        <FilterProvider>
          <div className="flex w-full min-h-screen">
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0">
              <FilterHeader />
              <main className="flex-1 p-6 lg:p-8 overflow-y-auto max-w-[1600px] w-full mx-auto">
                {children}
              </main>
            </div>
          </div>
        </FilterProvider>
      </body>
    </html>
  );
}
