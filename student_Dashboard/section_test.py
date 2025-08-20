from typing import List, Dict, Any
try:
    from bson import ObjectId  # type: ignore
except Exception:  # pragma: no cover
    class ObjectId:  # fallback stub
        pass


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _json_sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_sanitize(v) for v in value]
    try:
        return str(value)
    except Exception:
        return None


def _normalize_question(doc: Dict[str, Any]) -> Dict[str, Any]:
    # Normalize text fields to lowercase
    question_type = doc.get("questionType")
    if isinstance(question_type, str):
        question_type = question_type.lower()

    section = doc.get("section")
    if isinstance(section, str):
        section = section.lower()

    subject = doc.get("subject", section)
    if isinstance(subject, str):
        subject = subject.lower()

    result: Dict[str, Any] = {
        "question_id": str(doc.get("question_id")),
        "questionType": question_type,
        "section": section,
        "subject": subject,
        "topic": doc.get("topic"),
        "skillCode": doc.get("skillCode"),
        "skillDescription": doc.get("skillDescription"),
        "difficultyLevel": doc.get("difficultyLevel"),
        "iseeLevel": doc.get("iseeLevel"),
        "a_discrimination": doc.get("a_discrimination"),
        "b_difficulty": doc.get("b_difficulty"),
        "questionTitle": doc.get("questionTitle"),
        "options": _json_sanitize(doc.get("options", {})),
        "correctOption": doc.get("correctOption"),
        "correctAnswer": doc.get("correctAnswer", doc.get("correctOption")),
        "questionImages": _json_sanitize(doc.get("questionImages", [])),
        "explanation": doc.get("explanation", ""),
    }
    known_keys = set(result.keys()) | {"_id"}
    extra = {k: v for k, v in doc.items() if k not in known_keys}
    if extra:
        result["additional_fields"] = _json_sanitize(extra)
    return result


def fetch_section_questions(db_manager, section_name: str, num_questions: int = 25) -> List[Dict[str, Any]]:
    """Fetch up to num_questions for a section using questionType == section_name,
    falling back to section == section_name if needed.
    All comparisons are case-insensitive (normalized to lowercase)."""
    item_bank = db_manager.item_bank_collection

    if not isinstance(section_name, str):
        return []

    section_name = section_name.lower()

    primary = list(
        item_bank.aggregate([
            {"$match": {"$expr": {"$eq": [{"$toLower": "$questionType"}, section_name]}}},
            {"$sample": {"size": int(num_questions)}}
        ])
    )
    if len(primary) >= num_questions:
        return [_normalize_question(d) for d in primary[:num_questions]]

    remaining = num_questions - len(primary)
    fallback = list(
        item_bank.aggregate([
            {"$match": {"$expr": {"$eq": [{"$toLower": "$section"}, section_name]}}},
            {"$sample": {"size": int(remaining)}}
        ])
    )
    seen = {d.get("_id") for d in primary}
    for d in fallback:
        if d.get("_id") not in seen and len(primary) < num_questions:
            primary.append(d)
            seen.add(d.get("_id"))
    return [_normalize_question(d) for d in primary[:num_questions]]


def build_section_test_for_day(db_manager, student_id: str, day: int) -> Dict[str, Any]:
    """Build section-test payload for a specific day using the saved study plan.

    - If no section test is scheduled on that day, return allowed=False.
    - For each section present in that day's tests, return 25 questions.
    """
    if not student_id or not isinstance(student_id, str):
        return {"success": False, "error": "Invalid student_id"}
    if not isinstance(day, int) or day <= 0:
        return {"success": False, "error": "Invalid day"}

    plans_col = db_manager.db["studyPlans"]
    plan_doc = plans_col.find_one({"student_id": student_id})
    if not plan_doc:
        return {"success": False, "error": "Study plan not found for student"}

    daily_plans = plan_doc.get("daily_plans", [])
    target = next((dp for dp in daily_plans if dp.get("day") == day), None)
    if not target:
        return {"success": False, "error": "Requested day not found in study plan"}

    tests = target.get("tests", [])
    section_tests = [t for t in tests if t.get("type") == "section"]
    if not section_tests:
        return {
            "success": True,
            "student_id": student_id,
            "day": day,
            "allowed": False,
            "reason": "No section test scheduled for this day",
            "sections": []
        }

    results: List[Dict[str, Any]] = []
    for st in section_tests:
        section_name = st.get("category") or st.get("section") or st.get("questionType")
        if not section_name:
            continue
        section_name = section_name.lower()
        questions = fetch_section_questions(db_manager, section_name=section_name, num_questions=25)
        results.append({
            "section": section_name,
            "questions_recommended": 25,
            "fetched_count": len(questions),
            "questions": questions,
            "no_questions": len(questions) == 0,
            "message": (f"No questions found for section {section_name}" if len(questions) == 0 else "")
        })

    all_empty = all(r.get("fetched_count", 0) == 0 for r in results) if results else True
    return {
        "success": True,
        "student_id": student_id,
        "day": day,
        "allowed": True,
        "sections": results,
        "note": ("No questions found for any section on this day" if all_empty else "")
    }
