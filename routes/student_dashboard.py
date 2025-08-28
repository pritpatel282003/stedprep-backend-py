# routes/student_dashboard.py

from fastapi import APIRouter, Depends, HTTPException
from models.models import TopicTestRequest, CreateStudyPlanRequest, StudyPlanResponse, UpdateMasteryRequest, UpdateMasteryResponse
from app_context import get_db
from student_Dashboard.section_test import build_section_test_for_day
from student_Dashboard import study_plan_logic

# Create a new router for student dashboard endpoints
router = APIRouter(prefix="/student", tags=["student_dashboard"])


@router.post("/study-plan/create", response_model=StudyPlanResponse)
async def create_study_plan(request: CreateStudyPlanRequest, db=Depends(get_db)):
    """
    Creates a new study plan for a student.

    This endpoint generates a personalized study plan based on the student's needs,
    the total number of days available for study, and the daily time commitment.
    """
    try:
        # Validate the request parameters
        if request.total_days <= 0:
            raise HTTPException(status_code=400, detail="total_days must be greater than 0")
        if request.daily_time_minutes <= 0:
            raise HTTPException(status_code=400, detail="daily_time_minutes must be greater than 0")
        if not request.student_id.strip():
            raise HTTPException(status_code=400, detail="student_id cannot be empty")

        # Create the study plan using the logic from the student_Dashboard module
        study_plan = study_plan_logic.create_student_study_plan(
            student_id=request.student_id,
            total_days=request.total_days,
            db_manager=db,
            daily_time_minutes=request.daily_time_minutes
        )

        # If the study plan generation fails, raise an error
        if not study_plan.get("success", False):
            raise HTTPException(status_code=500, detail="Failed to generate study plan. Please check student data.")

        # Return the generated study plan
        return StudyPlanResponse(**study_plan)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/topic-test")
async def get_topic_test_for_day(payload: TopicTestRequest, db=Depends(get_db)):
    """
    Retrieves a topic test for a specific day from a student's study plan.
    """
    try:
        # Validate the request parameters
        if not payload.student_id.strip():
            raise HTTPException(status_code=400, detail="student_id cannot be empty")
        if payload.day <= 0:
            raise HTTPException(status_code=400, detail="day must be positive")

        # Build the topic test for the specified day
        from student_Dashboard.topic_test import build_topic_test_for_day
        result = build_topic_test_for_day(db, student_id=payload.student_id, day=payload.day)

        # If the topic test generation fails, raise an error
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating topic test: {str(e)}")


@router.post("/section-test")
async def get_section_test_for_day_route(payload: TopicTestRequest, db=Depends(get_db)):
    """
    Retrieves a section test for a specific day from a student's study plan.

    This endpoint builds the section test, persists it to the database, and returns the test details.
    """
    try:
        # Validate the request parameters
        if not payload.student_id.strip():
            raise HTTPException(status_code=400, detail="student_id cannot be empty")
        if payload.day <= 0:
            raise HTTPException(status_code=400, detail="day must be positive")

        # Build the section test for the specified day
        result = build_section_test_for_day(db, student_id=payload.student_id, day=payload.day)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

        # Persist each section of the test as a separate document in the database
        import uuid
        tests_col = db.client[db.database_name]["section_tests"]
        group_id = str(uuid.uuid4())
        created_tests = []
        for s in result.get("sections", []):
            section_name = s.get("section")
            question_ids = [q.get("question_id") for q in s.get("questions", [])]
            test_id = str(uuid.uuid4())
            tests_col.insert_one({
                "test_id": test_id,
                "group_id": group_id,
                "type": "section",
                "section": section_name,
                "student_id": payload.student_id,
                "day": payload.day,
                "created_at": study_plan_logic.datetime.now(),
                "status": "created",
                "packet": s,
                "question_ids": question_ids
            })
            created_tests.append({"test_id": test_id, "section": section_name, "fetched_count": s.get("fetched_count", len(question_ids))})

        # Enrich the result with the created test details
        enriched = dict(result)
        enriched["tests"] = created_tests
        enriched["group_id"] = group_id if created_tests else None
        enriched["status"] = "created" if created_tests else result.get("note", "")
        return enriched
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating section test: {str(e)}")


