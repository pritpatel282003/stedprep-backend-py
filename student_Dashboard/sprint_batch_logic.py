from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class BatchedTestError(Exception):
    """Custom exception for batched test related errors"""
    pass

class ClientValidationError(Exception):
    """Exception for client-side validation errors that shouldn't be logged as server errors"""
    pass

def get_batched_questions_for_skill(
    db_manager,
    student_id: str,
    skill_code: str,
    current_mastery_level: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get a batch of questions for a specific skill code based on student's mastery level.
    
    Args:
        db_manager: Database manager instance
        student_id: Student identifier
        skill_code: Skill code (e.g., 'MA01')
        current_mastery_level: Current mastery level (2-9), if None will fetch from student assessment
    
    Returns:
        Dict containing sprint_token, questions, and session info
    """
    if not student_id or not isinstance(student_id, str) or not re.match(r"^[a-zA-Z0-9_-]+$", student_id):
        logger.error(f"Invalid student_id: {student_id}")
        return {"success": False, "error": "Invalid student_id: must be alphanumeric with underscores or hyphens"}
    
    if not skill_code or not isinstance(skill_code, str):
        logger.error(f"Invalid skill_code: {skill_code}")
        return {"success": False, "error": "Invalid skill_code: must be a non-empty string"}

    try:
        # If mastery level not provided, fetch from student assessment
        if current_mastery_level is None:
            current_mastery_level = _get_student_mastery_level(db_manager, student_id, skill_code)
        
        if current_mastery_level is None:
            logger.warning(f"No mastery level found for student {student_id}, skill {skill_code}. Using default level 4")
            current_mastery_level = 4
        
        # Validate mastery level range
        if not (2 <= current_mastery_level <= 9):
            logger.error(f"Invalid mastery level: {current_mastery_level}. Must be between 2-9")
            return {"success": False, "error": "Invalid mastery level: must be between 2-9"}
        
        # Fetch batched questions for the skill and level
        questions = _fetch_batched_questions(db_manager, skill_code, current_mastery_level)
        
        if not questions:
            logger.warning(f"No batched questions found for skill_code={skill_code}, level={current_mastery_level}")
            return {
                "success": True,
                "student_id": student_id,
                "skill_code": skill_code,
                "current_mastery_level": current_mastery_level,
                "sprint_token": None,
                "questions": [],
                "fetched_count": 0,
                "message": f"No questions available for skill {skill_code} at level {current_mastery_level}"
            }
        
        # Create sprint session
        sprint_token = str(uuid.uuid4())
        session_data = _create_batched_session(
            student_id, skill_code, current_mastery_level, sprint_token, questions
        )
        
        # Store session in database
        _store_batched_session(db_manager, session_data)
        
        logger.info(f"Created batched test session for student {student_id}, skill {skill_code}, level {current_mastery_level}")
        
        return {
            "success": True,
            "student_id": student_id,
            "skill_code": skill_code,
            "current_mastery_level": current_mastery_level,
            "sprint_token": sprint_token,
            "questions": questions,
            "fetched_count": len(questions),
            "session_expires_at": session_data["expires_at"],
            "message": f"Retrieved {len(questions)} questions for skill {skill_code} at level {current_mastery_level}"
        }
        
    except Exception as e:
        logger.error(f"Error getting batched questions for student {student_id}, skill {skill_code}: {str(e)}", exc_info=True)
        return {"success": False, "error": f"Failed to get questions: {str(e)}"}

def submit_batched_answers_and_get_next(
    db_manager,
    sprint_token: str,
    answers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Submit answers for current batch and get next batch based on performance.
    """
    if not sprint_token or not isinstance(sprint_token, str):
        return {"success": False, "error": "Invalid sprint_token"}
    
    if not answers or not isinstance(answers, list):
        return {"success": False, "error": "Invalid answers: must be a non-empty list"}
    
    try:
        # Get current session
        session = _get_batched_session(db_manager, sprint_token)
        if not session:
            return {"success": False, "error": "Sprint session not found"}
        
        if session.get("status") != "active":
            return {"success": False, "error": f"Session is not active. Current status: {session.get('status')}"}
        
        # Validate and grade answers
        grading_result = _grade_batched_answers(session, answers)
        if not grading_result["success"]:
            return grading_result
        
        performance = grading_result["performance"]
        current_level = session["current_mastery_level"]
        skill_code = session["skill_code"]
        student_id = session["student_id"]
        correct_answers = grading_result["correct_answers"]
        total_questions = grading_result["total_questions"]
        
        # Update student mastery using simple accuracy
        _update_student_mastery_level(db_manager, student_id, skill_code, correct_answers, total_questions)
        
        # Calculate accuracy percentage for display
        accuracy_percentage = round(performance * 100)
        
        # Determine next difficulty level based on performance
        next_level = _determine_next_level(current_level, performance)
        
        # Update session with current batch results
        _update_session_with_results(db_manager, sprint_token, grading_result, next_level, student_id, skill_code)
        
        # Check for session completion conditions
        if next_level >= 9 and performance >= 0.8:
            return {
                "success": True,
                "sprint_token": sprint_token,
                "performance": performance,
                "accuracy_percentage": accuracy_percentage,
                "current_level": current_level,
                "next_level": next_level,
                "questions": [],
                "session_complete": True,
                "mastery_achieved": True,
                "message": f"Skill {skill_code} mastered! Accuracy: {correct_answers}/{total_questions} ({accuracy_percentage}%)",
                **grading_result
            }
        
        elif next_level <= 2 and performance < 0.3:
            return {
                "success": True,
                "sprint_token": sprint_token,
                "performance": performance,
                "accuracy_percentage": accuracy_percentage,
                "current_level": current_level,
                "next_level": next_level,
                "questions": [],
                "session_complete": True,
                "mastery_achieved": False,
                "message": f"Skill {skill_code} needs more practice. Accuracy: {correct_answers}/{total_questions} ({accuracy_percentage}%)",
                **grading_result
            }
        
        # Get next batch of questions
        next_questions = _fetch_batched_questions(db_manager, skill_code, next_level)
        
        if not next_questions:
            return {
                "success": True,
                "sprint_token": sprint_token,
                "performance": performance,
                "accuracy_percentage": accuracy_percentage,
                "current_level": current_level,
                "next_level": next_level,
                "questions": [],
                "session_complete": True,
                "mastery_achieved": accuracy_percentage >= 80,
                "message": f"No more questions available. Final accuracy: {correct_answers}/{total_questions} ({accuracy_percentage}%)",
                **grading_result
            }
        
        # Update session for next batch
        _prepare_next_batch(db_manager, sprint_token, next_level, next_questions)
        
        return {
            "success": True,
            "sprint_token": sprint_token,
            "performance": performance,
            "accuracy_percentage": accuracy_percentage,
            "current_level": current_level,
            "next_level": next_level,
            "questions": next_questions,
            "fetched_count": len(next_questions),
            "session_complete": False,
            "message": f"Accuracy: {correct_answers}/{total_questions} ({accuracy_percentage}%). Moving from level {current_level} to {next_level}",
            **grading_result
        }
        
    except Exception as e:
        logger.error(f"Error processing batched answers for sprint_token {sprint_token}: {str(e)}", exc_info=True)
        return {"success": False, "error": f"Failed to process answers: {str(e)}"}

def get_batched_session_status(db_manager, sprint_token: str) -> Dict[str, Any]:
    """Get current status of a batched test session"""
    try:
        session = _get_batched_session(db_manager, sprint_token)
        if not session:
            return {"success": False, "error": "Sprint session not found"}
        
        return {
            "success": True,
            "sprint_token": sprint_token,
            "student_id": session["student_id"],
            "skill_code": session["skill_code"],
            "current_mastery_level": session["current_mastery_level"],
            "status": session["status"],
            "batches_completed": len(session.get("completed_batches", [])),
            "overall_performance": session.get("overall_performance", 0.0),
            "created_at": session["created_at"],
            "updated_at": session.get("updated_at", session["created_at"]),
            "expires_at": session["expires_at"]
        }
        
    except Exception as e:
        logger.error(f"Error getting session status for sprint_token {sprint_token}: {str(e)}")
        return {"success": False, "error": f"Failed to get session status: {str(e)}"}

def complete_batched_session(db_manager, sprint_token: str) -> Dict[str, Any]:
    """Manually complete a batched session and update student mastery with simple accuracy"""
    try:
        session = _get_batched_session(db_manager, sprint_token)
        if not session:
            return {"success": False, "error": "Sprint session not found"}
        
        if session.get("status") == "completed":
            return {"success": True, "message": "Session already completed"}
        
        # Calculate cumulative accuracy from all completed batches
        completed_batches = session.get("completed_batches", [])
        if not completed_batches:
            return {"success": False, "error": "No completed batches found"}
        
        # Sum up all correct answers and total questions across batches
        total_correct = sum(batch.get("correct_answers", 0) for batch in completed_batches)
        total_questions = sum(batch.get("total_questions", 0) for batch in completed_batches)
        
        if total_questions == 0:
            return {"success": False, "error": "No questions found in completed batches"}
        
        # Update student mastery using cumulative accuracy
        _update_student_mastery_level(
            db_manager, session["student_id"], session["skill_code"], total_correct, total_questions
        )
        
        # Calculate final accuracy percentage
        final_accuracy_percentage = round((total_correct / total_questions) * 100)
        
        # Mark session as completed
        sessions_col = db_manager.db["batchedSessions"]
        sessions_col.update_one(
            {"sprint_token": sprint_token},
            {
                "$set": {
                    "status": "completed",
                    "final_accuracy_percentage": final_accuracy_percentage,
                    "total_correct_answers": total_correct,
                    "total_questions_answered": total_questions,
                    "completed_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {
            "success": True,
            "sprint_token": sprint_token,
            "final_accuracy_percentage": final_accuracy_percentage,
            "total_correct_answers": total_correct,
            "total_questions_answered": total_questions,
            "batches_completed": len(completed_batches),
            "message": f"Session completed. Final accuracy: {total_correct}/{total_questions} ({final_accuracy_percentage}%)"
        }
        
    except Exception as e:
        logger.error(f"Error completing session {sprint_token}: {str(e)}")
        return {"success": False, "error": f"Failed to complete session: {str(e)}"}

# Helper Functions

def _get_student_mastery_level(db_manager, student_id: str, skill_code: str) -> Optional[int]:
    """Get current mastery level for student and skill from studentSummary"""
    try:
        student_summary_col = db_manager.db["studentSummary"]
        summary = student_summary_col.find_one(
            {"student_id": student_id},
            sort=[("analysis_date", -1)]
        )
        
        if not summary:
            logger.warning(f"No studentSummary found for student {student_id}")
            return None
        
        mastery_data = summary.get("complete_topic_mastery", {})
        skill_data = mastery_data.get(skill_code)
        
        if not skill_data:
            logger.warning(f"No mastery data found for skill {skill_code}")
            return None
        
        mastery_percentage = skill_data.get("mastery_percentage", 0)
        
        # Convert percentage to level (2-9)
        if mastery_percentage >= 90:
            return 9
        elif mastery_percentage >= 80:
            return 8
        elif mastery_percentage >= 70:
            return 7
        elif mastery_percentage >= 60:
            return 6
        elif mastery_percentage >= 50:
            return 5
        elif mastery_percentage >= 40:
            return 4
        elif mastery_percentage >= 30:
            return 3
        else:
            return 2
            
    except Exception as e:
        logger.error(f"Error getting student mastery level: {str(e)}")
        return None

def _fetch_batched_questions(db_manager, skill_code: str, level: int) -> List[Dict[str, Any]]:
    """Fetch a batch of questions for specific skill and level from batched_questions collection"""
    try:
        batched_col = db_manager.db["batched_question"]
        
        # Find batch for skill code and level
        batch_doc = batched_col.find_one({
            "skill_code": skill_code,
            "difficulty_level": level,
            "is_active": True
        })
        
        if not batch_doc:
            logger.warning(f"No batched questions found for skill_code={skill_code}, level={level}")
            return []
        
        questions = batch_doc.get("questions", [])
        logger.info(f"Found {len(questions)} batched questions for {skill_code} level {level}")
        
        # Format questions for API response
        formatted_questions = []
        for i, question in enumerate(questions):
            formatted_question = {
                "question_id": question.get("question_id", f"{skill_code}_{level}_{i+1}"),
                "question_text": question.get("question_text", ""),
                "options": question.get("options", []),
                "correct_answer": question.get("correct_answer", ""),
                "difficulty_level": level,
                "skill_code": skill_code,
                "explanation": question.get("explanation", ""),
                "time_limit_seconds": question.get("time_limit_seconds", 120)
            }
            formatted_questions.append(formatted_question)
        
        return formatted_questions
        
    except Exception as e:
        logger.error(f"Error fetching batched questions: {str(e)}")
        return []

def _create_batched_session(student_id: str, skill_code: str, mastery_level: int, 
                           sprint_token: str, questions: List[Dict]) -> Dict[str, Any]:
    """Create batched test session data"""
    return {
        "sprint_token": sprint_token,
        "student_id": student_id,
        "skill_code": skill_code,
        "current_mastery_level": mastery_level,
        "initial_mastery_level": mastery_level,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        "current_questions": [q["question_id"] for q in questions],
        "completed_batches": [],
        "overall_performance": 0.0,
        "level_progression": [mastery_level]
    }

def _store_batched_session(db_manager, session_data: Dict[str, Any]):
    """Store batched session in database"""
    try:
        sessions_col = db_manager.db["batchedSessions"]
        sessions_col.insert_one(session_data)
        logger.debug(f"Stored batched session {session_data['sprint_token']}")
    except Exception as e:
        logger.error(f"Error storing batched session: {str(e)}")
        raise

def _get_batched_session(db_manager, sprint_token: str) -> Optional[Dict[str, Any]]:
    """Retrieve batched session from database"""
    try:
        sessions_col = db_manager.db["batchedSessions"]
        return sessions_col.find_one({"sprint_token": sprint_token})
    except Exception as e:
        logger.error(f"Error getting batched session: {str(e)}")
        return None

def _grade_batched_answers(session: Dict[str, Any], answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Grade submitted answers and calculate performance with improved error handling"""
    try:
        valid_question_ids = session.get("current_questions", [])
        
        # Comprehensive validation of all answers first
        validation_errors = []
        
        for i, answer in enumerate(answers):
            question_id = answer.get("question_id")
            
            # Check for missing question_id
            if not question_id:
                validation_errors.append(f"Answer {i+1}: Missing question_id field")
                continue
                
            # Check for invalid question_id
            if question_id not in valid_question_ids:
                valid_ids_display = ", ".join(valid_question_ids) if valid_question_ids else "none"
                validation_errors.append(f"Invalid question_id: {question_id}")
                
            # Check for missing is_correct field
            if "is_correct" not in answer:
                validation_errors.append(f"Answer {i+1} (question_id: {question_id}): Missing is_correct field")
        
        # If there are validation errors, return them all at once
        if validation_errors:
            if len(validation_errors) == 1 and "Invalid question_id" in validation_errors[0]:
                # Single invalid question_id - provide helpful context
                invalid_id = answers[0].get("question_id", "unknown")
                valid_ids_display = ", ".join(valid_question_ids) if valid_question_ids else "none"
                error_message = f"Invalid question_id: {invalid_id}. Expected one of: [{valid_ids_display}]"
            else:
                # Multiple errors or other validation issues
                error_message = "Validation errors: " + "; ".join(validation_errors)
                
            return {"success": False, "error": error_message}
        
        # All validations passed, calculate performance
        total_questions = len(answers)
        correct_answers = sum(1 for answer in answers if answer.get("is_correct", False))
        performance = correct_answers / total_questions if total_questions > 0 else 0.0
        
        return {
            "success": True,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "performance": performance,
            "answers": answers
        }
        
    except Exception as e:
        logger.error(f"Error grading batched answers: {str(e)}")
        return {"success": False, "error": f"Failed to grade answers: {str(e)}"}

def _determine_next_level(current_level: int, performance: float) -> int:
    """Determine next difficulty level based on current performance"""
    if performance >= 0.8:  # 80%+ correct
        return min(current_level + 1, 9)  # Increase level, max 9
    elif performance >= 0.6:  # 60-79% correct
        return current_level  # Same level
    elif performance >= 0.4:  # 40-59% correct
        return max(current_level - 1, 2)  # Decrease level, min 2
    else:  # < 40% correct
        return max(current_level - 2, 2)  # Decrease level significantly, min 2

def _calculate_updated_mastery_level(performance: float, current_level: int) -> int:
    """Calculate updated mastery level after each batch submission based on performance"""
    if performance >= 0.9:  # 90%+ performance - significant improvement
        return min(current_level + 1, 9)
    elif performance >= 0.8:  # 80-89% performance - maintain or slight improvement
        return current_level
    elif performance >= 0.6:  # 60-79% performance - maintain current level
        return current_level
    elif performance >= 0.4:  # 40-59% performance - slight decrease
        return max(current_level - 1, 2)
    else:  # < 40% performance - needs remediation
        return max(current_level - 1, 2)

def _calculate_final_mastery_level(current_level: int, performance: float) -> int:
    """Calculate final mastery level based on performance"""
    if performance >= 0.9:
        return min(current_level + 2, 9)
    elif performance >= 0.8:
        return min(current_level + 1, 9)
    elif performance >= 0.6:
        return current_level
    elif performance >= 0.4:
        return max(current_level - 1, 2)
    else:
        return max(current_level - 2, 2)

def _update_session_with_results(db_manager, sprint_token: str, grading_result: Dict[str, Any], next_level: int, student_id: str, skill_code: str):
    """Update session with current batch results and update student mastery"""
    try:
        sessions_col = db_manager.db["batchedSessions"]
        
        batch_result = {
            "level": next_level,
            "performance": grading_result["performance"],
            "total_questions": grading_result["total_questions"],
            "correct_answers": grading_result["correct_answers"],
            "completed_at": datetime.utcnow().isoformat(),
            "answers": grading_result["answers"]
        }
        
        sessions_col.update_one(
            {"sprint_token": sprint_token},
            {
                "$push": {"completed_batches": batch_result},
                "$set": {
                    "current_mastery_level": next_level,
                    "overall_performance": grading_result["performance"],
                    "updated_at": datetime.utcnow().isoformat(),
                    "current_questions": []
                }
            }
        )
        
        # Update student mastery in studentSummary/studentAssessments after each batch
        updated_mastery_level = _calculate_updated_mastery_level(grading_result["performance"], next_level)
        _update_student_mastery_level(db_manager, student_id, skill_code, grading_result["correct_answers"], grading_result["total_questions"])
        
    except Exception as e:
        logger.error(f"Error updating session with results: {str(e)}")
        raise

def _prepare_next_batch(db_manager, sprint_token: str, next_level: int, next_questions: List[Dict]):
    """Prepare session for next batch"""
    try:
        sessions_col = db_manager.db["batchedSessions"]
        
        question_ids = [q["question_id"] for q in next_questions]
        
        sessions_col.update_one(
            {"sprint_token": sprint_token},
            {
                "$set": {
                    "current_questions": question_ids,
                    "current_mastery_level": next_level,
                    "updated_at": datetime.utcnow().isoformat()
                },
                "$push": {"level_progression": next_level}
            }
        )
        
    except Exception as e:
        logger.error(f"Error preparing next batch: {str(e)}")
        raise

def _update_student_mastery_level(db_manager, student_id: str, skill_code: str, correct_answers: int, total_questions: int):
    """
    Update student's mastery level in studentSummary collection based on simple accuracy.
    
    Args:
        db_manager: Database manager instance
        student_id: Student identifier
        skill_code: Skill code (e.g., 'MA01') 
        correct_answers: Number of correct answers
        total_questions: Total number of questions answered
    """
    try:
        if total_questions == 0:
            logger.warning(f"Cannot update mastery - total_questions is 0 for student {student_id}, skill {skill_code}")
            return
            
        # Calculate simple accuracy percentage
        accuracy_percentage = round((correct_answers / total_questions) * 100)
        
        # Ensure percentage is within valid range (0-100)
        accuracy_percentage = max(0, min(100, accuracy_percentage))
        
        student_summary_col = db_manager.db["studentSummary"]
        
        # Update the student's mastery in studentSummary collection
        result = student_summary_col.update_one(
            {"student_id": student_id},
            {
                "$set": {
                    f"complete_topic_mastery.{skill_code}.mastery_percentage": accuracy_percentage,
                    f"complete_topic_mastery.{skill_code}.assessment_type": "assessed",
                    f"complete_topic_mastery.{skill_code}.correct_answers": correct_answers,
                    f"complete_topic_mastery.{skill_code}.total_questions": total_questions,
                    f"complete_topic_mastery.{skill_code}.last_updated": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow(),
                    "analysis_date": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated mastery for student {student_id}, skill {skill_code}: {correct_answers}/{total_questions} = {accuracy_percentage}%")
        else:
            logger.warning(f"No studentSummary record found for student {student_id}")
            
    except Exception as e:
        logger.error(f"Error updating student mastery level: {str(e)}")
        raise