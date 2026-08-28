from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import init_db
from app.routes import auth, documents, records, verification, dashboard

# Initialize tables
init_db()

app = FastAPI(
    title="Intelligent Land Record Digitization and Validation System API",
    description="SIH Land Record Digitization Backend Services",
    version="1.0.0"
)

# CORS Configuration
# React frontend is served on port 3000 (Dockerized) or 5173 (local Vite development)
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure absolute paths exist for mounting
uploads_abs_path = os.path.abspath(settings.UPLOAD_DIR)
preprocessed_abs_path = os.path.abspath(settings.PREPROCESSED_DIR)

# Mount Static Files for serving original and preprocessed images
app.mount("/static/uploads", StaticFiles(directory=uploads_abs_path), name="uploads")
app.mount("/static/preprocessed", StaticFiles(directory=preprocessed_abs_path), name="preprocessed")

# Register API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(records.router, prefix="/api")
app.include_router(verification.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "Healthy",
        "service": "Intelligent Land Record Digitization and Validation System",
        "api_documentation": "/docs"
    }
