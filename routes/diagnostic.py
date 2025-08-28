# routes/diagnostic.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from datetime import datetime
from diagnostic_test_folder.cat_bkt_system import EnhancedInteractiveCATSystem
from diagnostic_test_folder.diagnostic_test import analyze_comprehensive_performance
from models.models import (
    SessionResponse, StartSessionRequest, SubmitResponseRequest, GetQuestionRequest
)
from app_context import get_db

# Create a new router for diagnostic test endpoints
router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


@router.post("/start-session", response_model=SessionResponse)
async def start_session(request: StartSessionRequest, db=Depends(get_db)):
    """
    Starts a new diagnostic test session for a student.

    This endpoint generates a unique session token, and if a student_id is provided,
    it cleans up any existing data for that student to start a fresh session.
    It returns the session token and student ID.
    """
    try:
        # Check if the item bank is populated. If not, raise an error.
        item_count = db.item_bank_collection.count_documents({})
        if item_count == 0:
            raise HTTPException(status_code=400, detail="Item bank is empty. Please upload IRT CSV first using /util/upload-irt-csv endpoint.")

        # Generate a unique session token and determine the student ID
        import uuid
        session_token = str(uuid.uuid4())
        student_id = request.student_id or f"student_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Delete any existing data for this student to ensure a fresh start
        cleanup_results = {}
        diagnostic_deleted = db.db.diagnostic_test.delete_many({"student_id": student_id})
        cleanup_results["diagnostic_tests_deleted"] = diagnostic_deleted.deleted_count
        sessions_deleted = db.sessions_collection.delete_many({"student_id": student_id})
        cleanup_results["sessions_deleted"] = sessions_deleted.deleted_count
        summary_deleted = db.db.studentSummary.delete_many({"student_id": student_id})
        cleanup_results["student_summaries_deleted"] = summary_deleted.deleted_count
        responses_deleted = db.responses_collection.delete_many({"student_id": student_id})
        cleanup_results["responses_deleted"] = responses_deleted.deleted_count

        # Create a new CAT system instance for the session
        cat_system = EnhancedInteractiveCATSystem(
            session_token=session_token,
            student_id=student_id,
            db_manager=db
        )

        # Get information about the item bank
        item_bank_info = {
            "total_items": item_count,
            "question_types": [str(x) for x in db.item_bank_collection.distinct("questionType")],
            "sections": [str(x) for x in db.item_bank_collection.distinct("section")]
        }

        # Get a summary of the diagnostic test
        diagnostic_info = cat_system.get_diagnostic_test_summary()

        # Return the session response
        return SessionResponse(
            session_token=session_token,
            student_id=student_id,
            message="new profile" if sum(cleanup_results.values()) == 0 else "existing profile",
            item_bank_info=item_bank_info,
            diagnostic_test_info=diagnostic_info
        )
    except HTTPException:
        # Re-raise HTTPException to let FastAPI handle it
        raise
    except Exception as e:
        # Raise a 500 error for any other exceptions
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/get-question")
async def get_next_question(request: GetQuestionRequest, db=Depends(get_db)):
    """
    Gets the next question for the student in the diagnostic test.

    This endpoint uses the CAT system to select the next question based on the
    student's current ability level (theta).
    """
    try:
        # Get the session data from the database
        session_data = db.get_session(request.session_token)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Create a CAT system instance for the session
        cat_system = EnhancedInteractiveCATSystem(
            session_token=request.session_token,
            student_id=session_data['student_id'],
            db_manager=db
        )

        # Get the next question from the CAT system
        question_result = cat_system.get_next_question(question_type_filter=request.questionType)

        # Handle errors from the CAT system
        if question_result.get('error', False):
            raise HTTPException(status_code=400, detail=question_result['message'])

        # If the session is complete, return the final status
        if question_result.get('session_complete', False):
            return {
                "session_complete": True,
                "message": question_result['message'],
                "final_status": question_result.get('final_status', {}),
                "diagnostic_test_summary": cat_system.get_diagnostic_test_summary()
            }

        # Return the next question details
        details = question_result['question_details']
        return {
            "session_complete": False,
            "question_number": question_result['question_number'],
            "question_id": question_result['question_id'],
            "difficulty": round(details['b_difficulty'], 3),
            "discrimination": round(details['a_discrimination'], 3),
            "questionType": details.get('questionType', 'Unknown'),
            "topic": details.get('topic', 'Unknown'),
            "skillCode": details.get('skillCode', 'Unknown'),
            "skillDescription": details.get('skillDescription', ''),
            "difficultyLevel": details.get('difficultyLevel', 'Unknown'),
            "iseeLevel": details.get('iseeLevel', 'Unknown'),
            "section": details.get('section', 'Unknown'),
            "subject": details.get('subject', details.get('section', 'Unknown')),
            "questionTitle": details.get('questionTitle', ''),
            "options": details.get('options', {}),
            "correctOption": details.get('correctOption', ''),
            "correctAnswer": details.get('correctAnswer', details.get('correctOption', '')),
            "questionImages": details.get('questionImages', []),
            "explanation": details.get('explanation', ''),
            "current_theta": round(question_result['current_theta'], 3),
            "mastery_probability": round(question_result['mastery_prob'], 3),
            "awaiting_response": question_result.get('awaiting_response', True),
            "message": question_result.get('message', 'Question presented successfully'),
            "diagnostic_test_summary": cat_system.get_diagnostic_test_summary(),
            "additional_data": {k: v for k, v in details.items() if k not in ['question_id','a_discrimination','b_difficulty','questionType','topic','skillCode','skillDescription','difficultyLevel','iseeLevel','section','subject','questionTitle','options','correctOption','correctAnswer','questionImages','explanation']}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting question: {str(e)}")


@router.post("/submit-response")
async def submit_response(request: SubmitResponseRequest, db=Depends(get_db)):
    """
    Submits a student's response to a question.

    This endpoint records the student's response, updates their ability level (theta),
    and returns the result of the response.
    """
    try:
        # Get the session data from the database
        session_data = db.get_session(request.session_token)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Create a CAT system instance for the session
        cat_system = EnhancedInteractiveCATSystem(
            session_token=request.session_token,
            student_id=session_data['student_id'],
            db_manager=db
        )

        # Submit the response to the CAT system
        response_result = cat_system.submit_response(
            question_id=request.question_id,
            user_response=request.user_response,
            question_number=request.question_number,
            selected_option=request.selected_option
        )

        # Return the result of the response submission
        return {
            "success": response_result['success'],
            "message": response_result['message'],
            "question_id": response_result['question_id'],
            "question_number": response_result['question_number'],
            "user_response": response_result['user_response'],
            "is_correct": response_result['is_correct'],
            "selected_option": request.selected_option,
            "theta_change": response_result['theta_change'],
            "old_theta": response_result['old_theta'],
            "new_theta": response_result['new_theta'],
            "old_mastery": response_result['old_mastery'],
            "new_mastery": response_result['new_mastery'],
            "correct_streak": response_result['correct_streak'],
            "is_assessment_complete": response_result['is_assessment_complete'],
            "awaiting_response": response_result['awaiting_response'],
            "can_get_next_question": response_result['can_get_next_question'],
            "saved_response_id": response_result.get('saved_response_id'),
            "diagnostic_test_update": response_result.get('diagnostic_test_update', {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting response: {str(e)}")


@router.get("/session-status/{session_token}")
async def get_session_status(session_token: str, db=Depends(get_db)):
    """
    Gets the current status of a diagnostic test session.
    """
    try:
        # Get the session data from the database
        session_data = db.get_session(session_token)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Create a CAT system instance for the session
        cat_system = EnhancedInteractiveCATSystem(
            session_token=session_token,
            student_id=session_data['student_id'],
            db_manager=db
        )

        # Return the current status of the session
        return cat_system.get_current_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.post("/end-session/{session_token}")
async def end_session(session_token: str, db=Depends(get_db)):
    """
    Ends a diagnostic test session and performs a comprehensive analysis of the student's performance.
    """
    try:
        # Get the session data from the database
        session_data = db.get_session(session_token)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Create a CAT system instance for the session
        cat_system = EnhancedInteractiveCATSystem(
            session_token=session_token,
            student_id=session_data['student_id'],
            db_manager=db
        )

        # End the session in the CAT system
        session_end_result = cat_system.end_session()

        # Perform a comprehensive analysis of the student's performance
        comprehensive_analysis = analyze_comprehensive_performance(session_token, db)

        # Return the result of ending the session and the comprehensive analysis
        return {
            "session_end": session_end_result,
            "comprehensive_analysis": comprehensive_analysis,
            "message": "Session ended successfully and comprehensive analysis saved to studentSummary collection"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending session: {str(e)}")


