# Intelligent Land Record Digitization and Validation System

Bhumi-Digit is a full-stack, AI-powered system designed for the **Smart India Hackathon (SIH)**. It digitizes, normalizes, extracts, and validates historical Indian land records (scanned PDFs, handwritten registers, mutation records, cadastral maps, and printed receipts) into structured database registries with robust cross-document anomaly detection and a Human-in-the-Loop review workspace.

---

## 🚀 System Architecture & Features

```mermaid
graph TD
    A[Scanned Document PDF/JPG/PNG] --> B[OpenCV Preprocessing]
    B --> C[Language & Format Classification]
    C --> D[OCR / HTR Engine Telugu & English]
    D --> E[NLP Information Extractor]
    E --> F[Land Record Staging Schema]
    F --> G[Validation & Anomaly Engine]
    G --> H{Anomalies Detected? <br/> or Conf < 80%}
    H -- Yes --> I[Human Verification Workspace]
    H -- No --> J[Auto-Approved and Published]
    I --> K[Officer Edit & Audit Log]
    K --> J
    J --> L[(PostgreSQL Database)]
    J --> M[PDF/CSV Export & Map Viewer]
```

### Key Modules:
1. **OpenCV Image Preprocessing**: Quality assessment, deskewing (rotation correction), Gaussian noise removal, CLAHE contrast enhancement, and adaptive thresholding binarization.
2. **Language & Type Classification**: Detects document type (Survey, Mutation, Adangal/ROR, Cadastral Map, etc.), language (Telugu, English, Hindi), and layout format (Printed, Handwritten).
3. **OCR/HTR Engine**: Dual-language character mapper (English & Telugu) with a template-based demo injector fallback to guarantee SIH demonstration stability.
4. **NLP Information Extraction**: Regex and keyword patterns extraction of 14 key land registry fields (Owner, Survey, Khasra, Khata, Area, etc.).
5. **Logic Validation Engine**: Flags required field presence, date formats, negative/invalid area values, and cross-references the database to detect:
   - **Area Mismatch**: Survey sheets listing different area sizes than registered deeds.
   - **Owner Conflict**: Plot ownership changes without matching Mutation register records.
   - **Duplicate Records**: Flagging identical land registries to prevent database inflation.
6. **Human-in-the-Loop Workspace**: Interactive side-by-side editing dashboard where officials can view original scanned files against extracted text fields, inspect validation warnings, correct errors, and approve/reject entries.
7. **Security & Audit Logs**: Fully tracks historical changes on every land record: records old value, new value, official user ID, and timestamp.
8. **Interactive Cadastral GIS**: SVG vector viewer showcasing parcel boundary overlays detected by computer vision. Click on a parcel boundary to inspect linked ownership land records.

---

## 📂 Project Structure

```text
SIH/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy schemas (User, Document, LandRecord, ValidationResult, AuditLog)
│   │   ├── routes/          # REST Endpoints (auth, documents, records, verification, dashboard)
│   │   ├── schemas/         # Pydantic serialization models
│   │   ├── services/        # Logic: preprocessing, ocr, classification, nlp_extractor, validation
│   │   ├── config.py        # System configuration
│   │   ├── database.py      # Connection engine and database initializers
│   │   ├── dependencies.py  # Security and JWT route protectors
│   │   └── main.py          # FastAPI application entry point
│   ├── tests/               # PyTest unit tests for validation rules
│   ├── generate_samples.py  # Script generating mock test images
│   ├── seed.py              # Pre-seeds accounts and anomaly demo files
│   ├── requirements.txt     # Python backend requirements
│   └── Dockerfile           # Backend container dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # Common: Sidebar, Navbar, StatusBadge, FileUploader
│   │   ├── pages/           # Login, Dashboard, Upload, ProcessingResults, Verification, Search, RecordDetails, Map
│   │   ├── services/        # Axios API wrapper (api.js)
│   │   ├── App.jsx          # Route controller and guards
│   │   ├── index.css        # Tailwind styling
│   │   └── main.jsx         # React mount index
│   ├── index.html           # Main template
│   ├── tailwind.config.js   # Tailwind style tokens
│   ├── vite.config.js       # Vite proxy configurations
│   └── Dockerfile           # Frontend container dockerfile
├── sample_documents/        # Sample land records generated for testing uploads
├── docker-compose.yml       # Orchestrates PostgreSQL, API, and React Client
└── README.md                # This manual
```

---

## ⚡ Getting Started (Docker Compose)

The easiest way to start the entire system (Database, FastAPI Backend, React Frontend) is using Docker Compose:

1. **Verify Docker** is installed and running on your system.
2. In the project root folder `SIH`, execute:
   ```bash
   docker-compose up --build
   ```
3. Once running, access the services:
   - **Frontend UI Portal**: [http://localhost:3000](http://localhost:3000)
   - **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Database Connection**: `postgresql://postgres:postgrespassword@localhost:5432/land_digitization_db`

---

## 🛠️ Manual Installation (No Docker)

If you prefer to run the components locally on your host machine:

### Prerequisites:
- Python 3.10+ and Node.js 18+
- (Optional) Tesseract OCR installed on your system path.

### 1. Start Backend:
```bash
cd backend
pip install -r requirements.txt
python generate_samples.py
python seed.py
python -m pytest tests/
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Note: If PostgreSQL is not running, the backend automatically falls back to a local SQLite file (`backend/land_records.db`) so it works out of the box with zero database installation!*

### 2. Start Frontend:
```bash
cd ../frontend
npm install
npm run dev
```
Open your browser to [http://localhost:5173](http://localhost:5173).

---

## 🔑 SIH Evaluation Demonstration Script

Log in as the **Official** (`revenue_officer` / `sih2026password`) or the **Admin** (`admin_sih` / `sih2026admin`) and follow this demonstration path:

### Step 1: Inspect Seeded Dashboard & Anomaly Charts
* Logging in displays KPI summary cards indicating total files, verified entries, review queues, and unresolved validation anomalies.
* Horizontal status bars show the distribution of documents (Verified, Owner Conflict, Area Mismatch, Low Confidence, Processing).
* Recent activity displays historical uploads.

### Step 2: Upload a Telugu Adangal Scanned Document
* Click **Upload Document** on the sidebar.
* Choose `telugu_adangal_sample.jpg` from the `SIH/sample_documents/` folder.
* Monitor the progress timeline: Uploaded $\rightarrow$ Preprocessing (binarized/skew corrected) $\rightarrow$ Language identified (Telugu) $\rightarrow$ OCR character mapping $\rightarrow$ Field Extraction (Owner, Area, Survey No) $\rightarrow$ Logic checks.
* Since the details match standard registry formats with high confidence, the system **auto-approves** the record, marking it as **Verified**.
* View the side-by-side page showing the binarized visual preview on the left and structured tables on the right. Click **Download Land Certificate** to open a beautiful printable PDF certificate.

### Step 3: Review a Low Confidence Handwritten Register
* Click **Upload Document** and select `Telugu_Handwritten_Register.png`.
* The timeline completes. Because handwriting yields lower OCR confidence, the document status is flagged as **Low Confidence** and routed to the Officer's Review Queue.
* Click **Open Review** to open the side-by-side editing console.
* Note the warnings card alerting the officer of low character confidence.
* The form highlights the owner name and survey number with warnings. Correct spelling or missing values and click **Approve & Publish**.
* Go to **Registry Search**, click on the record, and scroll to **Audit Logs**. The history shows the exact modifications: the old value, the new value, your logged officer name, and the timestamp.

### Step 4: Validate Cross-Document Anomalies (Owner Conflict)
* Click **Upload Document** and select `conflict_owner_sample.png`.
* This document lists survey number `145/3A` but names owner `Bandi Ramesh` instead of the verified owner `Kondru Ramu`.
* The system flags an **Owner Conflict** error and blocks auto-publishing.
* Open the review panel, note the error warning: `Ownership conflict detected. A mutation record may be required`.
* Keep it pending or reject it.

### Step 5: Test Cadastral GIS & Interactive Maps
* Click **Cadastral Maps** on the sidebar.
* An interactive SVG block map is loaded representing parcel boundary segments parsed by OpenCV contours.
* Toggle the **CV Boundary Highlight** switch to see boundary contours highlighted.
* Click on **Plot 12**. The panel on the right queries the registry and instantly displays owner `Kondru Ramu`, survey `145/3A`, and area `2.50 Acres` from the database.
* Click **View Entire Land Registry File** to jump directly to its published detail page and audit history.
