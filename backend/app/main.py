import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database.session import init_db
from app.api import api_router

# Initialize database schema tables
init_db()

app = FastAPI(
    title="LandSure AI - Land Record Digitization & Validation API",
    description="SIH26018 Production-Ready Multilingual Land Records Digitization Backend Services",
    version="2.0.0"
)

# CORS Configuration
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

# Mount Static Files for serving original and preprocessed images securely
uploads_abs_path = os.path.abspath(settings.UPLOAD_DIR)
preprocessed_abs_path = os.path.abspath(settings.PREPROCESSED_DIR)

app.mount("/static/uploads", StaticFiles(directory=uploads_abs_path), name="uploads")
app.mount("/static/preprocessed", StaticFiles(directory=preprocessed_abs_path), name="preprocessed")

# Register API Router
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "Healthy",
        "service": "BhoomiSetu AI Land Record Digitization API",
        "version": "2.0.0",
        "docs": "/docs"
    }
