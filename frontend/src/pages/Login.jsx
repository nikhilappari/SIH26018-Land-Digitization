import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Landmark, Lock, User, AlertCircle, Loader2 } from 'lucide-react';
import { authService } from '../services/api';

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Redirect if already logged in
  useEffect(() => {
    if (authService.isAuthenticated()) {
      navigate('/', { replace: true });
    }
  }, [navigate]);

  const handleDemoLogin = (demoUser, demoPass) => {
    setUsername(demoUser);
    setPassword(demoPass);
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await authService.login(username, password);
      navigate('/', { replace: true });
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        "Authentication failed. Please verify credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-2xl overflow-hidden border border-slate-200">
        
        {/* Portal Banner Header */}
        <div className="bg-slate-950 p-8 text-center border-b border-slate-800">
          <div className="w-16 h-16 bg-emerald-500 rounded-2xl flex items-center justify-center mx-auto text-slate-950 shadow-md mb-4">
            <Landmark size={36} />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Land<span className="text-emerald-400">Sure</span> Portal</h1>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">
            National Land Records Digitization Platform
          </p>
        </div>

        <div className="p-8">
          <h2 className="text-lg font-bold text-slate-800 mb-6 text-center">
            Officer Authentication Secure Sign-In
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username Input */}
            <div>
              <label className="block text-xs font-bold text-slate-600 uppercase mb-2">Username</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                  <User size={16} />
                </span>
                <input
                  type="text"
                  required
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none text-slate-800 text-sm"
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <label className="block text-xs font-bold text-slate-600 uppercase mb-2">Password</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                  <Lock size={16} />
                </span>
                <input
                  type="password"
                  required
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none text-slate-800 text-sm"
                />
              </div>
            </div>

            {/* Error Notification */}
            {error && (
              <div className="flex items-center gap-2 text-rose-700 bg-rose-50 border border-rose-200 p-3 rounded-lg text-xs font-semibold">
                <AlertCircle size={16} className="shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-slate-900 text-amber-500 hover:bg-slate-950 font-bold py-3 rounded-lg text-sm transition-all shadow flex items-center justify-center gap-2 border border-slate-800 hover:border-amber-500"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Verifying Credentials...</span>
                </>
              ) : (
                <span>Sign In to Portal</span>
              )}
            </button>
          </form>

          {/* Credentials Helper Card */}
          <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-lg text-xs">
            <h4 className="font-bold text-amber-900 uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <AlertCircle size={14} />
              Demonstration Accounts (Click to Fill)
            </h4>
            <div className="space-y-2 text-slate-700">
              <button
                type="button"
                onClick={() => handleDemoLogin('revenue_officer', 'sih2026password')}
                className="w-full text-left p-2 bg-white rounded border border-amber-300 hover:bg-amber-100/50 transition cursor-pointer"
              >
                <span className="font-bold text-slate-900">Official Account:</span>
                <div className="text-[11px] text-slate-600 mt-0.5">
                  User: <code className="bg-slate-100 px-1 py-0.5 rounded font-bold text-amber-800">revenue_officer</code> • Pass: <code className="bg-slate-100 px-1 py-0.5 rounded font-bold text-amber-800">sih2026password</code>
                </div>
              </button>
              
              <button
                type="button"
                onClick={() => handleDemoLogin('admin_sih', 'sih2026admin')}
                className="w-full text-left p-2 bg-white rounded border border-amber-300 hover:bg-amber-100/50 transition cursor-pointer"
              >
                <span className="font-bold text-slate-900">Admin Account:</span>
                <div className="text-[11px] text-slate-600 mt-0.5">
                  User: <code className="bg-slate-100 px-1 py-0.5 rounded font-bold text-amber-800">admin_sih</code> • Pass: <code className="bg-slate-100 px-1 py-0.5 rounded font-bold text-amber-800">sih2026admin</code>
                </div>
              </button>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
};

export default Login;
