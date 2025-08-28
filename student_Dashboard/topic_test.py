# student_Dashboard/topic_test.py

from typing import List, Dict, Any, Optional, Union

# Attempt to import ObjectId from bson, with a fallback for environments where it's not available.
try:
    from bson import ObjectId  # type: ignore
except Exception:  # pragma: no cover
    class ObjectId:  # fallback stub for type hinting
        pass

# This module contains the logic for selecting questions for a topic test.
# It fetches 10 questions for a given topic from the item_bank collection,
# prioritizing a match on skillCode and falling back to topic name.


def _json_sanitize(value: Any) -> Any:
    """
    Recursively sanitizes a value to make it JSON serializable.
    Converts ObjectId to string and handles nested dicts and lists.
    """
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _json_sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_sanitize(v) for v in value]
    # Fallback for unknown types
    try:
        return str(value)
    except Exception:
        return None


def _normalize_question(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a question document from the database into a consistent format.
    """
    # Core fields commonly used by consumers
    result: Dict[str, Any] = {
        "question_id": str(doc.get("_id")),
        "questionType": doc.get("questionType"),
        "section": doc.get("section"),
        "subject": doc.get("subject", doc.get("section")),
        "topic": doc.get("topic"),
        "skillCode": doc.get("skillCode"),
        "skillDescription": doc.get("skillDescription"),
        "difficultyLevel": doc.get("difficultyLevel"),
        "iseeLevel": doc.get("iseeLevel"),
        # IRT parameters
        "a_discrimination": doc.get("a_discrimination"),
        "b_difficulty": doc.get("b_difficulty"),
        # Content
        "questionTitle": doc.get("questionTitle"),
        "options": _json_sanitize(doc.get("options", {})),
        "correctOption": doc.get("correctOption"),
        "correctAnswer": doc.get("correctAnswer", doc.get("correctOption")),
        "questionImages": _json_sanitize(doc.get("questionImages", [])),
        "explanation": doc.get("explanation", ""),
    }

    # Include any additional fields from the document for completeness
    known_keys = set(result.keys()) | {"_id"}
    additional_fields = {k: v for k, v in doc.items() if k not in known_keys}
    if additional_fields:
        result["additional_fields"] = _json_sanitize(additional_fields)

    return result


def fetch_topic_questions(
    db_manager,
    topic_code: str,
    topic_name: Optional[str] = None,
    num_questions: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fetches a specified number of questions for a given topic from the item bank.
    It matches documents where skillCode equals the topic_code.

    Args:
        db_manager: The database manager instance.
        topic_code (str): The code of the topic to fetch questions for.
        topic_name (Optional[str], optional): The name of the topic (currently unused). Defaults to None.
        num_questions (int, optional): The number of questions to fetch. Defaults to 10.

    Returns:
        A list of normalized question dictionaries.
    """
    item_bank = db_manager.item_bank_collection

    # Fetch questions by skillCode and sample the specified number of questions
    docs = list(
        item_bank.aggregate([
            {"$match": {"skillCode": topic_code}},
            {"$sample": {"size": int(num_questions)}}
        ])
    )

    return [_normalize_question(d) for d in docs[:num_questions]]


def build_topic_test_for_day(
    db_manager,
    student_id: str,
    day: int,
) -> Dict[str, Any]:
    """
    Builds a topic test payload for a specific day based on the student's study plan.

    This function disallows topic tests on days with full-length or section tests and
    fetches 10 questions for each topic scheduled on that day.

    Args:
        db_manager: The database manager instance.
        student_id (str): The ID of the student.
        day (int): The day of the study plan to build the test for.

    Returns:
        A dictionary containing the topic test payload.
    """
    # Validate input parameters
    if not student_id or not isinstance(student_id, str):
        return {"success": False, "error": "Invalid student_id"}
    if not isinstance(day, int) or day <= 0:
        return {"success": False, "error": "Invalid day"}

    # Retrieve the student's study plan
    plans_col = db_manager.db["studyPlans"]
    plan_doc = plans_col.find_one({"student_id": student_id})
    if not plan_doc:
        return {"success": False, "error": "Study plan not found for student"}

    # Find the plan for the specified day
    daily_plans = plan_doc.get("daily_plans", [])
    target = next((dp for dp in daily_plans if dp.get("day") == day), None)
    if not target:
        return {"success": False, "error": "Requested day not found in study plan"}

    # Disallow topic tests on days with other types of tests
    tests = target.get("tests", [])
    if any(t.get("type") in ("full_length", "section") for t in tests):
        return {
            "success": True,
            "student_id": student_id,
            "day": day,
            "allowed": False,
            "reason": "Topic test not allowed on full-length or section-test days",
            "topics": []
        }

    # Fetch questions for each topic scheduled for the day
    results: List[Dict[str, Any]] = []
    for t in target.get("topics", []):
        topic_code = t.get("topic_code")
        topic_name = t.get("topic_name")
        questions = fetch_topic_questions(db_manager, topic_code=topic_code, topic_name=topic_name, num_questions=10)
        results.append({
            "topic_code": topic_code,
            "topic_name": topic_name,
            "questions_recommended": 10,
            "fetched_count": len(questions),
            "questions": questions,
            "no_questions": len(questions) == 0,
            "message": (f"No questions found for topic_code {topic_code}" if len(questions) == 0 else "")
        })

    # Check if any questions were found for any of the topics
    all_empty = all(r.get("fetched_count", 0) == 0 for r in results) if results else True

    return {
        "success": True,
        "student_id": student_id,
        "day": day,
        "allowed": True,
        "topics": results,
        "note": ("No questions found for any topics on this day" if all_empty else "")
    }


