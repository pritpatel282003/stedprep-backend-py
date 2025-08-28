from typing import List, Dict, Any, Optional, Tuple
import uuid
import logging
import random
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class TopicTestError(Exception):
    """Custom exception for topic test related errors"""
    pass

def build_adaptive_topic_test(
    db_manager,
    student_id: str,
    day: int,
) -> Dict[str, Any]:
    """
    Build an adaptive topic test for a student on a specific day.
    """
    if not student_id or not isinstance(student_id, str) or not re.match(r"^[a-zA-Z0-9_-]+$", student_id):
        logger.error(f"Invalid student_id: {student_id}")
        return {"success": False, "error": "Invalid student_id: must be alphanumeric with underscores or hyphens"}
    if not isinstance(day, int) or day <= 0:
        logger.error(f"Invalid day: {day}")
        return {"success": False, "error": "Invalid day: must be a positive integer"}

    try:
        study_plan = _fetch_study_plan(db_manager, student_id)
        logger.debug(f"Fetched study plan for {student_id}: {bool(study_plan)}")
        
        if not study_plan:
            return {"success": False, "error": "Study plan not found for student"}

        daily_plan = _get_daily_plan(study_plan, day)
        logger.debug(f"Daily plan for day {day}: {bool(daily_plan)}")
        
        if not daily_plan:
            return {"success": False, "error": "Requested day not found in study plan"}

        is_allowed, reason = _is_topic_test_allowed(daily_plan)
        if not is_allowed:
            logger.info(f"Topic test not allowed for student {student_id} on day {day}: {reason}")
            return {
                "success": True,
                "student_id": student_id,
                "day": day,
                "allowed": False,
                "reason": reason,
                "topics": []
            }

        topics_data = _generate_topic_tests(db_manager, student_id, daily_plan)
        successful_topics = [t for t in topics_data if not t.get("no_questions", True)]
        all_empty = len(successful_topics) == 0
        
        logger.info(f"Generated {len(successful_topics)}/{len(topics_data)} successful topic tests for student {student_id}")

        return {
            "success": True,
            "student_id": student_id,
            "day": day,
            "allowed": True,
            "topics": topics_data,
            "note": "No questions found for any topics on this day" if all_empty else "",
            "summary": {
                "total_topics": len(topics_data),
                "topics_with_questions": len(successful_topics),
                "total_questions": sum(topic.get("fetched_count", 0) for topic in topics_data)
            }
        }

    except Exception as e:
        logger.error(f"Error building adaptive topic test for student {student_id}, day {day}: {str(e)}", exc_info=True)
        return {"success": False, "error": f"Internal error while building topic test: {str(e)}"}

def _create_adaptive_topic_test(
    db_manager, 
    student_id: str, 
    topic_data: Dict
) -> Dict[str, Any]:
    """Create adaptive test for a single topic with enhanced session storage"""
    topic_code = topic_data.get("topic_code")
    topic_name = topic_data.get("topic_name")
    current_mastery = topic_data.get("current_mastery", 50)
    
    if isinstance(current_mastery, (list, tuple)):
        logger.warning(f"current_mastery is an array for topic {topic_name}: {current_mastery}. Using first value.")
        current_mastery = float(current_mastery[0]) if current_mastery else 50.0
    elif not isinstance(current_mastery, (int, float)):
        logger.error(f"Invalid current_mastery type for topic {topic_name}: {type(current_mastery)}")
        raise TopicTestError(f"Invalid current_mastery type: expected float, got {type(current_mastery)}")
    
    target_difficulty = topic_data.get("target_difficulty", "Medium")
    sprint_token = str(uuid.uuid4())
    
    try:
        starting_difficulties = _determine_starting_difficulty(current_mastery, target_difficulty)
        if not starting_difficulties:  # Mastery >= 90
            logger.info(f"Topic {topic_name} mastered (current_mastery={current_mastery})")
            return {
                "topic_code": topic_code,
                "topic_name": topic_name,
                "sprint_token": sprint_token,
                "current_mastery": current_mastery,
                "target_difficulty": target_difficulty,
                "starting_difficulty": None,
                "questions_recommended": 0,
                "fetched_count": 0,
                "questions": [],
                "no_questions": True,
                "message": f"Topic {topic_name} mastered (current_mastery={current_mastery}%)",
                "adaptive_config": {
                    "difficulty_progression": _get_difficulty_progression_rules(),
                    "mastery_thresholds": _get_mastery_thresholds()
                }
            }
        
        questions = _fetch_questions_from_item_bank(
            db_manager, 
            topic_code, 
            difficulty=starting_difficulties,
            count=5,
            skill_field="skillCode"
        )
        
        if not questions:
            logger.warning(f"No questions found in item_bank for topic {topic_name} (skillCode: {topic_code})")
            return {
                "topic_code": topic_code,
                "topic_name": topic_name,
                "sprint_token": sprint_token,
                "current_mastery": current_mastery,
                "target_difficulty": target_difficulty,
                "starting_difficulty": starting_difficulties,
                "questions_recommended": 5,
                "fetched_count": 0,
                "questions": [],
                "no_questions": True,
                "message": f"No questions found for topic {topic_name} (skillCode: {topic_code})",
                "adaptive_config": {
                    "difficulty_progression": _get_difficulty_progression_rules(),
                    "mastery_thresholds": _get_mastery_thresholds()
                }
            }
        
        # Create enhanced adaptive session with complete exam structure
        question_ids = [q["question_id"] for q in questions]
        adaptive_session = {
            "session_id": sprint_token,
            "student_id": student_id,
            "topic_code": topic_code,
            "topic_name": topic_name,
            "current_difficulty": starting_difficulties,
            "current_mastery": current_mastery,
            "initial_mastery": current_mastery,
            "target_difficulty": target_difficulty,
            "questions_answered": 0,
            "correct_answers": 0,
            "performance": 0.0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "status": "active",
            "current_question_ids": question_ids,
            # Enhanced exam storage structure
            "exam_data": {
                "batches": [
                    {
                        "batch_number": 1,
                        "difficulty": starting_difficulties[0] if isinstance(starting_difficulties, list) else starting_difficulties,
                        "questions": [
                            {
                                "question_id": q["question_id"],
                                "question_text": q["question_text"],
                                "options": q["options"],
                                "correct_answer": q["correct_answer"],
                                "difficulty": q["difficulty"],
                                "topic_code": q["topic_code"],
                                "skillCode": q["skillCode"],
                                "subtopic": q.get("subtopic"),
                                "explanation": q.get("explanation"),
                                "time_limit_seconds": q.get("time_limit_seconds", 120),
                                # Answer fields - will be filled when answered
                                "student_answer": None,
                                "is_correct": None,
                                "time_taken": None,
                                "submitted_at": None,
                                "answered": False
                            } for q in questions
                        ],
                        "batch_performance": None,
                        "batch_completed": False,
                        "completed_at": None
                    }
                ],
                "overall_performance": 0.0,
                "difficulty_progression": [starting_difficulties[0] if isinstance(starting_difficulties, list) else starting_difficulties],
                "total_questions_answered": 0,
                "total_correct_answers": 0
            }
        }
        
        _store_adaptive_session(db_manager, adaptive_session)
        
        return {
            "topic_code": topic_code,
            "topic_name": topic_name,
            "sprint_token": sprint_token,
            "current_mastery": current_mastery,
            "target_difficulty": target_difficulty,
            "starting_difficulty": starting_difficulties,
            "questions_recommended": 5,
            "fetched_count": len(questions),
            "questions": questions,
            "no_questions": False,
            "session_expires_at": adaptive_session["expires_at"],
            "adaptive_config": {
                "difficulty_progression": _get_difficulty_progression_rules(),
                "mastery_thresholds": _get_mastery_thresholds(),
                "next_batch_endpoint": f"/sprint/next-questions/{sprint_token}",
                "grade_endpoint": f"/sprint/grade-answers/{sprint_token}"
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating adaptive test for topic {topic_name} (code: {topic_code}): {str(e)}")
        raise TopicTestError(f"Failed to generate adaptive test for {topic_name}: {str(e)}")

def grade_and_store_answers(
    db_manager,
    sprint_token: str,
    answers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Grade answers and store complete exam data in adaptiveSession"""
    try:
        sessions_col = db_manager.db["adaptiveSessions"]
        session = sessions_col.find_one({"session_id": sprint_token})
        if not session:
            logger.error(f"Adaptive session not found for sprint_token={sprint_token}")
            return {"success": False, "error": "Adaptive session not found"}

        # Validate answers against current question IDs
        valid_question_ids = session.get("current_question_ids", [])
        if not valid_question_ids:
            logger.error(f"No current question IDs in session for sprint_token={sprint_token}")
            return {
                "success": False,
                "error": "No questions assigned to this session",
                "sprint_token": sprint_token
            }

        # Validate answers
        if not answers:
            logger.warning(f"No answers provided for sprint_token={sprint_token}")
            return {
                "success": False,
                "error": "No answers provided",
                "sprint_token": sprint_token,
                "performance": 0.0,
                "total_questions": 0,
                "correct_questions": 0
            }

        # Get exam data
        exam_data = session.get("exam_data", {})
        batches = exam_data.get("batches", [])
        
        if not batches:
            logger.error(f"No exam batches found for sprint_token={sprint_token}")
            return {
                "success": False,
                "error": "No exam data found in session",
                "sprint_token": sprint_token
            }

        # Find current batch (last incomplete batch)
        current_batch = None
        current_batch_index = -1
        for i, batch in enumerate(batches):
            if not batch.get("batch_completed", False):
                current_batch = batch
                current_batch_index = i
                break
        
        if not current_batch:
            logger.error(f"No active batch found for sprint_token={sprint_token}")
            return {
                "success": False,
                "error": "No active batch found",
                "sprint_token": sprint_token
            }

        # Validate and process answers
        processed_answers = []
        answered_question_ids = []
        
        for answer in answers:
            question_id = answer.get("question_id")
            if not question_id or "is_correct" not in answer:
                logger.error(f"Invalid answer format: {answer}")
                return {
                    "success": False,
                    "error": f"Invalid answer format for question_id={question_id}",
                    "sprint_token": sprint_token
                }
            
            if question_id not in valid_question_ids:
                logger.error(f"Invalid question_id {question_id} for sprint_token={sprint_token}")
                return {
                    "success": False,
                    "error": f"Question ID {question_id} not assigned to current batch",
                    "sprint_token": sprint_token
                }
            
            # Find the question in current batch and update it
            question_found = False
            for question in current_batch["questions"]:
                if question["question_id"] == question_id:
                    if question.get("answered", False):
                        logger.warning(f"Duplicate answer submission for question_id={question_id}")
                        return {
                            "success": False,
                            "error": f"Duplicate answer submission for question_id={question_id}",
                            "sprint_token": sprint_token
                        }
                    
                    # Update question with answer details
                    question["student_answer"] = answer.get("student_answer")
                    question["is_correct"] = answer.get("is_correct", False)
                    question["time_taken"] = answer.get("time_taken", 0)
                    question["submitted_at"] = answer.get("submitted_at", datetime.utcnow().isoformat())
                    question["answered"] = True
                    
                    processed_answers.append({
                        "question_id": question_id,
                        "is_correct": answer.get("is_correct", False),
                        "student_answer": answer.get("student_answer"),
                        "correct_answer": question["correct_answer"],
                        "difficulty": question["difficulty"]
                    })
                    answered_question_ids.append(question_id)
                    question_found = True
                    break
            
            if not question_found:
                logger.error(f"Question {question_id} not found in current batch")
                return {
                    "success": False,
                    "error": f"Question {question_id} not found in current batch",
                    "sprint_token": sprint_token
                }

        # Calculate batch performance
        total_questions = len(processed_answers)
        correct_questions = sum(1 for ans in processed_answers if ans["is_correct"])
        batch_performance = correct_questions / total_questions if total_questions > 0 else 0.0

        # Update current batch
        current_batch["batch_performance"] = batch_performance
        current_batch["batch_completed"] = True
        current_batch["completed_at"] = datetime.utcnow().isoformat()

        # Update overall exam statistics
        total_answered_questions = exam_data.get("total_questions_answered", 0) + total_questions
        total_correct_answers = exam_data.get("total_correct_answers", 0) + correct_questions
        overall_performance = total_correct_answers / total_answered_questions if total_answered_questions > 0 else 0.0

        exam_data["total_questions_answered"] = total_answered_questions
        exam_data["total_correct_answers"] = total_correct_answers
        exam_data["overall_performance"] = overall_performance

        # Update current mastery based on overall performance
        current_mastery = session.get("current_mastery", 50.0)
        new_mastery = _calculate_updated_mastery(current_mastery, overall_performance, total_answered_questions)

        # Update study plan mastery
        _update_study_plan_mastery(db_manager, session.get("student_id"), session.get("topic_code"), new_mastery)

        # Update adaptive session
        sessions_col.update_one(
            {"session_id": sprint_token},
            {
                "$set": {
                    "exam_data": exam_data,
                    "current_mastery": new_mastery,
                    "performance": overall_performance,
                    "questions_answered": total_answered_questions,
                    "correct_answers": total_correct_answers,
                    "updated_at": datetime.utcnow().isoformat(),
                    "status": "completed" if new_mastery >= 90 else "active",
                    "current_question_ids": []  # Clear current questions as they're now answered
                }
            }
        )

        logger.info(f"Graded {total_questions} answers for sprint_token={sprint_token}, batch_performance={batch_performance:.2%}, overall_performance={overall_performance:.2%}, new_mastery={new_mastery:.2f}")
        
        message = f"Graded {correct_questions}/{total_questions} correct in current batch. Overall: {total_correct_answers}/{total_answered_questions} ({overall_performance:.1%})"
        if new_mastery >= 90:
            message += f". Topic mastered (current_mastery={new_mastery:.1f}%)"

        return {
            "success": True,
            "sprint_token": sprint_token,
            "batch_performance": batch_performance,
            "overall_performance": overall_performance,
            "total_questions": total_questions,
            "correct_questions": correct_questions,
            "total_answered_questions": total_answered_questions,
            "total_correct_answers": total_correct_answers,
            "current_mastery": new_mastery,
            "batch_number": current_batch_index + 1,
            "message": message,
            "exam_summary": {
                "batches_completed": sum(1 for batch in batches if batch.get("batch_completed", False)),
                "total_batches": len(batches),
                "mastery_achieved": new_mastery >= 90
            }
        }

    except Exception as e:
        logger.error(f"Error grading answers for sprint_token={sprint_token}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to grade answers: {str(e)}",
            "sprint_token": sprint_token,
            "performance": 0.0,
            "total_questions": 0,
            "correct_questions": 0
        }

def get_next_adaptive_questions(
    db_manager,
    sprint_token: str,
    previous_answers: List[Dict[str, Any]] = None  # Keep for backward compatibility
) -> Dict[str, Any]:
    """Get next set of adaptive questions based on stored exam data"""
    try:
        sessions_col = db_manager.db["adaptiveSessions"]
        session = sessions_col.find_one({"session_id": sprint_token})
        if not session:
            logger.error(f"Adaptive session not found for sprint_token={sprint_token}")
            return {"success": False, "error": "Adaptive session not found"}

        # Check if topic is mastered
        current_mastery = session.get("current_mastery", 50.0)
        if current_mastery >= 90:
            logger.info(f"Topic {session.get('topic_code')} mastered (current_mastery={current_mastery})")
            return {
                "success": True,
                "sprint_token": sprint_token,
                "performance": session.get("performance", 0.0),
                "previous_difficulty": session.get("current_difficulty", []),
                "current_difficulty": [],
                "questions": [],
                "fetched_count": 0,
                "message": f"Topic {session.get('topic_code')} mastered (current_mastery={current_mastery:.1f}%)",
                "mastery_achieved": True
            }

        # Get exam data from session
        exam_data = session.get("exam_data", {})
        if not exam_data or not exam_data.get("batches"):
            logger.error(f"No exam data found for sprint_token={sprint_token}")
            return {
                "success": False,
                "error": "No exam data found. Please answer some questions first.",
                "sprint_token": sprint_token
            }

        # Analyze performance from exam data
        performance_analysis = _analyze_exam_performance(exam_data)
        
        # Determine next difficulty based on performance analysis
        current_difficulty = session.get("current_difficulty", ["Medium"])
        current_difficulty_str = current_difficulty[0] if isinstance(current_difficulty, list) else current_difficulty
        
        next_difficulty = _determine_next_difficulty_from_exam_analysis(
            current_difficulty_str, 
            performance_analysis,
            exam_data.get("difficulty_progression", [])
        )
        
        logger.info(f"Performance analysis: {performance_analysis}")
        logger.info(f"Difficulty progression: {current_difficulty_str} -> {next_difficulty}")
        
        # Get all previously answered question IDs from exam data
        answered_question_ids = []
        for batch in exam_data.get("batches", []):
            answered_question_ids.extend([q["question_id"] for q in batch.get("questions", []) if q.get("answered", False)])
        
        # Fetch new questions with the determined difficulty
        questions = _fetch_questions_from_item_bank(
            db_manager,
            session.get("topic_code"),
            difficulty=[next_difficulty],
            count=5,
            skill_field="skillCode",
            exclude_ids=answered_question_ids
        )
        
        if not questions:
            logger.warning(f"No more questions available for topic {session.get('topic_code')} at difficulty {next_difficulty}")
            # Try with fallback difficulty
            fallback_difficulties = _get_fallback_difficulties(next_difficulty)
            for fallback_diff in fallback_difficulties:
                questions = _fetch_questions_from_item_bank(
                    db_manager,
                    session.get("topic_code"),
                    difficulty=[fallback_diff],
                    count=5,
                    skill_field="skillCode",
                    exclude_ids=answered_question_ids
                )
                if questions:
                    next_difficulty = fallback_diff
                    logger.info(f"Using fallback difficulty: {fallback_diff}")
                    break
            
            if not questions:
                return {
                    "success": True,
                    "sprint_token": sprint_token,
                    "performance": performance_analysis["overall_performance"],
                    "previous_difficulty": current_difficulty,
                    "current_difficulty": [next_difficulty],
                    "questions": [],
                    "fetched_count": 0,
                    "message": f"No more questions available for topic {session.get('topic_code')}",
                    "session_complete": True,
                    "final_exam_summary": _generate_exam_summary(exam_data)
                }
        
        # Create new batch in exam data
        new_batch_number = len(exam_data.get("batches", [])) + 1
        new_batch = {
            "batch_number": new_batch_number,
            "difficulty": next_difficulty,
            "questions": [
                {
                    "question_id": q["question_id"],
                    "question_text": q["question_text"],
                    "options": q["options"],
                    "correct_answer": q["correct_answer"],
                    "difficulty": q["difficulty"],
                    "topic_code": q["topic_code"],
                    "skillCode": q["skillCode"],
                    "subtopic": q.get("subtopic"),
                    "explanation": q.get("explanation"),
                    "time_limit_seconds": q.get("time_limit_seconds", 120),
                    # Answer fields - will be filled when answered
                    "student_answer": None,
                    "is_correct": None,
                    "time_taken": None,
                    "submitted_at": None,
                    "answered": False
                } for q in questions
            ],
            "batch_performance": None,
            "batch_completed": False,
            "completed_at": None
        }
        
        # Update exam data and session
        exam_data["batches"].append(new_batch)
        exam_data["difficulty_progression"].append(next_difficulty)
        
        question_ids = [q["question_id"] for q in questions]
        
        sessions_col.update_one(
            {"session_id": sprint_token},
            {
                "$set": {
                    "exam_data": exam_data,
                    "current_difficulty": [next_difficulty],
                    "current_question_ids": question_ids,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {
            "success": True,
            "sprint_token": sprint_token,
            "performance": performance_analysis["overall_performance"],
            "recent_performance": performance_analysis["recent_performance"],
            "previous_difficulty": current_difficulty_str,
            "current_difficulty": next_difficulty,
            "questions": questions,
            "fetched_count": len(questions),
            "batch_number": new_batch_number,
            "performance_analysis": performance_analysis,
            "difficulty_progression": exam_data.get("difficulty_progression", []),
            "total_questions_answered": exam_data.get("total_questions_answered", 0),
            "exam_progress": {
                "batches_completed": sum(1 for batch in exam_data.get("batches", []) if batch.get("batch_completed", False)),
                "total_batches": len(exam_data.get("batches", []))
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting next adaptive questions for sprint_token={sprint_token}: {str(e)}", exc_info=True)
        return {"success": False, "error": f"Failed to get next questions: {str(e)}"}

def get_exam_summary(db_manager, sprint_token: str) -> Dict[str, Any]:
    """Get complete exam summary with all questions and answers"""
    try:
        sessions_col = db_manager.db["adaptiveSessions"]
        session = sessions_col.find_one({"session_id": sprint_token})
        if not session:
            return {"success": False, "error": "Adaptive session not found"}

        exam_data = session.get("exam_data", {})
        if not exam_data:
            return {"success": False, "error": "No exam data found"}

        summary = _generate_exam_summary(exam_data)
        summary.update({
            "success": True,
            "sprint_token": sprint_token,
            "student_id": session.get("student_id"),
            "topic_code": session.get("topic_code"),
            "topic_name": session.get("topic_name"),
            "current_mastery": session.get("current_mastery"),
            "initial_mastery": session.get("initial_mastery"),
            "session_status": session.get("status"),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at")
        })

        return summary

    except Exception as e:
        logger.error(f"Error getting exam summary for sprint_token={sprint_token}: {str(e)}", exc_info=True)
        return {"success": False, "error": f"Failed to get exam summary: {str(e)}"}

def _analyze_exam_performance(exam_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze performance from complete exam data"""
    batches = exam_data.get("batches", [])
    completed_batches = [batch for batch in batches if batch.get("batch_completed", False)]
    
    if not completed_batches:
        return {
            "overall_performance": 0.0,
            "recent_performance": 0.0,
            "total_answered": 0,
            "total_correct": 0,
            "recent_answered": 0,
            "recent_correct": 0,
            "performance_trend": "neutral",
            "difficulty_breakdown": {},
            "batch_performances": []
        }
    
    # Calculate overall performance
    all_questions = []
    batch_performances = []
    
    for batch in completed_batches:
        answered_questions = [q for q in batch.get("questions", []) if q.get("answered", False)]
        all_questions.extend(answered_questions)
        
        if answered_questions:
            batch_correct = sum(1 for q in answered_questions if q.get("is_correct", False))
            batch_performance = batch_correct / len(answered_questions)
            batch_performances.append({
                "batch_number": batch.get("batch_number"),
                "difficulty": batch.get("difficulty"),
                "performance": batch_performance,
                "questions_count": len(answered_questions),
                "correct_count": batch_correct
            })
    
    total_answered = len(all_questions)
    total_correct = sum(1 for q in all_questions if q.get("is_correct", False))
    overall_performance = total_correct / total_answered if total_answered > 0 else 0.0
    
    # Calculate recent performance (last batch or last 5 questions)
    if completed_batches:
        recent_batch = completed_batches[-1]
        recent_questions = [q for q in recent_batch.get("questions", []) if q.get("answered", False)]
    else:
        recent_questions = all_questions[-5:] if len(all_questions) >= 5 else all_questions
    
    recent_answered = len(recent_questions)
    recent_correct = sum(1 for q in recent_questions if q.get("is_correct", False))
    recent_performance = recent_correct / recent_answered if recent_answered > 0 else 0.0
    
    # Determine performance trend
    if len(batch_performances) >= 2:
        last_two_performances = [bp["performance"] for bp in batch_performances[-2:]]
        if last_two_performances[1] > last_two_performances[0] + 0.1:
            performance_trend = "improving"
        elif last_two_performances[1] < last_two_performances[0] - 0.1:
            performance_trend = "declining"
        else:
            performance_trend = "stable"
    else:
        performance_trend = "neutral"
    
    # Analyze performance by difficulty
    difficulty_breakdown = {}
    for question in all_questions:
        difficulty = question.get("difficulty", "Medium")
        if difficulty not in difficulty_breakdown:
            difficulty_breakdown[difficulty] = {"correct": 0, "total": 0}
        difficulty_breakdown[difficulty]["total"] += 1
        if question.get("is_correct", False):
            difficulty_breakdown[difficulty]["correct"] += 1
    
    return {
        "overall_performance": overall_performance,
        "recent_performance": recent_performance,
        "total_answered": total_answered,
        "total_correct": total_correct,
        "recent_answered": recent_answered,
        "recent_correct": recent_correct,
        "performance_trend": performance_trend,
        "difficulty_breakdown": difficulty_breakdown,
        "batch_performances": batch_performances,
        "consistency_score": _calculate_consistency_score(batch_performances)
    }

def _determine_next_difficulty_from_exam_analysis(
    current_difficulty: str, 
    performance_analysis: Dict[str, Any],
    difficulty_progression: List[str]
) -> str:
    """Determine next difficulty based on comprehensive exam performance analysis"""
    difficulty_levels = ["Very Easy", "Easy", "Medium", "Hard"]
    current_index = difficulty_levels.index(current_difficulty) if current_difficulty in difficulty_levels else 2
    
    overall_performance = performance_analysis["overall_performance"]
    recent_performance = performance_analysis["recent_performance"]
    performance_trend = performance_analysis["performance_trend"]
    total_answered = performance_analysis["total_answered"]
    consistency_score = performance_analysis.get("consistency_score", 0.5)
    
    # Weight recent performance more heavily, but consider overall performance and consistency
    weighted_performance = (overall_performance * 0.3) + (recent_performance * 0.5) + (consistency_score * 0.2)
    
    logger.debug(f"Performance analysis: overall={overall_performance:.2%}, recent={recent_performance:.2%}, weighted={weighted_performance:.2%}, trend={performance_trend}, consistency={consistency_score:.2f}")
    
    # Determine difficulty adjustment based on weighted performance and trends
    if weighted_performance >= 0.85 and performance_trend != "declining" and consistency_score > 0.7:
        # Excellent performance with good consistency - increase difficulty
        next_index = min(current_index + 1, len(difficulty_levels) - 1)
        logger.debug("Excellent performance with consistency - increasing difficulty")
    elif weighted_performance >= 0.75 and performance_trend == "improving":
        # Good performance with improvement trend - increase difficulty
        next_index = min(current_index + 1, len(difficulty_levels) - 1)
        logger.debug("Good performance with improvement - increasing difficulty")
    elif weighted_performance >= 0.65 and consistency_score > 0.6:
        # Good performance with decent consistency - maintain difficulty
        next_index = current_index
        logger.debug("Good performance with consistency - maintaining difficulty")
    elif weighted_performance >= 0.5:
        # Average performance - maintain or slight decrease based on trend
        if performance_trend == "declining":
            next_index = max(current_index - 1, 0)
            logger.debug("Average performance declining - decreasing difficulty")
        else:
            next_index = current_index
            logger.debug("Average performance stable - maintaining difficulty")
    elif weighted_performance >= 0.35:
        # Below average - decrease difficulty
        next_index = max(current_index - 1, 0)
        logger.debug("Below average performance - decreasing difficulty")
    else:
        # Poor performance - significant decrease
        next_index = max(current_index - 2, 0)
        logger.debug("Poor performance - significantly decreasing difficulty")
    
    # Prevent rapid difficulty oscillations
    if len(difficulty_progression) >= 3:
        last_three = difficulty_progression[-3:]
        if len(set(last_three)) == 2:  # Oscillating between two levels
            # Stick with current difficulty to stabilize
            next_index = current_index
            logger.debug("Preventing difficulty oscillation - maintaining current level")
    
    return difficulty_levels[next_index]

def _calculate_consistency_score(batch_performances: List[Dict[str, Any]]) -> float:
    """Calculate consistency score based on performance variation across batches"""
    if len(batch_performances) < 2:
        return 0.5  # Neutral score for insufficient data
    
    performances = [bp["performance"] for bp in batch_performances]
    
    # Calculate standard deviation of performances
    mean_performance = sum(performances) / len(performances)
    variance = sum((p - mean_performance) ** 2 for p in performances) / len(performances)
    std_deviation = variance ** 0.5
    
    # Convert to consistency score (lower std_dev = higher consistency)
    # Scale from 0 to 1, where 1 is perfect consistency
    consistency_score = max(0, 1 - (std_deviation * 2))  # * 2 to make it more sensitive
    
    return min(1.0, consistency_score)

def _calculate_updated_mastery(current_mastery: float, performance: float, total_questions: int) -> float:
    """Calculate updated mastery based on performance with question count weighting"""
    # Weight the update based on number of questions answered
    weight = min(1.0, total_questions / 20.0)  # Full weight at 20+ questions
    
    # Convert performance to mastery points (0-100)
    performance_mastery = performance * 100
    
    # Blend current mastery with performance-based mastery
    new_mastery = (current_mastery * (1 - weight * 0.4)) + (performance_mastery * weight * 0.4)
    
    return min(100.0, max(0.0, new_mastery))

def _generate_exam_summary(exam_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive exam summary"""
    batches = exam_data.get("batches", [])
    completed_batches = [batch for batch in batches if batch.get("batch_completed", False)]
    
    # Collect all questions and answers
    all_questions_detail = []
    difficulty_stats = {}
    
    for batch in batches:
        for question in batch.get("questions", []):
            difficulty = question.get("difficulty", "Medium")
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {"total": 0, "correct": 0, "answered": 0}
            
            difficulty_stats[difficulty]["total"] += 1
            
            question_detail = {
                "batch_number": batch.get("batch_number"),
                "question_id": question.get("question_id"),
                "question_text": question.get("question_text"),
                "options": question.get("options"),
                "correct_answer": question.get("correct_answer"),
                "difficulty": difficulty,
                "answered": question.get("answered", False)
            }
            
            if question.get("answered", False):
                difficulty_stats[difficulty]["answered"] += 1
                question_detail.update({
                    "student_answer": question.get("student_answer"),
                    "is_correct": question.get("is_correct"),
                    "time_taken": question.get("time_taken"),
                    "submitted_at": question.get("submitted_at")
                })
                
                if question.get("is_correct", False):
                    difficulty_stats[difficulty]["correct"] += 1
            
            all_questions_detail.append(question_detail)
    
    # Calculate performance metrics
    total_questions = exam_data.get("total_questions_answered", 0)
    total_correct = exam_data.get("total_correct_answers", 0)
    overall_performance = exam_data.get("overall_performance", 0.0)
    
    return {
        "exam_overview": {
            "total_batches": len(batches),
            "completed_batches": len(completed_batches),
            "total_questions_attempted": total_questions,
            "total_correct_answers": total_correct,
            "overall_performance": overall_performance,
            "difficulty_progression": exam_data.get("difficulty_progression", [])
        },
        "batch_summary": [
            {
                "batch_number": batch.get("batch_number"),
                "difficulty": batch.get("difficulty"),
                "questions_count": len(batch.get("questions", [])),
                "completed": batch.get("batch_completed", False),
                "performance": batch.get("batch_performance"),
                "completed_at": batch.get("completed_at")
            } for batch in batches
        ],
        "difficulty_breakdown": {
            difficulty: {
                "total_questions": stats["total"],
                "answered_questions": stats["answered"],
                "correct_answers": stats["correct"],
                "accuracy": stats["correct"] / stats["answered"] if stats["answered"] > 0 else 0.0
            } for difficulty, stats in difficulty_stats.items()
        },
        "detailed_questions": all_questions_detail,
        "performance_trends": {
            "batch_performances": [batch.get("batch_performance") for batch in completed_batches if batch.get("batch_performance") is not None],
            "consistency_score": _calculate_consistency_score([
                {"performance": batch.get("batch_performance", 0)} 
                for batch in completed_batches 
                if batch.get("batch_performance") is not None
            ])
        }
    }

def _get_fallback_difficulties(target_difficulty: str) -> List[str]:
    """Get fallback difficulties when target difficulty has no questions"""
    difficulty_fallbacks = {
        "Very Easy": ["Easy", "Medium"],
        "Easy": ["Very Easy", "Medium", "Hard"],
        "Medium": ["Easy", "Hard", "Very Easy"],
        "Hard": ["Medium", "Easy", "Very Easy"]
    }
    return difficulty_fallbacks.get(target_difficulty, ["Easy", "Medium"])

# Helper functions from original code
def _fetch_study_plan(db_manager, student_id: str) -> Optional[Dict]:
    """Fetch study plan for a student from database"""
    try:
        plans_col = db_manager.db["studyPlans"]
        study_plan = plans_col.find_one({"student_id": student_id})
        if study_plan:
            logger.debug(f"Found study plan for student {student_id}")
        else:
            logger.warning(f"No study plan found for student {student_id}")
        return study_plan
    except Exception as e:
        logger.error(f"Database error fetching study plan for {student_id}: {str(e)}")
        return None

def _get_daily_plan(study_plan: Dict, day: int) -> Optional[Dict]:
    """Extract daily plan for a specific day"""
    daily_plans = study_plan.get("daily_plans", [])
    daily_plan = next((dp for dp in daily_plans if dp.get("day") == day), None)
    if daily_plan:
        logger.debug(f"Found daily plan for day {day}")
    else:
        logger.warning(f"No daily plan found for day {day}")
    return daily_plan

def _is_topic_test_allowed(daily_plan: Dict) -> Tuple[bool, Optional[str]]:
    """Check if topic tests are allowed on this day"""
    tests = daily_plan.get("tests", [])
    restricted_types = {"full_length", "section"}
    restricted_tests = [test for test in tests if test.get("type") in restricted_types]
    if restricted_tests:
        test_types = [test.get("type") for test in restricted_tests]
        return False, f"Topic test not allowed on {', '.join(test_types)} test days"
    return True, None

def _generate_topic_tests(
    db_manager, 
    student_id: str, 
    daily_plan: Dict
) -> List[Dict[str, Any]]:
    """Generate adaptive tests for all topics in the daily plan"""
    results = []
    topics = daily_plan.get("topics", [])
    logger.info(f"Generating topic tests for {len(topics)} topics")
    
    for topic in topics:
        topic_code = topic.get("topic_code")
        topic_name = topic.get("topic_name")
        if not topic_code or not topic_name:
            logger.warning(f"Skipping topic with missing data: {topic}")
            continue
        try:
            topic_test_data = _create_adaptive_topic_test(db_manager, student_id, topic)
            results.append(topic_test_data)
            question_count = topic_test_data.get("fetched_count", 0)
            logger.debug(f"Generated {question_count} questions for topic {topic_name} (code: {topic_code})")
        except Exception as e:
            logger.error(f"Error creating test for topic {topic_name} (code: {topic_code}): {str(e)}")
            results.append({
                "topic_code": topic_code,
                "topic_name": topic_name,
                "sprint_token": None,
                "questions_recommended": 5,
                "fetched_count": 0,
                "questions": [],
                "no_questions": True,
                "message": f"Error generating questions for topic {topic_name}",
                "error": str(e)
            })
    return results

def _determine_starting_difficulty(current_mastery: float, target_difficulty: str) -> Optional[List[str]]:
    """Determine starting difficulty levels based on current mastery level"""
    mastery_level = float(current_mastery) if current_mastery else 50.0
    if mastery_level >= 90:
        return None  # No questions if mastered
    elif mastery_level >= 70:
        return ["Medium", "Hard"]  # Mix of Medium and Hard for mastery 70-89
    elif mastery_level >= 50:
        return ["Easy", "Medium"]  # Mix of Easy and Medium for mastery 50-69
    elif mastery_level >= 30:
        return ["Very Easy", "Easy"]  # Mix of Very Easy and Easy for mastery 30-49
    else:
        return ["Very Easy"]  # Only Very Easy for mastery < 30

def _fetch_questions_from_item_bank(
    db_manager, 
    topic_code: str, 
    difficulty: Optional[List[str]] = None, 
    count: int = 5,
    skill_field: str = "skillCode",
    exclude_ids: List = None
) -> List[Dict[str, Any]]:
    """Fetch questions from item bank based on topic/skill and difficulty"""
    if exclude_ids is None:
        exclude_ids = []
    if not difficulty:
        return []
    
    try:
        item_bank_col = db_manager.db["item_bank"]
        logger.debug(f"Accessing item_bank collection: {item_bank_col}")
        
        questions = []
        if isinstance(difficulty, list) and len(difficulty) > 1:
            # Allocate questions: aim for 60% from first difficulty, 40% from second
            primary_count = max(1, int(count * 0.6))  # e.g., 3 for count=5
            secondary_count = count - primary_count   # e.g., 2 for count=5
            
            for diff, num in [(difficulty[0], primary_count), (difficulty[1], secondary_count)]:
                query = {
                    skill_field: topic_code,
                    "difficultyLevel": diff,
                    "isActive": True,
                    "question_id": {"$nin": exclude_ids}
                }
                logger.debug(f"Querying item_bank with: {query}")
                questions_cursor = item_bank_col.find(query).limit(num)
                batch_questions = list(questions_cursor)
                questions.extend(batch_questions)
                exclude_ids.extend([q.get("question_id") for q in batch_questions])
        else:
            # Single difficulty
            diff = difficulty[0] if isinstance(difficulty, list) else difficulty
            query = {
                skill_field: topic_code,
                "difficultyLevel": diff,
                "isActive": True,
                "question_id": {"$nin": exclude_ids}
            }
            logger.debug(f"Querying item_bank with: {query}")
            questions_cursor = item_bank_col.find(query).limit(count)
            questions = list(questions_cursor)
        
        logger.debug(f"Found {len(questions)} questions for {skill_field}={topic_code}, difficulty={difficulty}")
        
        # If we don't have enough questions, try fallback difficulties
        if len(questions) < count:
            logger.info(f"Only found {len(questions)} questions for {skill_field}={topic_code}, difficulty={difficulty}")
            additional_questions = _fetch_fallback_questions(
                db_manager, topic_code, difficulty[0] if isinstance(difficulty, list) else difficulty,
                count - len(questions), 
                exclude_ids=[q.get("question_id") for q in questions] + exclude_ids,
                skill_field=skill_field
            )
            questions.extend(additional_questions)
        
        # Shuffle and format questions
        random.shuffle(questions)
        questions = questions[:count]
        
        formatted_questions = []
        for question in questions:
            options = question.get("options", {})
            if isinstance(options, dict):
                formatted_options = [f"{key}: {value}" for key, value in options.items()]
            elif isinstance(options, list):
                formatted_options = options
            else:
                logger.error(f"Invalid options format for question_id={question.get('question_id')}: {options}")
                continue
                
            formatted_question = {
                "question_id": str(question.get("question_id")),
                "question_text": question.get("questionTitle"),
                "options": formatted_options,
                "correct_answer": question.get("correctOption"),
                "difficulty": question.get("difficultyLevel"),
                "topic_code": question.get("topic_code", question.get("skillCode")),
                "skillCode": question.get("skillCode"),
                "subtopic": question.get("topic"),
                "explanation": question.get("explanation"),
                "time_limit_seconds": question.get("time_limit_seconds", 120)
            }
            formatted_questions.append(formatted_question)
        
        logger.info(f"Formatted {len(formatted_questions)} questions for {skill_field}={topic_code} at difficulty={difficulty}")
        return formatted_questions
        
    except Exception as e:
        logger.error(f"Error fetching questions from item_bank for {skill_field}={topic_code}: {str(e)}", exc_info=True)
        return []

def _fetch_fallback_questions(
    db_manager, 
    topic_code: str, 
    original_difficulty: str, 
    count: int,
    exclude_ids: List = None,
    skill_field: str = "skillCode"
) -> List[Dict[str, Any]]:
    """Fetch additional questions with different difficulties as fallback"""
    if exclude_ids is None:
        exclude_ids = []
    
    difficulty_order = {
        "Very Easy": ["Easy", "Medium", "Hard"],
        "Easy": ["Very Easy", "Medium", "Hard"],
        "Medium": ["Easy", "Hard", "Very Easy"],
        "Hard": ["Medium", "Easy", "Very Easy"]
    }
    
    fallback_difficulties = difficulty_order.get(original_difficulty, ["Easy", "Medium", "Hard"])
    additional_questions = []
    
    try:
        item_bank_col = db_manager.db["item_bank"]
        for difficulty in fallback_difficulties:
            if len(additional_questions) >= count:
                break
            query = {
                skill_field: topic_code,
                "difficultyLevel": difficulty,
                "isActive": True,
                "question_id": {"$nin": exclude_ids}
            }
            logger.debug(f"Fallback query for {skill_field}={topic_code}, difficultyLevel={difficulty}: {query}")
            needed = count - len(additional_questions)
            questions_cursor = item_bank_col.find(query).limit(needed)
            questions = list(questions_cursor)
            additional_questions.extend(questions)
            exclude_ids.extend([q.get("question_id") for q in questions])
        
        logger.info(f"Fetched {len(additional_questions)} fallback questions for {skill_field}={topic_code}")
        return additional_questions
        
    except Exception as e:
        logger.error(f"Error fetching fallback questions for {skill_field}={topic_code}: {str(e)}", exc_info=True)
        return []

def _store_adaptive_session(db_manager, session_data: Dict):
    """Store adaptive test session data in database"""
    try:
        sessions_col = db_manager.db["adaptiveSessions"]
        sessions_col.insert_one(session_data)
        logger.debug(f"Stored adaptive session {session_data['session_id']}")
    except Exception as e:
        logger.error(f"Error storing adaptive session: {str(e)}")

def _update_study_plan_mastery(db_manager, student_id: str, topic_code: str, new_mastery: float):
    """Update current_mastery in studyPlans for a specific topic"""
    try:
        plans_col = db_manager.db["studyPlans"]
        result = plans_col.update_one(
            {"student_id": student_id, "daily_plans.topics.topic_code": topic_code},
            {"$set": {"daily_plans.$[day].topics.$[topic].current_mastery": new_mastery}},
            array_filters=[{"day.topics.topic_code": topic_code}, {"topic.topic_code": topic_code}]
        )
        if result.modified_count > 0:
            logger.debug(f"Updated current_mastery to {new_mastery} for student_id={student_id}, topic_code={topic_code}")
        else:
            logger.warning(f"No update performed for student_id={student_id}, topic_code={topic_code}")
    except Exception as e:
        logger.error(f"Error updating study plan mastery for student_id={student_id}, topic_code={topic_code}: {str(e)}")

def _get_difficulty_progression_rules() -> Dict[str, Any]:
    """Get rules for difficulty progression based on performance"""
    return {
        "performance_thresholds": {
            "excellent": 0.85,
            "good": 0.75,
            "average": 0.65,
            "below_average": 0.50,
            "poor": 0.35
        },
        "difficulty_adjustments": {
            "excellent": "increase",
            "good": "maintain_or_increase",
            "average": "maintain",
            "below_average": "decrease",
            "poor": "significant_decrease"
        },
        "difficulty_levels": ["Very Easy", "Easy", "Medium", "Hard"],
        "consistency_weight": 0.2,
        "trend_weight": 0.3,
        "recent_weight": 0.5
    }

def _get_mastery_thresholds() -> Dict[str, float]:
    """Get mastery level thresholds"""
    return {
        "mastered": 0.90,
        "proficient": 0.75,
        "developing": 0.60,
        "beginning": 0.40,
        "struggling": 0.25
    }

# Additional utility functions for exam management
def pause_exam_session(db_manager, sprint_token: str) -> Dict[str, Any]:
    """Pause an active exam session"""
    try:
        sessions_col = db_manager.db["adaptiveSessions"]
        result = sessions_col.update_one(
            {"session_id": sprint_token, "status": "active"},
            {
                "$set": {
                    "status": "paused",
                    "paused_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Exam session paused successfully"}
        else:
            return {"success": False, "error": "Session not found or already completed"}
    except Exception as e:
        logger.error(f"Error pausing session {sprint_token}: {str(e)}")
        return {"success": False, "error": f"Failed to pause session: {str(e)}"}

def resume_exam_session(db_manager, sprint_token: str) -> Dict[str, Any]:
    """Resume a paused exam session"""
    try:
        sessions_col = db_manager.db["adaptiveSessions"]
        result = sessions_col.update_one(
            {"session_id": sprint_token, "status": "paused"},
            {
                "$set": {
                    "status": "active",
                    "resumed_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Exam session resumed successfully"}
        else:
            return {"success": False, "error": "Session not found or not paused"}
    except Exception as e:
        logger.error(f"Error resuming session {sprint_token}: {str(e)}")
        return {"success": False, "error": f"Failed to resume session: {str(e)}"}

def get_session_status(db_manager, sprint_token: str) -> Dict[str, Any]:
    """Get current status of an exam session"""
    try:
        sessions_col = db_manager.db["adaptiveSessions"]
        session = sessions_col.find_one({"session_id": sprint_token})
        
        if not session:
            return {"success": False, "error": "Session not found"}
        
        exam_data = session.get("exam_data", {})
        batches = exam_data.get("batches", [])
        completed_batches = sum(1 for batch in batches if batch.get("batch_completed", False))
        
        return {
            "success": True,
            "sprint_token": sprint_token,
            "status": session.get("status"),
            "current_mastery": session.get("current_mastery"),
            "performance": session.get("performance", 0.0),
            "total_questions_answered": exam_data.get("total_questions_answered", 0),
            "total_correct_answers": exam_data.get("total_correct_answers", 0),
            "batches_completed": completed_batches,
            "total_batches": len(batches),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
            "expires_at": session.get("expires_at")
        }
    except Exception as e:
        logger.error(f"Error getting session status {sprint_token}: {str(e)}")
        return {"success": False, "error": f"Failed to get session status: {str(e)}"}
    
def find_questions_by_skill(db_manager, student_id: str, topic_code: str) -> Dict[str, Any]:
    """
    Fetch questions for a specific skill/topic for a student, creating an adaptive test session.
    """
    if not student_id or not isinstance(student_id, str) or not re.match(r"^[a-zA-Z0-9_-]+$", student_id):
        logger.error(f"Invalid student_id: {student_id}")
        return {"success": False, "error": "Invalid student_id: must be alphanumeric with underscores or hyphens"}
    
    if not topic_code or not isinstance(topic_code, str):
        logger.error(f"Invalid topic_code: {topic_code}")
        return {"success": False, "error": "Invalid topic_code: must be a non-empty string"}

    try:
        # Fetch study plan to get topic details and mastery
        study_plan = _fetch_study_plan(db_manager, student_id)
        topic_name = topic_code  # Default to topic_code if name not found
        current_mastery = 50.0   # Default mastery
        target_difficulty = "Medium"  # Default difficulty

        if study_plan:
            for daily_plan in study_plan.get("daily_plans", []):
                for topic in daily_plan.get("topics", []):
                    if topic.get("topic_code") == topic_code:
                        topic_name = topic.get("topic_name", topic_code)
                        current_mastery = topic.get("current_mastery", 50.0)
                        target_difficulty = topic.get("target_difficulty", "Medium")
                        break

        # Create topic data dictionary
        topic_data = {
            "topic_code": topic_code,
            "topic_name": topic_name,
            "current_mastery": current_mastery,
            "target_difficulty": target_difficulty
        }

        # Reuse _create_adaptive_topic_test to create the session and fetch questions
        result = _create_adaptive_topic_test(db_manager, student_id, topic_data)
        return result

    except Exception as e:
        logger.error(f"Error in find_questions_by_skill for student_id={student_id}, topic_code={topic_code}: {str(e)}", exc_info=True)
        return {"success": False, "error": f"Failed to fetch questions for topic {topic_code}: {str(e)}"}