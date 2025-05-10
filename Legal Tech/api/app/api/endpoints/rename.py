from fastapi import APIRouter, HTTPException, Depends
from app.services.renamer import RenamerService
from app.core.config import settings
from typing import List

router = APIRouter()

def get_renamer_service() -> RenamerService:
    return RenamerService(api_key=settings.GOOGLE_API_KEY)

@router.get("/job/{job_id}/rename-suggestions")
async def get_rename_suggestions(
    job_id: str,
    renamer: RenamerService = Depends(get_renamer_service)
) -> List[str]:
    """
    Get suggested filenames for all PDFs in a job.
    """
    try:
        # TODO: Get PDF paths from job storage
        # For now, return a mock response
        return ["2024-03-15_contract_review_document"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 