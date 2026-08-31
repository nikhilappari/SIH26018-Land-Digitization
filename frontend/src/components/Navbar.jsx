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
      <div className="flex items-center gap-3">
        <img 
          src="/landsure-logo-transparent.png" 
          alt="LandSure" 
          className="h-8 w-auto object-contain" 
        />
        <div className="h-5 w-px bg-slate-200 hidden sm:block"></div>
        <h2 className="text-xs sm:text-sm font-semibold text-slate-700 leading-tight hidden sm:block">
          Intelligent Land Record Digitization & Validation
        </h2>
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
