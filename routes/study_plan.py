# routes/study_plan.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app_context import get_db

# Create a new router for study plan endpoints
router = APIRouter(prefix="/student", tags=["student_dashboard"])


@router.get("/study-plan")
async def get_study_plan_week(
    student_id: str,
    week: int = 1,
    page_size: int = 7,
    day: Optional[int] = None,
    db=Depends(get_db)
):
    """
    Retrieves a student's study plan, either for a specific week or a specific day.

    This endpoint allows fetching the study plan in paginated weekly chunks or a single day's plan.
    """
    try:
        # Validate student ID
        if not student_id.strip():
            raise HTTPException(status_code=400, detail="student_id cannot be empty")

        page_size = max(1, int(page_size))
        week = max(1, int(week))

        # Retrieve the study plan from the database
        plans_col = db.client[db.database_name]["studyPlans"]
        study_plan = plans_col.find_one({"student_id": student_id})
        if not study_plan:
            raise HTTPException(status_code=404, detail="Study plan not found. Create it first.")

        # Get the daily plans and total number of days
        daily_plans = study_plan.get("daily_plans", [])
        total_days = len(daily_plans)

        # Handle cases where there are no daily plans
        if total_days == 0:
            return {
                "success": True,
                "student_id": student_id,
                "total_days": 0,
                "page_size": page_size,
                "total_weeks": 0,
                "current_week": 0,
                "has_prev_week": False,
                "has_next_week": False,
                "daily_plans": []
            }

        # If a specific day is requested, return that day's plan
        if day is not None:
            try:
                day_int = int(day)
            except Exception:
                raise HTTPException(status_code=400, detail="day must be an integer")
            if day_int <= 0 or day_int > total_days:
                raise HTTPException(status_code=400, detail=f"day must be between 1 and {total_days}")

            one_day_plan = daily_plans[day_int - 1]
            return {
                "success": True,
                "mode": "day",
                "student_id": student_id,
                "plan_id": study_plan.get("plan_id"),
                "plan_duration_days": study_plan.get("plan_duration_days", total_days),
                "daily_time_minutes": study_plan.get("daily_time_minutes", 60),
                "total_days": total_days,
                "page_size": 1,
                "total_weeks": total_days,
                "current_week": day_int,
                "has_prev_week": day_int > 1,
                "has_next_week": day_int < total_days,
                "start_day_index": day_int,
                "end_day_index": day_int,
                "daily_plans": [one_day_plan]
            }

        # Paginate the weekly study plan
        total_weeks = (total_days + page_size - 1) // page_size
        current_week = min(week, total_weeks)
        start_idx = (current_week - 1) * page_size
        end_idx = min(start_idx + page_size, total_days)
        page_days = daily_plans[start_idx:end_idx]

        has_prev = current_week > 1
        has_next = current_week < total_weeks

        # Return the paginated weekly plan
        return {
            "success": True,
            "mode": "week",
            "student_id": student_id,
            "plan_id": study_plan.get("plan_id"),
            "plan_duration_days": study_plan.get("plan_duration_days", total_days),
            "daily_time_minutes": study_plan.get("daily_time_minutes", 60),
            "total_days": total_days,
            "page_size": page_size,
            "total_weeks": total_weeks,
            "current_week": current_week,
            "has_prev_week": has_prev,
            "has_next_week": has_next,
            "start_day_index": start_idx + 1,
            "end_day_index": end_idx,
            "daily_plans": page_days
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weekly study plan: {str(e)}")


