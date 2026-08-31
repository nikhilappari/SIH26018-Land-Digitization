import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  UploadCloud, 
  ShieldCheck, 
  Search, 
  Map, 
  LogOut,
  Landmark
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
    <aside className="w-64 bg-slate-900 text-white min-h-[calc(100vh-4rem)] flex flex-col justify-between border-r border-slate-800 shrink-0">
      <div>

        {/* User profile brief */}
        {user && (
          <div className="px-6 py-4 bg-slate-900/50 border-b border-slate-800 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-amber-500/20 text-amber-500 font-bold flex items-center justify-center text-sm border border-amber-500/30">
              {user.username ? user.username.substring(0, 2).toUpperCase() : 'RO'}
            </div>
            <div>
              <p className="text-xs text-slate-400">Welcome Back</p>
              <p className="text-sm font-semibold text-slate-200 truncate max-w-[140px]">{user.username || 'Revenue Officer'}</p>
              <span className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded font-medium border border-slate-700">
                {user.role || 'Official'}
              </span>
            </div>
          </div>
        )}

        {/* Navigation Items */}
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-amber-500 text-slate-950 shadow-md font-semibold'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Logout Action */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-red-400 hover:bg-red-950/20 hover:text-red-300 transition-all"
        >
          <LogOut size={18} />
          <span>Logout Portal</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
