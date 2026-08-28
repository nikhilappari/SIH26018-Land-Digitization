import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  ArrowRight, 
  HelpCircle,
  AlertTriangle,
  Users,
  Scale,
  Copy
} from 'lucide-react';
import { verificationService } from '../services/api';
import StatusBadge from '../components/StatusBadge';

const VerificationQueue = () => {
  const navigate = useNavigate();
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchQueue = async () => {
      try {
        const data = await verificationService.getPendingList();
        setQueue(data);
      } catch (err) {
        setError("Failed to fetch pending review records.");
      } finally {
        setLoading(false);
      }
    };
    fetchQueue();
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <ShieldCheck className="text-amber-500" />
          Officer Verification Queue
        </h1>
        <p className="text-xs text-gray-500 font-semibold mt-1">
          Review documents flagged with low confidence, duplicate entries, area mismatches, or ownership conflicts.
        </p>
      </div>

      {/* Queue Table Card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-700">
            Awaiting Review Items ({queue.length})
          </h3>
          <span className="text-xs text-slate-400 font-semibold">
            Action: Click Review to open side-by-side verification console.
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="bg-slate-50 text-slate-600 text-xs font-bold uppercase border-b border-gray-100">
                <th className="px-6 py-4">Uploaded File</th>
                <th className="px-6 py-4">Audit Status</th>
                <th className="px-6 py-4">Survey / Khata</th>
                <th className="px-6 py-4">Staged Owner Name</th>
                <th className="px-6 py-4">Anomalies</th>
                <th className="px-6 py-4 text-right">Review Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-slate-700 font-medium">
              {queue.map((item) => (
                <tr key={item.document_id} className="hover:bg-slate-50/50">
                  <td className="px-6 py-4 truncate max-w-[220px]">
                    <div className="font-semibold text-slate-800">{item.original_filename}</div>
                    <div className="text-[10px] text-gray-400 font-semibold mt-0.5">
                      Uploaded {new Date(item.created_at).toLocaleDateString('en-IN')}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={item.status} />
                  </td>
                  <td className="px-6 py-4 text-xs font-mono font-semibold">
                    {item.land_record?.survey_number || "N/A"} / Khata {item.land_record?.khata_number || "N/A"}
                  </td>
                  <td className="px-6 py-4 text-slate-800">
                    {item.land_record?.owner_name || <span className="text-gray-300">N/A</span>}
                  </td>
                  <td className="px-6 py-4">
                    {item.anomalies_count > 0 ? (
                      <span className="inline-flex items-center gap-1 text-xs text-rose-600 font-bold bg-rose-50 border border-rose-100 px-2 py-0.5 rounded">
                        <AlertTriangle size={12} />
                        {item.anomalies_count} Flagged
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">None</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => navigate(`/verify/${item.document_id}`)}
                      className="bg-amber-500 hover:bg-amber-600 hover:text-slate-950 font-bold text-slate-900 py-1.5 px-3 rounded-lg text-xs border border-amber-400 inline-flex items-center gap-1.5 shadow-sm transition-all"
                    >
                      <span>Open Review</span>
                      <ArrowRight size={12} />
                    </button>
                  </td>
                </tr>
              ))}
              {queue.length === 0 && (
                <tr>
                  <td colSpan="6" className="text-center py-12 text-gray-400 font-medium">
                    Excellent! The verification queue is currently empty.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default VerificationQueue;
