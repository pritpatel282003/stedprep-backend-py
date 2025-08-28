# models/models.py

from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional

# --- Enums for categorizing data ---

class MasteryLevel(str, Enum):
    """
    Represents the mastery level of a student in a topic.
    """
    WEAK = "Weak"
    MODERATE = "Moderate"
    STRONG = "Strong"
    MASTERED = "Mastered"

class DifficultyLevel(str, Enum):
    """
    Represents the difficulty level of a question.
    """
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class StudyAction(str, Enum):
    """
    Represents the recommended study action for a topic.
    """
    PRACTICE = "Practice"
    REINFORCE = "Reinforce"
    CHALLENGE = "Challenge"
    REVIEW = "Review"
    MOVE_ON = "Move_On"

# --- Study Plan Models ---

class StudyPlanRequest(BaseModel):
    """
    Request model for creating a study plan.
    """
    student_id: str
    duration_days: int = 15
    daily_time_minutes: int = 60

class TopicStudyPlan(BaseModel):
    """
    Represents the study plan for a single topic.
    """
    topic: str
    current_mastery_percentage: float
    theta: float
    target_difficulty: DifficultyLevel
    study_action: StudyAction
    questions_recommended: int
    time_allocation_minutes: int
    learning_objective: str
    success_criteria: str
    next_action_threshold: float

class DailyStudyPlan(BaseModel):
    """
    Represents the study plan for a single day.
    """
    day: int
    date: datetime
    topics: List[TopicStudyPlan]
    total_time_minutes: int
    daily_focus: str
    performance_goals: List[str]

class StudyPlanResponse(BaseModel):
    """
    Response model for a generated study plan.
    """
    success: bool
    student_id: str
    plan_start_date: datetime
    daily_plans: List[DailyStudyPlan]
    weak_areas_focus: List[str]
    review_schedule: Dict[str, List[int]]
    progression_milestones: Dict[int, str]
    message: str

class NextActionRecommendation(BaseModel):
    """
    Represents a recommendation for the next action to take in a study plan.
    """
    action: StudyAction
    difficulty: DifficultyLevel
    rationale: str
    estimated_questions: int
    time_estimate_minutes: int

# --- Request/Response Models for Diagnostic Test and Sprints ---

class StartSessionRequest(BaseModel):
    """
    Request model for starting a new diagnostic test session.
    """
    student_id: Optional[str] = None

class SubmitResponseRequest(BaseModel):
    """
    Request model for submitting a response to a question.
    """
    session_token: str
    user_response: bool
    question_id: str
    question_number: int
    selected_option: Optional[str] = None
    crossed_options: Optional[list] = []

class StartSprintRequest(BaseModel):
    """
    Request model for starting a new sprint.
    """
    student_id: str
    topic: str
    num_questions: int

class SprintQuestionRequest(BaseModel):
    """
    Request model for getting the next question in a sprint.
    """
    sprint_token: str

class SprintSubmitRequest(BaseModel):
    """
    Request model for submitting a response to a question in a sprint.
    """
    sprint_token: str
    question_id: str
    question_number: int
    user_response: bool
    selected_option: Optional[str] = None

class GetQuestionRequest(BaseModel):
    """
    Request model for getting the next question in a diagnostic test.
    """
    session_token: str
    questionType: Optional[str] = None

class SessionResponse(BaseModel):
    """
    Response model for a new session.
    """
    session_token: str
    student_id: str
    message: str
    item_bank_info: dict
    diagnostic_test_info: dict

class CreateStudyPlanRequest(BaseModel):
    """
    Request model for creating a new study plan.
    """
    student_id: str
    total_days: int
    daily_time_minutes: int = 60

class UpdateMasteryRequest(BaseModel):
    """
    Request model for updating a student's mastery level for a topic.
    """
    student_id: str
    topic_code: str
    new_mastery: float

class TodaysPlanRequest(BaseModel):
    """
    Request model for getting today's study plan.
    """
    student_id: str

class StudyPlanResponse(BaseModel):
    """
    Response model for a student's study plan.
    """
    success: bool
    student_id: str
    plan_duration_days: int
    daily_time_minutes: int
    plan_start_date: str
    daily_plans: List[Dict[str, Any]]
    progress_summary: Dict[str, Any]
    created_at: str
    plan_id: Optional[str] = None

class TodaysPlanResponse(BaseModel):
    """
    Response model for today's study plan.
    """
    success: bool
    student_id: str
    date: str
    todays_plan: Optional[Dict[str, Any]]

class UpdateMasteryResponse(BaseModel):
    """
    Response model for updating a student's mastery level.
    """
    success: bool
    message: str

# --- Topic Test Models ---

class TopicTestRequest(BaseModel):
    """
    Request model for getting a topic test for a specific day.
    """
    student_id: str
    day: int

# --- Section Test Grading Models ---

class SectionTestAnswer(BaseModel):
    """
    Represents a single answer in a section test.
    """
    question_id: str
    selected_option: Optional[str] = None
    typed_answer: Optional[str] = None
    topic_code: Optional[str] = None  # Optional override if caller already knows topic/skill
    section: Optional[str] = None

class SectionTestGradeRequest(BaseModel):
    """
    Request model for grading a section test.
    """
    student_id: str
    test_id: str
    responses: List[SectionTestAnswer]

class IndexGradeRequest(BaseModel):
    """
    Request model for grading a test using an indexed list of answers.
    """
    test_id: str
    answers: List[Optional[str]]