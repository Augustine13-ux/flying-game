from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Dict
import uuid
import os
from pathlib import Path
from pydantic import BaseModel
import zipfile
import io
from app.services.signature_detector import SignatureDetector
from app.api.endpoints import rename

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

# Include routers
app.include_router(rename.router, prefix="/api", tags=["Rename"])

# Create storage directory if it doesn't exist
STORAGE_DIR = Path("./storage")
STORAGE_DIR.mkdir(exist_ok=True)

class UploadResponse(BaseModel):
    """Response model for file upload endpoint"""
    job_id: str
    files: List[str]

class RenameRequest(BaseModel):
    """Request model for file rename endpoint"""
    old_filename: str
    new_filename: str

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

@app.get("/api/job/{job_id}/download", tags=["Files"])
async def download_signature_pages(job_id: str):
    """
    Download signature pages as a ZIP file containing PDF and PNG files.
    
    Args:
        job_id: The job ID to download signature pages for
        
    Returns:
        StreamingResponse: ZIP file containing signature pages
    """
    job_dir = STORAGE_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Create a memory buffer for the ZIP file
    zip_buffer = io.BytesIO()
    
    # Create ZIP file in memory
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Process each PDF file in the job directory
        for pdf_file in job_dir.glob("*.pdf"):
            if pdf_file.name.endswith("_sigpages.pdf"):
                continue  # Skip already processed files
                
            # Create output directory for this PDF
            out_dir = job_dir / pdf_file.stem
            out_dir.mkdir(exist_ok=True)
            
            # Extract signature pages
            detector = SignatureDetector()
            manifest = detector.extract_pages(pdf_file, out_dir)
            
            # Add files to ZIP
            for page_info in manifest.values():
                # Add PDF file
                pdf_path = Path(page_info["pdf"])
                if pdf_path.exists():
                    zip_file.write(pdf_path, pdf_path.name)
                
                # Add PNG file
                png_path = Path(page_info["png"])
                if png_path.exists():
                    zip_file.write(png_path, png_path.name)
    
    # Reset buffer position
    zip_buffer.seek(0)
    
    # Return streaming response
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=signature_pages.zip"
        }
    )

@app.patch("/api/job/{job_id}/rename", tags=["Files"])
async def rename_file(job_id: str, rename_request: RenameRequest):
    """
    Rename a file within a job.
    
    Args:
        job_id: The job ID containing the file
        rename_request: Contains old and new filenames
        
    Returns:
        Dict: Updated file list
    """
    job_dir = STORAGE_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Find the file with the old name
    old_file = None
    for file in job_dir.glob("*"):
        if file.name.endswith(rename_request.old_filename):
            old_file = file
            break
    
    if not old_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Generate new filename with UUID prefix
    file_uuid = old_file.name.split('_')[0]
    new_file = job_dir / f"{file_uuid}_{rename_request.new_filename}"
    
    # Rename the file
    try:
        old_file.rename(new_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename file: {str(e)}")
    
    # Return updated file list
    files = [f.name for f in job_dir.glob("*") if not f.name.endswith("_sigpages.pdf")]
    return {"files": files} 