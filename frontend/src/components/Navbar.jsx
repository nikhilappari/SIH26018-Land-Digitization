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
    <header className="bg-white border-b border-gray-200 h-16 px-6 sm:px-8 flex items-center justify-between shadow-xs sticky top-0 z-40 w-full">
      {/* Top Left Brand & Title */}
      <div className="flex items-center gap-5">
        <div className="flex items-center shrink-0">
          <img 
            src="/landsure-logo-transparent.png" 
            alt="LandSure Cadastral Intelligence" 
            className="h-10 w-auto object-contain cursor-pointer" 
          />
        </div>
        <div className="h-6 w-px bg-slate-200 hidden md:block"></div>
        <h2 className="text-xs sm:text-sm font-semibold text-slate-700 leading-tight hidden md:block">
          Intelligent Land Record Digitization & Validation
        </h2>
      </div>

      {/* System Status Indicators */}
      <div className="flex items-center gap-4 sm:gap-6">
        {/* Connection Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold">
          <CheckCircle2 size={14} className="animate-pulse text-emerald-600" />
          <span className="hidden sm:inline">System Online</span>
          <span className="sm:hidden">Online</span>
        </div>

        {/* Date Display */}
        <div className="text-xs text-gray-500 font-semibold bg-gray-100 px-3 py-1.5 rounded-lg border border-gray-200 hidden sm:block">
          {today}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
