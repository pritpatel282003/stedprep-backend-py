from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app_context import get_db
from student_Dashboard.sprint_logic import (
    TopicTestError,
    build_adaptive_topic_test,
    get_next_adaptive_questions,
    grade_and_store_answers,
    find_questions_by_skill,  # Added import
    _fetch_study_plan,
    _get_daily_plan,
    _is_topic_test_allowed
)
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sprint", tags=["sprint"])

# Pydantic models
class AdaptiveTestResponse(BaseModel):
    success: bool
    student_id: str
    day: int
    allowed: bool = True
    reason: Optional[str] = None
    topics: List[Dict[str, Any]] = []
    note: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None

class StudyPlanSummary(BaseModel):
    student_id: str
    plan_duration_days: Optional[int]
    daily_time_minutes: Optional[int]
    plan_start_date: Optional[str]
    total_days: int
    days_with_topics: int
    days_with_tests: int
    available_days: List[int]
    progress_summary: Dict[str, Any]

class DayDetailsResponse(BaseModel):
    student_id: str
    day: int
    daily_plan: Dict[str, Any]
    topic_test_allowed: bool
    topic_test_restriction_reason: Optional[str]
    topic_count: int
    test_count: int
    total_time_minutes: int

class AnswerRequest(BaseModel):
    question_id: str
    is_correct: bool
    student_answer: Optional[str] = None
    submitted_at: Optional[str] = None

class GradeAnswersRequest(BaseModel):
    answers: List[AnswerRequest]

class GradeAnswersResponse(BaseModel):
    success: bool
    sprint_token: str
    performance: float
    total_questions: int
    correct_questions: int
    message: Optional[str] = None

class NextQuestionsRequest(BaseModel):
    previous_answers: List[Dict[str, Any]]  # Kept for backward compatibility

class NextQuestionsResponse(BaseModel):
    success: bool
    sprint_token: str
    performance: float
    previous_difficulty: str
    current_difficulty: str
    questions: List[Dict[str, Any]]
    fetched_count: int

class SkillQuestionsResponse(BaseModel):
    success: bool
    student_id: str
    topic_code: str
    topic_name: str
    sprint_token: str
    current_mastery: float
    target_difficulty: str
    starting_difficulty: Optional[str | List[str]]  # Adjusted to match sprint_logic
    questions_recommended: int
    fetched_count: int
    questions: List[Dict[str, Any]]
    no_questions: bool
    message: Optional[str] = None
    adaptive_config: Optional[Dict[str, Any]] = None

@router.post("/adaptive-topic-test/{student_id}/{day}", response_model=AdaptiveTestResponse)
async def get_adaptive_topic_test(
    student_id: str = Path(..., pattern=r"^[a-zA-Z0-9_-]+$"),
    day: int = Path(..., ge=1),
    db=Depends(get_db)
):
    logger.info(f"Generating adaptive topic test for student_id={student_id}, day={day}")
    try:
        adaptive_test = build_adaptive_topic_test(db, student_id.strip(), day)
        if not adaptive_test.get("success"):
            error_detail = adaptive_test.get("error", "Failed to build adaptive topic test")
            logger.warning(f"Failed to build adaptive topic test: {error_detail}")
            if "not found" in error_detail.lower():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_detail)
            elif "invalid" in error_detail.lower():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_detail)
        return adaptive_test
    except HTTPException:
        raise
    except TopicTestError as e:
        logger.error(f"TopicTestError: {str(e)}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Topic test generation error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_adaptive_topic_test: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/adaptive-topic-test", response_model=AdaptiveTestResponse)
async def get_adaptive_topic_test_get(
    student_id: str = Query(..., pattern=r"^[a-zA-Z0-9_-]+$", description="Unique identifier for the student"),
    day: int = Query(1, ge=1, description="Day number in the study plan"),
    db=Depends(get_db)
):
    logger.info(f"GET request for adaptive topic test: student_id={student_id}, day={day}")
    return await get_adaptive_topic_test(student_id, day, db)

@router.get("/study-plan/{student_id}", response_model=StudyPlanSummary)
async def get_study_plan_summary(
    student_id: str = Path(..., pattern=r"^[a-zA-Z0-9_-]+$"),
    db=Depends(get_db)
):
    logger.info(f"Fetching study plan summary for student_id={student_id}")
    try:
        study_plan = _fetch_study_plan(db, student_id)
        if not study_plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study plan not found for student")
        daily_plans = study_plan.get("daily_plans", [])
        return StudyPlanSummary(
            student_id=student_id,
            plan_duration_days=study_plan.get("plan_duration_days"),
            daily_time_minutes=study_plan.get("daily_time_minutes"),
            plan_start_date=study_plan.get("plan_start_date"),
            total_days=len(daily_plans),
            days_with_topics=len([dp for dp in daily_plans if dp.get("topics")]),
            days_with_tests=len([dp for dp in daily_plans if dp.get("tests")]),
            available_days=[dp.get("day") for dp in daily_plans],
            progress_summary=study_plan.get("progress_summary", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching study plan summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch study plan summary: {str(e)}")

@router.get("/day-details/{student_id}/{day}", response_model=DayDetailsResponse)
async def get_day_details(
    student_id: str = Path(..., pattern=r"^[a-zA-Z0-9_-]+$"),
    day: int = Path(..., ge=1),
    db=Depends(get_db)
):
    logger.info(f"Fetching day details for student_id={student_id}, day={day}")
    try:
        study_plan = _fetch_study_plan(db, student_id)
        if not study_plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study plan not found for student")
        daily_plan = _get_daily_plan(study_plan, day)
        if not daily_plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested day not found in study plan")
        is_allowed, reason = _is_topic_test_allowed(daily_plan)
        return DayDetailsResponse(
            student_id=student_id,
            day=day,
            daily_plan=daily_plan,
            topic_test_allowed=is_allowed,
            topic_test_restriction_reason=reason,
            topic_count=len(daily_plan.get("topics", [])),
            test_count=len(daily_plan.get("tests", [])),
            total_time_minutes=daily_plan.get("total_time_minutes", 0)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching day details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch day details: {str(e)}")

@router.post("/grade-answers/{sprint_token}", response_model=GradeAnswersResponse)
async def grade_answers(
    sprint_token: str = Path(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    body: GradeAnswersRequest = Body(...),
    db=Depends(get_db)
):
    logger.info(f"Grading answers for sprint_token={sprint_token}")
    try:
        # Convert Pydantic objects to dictionaries
        answers_dict = [
            {
                "question_id": answer.question_id,
                "is_correct": answer.is_correct,
                "student_answer": answer.student_answer,
                "submitted_at": answer.submitted_at
            }
            for answer in body.answers
        ]
        
        result = grade_and_store_answers(db, sprint_token, answers_dict)
        if not result.get("success"):
            error_detail = result.get("error", "Unknown error")
            logger.warning(f"Failed to grade answers: {error_detail}")
            if "not found" in error_detail.lower():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_detail)
            elif "invalid" in error_detail.lower() or "duplicate" in error_detail.lower():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_detail)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in grade_answers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to grade answers: {str(e)}")

@router.post("/next-questions/{sprint_token}", response_model=NextQuestionsResponse)
async def get_next_questions(
    sprint_token: str = Path(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    body: NextQuestionsRequest = Body(default_factory=NextQuestionsRequest),  # Make body optional
    db=Depends(get_db)
):
    logger.info(f"Fetching next adaptive questions for sprint_token={sprint_token}")
    try:
        result = get_next_adaptive_questions(db, sprint_token, body.previous_answers)
        if not result.get("success"):
            error_detail = result.get("error", "Unknown error")
            logger.warning(f"Failed to fetch next questions: {error_detail}")
            if "not found" in error_detail.lower():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_detail)
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_detail)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_next_questions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch next questions: {str(e)}")

@router.get("/skill-questions/{student_id}", response_model=SkillQuestionsResponse)
async def get_questions_by_skill(
    student_id: str = Path(..., pattern=r"^[a-zA-Z0-9_-]+$"),
    topic_code: str = Query("MS01", description="Topic code to search for"),
    db=Depends(get_db)
):
    logger.info(f"Finding questions for student_id={student_id}, topic_code={topic_code}")
    try:
        result = find_questions_by_skill(db, student_id, topic_code)
        if not result.get("success"):
            error_detail = result.get("error", "Failed to find questions")
            logger.warning(f"Failed to find questions: {error_detail}")
            if "not found" in error_detail.lower():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_detail)
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_detail)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_questions_by_skill: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to find questions: {str(e)}")

@router.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "ok", "service": "sprint", "message": "Sprint service is healthy ✅"}
