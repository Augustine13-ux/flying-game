from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uuid
import os
from pathlib import Path
from pydantic import BaseModel

app = FastAPI(
    title="Signature Toolkit API",
    description="API for extracting and processing signatures",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create storage directory if it doesn't exist
STORAGE_DIR = Path("./storage")
STORAGE_DIR.mkdir(exist_ok=True)

class UploadResponse(BaseModel):
    """Response model for file upload endpoint"""
    job_id: str
    files: List[str]

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/upload", response_model=UploadResponse, tags=["Files"])
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload one or multiple PDF files.
    
    Args:
        files: List of PDF files to upload
        
    Returns:
        UploadResponse: Contains job_id and list of file UUIDs
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    job_dir = STORAGE_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    
    file_uuids = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
        
        # Generate unique filename while preserving original name
        file_uuid = str(uuid.uuid4())
        original_name = file.filename
        file_path = job_dir / f"{file_uuid}_{original_name}"
        
        # Save the file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        file_uuids.append(file_uuid)
    
    return UploadResponse(job_id=job_id, files=file_uuids) 