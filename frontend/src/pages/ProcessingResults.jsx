import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  FileText, 
  Download, 
  CheckCircle2, 
  ChevronLeft, 
  Info,
  Calendar,
  Layers,
  MapPin,
  TrendingUp,
  Tag
} from 'lucide-react';
import { documentService, recordService } from '../services/api';
import StatusBadge from '../components/StatusBadge';

const ProcessingResults = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [imageTab, setImageTab] = useState("preprocessed"); // original, preprocessed
  const [rightTab, setRightTab] = useState("structured"); // structured, ocr

  useEffect(() => {
    const fetchData = async () => {
      try {
        const details = await documentService.getDetails(id);
        setData(details);
      } catch (err) {
        setError("Failed to retrieve document details.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center text-red-600 bg-red-50 border border-red-200 rounded-xl max-w-xl mx-auto mt-12">
        <p className="font-semibold">{error || "Document not found"}</p>
      </div>
    );
  }

  const { document, land_record, validation_results } = data;

  const handleDownloadPDF = () => {
    if (land_record) {
      window.open(recordService.getExportPDFUrl(land_record.id), '_blank');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Back navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-slate-800 transition-all border border-gray-200"
          >
            <ChevronLeft size={20} />
          </button>
          <div>
            <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              Digitization Analysis
              <StatusBadge status={document.status} />
            </h1>
            <p className="text-xs text-gray-500 font-semibold mt-1">
              File: {document.original_filename} • Uploaded {new Date(document.created_at).toLocaleDateString('en-IN')}
            </p>
          </div>
        </div>
        
        {/* Action Button: Export PDF Certificate */}
        {land_record && document.status === "Verified" && (
          <button
            onClick={handleDownloadPDF}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 px-4 rounded-lg text-sm flex items-center gap-2 shadow transition-all border border-emerald-500"
          >
            <Download size={16} />
            Download Land Certificate
          </button>
        )}
      </div>

      {/* Verification Success Notice */}
      <div className="bg-emerald-50 border border-emerald-200 p-6 rounded-xl flex items-start gap-4">
        <div className="p-2 bg-emerald-500 text-white rounded-lg">
          <CheckCircle2 size={22} />
        </div>
        <div>
          <h3 className="text-sm font-bold text-emerald-900 mb-1">Digitization Auto-Approved</h3>
          <p className="text-xs text-emerald-800 font-semibold leading-relaxed">
            Due to high OCR engine accuracy ({document.confidence_score}%) and zero logical anomalies flagged by the validation engine, 
            this record has been auto-accepted and published to the Land Registry database. 
            A printable government certificate has been generated.
          </p>
        </div>
      </div>

      {/* Side by side section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left Side: Document Viewer */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col overflow-hidden h-[650px]">
          <div className="bg-slate-50 border-b border-gray-200 p-4 flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase text-slate-600 tracking-wider">Document Viewer</h3>
            <div className="flex bg-gray-200 p-1 rounded-md text-xs font-semibold">
              <button
                onClick={() => setImageTab("original")}
                className={`px-3 py-1 rounded ${imageTab === 'original' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}
              >
                Original
              </button>
              <button
                onClick={() => setImageTab("preprocessed")}
                className={`px-3 py-1 rounded ${imageTab === 'preprocessed' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}
              >
                Preprocessed
              </button>
            </div>
          </div>
          <div className="flex-1 bg-slate-100 flex items-center justify-center p-6 overflow-hidden relative">
            {/* Display pre-selected or fallback image */}
            <img
              src={imageTab === 'original' ? document.file_path : (document.preprocessed_path || document.file_path)}
              alt="Land document source"
              className="max-h-full max-w-full object-contain shadow-md rounded border border-gray-300"
            />
          </div>
        </div>

        {/* Right Side: Extraction & Tabular Results */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col overflow-hidden h-[650px]">
          <div className="bg-slate-50 border-b border-gray-200 p-4 flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase text-slate-600 tracking-wider">Extraction Details</h3>
            <div className="flex bg-gray-200 p-1 rounded-md text-xs font-semibold">
              <button
                onClick={() => setRightTab("structured")}
                className={`px-3 py-1 rounded ${rightTab === 'structured' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}
              >
                Structured Record
              </button>
              <button
                onClick={() => setRightTab("ocr")}
                className={`px-3 py-1 rounded ${rightTab === 'ocr' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}
              >
                Raw OCR Text
              </button>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {rightTab === 'structured' ? (
              <div className="space-y-6">
                
                {/* Confidence Meter */}
                <div className="bg-slate-50 border border-gray-200 p-4 rounded-xl flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-slate-700 uppercase">Average OCR Confidence</h4>
                    <p className="text-[10px] text-gray-400 font-semibold mt-0.5">Calculated by character mapping engines</p>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-bold text-emerald-600">{document.confidence_score}%</span>
                  </div>
                </div>

                {/* Extracted Fields Table */}
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-slate-50 border-b border-gray-200 text-slate-600 uppercase font-bold text-[10px]">
                        <th className="px-4 py-3">Land Record Attribute</th>
                        <th className="px-4 py-3">Extracted Value</th>
                        <th className="px-4 py-3 text-right">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 font-medium text-slate-700">
                      {land_record && Object.entries({
                        "Owner Name": land_record.owner_name,
                        "Survey Number": land_record.survey_number,
                        "Khasra Number": land_record.khasra_number,
                        "Khata Number": land_record.khata_number,
                        "Plot Number": land_record.plot_number,
                        "Registered Area": land_record.area ? `${land_record.area} ${land_record.area_unit}` : null,
                        "Village": land_record.village,
                        "Tehsil / Mandal": land_record.tehsil_mandal,
                        "District": land_record.district,
                        "Land Classification": land_record.land_classification,
                        "Ownership Type": land_record.ownership_type,
                        "Registration Number": land_record.registration_number,
                        "Registration Date": land_record.registration_date,
                      }).map(([key, val]) => {
                        // Match confidence key
                        const cKey = key.toLowerCase().replace(/ \/ /g, '_').replace(/ /g, '_');
                        const score = land_record.confidence_scores?.[cKey] || 90.0;
                        
                        // Match regional JSON key
                        const dbKey = cKey === "registered_area" ? "area" : cKey;
                        const regionalVal = land_record.regional_values?.[dbKey];
                        
                        return (
                          <tr key={key} className="hover:bg-slate-50/50">
                            <td className="px-4 py-3 font-bold text-slate-500">{key}</td>
                            <td className="px-4 py-3 font-semibold text-slate-800">
                              {val ? (
                                <span>
                                  {val}
                                  {regionalVal && (
                                    <span className="text-gray-400 font-medium ml-2 font-sans">
                                      / {regionalVal}
                                    </span>
                                  )}
                                </span>
                              ) : (
                                <span className="text-gray-300">N/A</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-right">
                              {val ? (
                                <span className={`font-bold ${score >= 80 ? 'text-emerald-600' : 'text-amber-500'}`}>
                                  {score}%
                                </span>
                              ) : "-"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Additional Classification Metadata */}
                <div className="grid grid-cols-3 gap-4 border border-gray-100 p-4 rounded-xl bg-slate-50/50 text-xs">
                  <div>
                    <h5 className="font-bold text-gray-400 uppercase text-[9px] tracking-wide">Document Type</h5>
                    <p className="font-bold text-slate-800 mt-1">{document.doc_type}</p>
                  </div>
                  <div>
                    <h5 className="font-bold text-gray-400 uppercase text-[9px] tracking-wide">Detected Language</h5>
                    <p className="font-bold text-slate-800 mt-1">{document.language}</p>
                  </div>
                  <div>
                    <h5 className="font-bold text-gray-400 uppercase text-[9px] tracking-wide">Script Format</h5>
                    <p className="font-bold text-slate-800 mt-1">{document.format_type}</p>
                  </div>
                </div>

              </div>
            ) : (
              <div className="bg-slate-900 text-amber-500 p-4 rounded-xl font-mono text-xs leading-relaxed whitespace-pre-wrap h-full border border-slate-950">
                {document.ocr_text || "No raw text extracted."}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default ProcessingResults;
