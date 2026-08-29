import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ChevronLeft, 
  Check, 
  X, 
  AlertTriangle, 
  HelpCircle,
  Clock,
  Layers,
  Sparkles,
  Info,
  Code,
  FileText,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { documentService, verificationService } from '../services/api';
import StatusBadge from '../components/StatusBadge';

const VerificationWorkspace = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // Image Viewer state
  const [imageTab, setImageTab] = useState("preprocessed");
  
  // Extraction Debug state
  const [showDebugModal, setShowDebugModal] = useState(false);
  const [debugData, setDebugData] = useState(null);
  const [debugLoading, setDebugLoading] = useState(false);

  // Form edit states
  const [formFields, setFormFields] = useState({
    owner_name: "",
    survey_number: "",
    khasra_number: "",
    khata_number: "",
    plot_number: "",
    area: "",
    area_unit: "Acres",
    village: "",
    tehsil_mandal: "",
    district: "",
    land_classification: "",
    ownership_type: "",
    mutation_number: "",
    registration_number: "",
    registration_date: ""
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const details = await documentService.getDetails(id);
        setData(details);
        
        if (details.land_record) {
          const rec = details.land_record;
          setFormFields({
            owner_name: rec.owner_name || "",
            survey_number: rec.survey_number || "",
            khasra_number: rec.khasra_number || "",
            khata_number: rec.khata_number || "",
            plot_number: rec.plot_number || "",
            area: rec.area !== null && rec.area !== undefined ? rec.area.toString() : "",
            area_unit: rec.area_unit || "Acres",
            village: rec.village || "",
            tehsil_mandal: rec.tehsil_mandal || "",
            district: rec.district || "",
            land_classification: rec.land_classification || "",
            ownership_type: rec.ownership_type || "",
            mutation_number: rec.mutation_number || "",
            registration_number: rec.registration_number || "",
            registration_date: rec.registration_date || ""
          });
        }
      } catch (err) {
        setError("Failed to retrieve document verification details.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleOpenDebug = async () => {
    setShowDebugModal(true);
    if (!debugData) {
      setDebugLoading(true);
      try {
        const res = await documentService.getExtractionDebug(id);
        setDebugData(res);
      } catch (err) {
        console.error("Failed to load debug extraction data", err);
      } finally {
        setDebugLoading(false);
      }
    }
  };

  const handleInputChange = (field, value) => {
    setFormFields(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleVerificationDecision = async (approved = true) => {
    try {
      const payload = {
        ...formFields,
        area: formFields.area ? parseFloat(formFields.area) : null
      };

      await verificationService.verifyRecord(data.document.id, payload, approved);
      alert(approved ? "Record approved & updated in registry." : "Record marked as rejected.");
      navigate('/verification');
    } catch (err) {
      alert("Failed to submit verification action: " + (err.response?.data?.detail || err.message));
    }
  };

  const renderFieldConfidenceBadge = (fieldName) => {
    const val = formFields[fieldName];
    const score = data?.land_record?.confidence_scores?.[fieldName];

    if (!val || val.trim() === "") {
      return (
        <span className="text-[9px] font-bold text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
          NOT DETECTED / MANUAL ENTRY
        </span>
      );
    }

    if (score !== undefined && score >= 70) {
      return (
        <span className="text-[9px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
          AI Conf: {score}%
        </span>
      );
    }

    if (score !== undefined && score > 0) {
      return (
        <span className="text-[9px] font-bold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
          Low Conf: {score}%
        </span>
      );
    }

    return null;
  };

  const getFieldStyling = (fieldName) => {
    const val = formFields[fieldName];
    const score = data?.land_record?.confidence_scores?.[fieldName];
    const hasAnomaly = data?.validation_results?.some(v => 
      !v.is_resolved && 
      v.description.toLowerCase().includes(fieldName.replace('_', ' '))
    );

    if (hasAnomaly || (!val && ["owner_name", "survey_number", "area", "village", "district"].includes(fieldName))) {
      return "border-amber-300 focus:border-amber-500 focus:ring-amber-200 bg-amber-50/20";
    }
    if (score !== undefined && score >= 70) {
      return "border-emerald-300 focus:border-emerald-500 focus:ring-emerald-200";
    }
    return "border-slate-300 focus:border-amber-500 focus:ring-amber-200";
  };

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
        <p className="font-semibold">{error || "Verification item not found."}</p>
      </div>
    );
  }

  const { document, land_record, validation_results } = data;

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/verification')}
            className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-slate-800 transition-all border border-gray-200 cursor-pointer"
          >
            <ChevronLeft size={20} />
          </button>
          <div>
            <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              Side-by-Side Human Verification
              <StatusBadge status={document.status} />
            </h1>
            <p className="text-xs text-gray-500 font-semibold mt-1">
              File: {document.original_filename} • Conf: {document.confidence_score}% • Lang: {document.language}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleOpenDebug}
            className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold border border-slate-300 rounded-lg text-xs flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
          >
            <Code size={14} />
            Inspect OCR & Provenance
          </button>
          <button
            onClick={() => handleVerificationDecision(false)}
            className="px-4 py-2 bg-white hover:bg-red-50 text-red-600 font-bold border border-red-200 rounded-lg text-xs flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
          >
            <X size={14} />
            Reject Record
          </button>
          <button
            onClick={() => handleVerificationDecision(true)}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg text-xs flex items-center gap-1.5 shadow transition-all border border-emerald-500 cursor-pointer"
          >
            <Check size={14} />
            Approve & Publish
          </button>
        </div>
      </div>

      {/* Side-by-Side Review Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        
        {/* Left Side: Document Viewer */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col overflow-hidden h-[750px]">
          <div className="bg-slate-50 border-b border-gray-200 p-4 flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase text-slate-600 tracking-wider">Document Viewer</h3>
            <div className="flex bg-gray-200 p-1 rounded-md text-xs font-semibold">
              <button
                onClick={() => setImageTab("original")}
                className={`px-3 py-1 rounded cursor-pointer ${imageTab === 'original' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}
              >
                Original
              </button>
              <button
                onClick={() => setImageTab("preprocessed")}
                className={`px-3 py-1 rounded cursor-pointer ${imageTab === 'preprocessed' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}
              >
                Preprocessed
              </button>
            </div>
          </div>
          <div className="flex-1 bg-slate-100 flex items-center justify-center p-6 overflow-hidden">
            <img
              src={imageTab === 'original' ? document.file_path : (document.preprocessed_path || document.file_path)}
              alt="Source Land Record"
              className="max-h-full max-w-full object-contain shadow-md rounded border border-gray-300"
            />
          </div>
        </div>

        {/* Right Side: Staged Form Editor */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col overflow-hidden h-[750px]">
          <div className="bg-slate-50 border-b border-gray-200 p-4 flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase text-slate-600 tracking-wider">
              Verify Staged Attributes
            </h3>
            <span className="text-[10px] text-slate-400 font-semibold">
              Officer Manual Review Mode
            </span>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            
            {/* Active Validation Warnings alert card */}
            {validation_results.filter(v => !v.is_resolved).length > 0 && (
              <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl space-y-2">
                <h4 className="text-xs font-bold text-amber-900 flex items-center gap-1.5 uppercase">
                  <AlertTriangle size={14} />
                  Pending Review Items ({validation_results.filter(v => !v.is_resolved).length})
                </h4>
                <ul className="list-disc pl-5 text-[11px] text-amber-800 font-semibold space-y-1">
                  {validation_results.filter(v => !v.is_resolved).map((vr) => (
                    <li key={vr.id}>
                      <span className="font-bold">{vr.rule_name}:</span> {vr.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Editing Form fields */}
            <div className="space-y-4">
              
              {/* Primary Location Hierarchy Section */}
              <div className="border border-gray-100 p-4 rounded-xl bg-slate-50/50 space-y-3">
                <h4 className="text-[10px] font-bold uppercase text-slate-400 tracking-wide mb-2">Location Hierarchy</h4>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <label className="block text-[10px] font-bold text-slate-600 uppercase">District</label>
                    </div>
                    <input
                      type="text"
                      placeholder="Enter district"
                      value={formFields.district}
                      onChange={(e) => handleInputChange("district", e.target.value)}
                      className={`w-full px-3 py-1.5 rounded-lg border text-xs font-semibold outline-none ${getFieldStyling("district")}`}
                    />
                    <div className="mt-1">{renderFieldConfidenceBadge("district")}</div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <label className="block text-[10px] font-bold text-slate-600 uppercase">Tehsil / Mandal</label>
                    </div>
                    <input
                      type="text"
                      placeholder="Enter mandal"
                      value={formFields.tehsil_mandal}
                      onChange={(e) => handleInputChange("tehsil_mandal", e.target.value)}
                      className={`w-full px-3 py-1.5 rounded-lg border text-xs font-semibold outline-none ${getFieldStyling("tehsil_mandal")}`}
                    />
                    <div className="mt-1">{renderFieldConfidenceBadge("tehsil_mandal")}</div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <label className="block text-[10px] font-bold text-slate-600 uppercase">Village</label>
                    </div>
                    <input
                      type="text"
                      placeholder="Enter village"
                      value={formFields.village}
                      onChange={(e) => handleInputChange("village", e.target.value)}
                      className={`w-full px-3 py-1.5 rounded-lg border text-xs font-semibold outline-none ${getFieldStyling("village")}`}
                    />
                    <div className="mt-1">{renderFieldConfidenceBadge("village")}</div>
                  </div>
                </div>
              </div>

              {/* General Property details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Owner Name */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-[10px] font-bold text-slate-600 uppercase">Pattadar / Owner Name</label>
                    {renderFieldConfidenceBadge("owner_name")}
                  </div>
                  <input
                    type="text"
                    placeholder="Enter owner name"
                    value={formFields.owner_name}
                    onChange={(e) => handleInputChange("owner_name", e.target.value)}
                    className={`w-full px-3 py-2 rounded-lg border text-xs font-semibold outline-none ${getFieldStyling("owner_name")}`}
                  />
                </div>

                {/* Survey Number */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-[10px] font-bold text-slate-600 uppercase">Survey Number</label>
                    {renderFieldConfidenceBadge("survey_number")}
                  </div>
                  <input
                    type="text"
                    placeholder="e.g. 124/2A"
                    value={formFields.survey_number}
                    onChange={(e) => handleInputChange("survey_number", e.target.value)}
                    className={`w-full px-3 py-2 rounded-lg border text-xs font-semibold outline-none ${getFieldStyling("survey_number")}`}
                  />
                </div>

                {/* Khasra / Khata */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <label className="block text-[10px] font-bold text-slate-600 uppercase">Khasra No</label>
                    </div>
                    <input
                      type="text"
                      value={formFields.khasra_number}
                      onChange={(e) => handleInputChange("khasra_number", e.target.value)}
                      className={`w-full px-3 py-2 rounded-lg border text-xs font-semibold outline-none ${getFieldStyling("khasra_number")}`}
                    />
                    <div className="mt-1">{renderFieldConfidenceBadge("khasra_number")}</div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <label className="block text-[10px] font-bold text-slate-600 uppercase">Khata No</label>
                    </div>
                    <input
                      type="text"
                      value={formFields.khata_number}
                      onChange={(e) => handleInputChange("khata_number", e.target.value)}
                      className={`w-full px-3 py-2 rounded-lg border text-xs font-semibold outline-none ${getFieldStyling("khata_number")}`}
                    />
                    <div className="mt-1">{renderFieldConfidenceBadge("khata_number")}</div>
                  </div>
                </div>

                {/* Plot / Area */}
                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-1">
                    <label className="block text-[10px] font-bold text-slate-600 mb-1 uppercase">Plot No</label>
                    <input
                      type="text"
                      value={formFields.plot_number}
                      onChange={(e) => handleInputChange("plot_number", e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold outline-none"
                    />
                  </div>
                  <div className="col-span-1">
                    <label className="block text-[10px] font-bold text-slate-600 mb-1 uppercase">Area</label>
                    <input
                      type="text"
                      placeholder="e.g. 2.35"
                      value={formFields.area}
                      onChange={(e) => handleInputChange("area", e.target.value)}
                      className={`w-full px-3 py-2 rounded-lg border text-xs font-semibold outline-none ${getFieldStyling("area")}`}
                    />
                  </div>
                  <div className="col-span-1">
                    <label className="block text-[10px] font-bold text-slate-600 mb-1 uppercase">Unit</label>
                    <select
                      value={formFields.area_unit}
                      onChange={(e) => handleInputChange("area_unit", e.target.value)}
                      className="w-full px-2 py-2 bg-white rounded-lg border border-slate-300 text-xs font-semibold outline-none"
                    >
                      <option value="Acres">Acres</option>
                      <option value="Guntas">Guntas</option>
                      <option value="Hectares">Hectares</option>
                      <option value="Sq Yards">Sq Yards</option>
                      <option value="Cents">Cents</option>
                    </select>
                  </div>
                </div>

                {/* Registration Number & Date */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-[10px] font-bold text-slate-600 uppercase">Reg Number</label>
                    {renderFieldConfidenceBadge("registration_number")}
                  </div>
                  <input
                    type="text"
                    value={formFields.registration_number}
                    onChange={(e) => handleInputChange("registration_number", e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold outline-none"
                  />
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-[10px] font-bold text-slate-600 uppercase">Reg Date (YYYY-MM-DD)</label>
                    {renderFieldConfidenceBadge("registration_date")}
                  </div>
                  <input
                    type="text"
                    value={formFields.registration_date}
                    onChange={(e) => handleInputChange("registration_date", e.target.value)}
                    className={`w-full px-3 py-2 rounded-lg border text-xs font-semibold outline-none ${getFieldStyling("registration_date")}`}
                    placeholder="YYYY-MM-DD"
                  />
                </div>

              </div>
            </div>

            {/* Help guidelines */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex gap-3 text-xs leading-normal">
              <Info size={16} className="text-slate-500 shrink-0 mt-0.5" />
              <div className="text-slate-600 font-semibold">
                <p className="font-bold text-slate-800">Officer Verification Workflow:</p>
                <p className="mt-1">
                  Fields marked as <span className="text-rose-600 font-bold">NOT DETECTED</span> can be filled by inspecting the original document on the left.
                  Clicking <strong>Approve & Publish</strong> will update the official land registry database and clear anomaly warnings.
                </p>
              </div>
            </div>

          </div>
        </div>

      </div>

      {/* OCR & Extraction Provenance Modal */}
      {showDebugModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden">
            <div className="bg-slate-900 text-white p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code size={18} className="text-amber-400" />
                <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wide">
                  AI Extraction & OCR Provenance Inspector
                </h3>
              </div>
              <button
                onClick={() => setShowDebugModal(false)}
                className="p-1 text-slate-400 hover:text-white rounded-lg cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              {debugLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
                </div>
              ) : debugData ? (
                <div className="space-y-4 text-xs">
                  <div className="grid grid-cols-3 gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <div>
                      <span className="text-slate-500 block">Detected Language:</span>
                      <strong className="text-slate-900">{debugData.language}</strong>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Overall Confidence:</span>
                      <strong className="text-emerald-700">{debugData.overall_confidence}%</strong>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Processing Stage:</span>
                      <strong className="text-slate-900">{debugData.processing_stage}</strong>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-bold text-slate-800 uppercase mb-1">Raw OCR Text Produced:</h4>
                    <pre className="bg-slate-900 text-amber-200 p-3 rounded-lg overflow-x-auto text-[11px] font-mono whitespace-pre-wrap max-h-48">
                      {debugData.raw_ocr || "(No OCR text captured)"}
                    </pre>
                  </div>

                  <div>
                    <h4 className="font-bold text-slate-800 uppercase mb-1">Structured Field Provenance:</h4>
                    <pre className="bg-slate-50 text-slate-800 border border-slate-200 p-3 rounded-lg overflow-x-auto text-[11px] font-mono whitespace-pre-wrap max-h-48">
                      {JSON.stringify(debugData.fields, null, 2)}
                    </pre>
                  </div>
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">No debug information available.</p>
              )}
            </div>

            <div className="bg-slate-100 p-4 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setShowDebugModal(false)}
                className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-bold hover:bg-slate-800 cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VerificationWorkspace;
