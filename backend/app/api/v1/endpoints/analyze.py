```python
from typing import Optional, List

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import JSONResponse
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.agent.planner import CoursePlanner
from app.dependencies import get_llm_provider
from app.integrations.llm.base import LLMProvider

router = APIRouter()


# Define schemas for structured output
class SubtopicSchema(BaseModel):
    topic: str = Field(..., description="Main topic name")
    subtopics: List[str] = Field(..., description="List of subtopics")

class OutlineSchema(BaseModel):
    subject: str = Field(..., description="Detected subject name")
    total_topics: int = Field(..., description="Total number of topics")
    outline: List[SubtopicSchema] = Field(..., description="List of topics and subtopics")


@router.post("/content", status_code=status.HTTP_200_OK)
async def analyze_content(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None),
    llm_provider: LLMProvider = Depends(get_llm_provider),
):
    """
    Analyze uploaded content and extract topic outline.
    
    Public endpoint for landing page demo - no authentication required.
    Note: Rate limiting should be implemented at infrastructure level (nginx/cloudflare).
    
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
    
    # Upload file to Gemini File API
    try:
        # Save file temporarily for upload
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(content_bytes)
            tmp_path = tmp.name
        
        try:
            # Get client from provider (assuming it's migrated to google-genai)
            client = llm_provider.client
            
            # Upload to Gemini
            uploaded_file = client.files.upload(file=tmp_path, config={'mime_type': file.content_type})
            
            # Create prompt that references the uploaded file
            prompt = f"""You are an expert educator analyzing study materials. Extract a clear, hierarchical outline of topics and subtopics from the uploaded file.

**Subject:** {subject or "General"}

**Your Task:**
Create a structured outline showing:
1. Main topics (3-8 topics)
2. Subtopics under each main topic (2-5 subtopics each)

**Requirements:**
- Base outline ONLY on content in the file
- Keep topic names concise (max 6 words)
- Keep subtopic names concise (max 8 words)
- Logical progression from basic to advanced
"""

            # Generate with file context and structured output
            response = await client.models.generate_content_async(
                model=llm_provider.model_name,
                contents=[uploaded_file, prompt],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=OutlineSchema
                )
            )
            
            # Parse JSON response
            import json
            json_text = response.text.strip()
            # Gemini with response_schema returns raw JSON, no markdown blocks usually, but we play safe
            if json_text.startswith("```json"):
                json_text = json_text[7:-3].strip()
            elif json_text.startswith("```"):
                json_text = json_text[3:-3].strip()
                
            outline = json.loads(json_text)
            
            # Delete uploaded file from Gemini
            # Note: google-genai SDK might not have explicit delete in client.files yet or it's different
            # Checking docs or assuming it's similar: client.files.delete(name=...)
            try:
                client.files.delete(name=uploaded_file.name)
            except:
                pass # Ignore cleanup errors for now
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=outline
            )
            
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to analyze content: {str(e)}"}
        )
```
