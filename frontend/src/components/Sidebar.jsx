import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  UploadCloud, 
  ShieldCheck, 
  Search, 
  Map, 
  LogOut,
  ChevronRight
} from 'lucide-react';
import { authService } from '../services/api';

const Sidebar = () => {
  const navigate = useNavigate();
  const user = authService.getCurrentUser();

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/upload', label: 'Upload Document', icon: UploadCloud },
    { to: '/verification', label: 'Review Queue', icon: ShieldCheck },
    { to: '/search', label: 'Registry Search', icon: Search },
    { to: '/map', label: 'Cadastral Maps', icon: Map },
  ];

  return (
    <aside className="w-68 bg-slate-900 min-h-[calc(100vh-70px)] flex flex-col justify-between border-r border-slate-800 shadow-md shrink-0 select-none">
      <div className="p-4 space-y-4">
        {/* Navigation Menu */}
        <div>
          <div className="px-3 mb-3 flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">
              Navigation Menu
            </span>
          </div>

          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `group flex items-center justify-between px-4 py-3 rounded-xl text-sm font-bold transition-all ${
                      isActive
                        ? 'bg-emerald-600 text-white shadow-md shadow-emerald-950/50 border border-emerald-500'
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/90 font-medium'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <div className="flex items-center gap-3.5">
                        <Icon 
                          size={20} 
                          className={`transition shrink-0 ${
                            isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
                          }`} 
                        />
                        <span className="text-sm font-semibold tracking-tight">{item.label}</span>
                      </div>
                      <ChevronRight 
                        size={16} 
                        className={`transition shrink-0 ${
                          isActive ? 'text-emerald-200 opacity-100' : 'opacity-0 group-hover:opacity-40 text-slate-500'
                        }`} 
                      />
                    </>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer Section & Logout Action */}
      <div className="p-4 border-t border-slate-800/80 space-y-3 bg-slate-950/60">
        <div className="px-2 flex items-center justify-between text-xs font-medium text-slate-400">
          <span>Portal Session</span>
          <span className="text-[11px] font-bold text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded-full border border-emerald-800/60">
            Encrypted
          </span>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2.5 px-4 py-3 rounded-xl text-sm font-bold text-rose-400 hover:text-rose-300 hover:bg-rose-950/40 border border-slate-800 hover:border-rose-900/60 transition cursor-pointer"
        >
          <LogOut size={17} />
          <span>Sign Out of Portal</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
