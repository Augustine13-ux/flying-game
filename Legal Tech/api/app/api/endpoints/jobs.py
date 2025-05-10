from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from app.services.renamer import RenamerService
from app.core.config import settings
from pathlib import Path
from pydantic import BaseModel

router = APIRouter()

class RenameRequest(BaseModel):
    old_filename: str
    new_filename: str

class RenameBatchRequest(BaseModel):
    renames: List[RenameRequest]

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

@router.patch("/{job_id}/rename")
async def apply_renames(job_id: str, rename_batch: RenameBatchRequest):
    """Apply multiple file renames in a job."""
    try:
        job_dir = Path(settings.UPLOAD_DIR) / job_id
        if not job_dir.exists():
            raise HTTPException(status_code=404, detail="Job not found")

        # Process each rename request
        for rename in rename_batch.renames:
            old_path = job_dir / rename.old_filename
            new_path = job_dir / rename.new_filename

            if not old_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {rename.old_filename}"
                )

            # Rename the file
            try:
                old_path.rename(new_path)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to rename {rename.old_filename}: {str(e)}"
                )

        # Return updated file list
        files = [f.name for f in job_dir.glob("*.pdf")]
        return {"files": files}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 