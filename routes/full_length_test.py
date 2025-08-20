from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Any, List
from datetime import datetime
from app_context import get_db
from models.models import IndexGradeRequest
from student_Dashboard.full_length import build_full_length_test, SECTION_ORDER_DEFAULT
from pydantic import BaseModel

router = APIRouter(prefix="/full-length-test", tags=["full_length_test"])


@router.post("/create")
async def create_full_length_test(student_id: str, day: Optional[int] = None, db = Depends(get_db)):
    try:
        if not student_id.strip():
            raise HTTPException(status_code=400, detail="student_id cannot be empty")
        # Build and persist
        sections = build_full_length_test(db)
        import uuid
        test_id = str(uuid.uuid4())
        sections_meta = [
            {
                "section": s.get("section"),
                "question_ids": [q.get("question_id") for q in s.get("questions", [])],
                "fetched_count": s.get("fetched_count", 0)
            }
            for s in sections
        ]
        db.client[db.database_name]["full_length_tests"].insert_one({
            "test_id": test_id,
            "type": "full_length",
            "student_id": student_id,
            "day": day,
            "created_at": datetime.now(),
            "status": "created",
            "sections_meta": sections_meta,
            "packet": sections
        })
        return {
            "success": True,
            "student_id": student_id,
            "test_id": test_id,
            "sections": sections_meta,
            "order": SECTION_ORDER_DEFAULT
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating full-length test: {str(e)}")


@router.get("")
async def get_full_length_test(
    student_id: str,
    page: int = 1,
    page_size: int = 1,
    test_id: Optional[str] = None,
    db = Depends(get_db)
):
    """Return full-length test sections paginated by section, default one section per page.

    Frontend can request page=1 (first section), page=2 (next section), etc.
    Each page returns one section packet with up to 25 questions.
    """
    try:
        if not student_id.strip():
            raise HTTPException(status_code=400, detail="student_id cannot be empty")
        page = max(1, int(page))
        page_size = max(1, int(page_size))

        if test_id:
            doc = db.client[db.database_name]["full_length_tests"].find_one({"test_id": test_id, "student_id": student_id})
            if not doc:
                raise HTTPException(status_code=404, detail="full-length test not found for given test_id and student_id")
            all_sections = doc.get("packet", [])
        else:
            all_sections = build_full_length_test(db)
        total_sections = len(all_sections)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_sections)
        if start_idx >= total_sections:
            return {
                "success": True,
                "student_id": student_id,
                "total_sections": total_sections,
                "sections": [],
                "has_next": False,
                "has_prev": page > 1,
                "page": page,
                "page_size": page_size
            }

        page_sections = all_sections[start_idx:end_idx]
        return {
            "success": True,
            "student_id": student_id,
            "total_sections": total_sections,
            "sections": page_sections,
            "has_next": end_idx < total_sections,
            "has_prev": start_idx > 0,
            "page": page,
            "page_size": page_size,
            "order": SECTION_ORDER_DEFAULT,
            "test_id": test_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating full-length test: {str(e)}")


@router.post("/grade-old-disabled")
async def grade_full_length_test_disabled():
    # This endpoint is intentionally disabled in favor of index-based grading
    raise HTTPException(status_code=410, detail="Deprecated. Use /full-length-test/grade/indexed")





@router.post("/grade")
async def grade_full_length_test_indexed(payload: IndexGradeRequest, db = Depends(get_db)):
    try:
        tests_col = db.client[db.database_name]["full_length_tests"]
        test_doc = tests_col.find_one({"test_id": payload.test_id})
        if not test_doc:
            raise HTTPException(status_code=404, detail="full-length test not found for given test_id and student_id")
        student_id = test_doc.get("student_id") or ""

        # Build ordered list of question_ids across all sections in fixed order
        ordered_qids: List[str] = []
        sections_meta = test_doc.get("sections_meta", []) or []
        section_to_qids = {str(s.get("section")).lower(): [str(q) for q in (s.get("question_ids") or []) if q] for s in sections_meta}
        seen = set()
        for name in (SECTION_ORDER_DEFAULT or []):
            key = str(name).lower()
            if key in section_to_qids:
                ordered_qids.extend(section_to_qids[key])
                seen.add(key)
        for key, qids in section_to_qids.items():
            if key not in seen:
                ordered_qids.extend(qids)

        # Enforce full-test grading: answers length must match
        if len(payload.answers) != len(ordered_qids):
            raise HTTPException(status_code=400, detail=f"answers length must be {len(ordered_qids)} to grade the full test")

        def normalize(val: Any) -> str:
            try:
                return str(val).strip().lower()
            except Exception:
                return ""

        question_results = []
        per_topic: Dict[str, Dict[str, Any]] = {}

        for idx in range(len(ordered_qids)):
            qid = ordered_qids[idx]
            selected_raw = payload.answers[idx] or ""
            item = db.get_item_by_question_id(qid)
            if not item:
                question_results.append({"question_id": qid, "is_correct": False, "error": "Question not found in item_bank"})
                continue
            correct_option = item.get("correctOption")
            correct_answer = item.get("correctAnswer", correct_option)
            user_answer_norm = normalize(selected_raw)
            skipped = (user_answer_norm == "")
            correct_norm = normalize(correct_answer)
            is_correct = (user_answer_norm == correct_norm) if (not skipped and correct_norm) else False
            topic_code = (item.get("skillCode") or "").strip()
            topic_name = item.get("topic") or item.get("skillDescription") or item.get("section") or "Unknown"
            question_results.append({
                "question_id": qid,
                "selected_option": selected_raw,
                "typed_answer": None,
                "correct_answer": correct_answer,
                "topic_code": topic_code or None,
                "topic": topic_name,
                "is_correct": is_correct,
                "skipped": skipped
            })
            if topic_code:
                stats = per_topic.setdefault(topic_code, {"correct": 0, "total": 0, "topic": topic_name})
                stats["total"] += 1
                if is_correct:
                    stats["correct"] += 1

        # Update studentSummary identical to other graders
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

        expected_count = len(ordered_qids)
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
            recent_adjustments: Dict[str, Dict[str, Any]] = {}
            for code, stats in per_topic.items():
                accuracy = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0.0
                if accuracy >= 80:
                    recent_adjustments[code] = {"questions_delta": -2, "force_difficulty": "Hard"}
                elif accuracy >= 60:
                    recent_adjustments[code] = {"questions_delta": 0, "force_difficulty": "Medium"}
                else:
                    recent_adjustments[code] = {"questions_delta": +2, "force_difficulty": "Easy"}
            from student_Dashboard import study_plan_logic
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
        raise HTTPException(status_code=500, detail=f"Error grading full-length test (indexed): {str(e)}")

