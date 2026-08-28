import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText, 
  ArrowRight, 
  HelpCircle, 
  Loader2, 
  CheckCircle2, 
  ChevronRight,
  Info,
  Layers,
  Sparkles
} from 'lucide-react';
import { documentService } from '../services/api';
import FileUploader from '../components/FileUploader';

const Upload = () => {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [docId, setDocId] = useState(null);
  const [pipelineStep, setPipelineStep] = useState(0); // 0: Idle, 1: Preprocessing, 2: Classification, 3: OCR, 4: NLP, 5: Validation, 6: Finished
  const [pollInterval, setPollInterval] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState("Auto");

  const stepsList = [
    { label: "Document Uploaded", desc: "Original scanned file saved securely" },
    { label: "Image Preprocessing", desc: "OpenCV deskewing, noise reduction, and binarization" },
    { label: "Document Classification", desc: "Detecting document type, language, and script format" },
    { label: "OCR & Handwriting Recognition", desc: "Running character-mapping engine (English/Telugu)" },
    { label: "NLP Entity Extraction", desc: "Parsing fields: Owner Name, Survey, Khasra, Area" },
    { label: "Validation Engine Check", desc: "Checking area consistency, duplicates, and conflicts" }
  ];

  const handleFileSelect = async (file) => {
    setUploading(true);
    setPipelineStep(1); // Started preprocessing
    
    try {
      const response = await documentService.upload(file, selectedLanguage);
      setDocId(response.id);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to initiate document upload.");
      setUploading(false);
      setPipelineStep(0);
    }
  };

  // Poll for document status
  useEffect(() => {
    if (!docId) return;

    const checkStatus = async () => {
      try {
        const details = await documentService.getDetails(docId);
        const status = details.document.status;
        const stage = details.document.processing_stage;
        
        // Map backend stage to stepsList index
        if (stage === "UPLOADED") {
          setPipelineStep(0);
        } else if (stage === "PREPROCESSING") {
          setPipelineStep(1);
        } else if (stage === "CLASSIFYING") {
          setPipelineStep(2);
        } else if (stage === "OCR_PROCESSING") {
          setPipelineStep(3);
        } else if (stage === "EXTRACTING") {
          setPipelineStep(4);
        } else if (stage === "VALIDATING") {
          setPipelineStep(5);
        }

        if (status !== 'Processing') {
          clearInterval(poll);
          setPipelineStep(6); // Finished
          
          // Wait briefly before redirecting
          setTimeout(() => {
            if (status === 'Verified') {
              navigate(`/processing/${docId}`);
            } else {
              navigate(`/verify/${docId}`);
            }
          }, 800);
        }
      } catch (err) {
        console.error("Error polling document status:", err);
      }
    };

    // Run first check immediately, then poll every 1.5s
    checkStatus();
    const poll = setInterval(checkStatus, 1500);

    return () => {
      clearInterval(poll);
    };
  }, [docId, navigate]);

  // Demo simulation files info
  const demoFiles = [
    { name: "telugu_adangal_sample.jpg", type: "Telugu ROR/Adangal", desc: "A printed Telugu land registry record containing Owner, Survey No, Khata No and Area fields." },
    { name: "english_survey_sample.png", type: "English Survey Record", desc: "An English land survey sheet. Contains clear location hierarchy, survey number, and area measurements." },
    { name: "mutation_record_sample.png", type: "Mutation Order Record", desc: "An official Mutation Order Form changing owner from Kondru Ramu to Kondru Suresh." },
    { name: "conflict_owner_sample.png", type: "Owner Conflict Test File", desc: "Pattadar record containing the same survey number (145/3A) but listing owner Bandi Ramesh." },
    { name: "area_mismatch_sample.png", type: "Area Mismatch Test File", desc: "Survey sheet listing measured area 3.10 Acres instead of the recorded 2.50 Acres." },
  ];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
      {/* Upload Column */}
      <div className="xl:col-span-2 space-y-6">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h2 className="text-lg font-bold text-slate-800 mb-2">Upload Land Registry Document</h2>
          <p className="text-sm text-gray-500 mb-6">
            Upload historical registers, scanned legacy records, sale deeds, or cadastral maps. 
            The system automatically preprocesses, recognizes languages, runs OCR/HTR, and validates details.
          </p>

          {!uploading && (
            <div className="mb-6 p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
              <label className="block text-xs font-bold text-slate-700 uppercase flex items-center gap-1">
                <span>Force Document Language (Optional)</span>
              </label>
              <p className="text-[10px] text-slate-500 font-semibold">
                Choose the script to help the OCR engine read accurately (defaults to auto-detect if unsure).
              </p>
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="w-full sm:w-64 px-3.5 py-2.5 text-xs font-bold border border-slate-300 rounded-lg outline-none bg-white focus:ring-1 focus:ring-amber-500 text-slate-800 cursor-pointer shadow-sm transition-all"
              >
                <option value="Auto">Auto-Detect Language</option>
                <option value="Telugu">Telugu (తెలుగు)</option>
                <option value="Hindi">Hindi (हिन्दी)</option>
                <option value="Tamil">Tamil (தமிழ்)</option>
                <option value="English">English</option>
              </select>
            </div>
          )}

          {!uploading ? (
            <FileUploader onFileSelect={handleFileSelect} isUploading={uploading} />
          ) : (
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-amber-500 rounded text-slate-900">
                    <Layers size={18} />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800 text-sm">Digitization Pipeline Running</h3>
                    <p className="text-xs text-slate-500 mt-0.5">Running automated extraction and logic audits</p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 text-amber-600 text-xs font-bold bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
                  <Loader2 size={12} className="animate-spin" />
                  <span>Processing...</span>
                </div>
              </div>

              {/* Progress Steps Timeline */}
              <div className="space-y-4">
                {stepsList.map((step, index) => {
                  const isCompleted = pipelineStep > index;
                  const isCurrent = pipelineStep === index;
                  
                  return (
                    <div 
                      key={index} 
                      className={`flex items-start gap-4 transition-all duration-300 ${
                        isCompleted ? "opacity-100" : isCurrent ? "opacity-100 scale-[1.01]" : "opacity-40"
                      }`}
                    >
                      <div className="flex flex-col items-center">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center border font-bold text-xs ${
                          isCompleted 
                            ? "bg-emerald-500 border-emerald-500 text-white" 
                            : isCurrent 
                              ? "bg-amber-100 border-amber-500 text-amber-700 animate-pulse" 
                              : "bg-white border-slate-300 text-slate-400"
                        }`}>
                          {isCompleted ? <CheckCircle2 size={14} /> : index + 1}
                        </div>
                        {index < stepsList.length - 1 && (
                          <div className={`w-0.5 h-8 my-1 ${
                            isCompleted ? "bg-emerald-500" : "bg-slate-200"
                          }`}></div>
                        )}
                      </div>
                      <div>
                        <h4 className={`text-xs font-bold leading-none ${
                          isCompleted ? "text-slate-800" : isCurrent ? "text-amber-700" : "text-slate-500"
                        }`}>
                          {step.label}
                        </h4>
                        <p className="text-[10px] text-slate-400 mt-1 font-semibold">{step.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Informational Guidance Panel */}
        <div className="bg-blue-50 border border-blue-200 p-6 rounded-xl flex items-start gap-4">
          <div className="p-2 bg-blue-500 text-white rounded-lg">
            <Info size={20} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-blue-900 mb-1">Government Compliance Notice</h3>
            <p className="text-xs text-blue-800 leading-relaxed font-semibold">
              BHUMI-DIGIT complies with the National Land Records Modernization Programme (NLRMP). All AI extracts 
              require official approval before writing to the state database. Modified fields are automatically 
              logged under the official's unique digital token for legal audits.
            </p>
          </div>
        </div>
      </div>

      {/* Demo helper column */}
      <div className="xl:col-span-1 space-y-6">
        <div className="bg-slate-900 text-white p-6 rounded-xl border border-slate-800 shadow-lg">
          <h3 className="text-base font-bold text-amber-500 flex items-center gap-1.5 mb-4">
            <Sparkles size={18} />
            Demo Evaluation Files
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed font-semibold mb-6">
            For Smart India Hackathon sandbox evaluation, the registry database contains pre-seeded test records representing various validation states (Owner Conflicts, Area Mismatches, and Duplicates). You can search for these names under Registry Search or find them in the Review Queue:
          </p>

          <div className="space-y-4">
            {demoFiles.map((file, index) => (
              <div 
                key={index} 
                className="bg-slate-950 p-4 rounded-lg border border-slate-800 hover:border-amber-500/50 transition-all group"
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs font-bold text-slate-100 break-all select-all font-mono">
                    {file.name}
                  </span>
                  <span className="text-[9px] bg-slate-800 text-amber-500 font-semibold px-2 py-0.5 rounded border border-slate-700">
                    {file.type.split(' ')[0]}
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 mt-1 leading-normal">
                  {file.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;
