from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional

class MasteryLevel(str, Enum):
    WEAK = "Weak"
    MODERATE = "Moderate"
    STRONG = "Strong"
    MASTERED = "Mastered"

class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class StudyAction(str, Enum):
    PRACTICE = "Practice"
    REINFORCE = "Reinforce"
    CHALLENGE = "Challenge"
    REVIEW = "Review"
    MOVE_ON = "Move_On"

class StudyPlanRequest(BaseModel):
    student_id: str
    duration_days: int = 15
    daily_time_minutes: int = 60

class TopicStudyPlan(BaseModel):
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
    day: int
    date: datetime
    topics: List[TopicStudyPlan]
    total_time_minutes: int
    daily_focus: str
    performance_goals: List[str]

class StudyPlanResponse(BaseModel):
    success: bool
    student_id: str
    plan_start_date: datetime
    daily_plans: List[DailyStudyPlan]
    weak_areas_focus: List[str]
    review_schedule: Dict[str, List[int]]
    progression_milestones: Dict[int, str]
    message: str

class NextActionRecommendation(BaseModel):
    action: StudyAction
    difficulty: DifficultyLevel
    rationale: str
    estimated_questions: int
    time_estimate_minutes: int

# Request/Response Models
class StartSessionRequest(BaseModel):
    student_id: Optional[str] = None

class SubmitResponseRequest(BaseModel):
    session_token: str
    user_response: bool
    question_id: str
    question_number: int
    selected_option: Optional[str] = None
    crossed_options: Optional[list] = []

class StartSprintRequest(BaseModel):
    student_id: str
    topic: str
    num_questions: int

class SprintQuestionRequest(BaseModel):
    sprint_token: str

class SprintSubmitRequest(BaseModel):
    sprint_token: str
    question_id: str
    question_number: int
    user_response: bool
    selected_option: Optional[str] = None

class GetQuestionRequest(BaseModel):
    session_token: str
    questionType: Optional[str] = None

class SessionResponse(BaseModel):
    session_token: str
    student_id: str
    message: str
    item_bank_info: dict
    diagnostic_test_info: dict

class CreateStudyPlanRequest(BaseModel):
    student_id: str
    total_days: int
    daily_time_minutes: int = 60

class UpdateMasteryRequest(BaseModel):
    student_id: str
    topic_code: str
    new_mastery: float

class TodaysPlanRequest(BaseModel):
    student_id: str

class StudyPlanResponse(BaseModel):
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
    success: bool
    student_id: str
    date: str
    todays_plan: Optional[Dict[str, Any]]

class UpdateMasteryResponse(BaseModel):
    success: bool
    message: str

# Topic test request model
class TopicTestRequest(BaseModel):
    student_id: str
    day: int

# Section Test grading models
class SectionTestAnswer(BaseModel):
    question_id: str
    selected_option: Optional[str] = None
    typed_answer: Optional[str] = None
    # Optional override if caller already knows topic/skill
    topic_code: Optional[str] = None
    section: Optional[str] = None

class SectionTestGradeRequest(BaseModel):
    student_id: str
    test_id: str
    responses: List[SectionTestAnswer]

class IndexGradeRequest(BaseModel):
    test_id: str
    answers: List[Optional[str]]  

class AdaptiveTestResponse(BaseModel):
    success: bool
    student_id: str
    day: int
    allowed: bool = True
    reason: Optional[str] = None
    topics: List[Dict[str, Any]] = []
    note: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None

class StudyPlanSummary(BaseModel):
    student_id: str
    plan_duration_days: Optional[int]
    daily_time_minutes: Optional[int]
    plan_start_date: Optional[str]
    total_days: int
    days_with_topics: int
    days_with_tests: int
    available_days: List[int]
    progress_summary: Dict[str, Any]

class DayDetailsResponse(BaseModel):
    student_id: str
    day: int
    daily_plan: Dict[str, Any]
    topic_test_allowed: bool
    topic_test_restriction_reason: Optional[str]
    topic_count: int
    test_count: int
    total_time_minutes: int

class NextQuestionsRequest(BaseModel):
    previous_answers: List[Dict[str, Any]]

class NextQuestionsResponse(BaseModel):
    success: bool
    sprint_token: str
    performance: float
    previous_difficulty: str
    current_difficulty: str
    questions: List[Dict[str, Any]]
    fetched_count: int

class SkillQuestionsResponse(BaseModel):
    success: bool
    student_id: str
    topic_code: str
    topic_name: str
    sprint_token: str
    current_mastery: float
    target_difficulty: str
    starting_difficulty: str
    questions_recommended: int
    fetched_count: int
    questions: List[Dict[str, Any]]
    no_questions: bool
    message: Optional[str] = None
    adaptive_config: Optional[Dict[str, Any]] = None