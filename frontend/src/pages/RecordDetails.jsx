import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ChevronLeft, 
  Download, 
  History, 
  FileText, 
  MapPin, 
  Calendar,
  Landmark,
  Scale
} from 'lucide-react';
import { recordService, verificationService } from '../services/api';

const RecordDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [record, setRecord] = useState(null);
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const recData = await recordService.getRecordDetails(id);
        setRecord(recData);
        
        // Fetch audit logs
        const auditData = await verificationService.getAudits(id);
        setAudits(auditData);
      } catch (err) {
        setError("Failed to retrieve land record details.");
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="p-8 text-center text-red-600 bg-red-50 border border-red-200 rounded-xl max-w-xl mx-auto mt-12">
        <p className="font-semibold">{error || "Record not found."}</p>
      </div>
    );
  }

  const handleDownloadPDF = () => {
    window.open(recordService.getExportPDFUrl(record.id), '_blank');
  };

  const getBilingualValue = (field, englishVal) => {
    if (!englishVal) return "N/A";
    const regVal = record.regional_values?.[field];
    return regVal ? `${englishVal} / ${regVal}` : englishVal;
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/search')}
            className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-slate-800 transition-all border border-gray-200"
          >
            <ChevronLeft size={20} />
          </button>
          <div>
            <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              Land Record: DIG-LR-{String(record.id).padStart(6, '0')}
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border bg-emerald-50 text-emerald-700 border-emerald-200`}>
                {record.verification_status.toUpperCase()}
              </span>
            </h1>
            <p className="text-xs text-gray-500 font-semibold mt-1">
              Registered Owner: {record.owner_name} • Digitized on {new Date(record.created_at).toLocaleDateString('en-IN')}
            </p>
          </div>
        </div>

        <button
          onClick={handleDownloadPDF}
          className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 px-4 rounded-lg text-sm flex items-center gap-2 shadow transition-all border border-emerald-500"
        >
          <Download size={16} />
          Download Certificate (PDF)
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Land Property Specifications Column */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-6">
            <h3 className="text-base font-bold text-slate-800 border-b border-gray-100 pb-3 flex items-center gap-2">
              <Landmark size={18} className="text-slate-500" />
              Property Specifications
            </h3>

            {/* Structured specifications display */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 text-xs font-medium">
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-slate-500 font-bold">Pattadar / Owner Name</span>
                <span className="text-slate-900 font-bold">{getBilingualValue("owner_name", record.owner_name)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-slate-500 font-bold">Survey Number</span>
                <span className="text-slate-900 font-bold">{getBilingualValue("survey_number", record.survey_number)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-slate-500 font-bold">Khasra Number</span>
                <span className="text-slate-900 font-bold">{getBilingualValue("khasra_number", record.khasra_number)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-slate-500 font-bold">Khata Number</span>
                <span className="text-slate-900 font-bold">{getBilingualValue("khata_number", record.khata_number)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-slate-500 font-bold">Plot Number</span>
                <span className="text-slate-900 font-bold">{getBilingualValue("plot_number", record.plot_number)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-slate-500 font-bold">Total Registered Area</span>
                <span className="text-slate-900 font-bold">{getBilingualValue("area", record.area !== null ? `${record.area} ${record.area_unit}` : "")}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-slate-500 font-bold">Land Classification</span>
                <span className="text-slate-900 font-bold">{getBilingualValue("land_classification", record.land_classification)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-slate-500 font-bold">Ownership Type</span>
                <span className="text-slate-900 font-bold">{getBilingualValue("ownership_type", record.ownership_type)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-slate-500 font-bold">Mutation Reference</span>
                <span className="text-slate-900 font-bold">{getBilingualValue("mutation_number", record.mutation_number)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-slate-500 font-bold">Registration Number</span>
                <span className="text-slate-900 font-bold">{getBilingualValue("registration_number", record.registration_number)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100 md:col-span-2">
                <span className="text-slate-500 font-bold">Registration Date</span>
                <span className="text-slate-900 font-bold">{getBilingualValue("registration_date", record.registration_date)}</span>
              </div>
            </div>
          </div>

          {/* Audit Logs Log Table */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-gray-100 flex items-center gap-2">
              <History size={18} className="text-slate-500" />
              <h3 className="text-base font-bold text-slate-800">
                Verification Modifications & Audit Log
              </h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-semibold">
                <thead>
                  <tr className="bg-slate-50 text-slate-600 text-[10px] font-bold uppercase border-b border-gray-100">
                    <th className="px-6 py-4">Modified Field</th>
                    <th className="px-6 py-4">Old Staged Value</th>
                    <th className="px-6 py-4">New Verified Value</th>
                    <th className="px-6 py-4">Audited User</th>
                    <th className="px-6 py-4 text-right">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 text-slate-700">
                  {audits.map((a) => (
                    <tr key={a.id} className="hover:bg-slate-50/50">
                      <td className="px-6 py-4 font-bold text-slate-800">
                        {a.field_name}
                      </td>
                      <td className="px-6 py-4 text-rose-600 line-through">
                        {a.old_value || "None"}
                      </td>
                      <td className="px-6 py-4 text-emerald-600 font-bold">
                        {a.new_value || "None"}
                      </td>
                      <td className="px-6 py-4 text-slate-500 font-bold">
                        {a.user_username}
                      </td>
                      <td className="px-6 py-4 text-right text-gray-400 font-bold">
                        {new Date(a.timestamp).toLocaleString('en-IN')}
                      </td>
                    </tr>
                  ))}
                  {audits.length === 0 && (
                    <tr>
                      <td colSpan="5" className="text-center py-8 text-gray-400 font-medium">
                        No manual edits have been logged for this record.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Location & Metadata Panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase text-slate-500 tracking-wider">Location Hierarchy</h3>
            
            <div className="space-y-4 font-medium text-xs">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-start gap-3">
                <MapPin size={16} className="text-slate-400 mt-0.5" />
                <div>
                  <div className="text-[10px] text-gray-400 font-bold uppercase">District Boundary</div>
                  <div className="font-bold text-slate-800 mt-0.5">{record.district}</div>
                </div>
              </div>
              
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-start gap-3">
                <MapPin size={16} className="text-slate-400 mt-0.5" />
                <div>
                  <div className="text-[10px] text-gray-400 font-bold uppercase">Tehsil / Mandal Office</div>
                  <div className="font-bold text-slate-800 mt-0.5">{record.tehsil_mandal}</div>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-start gap-3">
                <MapPin size={16} className="text-slate-400 mt-0.5" />
                <div>
                  <div className="text-[10px] text-gray-400 font-bold uppercase">Revenue Village Area</div>
                  <div className="font-bold text-slate-800 mt-0.5">{record.village}</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Back Action link */}
          <button
            onClick={() => {
              if (record.document_id) {
                navigate(`/processing/${record.document_id}`);
              }
            }}
            className="w-full flex items-center justify-center gap-2 bg-slate-50 hover:bg-slate-100 text-slate-700 py-3 rounded-lg border border-slate-200 text-xs font-bold transition-all shadow-sm"
          >
            <FileText size={14} />
            Inspect Original Scanning Result
          </button>
        </div>
      </div>
    </div>
  );
};

export default RecordDetails;
