"""Subtitle upload and analysis endpoint."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.models.schemas import AnalysisResponse
from app.services.analysis_pipeline import AnalysisPipeline, decode_subtitle_content
from app.services.srt_parser import SRTParseError

router = APIRouter(tags=["analysis"])
pipeline = AnalysisPipeline()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_subtitle(file: UploadFile = File(...)) -> AnalysisResponse:
    """Analyze a UTF-8/CP932 SubRip subtitle upload without persisting it."""
    filename = file.filename or "subtitle.srt"
    if not filename.lower().endswith(".srt"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload a valid .srt file.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subtitle file is empty.")
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subtitle file exceeds the 10 MB limit.")

    try:
        return pipeline.analyze(decode_subtitle_content(content), filename)
    except (SRTParseError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="NLP processing failed.") from error
