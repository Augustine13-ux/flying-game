from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import uuid
import shutil
from typing import List
import json

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories if they don't exist
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Store job status
jobs = {}

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Save uploaded files
    for file in files:
        file_path = os.path.join(job_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    # Initialize job status
    jobs[job_id] = {
        "status": "processing",
        "files": [{"id": str(uuid.uuid4()), "filename": f.filename, "status": "processing"} for f in files]
    }
    
    # Simulate processing (in a real app, this would be async)
    for file_info in jobs[job_id]["files"]:
        file_info["status"] = "completed"
        file_info["thumbnail_url"] = f"/api/thumbnails/{job_id}/{file_info['id']}"
    
    return {"job_id": job_id}

@app.get("/api/job/{job_id}/manifest")
async def get_job_manifest(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]["files"]

@app.get("/api/download/{job_id}")
async def download_files(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    if not os.path.exists(job_dir):
        raise HTTPException(status_code=404, detail="Files not found")
    
    # Create a ZIP file of the processed files
    zip_path = os.path.join(PROCESSED_DIR, f"{job_id}.zip")
    shutil.make_archive(zip_path[:-4], 'zip', job_dir)
    
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"processed_files_{job_id}.zip"
    ) 