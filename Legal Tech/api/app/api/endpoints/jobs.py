from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.renamer import RenamerService
from app.core.config import settings
from pathlib import Path

router = APIRouter()

@router.get("/{job_id}/rename-suggestions")
async def get_rename_suggestions(job_id: str):
    """Get suggested filenames for all PDFs in a job."""
    try:
        # Initialize renamer service
        renamer = RenamerService(api_key=settings.GOOGLE_API_KEY)
        
        # Get job directory
        job_dir = Path(settings.UPLOAD_DIR) / job_id
        if not job_dir.exists():
            raise HTTPException(status_code=404, detail="Job not found")
            
        # Get all PDFs in job directory
        pdf_files = list(job_dir.glob("*.pdf"))
        if not pdf_files:
            raise HTTPException(status_code=404, detail="No PDF files found in job")
            
        # Generate suggestions for each PDF
        suggestions = {}
        for pdf_path in pdf_files:
            suggested_name = renamer.suggest_filename(pdf_path)
            suggestions[pdf_path.name] = suggested_name
            
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 