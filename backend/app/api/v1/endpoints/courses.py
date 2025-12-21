from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_course_service, get_current_active_user
from app.domain.user import User
from app.schemas.course import CourseCreate, CourseListResponse, CourseResponse, CourseUpdate
from app.services.course_service import CourseService
from app.schemas.exam import ExamResponse
from app.db.mappers.exam_mapper import ExamMapper

router = APIRouter()


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_in: CourseCreate,
    current_user: User = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
):
    """Create a new course/folder"""
    try:
        course = await course_service.create_course(
            user=current_user,
            title=course_in.title,
            subject=course_in.subject,
            description=course_in.description,
            semester_start=course_in.semester_start,
            semester_end=course_in.semester_end,
        )
        return CourseResponse.from_domain(course)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=CourseListResponse)
async def list_courses(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
):
    """List all user's courses with aggregated stats"""
    courses = await course_service.list_user_courses(current_user.id, limit, offset)
    return {
        "items": [CourseResponse.from_domain(c) for c in courses],
        "total": len(courses),
    }


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
):
    """Get course by ID with aggregated stats"""
    course = await course_service.get_course(current_user.id, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    return CourseResponse.from_domain(course)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    course_in: CourseUpdate,
    current_user: User = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
):
    """Update course metadata"""
    try:
        course = await course_service.update_course(
            current_user.id, course_id, course_in.dict(exclude_unset=True)
        )
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
            )
        return CourseResponse.from_domain(course)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
):
    """Delete course folder. Exams remain as standalone."""
    success = await course_service.delete_course(current_user.id, course_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    return None


@router.get("/{course_id}/exams", response_model=List[ExamResponse])
async def list_course_exams(
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
):
    """List all exams in a course"""
    exams = await course_service.get_course_exams(current_user.id, course_id)
    return [ExamResponse.from_orm(e) for e in exams]


@router.post("/{course_id}/exams/{exam_id}", status_code=status.HTTP_200_OK)
async def add_exam_to_course(
    course_id: UUID,
    exam_id: UUID,
    current_user: User = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
):
    """Add existing exam to a course folder"""
    try:
        await course_service.add_exam_to_course(current_user.id, course_id, exam_id)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{course_id}/exams/{exam_id}", status_code=status.HTTP_200_OK)
async def remove_exam_from_course(
    course_id: UUID,
    exam_id: UUID,
    current_user: User = Depends(get_current_active_user),
    course_service: CourseService = Depends(get_course_service),
):
    """Remove exam from its course folder (back to standalone)"""
    try:
        await course_service.remove_exam_from_course(current_user.id, exam_id)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
