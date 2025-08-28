# routes/section_test.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime

from pydantic import BaseModel
from models.models import TopicTestRequest
from app_context import get_db
from student_Dashboard.section_test import build_section_test_for_day
from student_Dashboard import study_plan_logic

class SectionIndexGradeRequest(BaseModel):
    """
    Request model for grading a section test using an indexed list of answers.
    """
    test_id: str
    answers: list  # A list of selected options or None/"" ordered by the stored test order

# Create a new router for section test endpoints
router = APIRouter(prefix="/section-test", tags=["section_test"])

@router.post("/grade")
async def grade_section_test_indexed(payload: SectionIndexGradeRequest, db=Depends(get_db)):
    """
    Grades a section test based on an indexed list of answers.

    This endpoint processes the student's answers, calculates their performance,
    updates their mastery data, and regenerates their study plan based on the results.
    """
    try:
        # Retrieve the section test from the database
        tests_col = db.client[db.database_name]["section_tests"]
        test_doc = tests_col.find_one({"test_id": payload.test_id})
        if not test_doc:
            raise HTTPException(status_code=404, detail="section test not found for given test_id and student_id")
        student_id = test_doc.get("student_id") or ""

        # Get the ordered list of question IDs for the test
        ordered_qids = [str(q) for q in (test_doc.get("question_ids") or []) if q]

        # Ensure the number of answers matches the number of questions
        expected_count = len(ordered_qids)
        if len(payload.answers) != expected_count:
            raise HTTPException(status_code=400, detail=f"answers length must be {expected_count} to grade this section test")

        # Helper function to normalize answer strings
        def normalize(val: Any) -> str:
            try:
                return str(val).strip().lower()
            except Exception:
                return ""

        # Grade each question
        question_results = []
        per_topic: Dict[str, Dict[str, Any]] = {}
        for idx in range(len(ordered_qids)):
            qid = ordered_qids[idx]
            selected_raw = payload.answers[idx] if idx < len(payload.answers) else ""
            item = db.get_item_by_question_id(qid)
            if not item:
                question_results.append({"question_id": qid, "is_correct": False, "error": "Question not found in item_bank"})
                continue

            # Check if the answer is correct
            correct_option = item.get("correctOption")
            correct_answer = item.get("correctAnswer", correct_option)
            user_answer_norm = normalize(selected_raw)
            skipped = (user_answer_norm == "")
            correct_norm = normalize(correct_answer)
            is_correct = (user_answer_norm == correct_norm) if (not skipped and correct_norm) else False

            # Store the result for each question
            topic_code = (item.get("skillCode") or "").strip()
            topic_name = item.get("topic") or item.get("skillDescription") or item.get("section") or "Unknown"
            question_results.append({
                "question_id": qid,
                "selected_option": selected_raw or "",
                "typed_answer": None,
                "correct_answer": correct_answer,
                "topic_code": topic_code or None,
                "topic": topic_name,
                "is_correct": is_correct,
                "skipped": skipped
            })

            # Aggregate results by topic
            if topic_code:
                stats = per_topic.setdefault(topic_code, {"correct": 0, "total": 0, "topic": topic_name})
                stats["total"] += 1
                if is_correct:
                    stats["correct"] += 1

        # Update the student's summary with the new mastery data
        if per_topic and student_id:
            collection = db.client[db.database_name]["studentSummary"]
            now_ts = datetime.now()
            existing = collection.find_one({"student_id": student_id}, sort=[("analysis_date", -1)])
            update_fields = {"analysis_date": now_ts, "updated_at": now_ts}
            set_on_insert = {"student_id": student_id, "created_at": now_ts}
            for code, stats in per_topic.items():
                prev = (existing or {}).get("complete_topic_mastery", {}).get(code, {})
                prev_correct = int(prev.get("correct_answers", 0) or 0)
                prev_total = int(prev.get("total_questions", 0) or 0)
                new_correct = prev_correct + int(stats["correct"])
                new_total = prev_total + int(stats["total"])
                accuracy = (new_correct / new_total) * 100 if new_total > 0 else 0.0
                path = f"complete_topic_mastery.{code}"
                update_fields[f"{path}.topic"] = stats["topic"]
                update_fields[f"{path}.correct_answers"] = new_correct
                update_fields[f"{path}.total_questions"] = new_total
                update_fields[f"{path}.mastery_percentage"] = round(accuracy, 2)
                update_fields[f"{path}.assessment_type"] = "assessed"
            collection.update_one({"student_id": student_id}, {"$set": update_fields, "$setOnInsert": set_on_insert}, upsert=True)

        # Regenerate the study plan based on the test results
        skipped_count = sum(1 for d in question_results if d.get("skipped"))
        plan_regenerated = False
        new_plan_id = None
        plan_duration_days = None
        daily_time_minutes_used = None
        try:
            plans_col = db.client[db.database_name]["studyPlans"]
            current_plan = plans_col.find_one({"student_id": student_id})
            plan_duration_days = current_plan.get("plan_duration_days") if current_plan else None
            if not isinstance(plan_duration_days, int) or plan_duration_days <= 0:
                plan_duration_days = len(current_plan.get("daily_plans", [])) if current_plan else 15
                if plan_duration_days <= 0:
                    plan_duration_days = 15
            daily_time_minutes_used = current_plan.get("daily_time_minutes", 60) if current_plan else 60

            # Adjust study plan based on performance in each topic
            recent_adjustments: Dict[str, Dict[str, Any]] = {}
            for code, stats in per_topic.items():
                accuracy = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0.0
                if accuracy >= 80:
                    recent_adjustments[code] = {"questions_delta": -2, "force_difficulty": "Hard"}
                elif accuracy >= 60:
                    recent_adjustments[code] = {"questions_delta": 0, "force_difficulty": "Medium"}
                else:
                    recent_adjustments[code] = {"questions_delta": +2, "force_difficulty": "Easy"}

            # Generate and save the new study plan
            engine = study_plan_logic.AdaptiveStudyPlanEngine(db)
            fresh_plan = engine.generate_study_plan(
                student_id=student_id,
                total_days=plan_duration_days,
                daily_time_minutes=int(daily_time_minutes_used),
                recent_topic_adjustments=recent_adjustments
            )
            plan_regenerated = bool(fresh_plan.get("success"))
            if plan_regenerated:
                engine.save_study_plan(fresh_plan)
                new_plan_id = fresh_plan.get("plan_id")
        except Exception:
            plan_regenerated = False

        # Update the test document with the grading results
        tests_col.update_one(
            {"_id": test_doc["_id"]},
            {"$set": {
                "graded_at": datetime.now(),
                "status": "graded",
                "grading": {
                    "per_topic": {code: {"correct": v["correct"], "total": v["total"], "mastery_percentage": round((v["correct"] / v["total"]) * 100, 2) if v["total"] > 0 else 0.0, "topic": v["topic"]} for code, v in per_topic.items()},
                    "details": question_results,
                    "expected_questions": expected_count,
                    "received_responses": len(payload.answers),
                    "skipped_count": skipped_count
                },
                "study_plan_regenerated": plan_regenerated,
                "new_plan_id": new_plan_id,
                "plan_duration_days": plan_duration_days,
                "daily_time_minutes": daily_time_minutes_used
            }}
        )

        # Return the grading results
        return {
            "success": True,
            "student_id": student_id,
            "test_id": payload.test_id,
            "graded_count": len(question_results),
            "expected_questions": expected_count,
            "received_responses": len(payload.answers),
            "skipped_count": skipped_count,
            "study_plan_regenerated": plan_regenerated,
            "new_plan_id": new_plan_id,
            "plan_duration_days": plan_duration_days,
            "daily_time_minutes": daily_time_minutes_used,
            "per_topic": {code: {"correct": v["correct"], "total": v["total"], "mastery_percentage": round((v["correct"] / v["total"]) * 100, 2) if v["total"] > 0 else 0.0, "topic": v["topic"]} for code, v in per_topic.items()},
            "details": question_results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error grading section test (indexed): {str(e)}")


@router.post("")
async def create_section_tests(payload: TopicTestRequest, db=Depends(get_db)):
    """
    Creates new section tests for a student for a specific day.

    This endpoint builds the section tests based on the student's study plan,
    persists them to the database, and returns the test details.
    """
    try:
        # Validate student ID and day
        if not payload.student_id.strip():
            raise HTTPException(status_code=400, detail="student_id cannot be empty")
        if payload.day <= 0:
            raise HTTPException(status_code=400, detail="day must be positive")

        # Build the section test for the specified day
        result = build_section_test_for_day(db, student_id=payload.student_id, day=payload.day)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

        # Persist each section as its own test in the database
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
                "created_at": datetime.now(),
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




