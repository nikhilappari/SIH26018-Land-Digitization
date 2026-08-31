import React from 'react';
import { ShieldAlert, CheckCircle2 } from 'lucide-react';

const Navbar = () => {
  const today = new Date().toLocaleDateString('en-IN', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <header className="bg-white border-b border-gray-200 h-16 px-8 flex items-center justify-between shadow-sm sticky top-0 z-30">
      {/* Title */}
      <div className="flex items-center gap-3.5">
        <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 p-0.5 flex items-center justify-center shadow-xs overflow-hidden shrink-0">
          <img src="/landsure-logo.png" alt="LandSure Logo" className="w-full h-full object-contain" />
        </div>
        <div>
          <h2 className="text-base font-bold text-slate-900 leading-tight flex items-center gap-2">
            <span>Land<span className="text-emerald-600">Sure</span></span>
            <span className="text-slate-300 font-normal">|</span>
            <span className="text-slate-800 text-sm font-semibold">Intelligent Land Record Digitization & Validation</span>
          </h2>
        </div>
      </div>

      {/* System Status Indicators */}
      <div className="flex items-center gap-6">
        {/* Connection Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold">
          <CheckCircle2 size={14} className="animate-pulse" />
          <span>System Online</span>
        </div>

        {/* Date Display */}
        <div className="text-xs text-gray-500 font-semibold bg-gray-100 px-3 py-1.5 rounded-md border border-gray-200">
          {today}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
