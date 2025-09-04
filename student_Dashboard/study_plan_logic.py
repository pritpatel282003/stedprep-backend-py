# student_Dashboard/study_plan_logic.py

import math
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# This script defines the core logic for generating adaptive study plans.
# It includes the definition of the learning flow, prerequisites, and the main
# engine for creating, managing, and updating study plans.

from models.learning_flow import COMPLETE_LEARNING_FLOW as PERFECT_LEARNING_FLOW, TOPIC_PREREQUISITES as PREREQUISITES

class StudyAction(Enum):
    """
    Enum for the different study actions a student can take.
    """
    LEARN = "learn"           # New topic (0-40%)
    PRACTICE = "practice"     # Building skills (40-65%)
    REINFORCE = "reinforce"   # Strengthening (65-80%)
    MASTERED = "mastered"     # Completed (80%+)
    REVIEW = "review"         # Periodic maintenance

@dataclass
class TopicStudyPlan:
    """
    Data class for a topic-specific study plan.
    """
    day: int
    topic_code: str
    topic_name: str
    current_mastery: float
    target_mastery: float
    target_difficulty: str
    study_action: StudyAction
    time_minutes: int
    questions_recommended: int
    focus_areas: List[str]
    success_criteria: str

@dataclass
class DailyStudyPlan:
    """
    Data class for a daily study plan.
    """
    day: int
    date: datetime
    topics: List[TopicStudyPlan]
    total_time_minutes: int
    daily_focus: str
    review_topics: List[str]
    tests: List[Dict[str, Any]]

class AdaptiveStudyPlanEngine:
    """
    The main engine for generating and managing adaptive study plans.
    """
    
    def __init__(self, db_manager, section_test_categories: Optional[List[str]] = None, max_section_tests_per_day: int = 2):
        self.db_manager = db_manager
        self.mastery_threshold = 80.0  # Topics above this are considered mastered
        self.daily_time_minutes = 60   # Default daily study time
        self.near_mastery_min = 85.0   # Near-mastery lower bound
        self.near_mastery_target = 90.0  # Target to push past near-mastery
        # Test configuration
        self.full_length_time_minutes = 70
        self.section_test_time_minutes = 30
        # Question counts
        self.sprint_questions_per_topic = 10
        self.section_questions = 25
        self.full_length_questions = 100
        self.section_test_categories = section_test_categories or [
            "verbal reasoning",
            "mathematics achievement",
            "quant comparisions",
            "reading comprehension"
        ]
        self.max_section_tests_per_day = max(1, min(2, int(max_section_tests_per_day)))

    def schedule_micro_practice_next_day(self, student_id: str, topic_code: str, new_mastery: float, minutes: int = 5) -> bool:
        """
        Injects a short micro-practice session for a topic into the next day's plan.
        This is typically used for topics where the student is near mastery.
        """
        try:
            database = self.db_manager.client[self.db_manager.database_name]
            collection = database["studyPlans"]

            # Find the student's study plan
            study_plan = collection.find_one({"student_id": student_id})
            if not study_plan:
                return False

            # Find the plan for the next day
            daily_plans = study_plan.get("daily_plans", [])
            if not daily_plans:
                return False

            tomorrow = (datetime.now().date() + timedelta(days=1))
            target_plan = None
            for dp in daily_plans:
                try:
                    dp_date = datetime.fromisoformat(dp["date"]).date()
                except Exception:
                    continue
                if dp_date == tomorrow:
                    target_plan = dp
                    break

            if not target_plan:
                return False

            # Build the micro-practice topic entry
            topic_info = next((t for t in PERFECT_LEARNING_FLOW if t['code'] == topic_code), None)
            if not topic_info:
                return False

            study_action = "reinforce" if new_mastery >= 85 else "practice"
            micro_topic = {
                "topic_code": topic_code,
                "topic_name": topic_info['name'],
                "current_mastery": new_mastery,
                "target_mastery": min(self.near_mastery_target, new_mastery + 1),
                "study_action": study_action,
                "time_minutes": minutes,
                "questions_recommended": 10,
                "focus_areas": ["Near-mastery tuning", "Error review"],
                "success_criteria": "Push to 90%+ accuracy"
            }

            # Append the micro-practice if it's not already there for the same topic
            if not any(t.get("topic_code") == topic_code and t.get("time_minutes", 0) <= minutes for t in target_plan.get("topics", [])):
                target_plan.setdefault("topics", []).append(micro_topic)
                # Increase the total time for that day
                target_plan["total_time_minutes"] = target_plan.get("total_time_minutes", 0) + minutes

                # Persist the modified daily plans
                collection.update_one(
                    {"_id": study_plan["_id"]},
                    {"$set": {"daily_plans": daily_plans}}
                )
                return True

            return False
        except Exception as e:
            print(f"Error scheduling micro practice: {e}")
            return False
        
    def get_student_mastery(self, student_id: str) -> Dict[str, float]:
        """
        Fetches the current mastery levels for a student from the studentSummary collection.
        """
        try:
            database = self.db_manager.client[self.db_manager.database_name]
            collection = database["studentSummary"]
            
            # Get the latest summary for the student
            student_data = collection.find_one(
                {"student_id": student_id},
                sort=[("analysis_date", -1)]
            )
            
            if not student_data:
                # Return zero mastery for all topics if no data is found
                return {topic['code']: 0.0 for topic in PERFECT_LEARNING_FLOW}
            
            mastery_data = student_data.get("complete_topic_mastery", {})

            # Include all topics from the learning flow, and also any new topics from the summary
            all_topic_codes = {topic['code'] for topic in PERFECT_LEARNING_FLOW}
            all_topic_codes.update(mastery_data.keys())

            return {code: mastery_data.get(code, {}).get('mastery_percentage', 0.0)
                   for code in all_topic_codes}
            
        except Exception as e:
            print(f"Error fetching student mastery: {e}")
            return {topic['code']: 0.0 for topic in PERFECT_LEARNING_FLOW}
    
    def update_mastery_after_test(self, student_id: str, topic_code: str, new_mastery: float):
        """
        Updates a student's mastery for a topic after a test.
        """
        try:
            database = self.db_manager.client[self.db_manager.database_name]
            collection = database["studentSummary"]
            
            # Update the mastery in the latest summary
            collection.update_one(
                {"student_id": student_id},
                {
                    "$set": {
                        f"complete_topic_mastery.{topic_code}.mastery_percentage": new_mastery,
                        f"complete_topic_mastery.{topic_code}.total_questions": 
                            collection.find_one({"student_id": student_id})
                            .get("complete_topic_mastery", {})
                            .get(topic_code, {})
                            .get("total_questions", 0) + 5,  # Assume 5 questions per test
                        "updated_at": datetime.now()
                    }
                },
                upsert=True
            )
            print(f"✅ Updated mastery for {topic_code}: {new_mastery}%")
            
        except Exception as e:
            print(f"Error updating mastery: {e}")
    
    def check_prerequisites_satisfied(self, topic_code: str, current_masteries: Dict[str, float]) -> bool:
        """
        Checks if all prerequisites for a topic are satisfied (mastery >= 65%).
        """
        prerequisites = PREREQUISITES.get(topic_code, [])
        
        for prereq in prerequisites:
            if current_masteries.get(prereq, 0) < 65:
                return False
        
        return True
    
    def get_next_available_topics(self, current_masteries: Dict[str, float]) -> List[str]:
        """
        Gets a list of topics that are ready for the student to study (prerequisites met, not mastered).
        """
        available_topics = []
        
        for topic in PERFECT_LEARNING_FLOW:
            topic_code = topic['code']
            current_mastery = current_masteries.get(topic_code, 0)
            
            # Skip if the topic is already mastered
            if current_mastery >= self.mastery_threshold:
                continue
            
            # Check if prerequisites are satisfied
            if self.check_prerequisites_satisfied(topic_code, current_masteries):
                available_topics.append(topic_code)
        
        return available_topics
    
    def determine_study_action(self, mastery_percentage: float) -> StudyAction:
        """
        Determines the appropriate study action based on the current mastery percentage.
        """
        if mastery_percentage >= 80:
            return StudyAction.MASTERED
        elif mastery_percentage >= 65:
            return StudyAction.REINFORCE
        elif mastery_percentage >= 40:
            return StudyAction.PRACTICE
        else:
            return StudyAction.LEARN
    
    def calculate_time_allocation(self, topics: List[str], current_masteries: Dict[str, float], 
                                daily_time: int) -> Dict[str, int]:
        """
        Allocates the daily study time across a list of topics based on their mastery levels.
        Topics with lower mastery get more time.
        """
        if not topics:
            return {}
        
        # Calculate weights based on inverse mastery (lower mastery = more time)
        weights = {}
        for topic in topics:
            mastery = current_masteries.get(topic, 0)
            weight = max(1, 100 - mastery)
            weights[topic] = weight
        
        total_weight = sum(weights.values())
        
        # Allocate time proportionally
        time_allocation = {}
        remaining_time = daily_time
        
        for topic in topics[:-1]:  # Allocate time for all but the last topic
            allocated_time = max(15, int((weights[topic] / total_weight) * daily_time))
            time_allocation[topic] = min(allocated_time, remaining_time - 15)
            remaining_time -= time_allocation[topic]
        
        # Give the remaining time to the last topic
        if topics:
            time_allocation[topics[-1]] = max(15, remaining_time)
        
        return time_allocation
    
    def get_review_topics(self, current_masteries: Dict[str, float], day: int) -> List[str]:
        """
        Gets a list of topics that need periodic review based on their mastery level and the current day.
        """
        review_topics = []
        
        for topic_code, mastery in current_masteries.items():
            # Review mastered topics every 7 days, and reinforced topics every 5 days
            if mastery >= 80 and day % 7 == 0:
                review_topics.append(topic_code)
            elif 65 <= mastery < 80 and day % 5 == 0:
                review_topics.append(topic_code)
        
        return review_topics[:2]  # Limit to 2 review topics per day
    
    def generate_study_plan(self, student_id: str, total_days: int,
                          daily_time_minutes: int = 60,
                          recent_topic_adjustments: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generates a comprehensive study plan for a specified duration, ensuring all topics are covered.
        The plan is ordered by mastery (lowest to highest), with prerequisites handled correctly.
        """
        recent_topic_adjustments = recent_topic_adjustments or {}

        # 1. Get student's mastery for all topics
        current_masteries = self.get_student_mastery(student_id)

        # 2. Filter out mastered topics and sort by mastery (low to high)
        unmastered_topics = {code: mastery for code, mastery in current_masteries.items() if mastery < self.mastery_threshold}
        sorted_topics = sorted(unmastered_topics.items(), key=lambda item: item[1])

        # 3. Create a final ordered list of topics, handling prerequisites
        scheduled_topics = []
        
        def schedule_topic_and_prerequisites(topic_code):
            if topic_code in scheduled_topics:
                return

            # Recursively schedule prerequisites first
            for prereq_code in PREREQUISITES.get(topic_code, []):
                schedule_topic_and_prerequisites(prereq_code)

            # Add the topic itself if it's not already scheduled
            if topic_code not in scheduled_topics:
                scheduled_topics.append(topic_code)

        for topic_code, mastery in sorted_topics:
            schedule_topic_and_prerequisites(topic_code)

        # 4. Distribute the scheduled topics across the total days
        topics_per_day = max(1, math.ceil(len(scheduled_topics) / max(1, total_days)))
        
        # 5. Generate daily plans
        daily_plans = []
        start_date = datetime.now()
        
        for day in range(1, total_days + 1):
            day_topics = scheduled_topics[(day - 1) * topics_per_day : day * topics_per_day]

            if not day_topics:
                continue

            current_date = start_date + timedelta(days=day - 1)
            topic_plans = []

            time_allocation = self.calculate_time_allocation(day_topics, current_masteries, daily_time_minutes)

            for topic_code in day_topics:
                topic_info = next((t for t in PERFECT_LEARNING_FLOW if t['code'] == topic_code), None)
                if not topic_info:
                    topic_info = {'name': 'Unknown Topic'} # Handle new topics

                current_mastery = current_masteries.get(topic_code, 0)
                study_action = self.determine_study_action(current_mastery)
                
                # Set target mastery
                if current_mastery < 40: target_mastery = 50
                elif current_mastery < 65: target_mastery = 70
                elif current_mastery < 80: target_mastery = 85
                else: target_mastery = min(95, current_mastery + 5)
                
                time_minutes = time_allocation.get(topic_code, 20)
                
                if study_action == StudyAction.LEARN:
                    focus_areas = ["Basic concepts", "Fundamental skills"]
                    success_criteria = "Achieve 50% accuracy"
                elif study_action == StudyAction.PRACTICE:
                    focus_areas = ["Skill building", "Practice problems"]
                    success_criteria = "Achieve 70% accuracy"
                else:
                    focus_areas = ["Advanced problems", "Edge cases"]
                    success_criteria = "Achieve 85% accuracy"

                topic_plans.append(TopicStudyPlan(
                    day=day,
                    topic_code=topic_code,
                    topic_name=topic_info['name'],
                    current_mastery=current_mastery,
                    target_mastery=target_mastery,
                    target_difficulty="Medium",
                    study_action=study_action,
                    time_minutes=time_minutes,
                    questions_recommended=10,
                    focus_areas=focus_areas,
                    success_criteria=success_criteria
                ))

            daily_plan = DailyStudyPlan(
                day=day,
                date=current_date,
                topics=topic_plans,
                total_time_minutes=sum(tp.time_minutes for tp in topic_plans),
                daily_focus="Focused Study",
                review_topics=[],
                tests=[]
            )
            daily_plans.append(daily_plan)

        return {
            "success": True,
            "student_id": student_id,
            "plan_duration_days": total_days,
            "daily_time_minutes": daily_time_minutes,
            "plan_start_date": start_date.isoformat(),
            "daily_plans": [dp.__dict__ for dp in daily_plans],
            "created_at": datetime.now().isoformat()
        }
    
    def get_todays_plan(self, student_id: str) -> Dict[str, Any]:
        """
        Gets the study plan for the current day for a student.
        """
        try:
            database = self.db_manager.client[self.db_manager.database_name]
            collection = database["studyPlans"]
            
            today = datetime.now().date()
            
            # Find a study plan that includes today
            study_plan = collection.find_one({
                "student_id": student_id,
                "daily_plans.date": {
                    "$gte": datetime.combine(today, datetime.min.time()),
                    "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
                }
            })
            
            if not study_plan:
                # Generate a single-day plan if no plan exists
                return self.generate_study_plan(student_id, 1)
            
            # Find today's plan within the study plan
            todays_plan = None
            for daily_plan in study_plan.get("daily_plans", []):
                plan_date = datetime.fromisoformat(daily_plan["date"]).date()
                if plan_date == today:
                    todays_plan = daily_plan
                    break
            
            return {
                "success": True,
                "student_id": student_id,
                "date": today.isoformat(),
                "todays_plan": todays_plan
            }
            
        except Exception as e:
            print(f"Error getting today's plan: {e}")
            return {"success": False, "error": str(e)}
    
    def save_study_plan(self, study_plan: Dict[str, Any]):
        """
        Saves a study plan to the database.
        """
        try:
            database = self.db_manager.client[self.db_manager.database_name]
            collection = database["studyPlans"]
            
            # Remove any existing plan for this student
            collection.delete_many({"student_id": study_plan["student_id"]})
            
            # Insert the new plan
            result = collection.insert_one(study_plan)
            print(f"✅ Study plan saved for student: {study_plan['student_id']}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error saving study plan: {e}")
            return None

def create_student_study_plan(student_id: str, total_days: int, db_manager, 
                            daily_time_minutes: int = 60,
                            section_test_categories: Optional[List[str]] = None,
                            max_section_tests_per_day: int = 1) -> Dict[str, Any]:
    """
    Main function to create and save a study plan for a student.
    
    This function ensures comprehensive coverage of all topics in the curriculum,
    respecting prerequisites and the defined learning flow.
    
    Args:
        student_id (str): The student's identifier.
        total_days (int): The number of days for the study plan.
        db_manager: The database connection manager.
        daily_time_minutes (int, optional): The daily study time in minutes. Defaults to 60.
        section_test_categories (Optional[List[str]], optional): The categories for section tests. Defaults to None.
        max_section_tests_per_day (int, optional): The maximum number of section tests per day. Defaults to 1.
    
    Returns:
        A dictionary representing the complete study plan.
    """
    
    engine = AdaptiveStudyPlanEngine(db_manager,
                                     section_test_categories=section_test_categories,
                                     max_section_tests_per_day=max_section_tests_per_day)
    
    # Generate the study plan
    study_plan = engine.generate_study_plan(student_id, total_days, daily_time_minutes)
    
    if study_plan["success"]:
        # Save the study plan to the database
        plan_id = engine.save_study_plan(study_plan)
        study_plan["plan_id"] = plan_id
    
    return study_plan

def update_student_mastery(student_id: str, topic_code: str, new_mastery: float, db_manager):
    """
    Updates a student's mastery for a topic after they complete a topic test.
    
    Args:
        student_id (str): The student's identifier.
        topic_code (str): The code of the topic to update (e.g., 'MS01', 'QC03').
        new_mastery (float): The new mastery percentage (0-100).
        db_manager: The database connection manager.
    """
    engine = AdaptiveStudyPlanEngine(db_manager)
    engine.update_mastery_after_test(student_id, topic_code, new_mastery)

    # If the student is near mastery, schedule a micro-practice for the next day
    scheduled_msg = ""
    if engine.near_mastery_min <= new_mastery < engine.near_mastery_target:
        did_schedule = engine.schedule_micro_practice_next_day(student_id, topic_code, new_mastery, minutes=5)
        if did_schedule:
            scheduled_msg = " Micro-practice (5 min) added for tomorrow."
        else:
            scheduled_msg = " Could not schedule micro-practice for tomorrow (no plan day found)."
    
    # If mastery reaches the threshold, note the achievement
    if new_mastery >= engine.mastery_threshold:
        print(f"🎉 Topic {topic_code} at/above mastery threshold. {new_mastery}%")
    
    return {"success": True, "message": f"Mastery updated for {topic_code}: {new_mastery}%{scheduled_msg}"}