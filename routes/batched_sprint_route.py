from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Dict, Any, Optional
import logging
from app_context import get_db
from pydantic import BaseModel, Field

from models.models import BatchSubmission
from student_Dashboard.sprint_batch_logic import (
    get_batched_questions_for_skill,
    submit_batched_answers_and_get_next,
    get_batched_session_status,
    complete_batched_session,
    BatchedTestError,
    _get_student_mastery_level
)

router = APIRouter(prefix="/sprint/batched", tags=["sprint-batched"])
logger = logging.getLogger(__name__)

# Configure logger for production (write to file, suppress console output)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler('app.log')  # Log to file instead of console
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Custom exception for client errors that shouldn't be logged as server errors
class ClientValidationError(Exception):
    """Exception for client-side validation errors that don't need server logging"""
    pass


@router.get("/skills/{skill_code}/questions")
async def get_skill_questions(
    skill_code: str = Path(..., description="Skill code (e.g., MA01)"),
    student_id: str = Query(..., pattern=r"^[a-zA-Z0-9_-]+$", description="Student identifier"),
    mastery_level: Optional[int] = Query(None, ge=2, le=9, description="Override mastery level (2-9)"),
    db = Depends(get_db)
):
    """Get batched questions for a specific skill code"""
    try:
        result = get_batched_questions_for_skill(
            db_manager=db,
            student_id=student_id,
            skill_code=skill_code,
            current_mastery_level=mastery_level
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get questions"))
            
        return result
        
    except BatchedTestError as e:
        logger.error(f"Batched test error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting skill questions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get skill questions")

@router.post("/sessions/{sprint_token}/submit")
async def submit_answers_and_get_next(
    sprint_token: str = Path(..., description="Sprint session token"),
    submission: BatchSubmission = Body(...),
    db = Depends(get_db)
):
    """Submit answers and get next batch of questions"""
    try:
        result = submit_batched_answers_and_get_next(
            db_manager=db,
            sprint_token=sprint_token,
            answers=[answer.dict() for answer in submission.answers]
        )
        
        if not result.get("success"):
            error_message = result.get("error", "Failed to submit answers")
            
            # Check if this is a client validation error (invalid question_id)
            if "Invalid question_id" in error_message:
                # This is expected client behavior, don't log as server error
                raise ClientValidationError(error_message)
            elif "Session is not active" in error_message or "Sprint session not found" in error_message:
                # Session-related client errors
                raise ClientValidationError(error_message)
            elif "Missing is_correct field" in error_message:
                # Request validation error
                raise ClientValidationError(error_message)
            else:
                # This is an unexpected error, should be logged
                logger.warning(f"Submission failed for sprint_token {sprint_token}: {error_message}")
                raise HTTPException(status_code=400, detail=error_message)
            
        return result
        
    except ClientValidationError as e:
        # Client validation errors - return 400 but don't log as server error
        raise HTTPException(status_code=400, detail=str(e))
    except BatchedTestError as e:
        # Business logic errors - these should be logged
        logger.error(f"Batched test error for sprint_token {sprint_token}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected server errors - these should definitely be logged
        logger.error(f"Unexpected error submitting answers for sprint_token {sprint_token}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit answers")

@router.get("/sessions/{sprint_token}/status")
async def get_session_status(
    sprint_token: str = Path(..., description="Sprint session token"),
    db = Depends(get_db)
):
    """Get current status of a batched test session"""
    try:
        result = get_batched_session_status(db_manager=db, sprint_token=sprint_token)
        
        if not result.get("success"):
            error = result.get("error", "Session not found")
            status_code = 404 if "not found" in error.lower() else 400
            raise HTTPException(status_code=status_code, detail=error)
            
        return result
        
    except Exception as e:
        logger.error(f"Error getting session status for sprint_token {sprint_token}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session status")

@router.post("/sessions/{sprint_token}/complete")
async def complete_session(
    sprint_token: str = Path(..., description="Sprint session token"),
    db = Depends(get_db)
):
    """Complete a batched test session"""
    try:
        result = complete_batched_session(db_manager=db, sprint_token=sprint_token)
        
        if not result.get("success"):
            error = result.get("error", "Failed to complete session")
            status_code = 404 if "not found" in error.lower() else 400
            raise HTTPException(status_code=status_code, detail=error)
            
        return result
        
    except Exception as e:
        logger.error(f"Error completing session for sprint_token {sprint_token}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete session")

@router.get("/students/{student_id}/skills/{skill_code}/mastery")
async def get_student_skill_mastery(
    student_id: str = Path(..., pattern=r"^[a-zA-Z0-9_-]+$"),
    skill_code: str = Path(...),
    db = Depends(get_db)
):
    """Get current mastery level for a student and skill"""
    try:
        mastery_level = _get_student_mastery_level(db, student_id, skill_code)
        
        if mastery_level is None:
            raise HTTPException(
                status_code=404,
                detail=f"No mastery data found for student {student_id} and skill {skill_code}"
            )
        
        # Convert level to percentage for display
        percentage_map = {
            2: 25, 3: 35, 4: 45, 5: 55, 6: 65, 7: 75, 8: 85, 9: 95
        }
        mastery_percentage = percentage_map.get(mastery_level, 50)
        
        return {
            "success": True,
            "student_id": student_id,
            "skill_code": skill_code,
            "mastery_level": mastery_level,
            "mastery_percentage": mastery_percentage
        }
        
    except Exception as e:
        logger.error(f"Error getting student mastery: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get student mastery")