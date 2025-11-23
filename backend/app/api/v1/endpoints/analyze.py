from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import JSONResponse

from app.agent.planner import CoursePlanner
from app.core.rate_limit import rate_limit
from app.dependencies import get_llm_provider
from app.integrations.llm.base import LLMProvider

router = APIRouter()


@router.post("/content", status_code=status.HTTP_200_OK)
@rate_limit(max_requests=5, window_seconds=3600)  # 5 requests per hour for anonymous users
async def analyze_content(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None),
    llm_provider: LLMProvider = Depends(get_llm_provider),
):
    """
    Analyze uploaded content and extract topic outline.
    
    Public endpoint for landing page demo - no authentication required.
    Rate limited to 5 requests per IP per hour.
    
    Args:
        file: Uploaded file (PDF, DOCX, TXT, MP3, MP4)
        subject: Optional subject hint
        
    Returns:
        JSON with structured topic/subtopic outline
    """
    
    # Validate file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Read file content
    content_bytes = await file.read()
    
    if len(content_bytes) > MAX_FILE_SIZE:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"error": "File too large. Maximum size is 10MB."}
        )
    
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "audio/mpeg",
        "video/mp4",
    ]
    
    if file.content_type not in allowed_types:
        return JSONResponse(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content={
                "error": f"Unsupported file type: {file.content_type}. "
                "Supported types: PDF, DOCX, TXT, MP3, MP4"
            }
        )
    
    # Parse file content based on type
    try:
        if file.content_type == "text/plain":
            content = content_bytes.decode("utf-8")
        elif file.content_type == "application/pdf":
            # For PDF, we'll need to use a PDF parser
            # For now, return a placeholder - will implement PDF parsing
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
            content = ""
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
                
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # For DOCX, use python-docx
            import docx
            import io
            
            doc = docx.Document(io.BytesIO(content_bytes))
            content = "\n".join([para.text for para in doc.paragraphs])
            
        elif file.content_type in ["audio/mpeg", "video/mp4"]:
            # For audio/video, return a message that transcription is needed
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "subject": subject or "Media File",
                    "total_topics": 1,
                    "outline": [
                        {
                            "topic": "Media Content Analysis",
                            "subtopics": [
                                "Audio/Video transcription required",
                                "Upload text-based materials for instant analysis"
                            ]
                        }
                    ],
                    "message": "Audio and video files require transcription. Please upload text-based materials (PDF, DOCX, TXT) for instant analysis."
                }
            )
        else:
            content = content_bytes.decode("utf-8", errors="ignore")
            
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": f"Failed to parse file: {str(e)}"}
        )
    
    # Check if content is empty
    if not content.strip():
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "No text content found in file"}
        )
    
    # Extract topic outline using AI
    try:
        planner = CoursePlanner(llm_provider)
        outline = await planner.extract_topic_outline(
            content=content,
            subject=subject or "General"
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=outline
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to analyze content: {str(e)}"}
        )
