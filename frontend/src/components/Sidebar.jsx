import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  UploadCloud, 
  ShieldCheck, 
  Search, 
  Map, 
  LogOut,
  UserCheck,
  Building2,
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
    { to: '/', label: 'Dashboard', icon: LayoutDashboard, description: 'Overview & Statistics' },
    { to: '/upload', label: 'Upload Document', icon: UploadCloud, description: 'AI Extraction Pipeline' },
    { to: '/verification', label: 'Review Queue', icon: ShieldCheck, description: 'Officer Verification' },
    { to: '/search', label: 'Registry Search', icon: Search, description: 'Cadastral Database' },
    { to: '/map', label: 'Cadastral Maps', icon: Map, description: 'Spatial Visualizer' },
  ];

  return (
    <aside className="w-64 bg-white min-h-[calc(100vh-4rem)] flex flex-col justify-between border-r border-slate-200/90 shadow-xs shrink-0 select-none">
      <div className="p-4 space-y-4">
        {/* Navigation Menu */}
        <div>
          <div className="px-3 mb-2 flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              Navigation Menu
            </span>
          </div>

          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `group flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                      isActive
                        ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/20'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <div className="flex items-center gap-3">
                        <Icon 
                          size={17} 
                          className={`transition ${
                            isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-700'
                          }`} 
                        />
                        <span>{item.label}</span>
                      </div>
                      <ChevronRight 
                        size={14} 
                        className={`transition ${
                          isActive ? 'text-emerald-200 opacity-100' : 'opacity-0 group-hover:opacity-40 text-slate-400'
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
      <div className="p-4 border-t border-slate-100 space-y-3 bg-slate-50/40">
        <div className="px-2 flex items-center justify-between text-[11px] font-medium text-slate-400">
          <span>Portal Session</span>
          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/60">
            Encrypted
          </span>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold text-rose-600 hover:text-rose-700 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition cursor-pointer"
        >
          <LogOut size={15} />
          <span>Sign Out of Portal</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
