import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search as SearchIcon, 
  Download, 
  MapPin, 
  Eye, 
  Filter,
  RefreshCw,
  Database
} from 'lucide-react';
import { recordService } from '../services/api';
import StatusBadge from '../components/StatusBadge';

const Search = () => {
  const navigate = useNavigate();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Filter states
  const [filters, setFilters] = useState({
    owner_name: "",
    survey_number: "",
    khata_number: "",
    village: "",
    tehsil_mandal: "",
    district: "",
    verification_status: ""
  });

  const handleInputChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const fetchResults = async (activeFilters = {}) => {
    setLoading(true);
    try {
      // Remove empty parameters
      const params = {};
      Object.entries(activeFilters).forEach(([k, v]) => {
        if (v) params[k] = v;
      });
      const data = await recordService.search(params);
      setResults(data);
    } catch (err) {
      console.error("Failed to query registry:", err);
    } finally {
      setLoading(false);
    }
  };

  // Run initial search on mount
  useEffect(() => {
    fetchResults();
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchResults(filters);
  };

  const handleReset = () => {
    const defaultFilters = {
      owner_name: "",
      survey_number: "",
      khata_number: "",
      village: "",
      tehsil_mandal: "",
      district: "",
      verification_status: ""
    };
    setFilters(defaultFilters);
    fetchResults(defaultFilters);
  };

  const handleExportCSV = () => {
    // Download directly via window trigger
    window.open(recordService.getExportCSVUrl(), '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Title & Export bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Database className="text-govteal-700" />
            Registry Search Database
          </h1>
          <p className="text-xs text-gray-500 font-semibold mt-1">
            Query published and verified land record digitizations. Apply filters to narrow results.
          </p>
        </div>
        
        <button
          onClick={handleExportCSV}
          className="bg-white hover:bg-slate-50 text-slate-800 font-bold py-2 px-4 rounded-lg text-sm flex items-center gap-2 shadow-sm transition-all border border-slate-200"
        >
          <Download size={16} />
          Export Registry (CSV)
        </button>
      </div>

      {/* Filter panel */}
      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Owner Name */}
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Owner Name</label>
              <input
                type="text"
                value={filters.owner_name}
                onChange={(e) => handleInputChange("owner_name", e.target.value)}
                placeholder="e.g. Kondru Ramu"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:ring-1 focus:ring-amber-500 outline-none text-xs font-semibold text-slate-800"
              />
            </div>

            {/* Survey Number */}
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Survey Number</label>
              <input
                type="text"
                value={filters.survey_number}
                onChange={(e) => handleInputChange("survey_number", e.target.value)}
                placeholder="e.g. 145/3A"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:ring-1 focus:ring-amber-500 outline-none text-xs font-semibold text-slate-800"
              />
            </div>

            {/* Khata Number */}
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Khata Number</label>
              <input
                type="text"
                value={filters.khata_number}
                onChange={(e) => handleInputChange("khata_number", e.target.value)}
                placeholder="e.g. 412"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:ring-1 focus:ring-amber-500 outline-none text-xs font-semibold text-slate-800"
              />
            </div>

            {/* Verification Status */}
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Verification Status</label>
              <select
                value={filters.verification_status}
                onChange={(e) => handleInputChange("verification_status", e.target.value)}
                className="w-full px-2 py-2 bg-white rounded-lg border border-slate-300 focus:ring-1 focus:ring-amber-500 outline-none text-xs font-semibold text-slate-800"
              >
                <option value="">All Statuses</option>
                <option value="Verified">Verified</option>
                <option value="Pending">Pending</option>
                <option value="Rejected">Rejected</option>
              </select>
            </div>

            {/* District */}
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">District</label>
              <input
                type="text"
                value={filters.district}
                onChange={(e) => handleInputChange("district", e.target.value)}
                placeholder="e.g. West Godavari"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:ring-1 focus:ring-amber-500 outline-none text-xs font-semibold text-slate-800"
              />
            </div>

            {/* Tehsil/Mandal */}
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Tehsil / Mandal</label>
              <input
                type="text"
                value={filters.tehsil_mandal}
                onChange={(e) => handleInputChange("tehsil_mandal", e.target.value)}
                placeholder="e.g. Pedapadu"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:ring-1 focus:ring-amber-500 outline-none text-xs font-semibold text-slate-800"
              />
            </div>

            {/* Village */}
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1">Village</label>
              <input
                type="text"
                value={filters.village}
                onChange={(e) => handleInputChange("village", e.target.value)}
                placeholder="e.g. Krishnapuram"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:ring-1 focus:ring-amber-500 outline-none text-xs font-semibold text-slate-800"
              />
            </div>

            {/* Actions */}
            <div className="flex items-end gap-2">
              <button
                type="button"
                onClick={handleReset}
                className="flex-1 bg-gray-100 hover:bg-gray-200 text-slate-800 font-bold py-2 px-3 rounded-lg text-xs border border-gray-200 flex items-center justify-center gap-1.5 transition-all"
              >
                <RefreshCw size={14} />
                Reset
              </button>
              <button
                type="submit"
                className="flex-1 bg-slate-900 hover:bg-slate-950 text-amber-500 font-bold py-2 px-3 rounded-lg text-xs border border-slate-800 hover:border-amber-500 flex items-center justify-center gap-1.5 shadow transition-all"
              >
                <SearchIcon size={14} />
                Search
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Results grid */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-20 text-center flex flex-col items-center justify-center gap-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
            <p className="text-xs text-gray-500 font-semibold">Running registry search query...</p>
          </div>
        ) : (
          <div>
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-700">
                QueryResult Entries ({results.length})
              </h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-slate-50 text-slate-600 text-xs font-bold uppercase border-b border-gray-100">
                    <th className="px-6 py-4">Record ID</th>
                    <th className="px-6 py-4">Owner Name</th>
                    <th className="px-6 py-4">Survey & Plot</th>
                    <th className="px-6 py-4">Area/Extent</th>
                    <th className="px-6 py-4">Location (V/M/D)</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-right">Registry File</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 text-slate-700 font-medium">
                  {results.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50/50">
                      <td className="px-6 py-4 font-bold text-slate-900 text-xs">
                        DIG-LR-{String(r.id).padStart(6, '0')}
                      </td>
                      <td className="px-6 py-4 font-bold text-slate-800">
                        {r.owner_name || <span className="text-gray-300">N/A</span>}
                      </td>
                      <td className="px-6 py-4 text-xs font-mono font-bold">
                        {r.survey_number || "N/A"} {r.plot_number ? `/ Plot ${r.plot_number}` : ""}
                      </td>
                      <td className="px-6 py-4 text-xs">
                        {r.area !== null ? `${r.area} ${r.area_unit}` : "N/A"}
                      </td>
                      <td className="px-6 py-4 text-xs font-semibold">
                        <div className="flex items-center gap-1 text-slate-500">
                          <MapPin size={12} className="text-slate-400" />
                          <span>
                            {r.village}, {r.tehsil_mandal}, {r.district}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-xs">
                        {/* LandRecord verification_status map to badges */}
                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          r.verification_status === 'Verified' 
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : r.verification_status === 'Rejected'
                              ? 'bg-red-50 text-red-700 border-red-200'
                              : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}>
                          {r.verification_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => navigate(`/details/${r.id}`)}
                          className="bg-slate-100 hover:bg-slate-200 text-slate-800 hover:text-slate-900 font-bold py-1.5 px-3 rounded-lg text-xs border border-slate-200 inline-flex items-center gap-1.5 shadow-sm transition-all"
                        >
                          <Eye size={12} />
                          <span>View File</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                  {results.length === 0 && (
                    <tr>
                      <td colSpan="7" className="text-center py-12 text-gray-400 font-medium">
                        No matches found in registry database.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;
