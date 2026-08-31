import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  ShieldAlert, 
  ArrowRight,
  TrendingUp,
  Clock,
  ChevronRight
} from 'lucide-react';
import { dashboardService } from '../services/api';
import StatusBadge from '../components/StatusBadge';

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await dashboardService.getStats();
        setStats(data);
      } catch (err) {
        setError("Failed to fetch dashboard metrics.");
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-600 bg-red-50 border border-red-200 rounded-xl max-w-xl mx-auto mt-12">
        <p className="font-semibold">{error}</p>
      </div>
    );
  }

  const kpis = stats?.kpis || {
    total_documents: stats?.total_documents_processed || 0,
    digitized_records: stats?.verified_records_count || 0,
    pending_review: stats?.pending_human_review_count || 0,
    detected_anomalies: 0,
    total_area_acres: stats?.total_area_digitized_acres || 0
  };

  const status_distribution = stats?.status_distribution || {
    "Verified": 0,
    "Pending Review": 0,
    "Low Confidence": 0,
    "Owner Conflict": 0,
    "Area Mismatch": 0,
    "Duplicate": 0
  };

  const recent_activity = stats?.recent_activity || stats?.recent_documents || [];

  const kpiCards = [
    { 
      label: "Total Uploaded Documents", 
      value: kpis.total_documents ?? 0, 
      icon: FileText, 
      color: "bg-blue-50 text-blue-600 border-blue-100", 
      desc: "All historical uploaded files" 
    },
    { 
      label: "Verified Digital Records", 
      value: kpis.digitized_records ?? 0, 
      icon: CheckCircle, 
      color: "bg-emerald-50 text-emerald-600 border-emerald-100", 
      desc: "Digitized records stored in db" 
    },
    { 
      label: "Awaiting Officer Review", 
      value: kpis.pending_review ?? 0, 
      icon: AlertTriangle, 
      color: "bg-amber-50 text-amber-600 border-amber-100", 
      desc: "Requires human-in-the-loop review" 
    },
    { 
      label: "Active Validation Anomalies", 
      value: kpis.detected_anomalies ?? 0, 
      icon: ShieldAlert, 
      color: "bg-rose-50 text-rose-600 border-rose-100", 
      desc: "Unresolved logic flags & conflicts" 
    }
  ];

  // For drawing distribution chart
  const distributionValues = Object.values(status_distribution);
  const maxCount = distributionValues.length > 0 ? Math.max(...distributionValues, 1) : 1;

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-950 p-8 rounded-2xl text-white shadow-lg border border-slate-700 relative overflow-hidden">
        <div className="absolute right-0 top-0 opacity-10 pointer-events-none transform translate-x-12 -translate-y-6">
          <TrendingUp size={240} />
        </div>
        <div className="max-w-2xl relative z-10">
          <h1 className="text-2xl font-bold text-emerald-400 mb-2">LandSure AI Management Console</h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Monitor, validate, and verify historical Indian land record digitizations. 
            All extracted structures are audited, cross-referenced, and checked for anomalies.
          </p>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {kpiCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <div key={index} className={`p-6 rounded-xl border bg-white shadow-sm flex items-start gap-4 transition-all hover:shadow-md`}>
              <div className={`p-3 rounded-lg border ${card.color}`}>
                <Icon size={24} />
              </div>
              <div>
                <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider">{card.label}</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{card.value}</h3>
                <p className="text-xs text-gray-400 mt-1">{card.desc}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Analytics & Queue split grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Status Distribution */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-1">
          <h3 className="text-base font-bold text-slate-800 border-b border-gray-100 pb-3 mb-4">
            Digitization Status Distribution
          </h3>
          <div className="space-y-4">
            {Object.entries(status_distribution).map(([status, count]) => {
              const percentage = Math.round((count / maxCount) * 100);
              let barColor = "bg-blue-600";
              if (status === 'Verified') barColor = "bg-emerald-600";
              else if (status === 'Pending Review') barColor = "bg-amber-500";
              else if (status === 'Low Confidence') barColor = "bg-orange-500";
              else if (['Duplicate', 'Area Mismatch', 'Owner Conflict', 'Error'].includes(status)) barColor = "bg-rose-600";

              return (
                <div key={status} className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs font-semibold">
                    <span className="text-slate-700">{status}</span>
                    <span className="text-slate-900 font-bold">{count}</span>
                  </div>
                  <div className="w-full bg-gray-100 h-2.5 rounded-full overflow-hidden border border-gray-200">
                    <div 
                      className={`${barColor} h-full rounded-full transition-all duration-500`}
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Activity Table */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                <Clock size={16} />
                Recent Digitization Activity
              </h3>
              <button 
                onClick={() => navigate('/search')}
                className="text-xs text-amber-600 hover:text-amber-700 font-bold flex items-center gap-1"
              >
                View Registry
                <ChevronRight size={14} />
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-slate-50 text-slate-600 text-xs font-bold uppercase border-b border-gray-100">
                    <th className="px-6 py-3">File Name</th>
                    <th className="px-6 py-3">Confidence</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Uploaded</th>
                    <th className="px-6 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {recent_activity.map((activity) => (
                    <tr key={activity.id} className="hover:bg-slate-50/50">
                      <td className="px-6 py-4 font-semibold text-slate-800 truncate max-w-[200px]">
                        {activity.filename}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-xs font-bold ${
                          activity.confidence_score >= 80 ? "text-emerald-600" :
                          activity.confidence_score >= 60 ? "text-amber-600" : "text-rose-600"
                        }`}>
                          {activity.confidence_score}%
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={activity.status} />
                      </td>
                      <td className="px-6 py-4 text-xs text-gray-500 font-semibold">
                        {new Date(activity.created_at).toLocaleDateString('en-IN')}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {/* Route verified ones to details, pending ones to verification */}
                        <button
                          onClick={() => {
                            if (activity.status === 'Verified') {
                              // We need the land record id to view details.
                              // So we can search or direct to the document page.
                              // Let's redirect to `/processing/{id}` to see its extracted details
                              navigate(`/processing/${activity.id}`);
                            } else {
                              navigate(`/verify/${activity.id}`);
                            }
                          }}
                          className="text-xs text-slate-800 font-bold bg-slate-100 hover:bg-slate-200 hover:text-slate-900 py-1.5 px-3 rounded-lg border border-slate-200 inline-flex items-center gap-1"
                        >
                          Review
                          <ArrowRight size={12} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {recent_activity.length === 0 && (
                    <tr>
                      <td colSpan="5" className="text-center py-8 text-gray-400 font-medium">
                        No recent activity found. Upload a file to begin.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
          <div className="p-4 bg-slate-50 border-t border-gray-100 text-center rounded-b-xl">
            <p className="text-xs text-slate-500 font-semibold">
              LandSure AI performs validation automatically. Records below 80% confidence or with warnings require verification.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
