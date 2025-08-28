# student_Dashboard/study_plan_logic.py

import math
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# This script defines the core logic for generating adaptive study plans.
# It includes the definition of the learning flow, prerequisites, and the main
# engine for creating, managing, and updating study plans.

# Defines the perfect learning flow in a sequential order with tiers.
PERFECT_LEARNING_FLOW = [
    # TIER 1: FOUNDATIONAL
    {'code': 'MS01', 'name': 'Whole-number operations & order of operations', 'tier': 1},
    {'code': 'MS02', 'name': 'Prime factors, GCF & LCM', 'tier': 1},
    {'code': 'QC03', 'name': 'GCF & LCM Reasoning', 'tier': 1},
    {'code': 'MS03', 'name': 'Integer operations & absolute value', 'tier': 1},
    {'code': 'QC01', 'name': 'Signed Integers & Absolute Value', 'tier': 1},
    
    # TIER 2: NUMBER SYSTEMS
    {'code': 'MS04', 'name': 'Fraction & mixed-number operations', 'tier': 2},
    {'code': 'QC02', 'name': 'Fractions & Mixed Numbers', 'tier': 2},
    {'code': 'MS05', 'name': 'Decimal & percent reasoning', 'tier': 2},
    {'code': 'QC04', 'name': 'Decimals & Percents', 'tier': 2},
    
    # TIER 3: PROPORTIONAL REASONING
    {'code': 'MS06', 'name': 'Ratios, unit rates, scale drawings & proportions', 'tier': 3},
    {'code': 'QC05', 'name': 'Ratios & Unit Rates', 'tier': 3},
    
    # TIER 4: EXPONENTIAL
    {'code': 'MS07', 'name': 'Exponents, squares & square roots', 'tier': 4},
    {'code': 'QC06', 'name': 'Exponents & Roots', 'tier': 4},
    {'code': 'QC19', 'name': 'Scientific Notation & Order of Magnitude', 'tier': 4},
    
    # TIER 5: ALGEBRAIC BASIC
    {'code': 'MS08', 'name': 'Evaluating & simplifying algebraic expressions', 'tier': 5},
    {'code': 'QC07a', 'name': 'Variable Expressions (Fixed Order)', 'tier': 5},
    {'code': 'QC07b', 'name': 'Variable Expressions (Indeterminate)', 'tier': 5},
    
    # TIER 6: ALGEBRAIC ADVANCED
    {'code': 'MS09', 'name': 'One-variable linear equations & inequalities', 'tier': 6},
    {'code': 'MS10', 'name': 'Coordinate-plane basics', 'tier': 6},
    {'code': 'QC13', 'name': 'Coordinate Plane Slope & Distance', 'tier': 6},
    {'code': 'MS11', 'name': 'Patterns, sequences & basic function rules', 'tier': 6},
    {'code': 'QC08', 'name': 'Sequences & Patterns', 'tier': 6},
    
    # TIER 7: GEOMETRIC
    {'code': 'MS12', 'name': 'Angle relationships & polygon properties', 'tier': 7},
    {'code': 'QC09', 'name': 'Angle & Segment Relations', 'tier': 7},
    {'code': 'MS13', 'name': 'Perimeter, area & circumference of 2-D shapes', 'tier': 7},
    {'code': 'QC11', 'name': 'Area & Perimeter Reasoning', 'tier': 7},
    {'code': 'QC12', 'name': 'Circle Measures', 'tier': 7},
    {'code': 'QC10', 'name': 'Similar Figures & Scale', 'tier': 7},
    {'code': 'MS14', 'name': 'Surface area & volume of 3-D solids', 'tier': 7},
    {'code': 'QC16', 'name': 'Volume & Surface Area', 'tier': 7},
    
    # TIER 8: MEASUREMENT
    {'code': 'MS16', 'name': 'Measurement units, tools & conversions', 'tier': 8},
    {'code': 'QC14', 'name': 'Unit Conversion', 'tier': 8},
    {'code': 'QC15', 'name': 'Rate/Time/Distance & Density', 'tier': 8},
    
    # TIER 9: DATA ANALYSIS
    {'code': 'MS17', 'name': 'Data representation & statistics', 'tier': 9},
    {'code': 'QC17', 'name': 'Data Displays & Central Tendency', 'tier': 9},
    {'code': 'MS18', 'name': 'Probability of simple & compound events', 'tier': 9},
    {'code': 'QC18', 'name': 'Probability Comparisons', 'tier': 9}
]

# Defines the prerequisites for each topic based on the learning flow.
PREREQUISITES = {
    # TIER 1 - Foundation (no prerequisites)
    'MS01': [],
    'MS02': ['MS01'],
    'QC03': ['MS02'],
    'MS03': ['MS01'],
    'QC01': ['MS03'],
    
    # TIER 2 - Number Systems (requires Tier 1)
    'MS04': ['MS02', 'MS03'],
    'QC02': ['MS04'],
    'MS05': ['MS04'],
    'QC04': ['MS05'],
    
    # TIER 3 - Proportional (requires Tier 2)
    'MS06': ['MS04', 'MS05'],
    'QC05': ['MS06'],
    
    # TIER 4 - Exponential (requires Tier 1-3)
    'MS07': ['MS03', 'MS04'],
    'QC06': ['MS07'],
    'QC19': ['MS07', 'QC06'],
    
    # TIER 5 - Algebraic Basic (requires Tier 4)
    'MS08': ['MS07', 'QC06'],
    'QC07a': ['MS08'],
    'QC07b': ['QC07a'],
    
    # TIER 6 - Algebraic Advanced (requires Tier 5)
    'MS09': ['MS08', 'QC07a'],
    'MS10': ['MS09'],
    'QC13': ['MS10'],
    'MS11': ['MS08', 'MS09'],
    'QC08': ['MS11'],
    
    # TIER 7 - Geometric (requires basic algebra)
    'MS12': ['MS08'],
    'QC09': ['MS12'],
    'MS13': ['MS06', 'MS08'],  # Needs proportions and algebra
    'QC11': ['MS13'],
    'QC12': ['MS13', 'QC11'],
    'QC10': ['MS13', 'QC11'],  # Similar figures need area concepts
    'MS14': ['MS13', 'QC11'],  # 3D needs 2D mastery
    'QC16': ['MS14'],
    
    # TIER 8 - Measurement (requires proportional reasoning)
    'MS16': ['MS06'],
    'QC14': ['MS16'],
    'QC15': ['MS16', 'QC14'],
    
    # TIER 9 - Data Analysis (requires fractions and algebra)
    'MS17': ['MS04', 'MS08'],
    'QC17': ['MS17'],
    'MS18': ['MS04', 'MS05'],  # Probability needs fractions/decimals
    'QC18': ['MS18']
}

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
            return {topic['code']: mastery_data.get(topic['code'], {}).get('mastery_percentage', 0.0) 
                   for topic in PERFECT_LEARNING_FLOW}
            
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
    
    def ensure_comprehensive_coverage(self, daily_plans: List[DailyStudyPlan], 
                                    all_topics_to_cover: List[str], 
                                    current_masteries: Dict[str, float]) -> List[DailyStudyPlan]:
        """
        Ensures that all topics are covered in the study plan within the existing timeline.
        This function adds any remaining topics to the least-loaded days in the plan.
        """
        # Map scheduled topics to their assigned day
        assigned_day_by_topic: Dict[str, int] = {}
        for plan in daily_plans:
            for topic in plan.topics:
                assigned_day_by_topic[topic.topic_code] = plan.day

        # Determine the topics that are not yet scheduled
        remaining_topics = [t for t in all_topics_to_cover if t not in assigned_day_by_topic]
        if not remaining_topics:
            return daily_plans

        # Helper to compute the earliest day a topic can be placed based on its prerequisites
        def earliest_day_for_topic(topic_code: str) -> int:
            prereqs = PREREQUISITES.get(topic_code, [])
            if not prereqs:
                return 1
            latest_prereq_day = 1
            for prereq in prereqs:
                prereq_day = assigned_day_by_topic.get(prereq, 1)
                latest_prereq_day = max(latest_prereq_day, prereq_day)
            return latest_prereq_day

        # Schedule the remaining topics following the learning flow order
        for flow_topic in PERFECT_LEARNING_FLOW:
            topic_code = flow_topic['code']
            if topic_code not in remaining_topics:
                continue

            # Find the earliest eligible day and choose the least-loaded day from that point
            earliest_day = earliest_day_for_topic(topic_code)

            # Exclude days that have full-length or section tests
            def is_test_day(p: DailyStudyPlan) -> bool:
                try:
                    return any(t.get("type") in ("full_length", "section") for t in getattr(p, "tests", []))
                except Exception:
                    return False
            candidate_days = [p for p in daily_plans if p.day >= earliest_day and not is_test_day(p)]
            if not candidate_days:
                # Fallback to any non-test day if no eligible days are found
                candidate_days = [p for p in daily_plans if not is_test_day(p)]
            target_plan = min(candidate_days, key=lambda p: len(p.topics)) if candidate_days else daily_plans[-1]

            # Create a topic plan for the remaining topic
            current_mastery = current_masteries.get(topic_code, 0)
            study_action = self.determine_study_action(current_mastery)
            if current_mastery < 40:
                target_mastery = 50
            elif current_mastery < 65:
                target_mastery = 70
            elif current_mastery < 80:
                target_mastery = 85
            else:
                target_mastery = min(95, current_mastery + 5)

            topic_info = next(t for t in PERFECT_LEARNING_FLOW if t['code'] == topic_code)
            topic_plan = TopicStudyPlan(
                day=target_plan.day,
                topic_code=topic_code,
                topic_name=topic_info['name'],
                current_mastery=current_mastery,
                target_mastery=target_mastery,
                target_difficulty="Medium",
                study_action=study_action,
                time_minutes=15,
                questions_recommended=10,
                focus_areas=["Basic concepts", "Fundamental skills"],
                success_criteria=f"Understand basic concepts, achieve 50% accuracy"
            )
            target_plan.topics.append(topic_plan)
            target_plan.total_time_minutes += 15
            assigned_day_by_topic[topic_code] = target_plan.day
        
        return daily_plans
    
    def generate_study_plan(self, student_id: str, total_days: int, 
                          daily_time_minutes: int = 60,
                          recent_topic_adjustments: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generates a comprehensive study plan for a specified duration, ensuring all topics are covered.
        """
        recent_topic_adjustments = recent_topic_adjustments or {}
        
        # Get the student's current mastery levels
        current_masteries = self.get_student_mastery(student_id)
        
        # Get all topics that need to be covered (i.e., not mastered)
        all_topics_to_cover = []
        for topic in PERFECT_LEARNING_FLOW:
            topic_code = topic['code']
            current_mastery = current_masteries.get(topic_code, 0)
            if current_mastery < self.mastery_threshold:
                all_topics_to_cover.append(topic_code)
        
        # Calculate the number of topics to cover per day
        topics_per_day = max(1, math.ceil(len(all_topics_to_cover) / max(1, total_days)))
        
        # Increase the daily study time if needed to reasonably cover the topics
        effective_daily_time_minutes = max(daily_time_minutes, topics_per_day * 20)
        
        # Generate the daily plans
        daily_plans = []
        start_date = datetime.now()
        topic_index = 0
        
        for day in range(1, total_days + 1):
            current_date = start_date + timedelta(days=day - 1)

            # Decide which tests to schedule for the day based on a cadence
            tests: List[Dict[str, Any]] = []
            is_full_length_day = (day % 15 == 0)
            is_section_test_day = (day % 3 == 0) and not is_full_length_day

            if is_full_length_day:
                tests.append({
                    "type": "full_length",
                    "time_minutes": self.full_length_time_minutes,
                    "questions": self.full_length_questions
                })
            elif is_section_test_day:
                # Schedule two section tests, alternating between pairs of categories
                pair_a = [0, 2]
                pair_b = [1, 3]
                cycle_index = (day // 3) % 2
                indices = pair_a if cycle_index == 0 else pair_b
                for idx in indices:
                    if idx < len(self.section_test_categories):
                        cat = self.section_test_categories[idx]
                        tests.append({
                            "type": "section",
                            "category": cat,
                            "time_minutes": self.section_test_time_minutes,
                            "questions": self.section_questions
                        })

            # Get the available topics for study, respecting prerequisites
            available_topics = self.get_next_available_topics(current_masteries)
            
            # Prioritize uncovered topics to ensure all topics are covered
            daily_topics = []
            max_topics_today = topics_per_day
            if is_full_length_day:
                max_topics_today = 0
            elif is_section_test_day:
                max_topics_today = max(1, topics_per_day - 1)
            
            # Add available and uncovered topics to the daily plan
            for topic_code in available_topics:
                if topic_code in all_topics_to_cover and len(daily_topics) < max_topics_today:
                    daily_topics.append(topic_code)
                    all_topics_to_cover.remove(topic_code)
            
            # If there's still room, add more uncovered topics
            if len(daily_topics) < max_topics_today and all_topics_to_cover:
                for topic_code in all_topics_to_cover[:max_topics_today - len(daily_topics)]:
                    if len(daily_topics) < max_topics_today:
                        daily_topics.append(topic_code)
                        all_topics_to_cover.remove(topic_code)
            
            # If there's still room, add review topics
            if len(daily_topics) < max_topics_today:
                review_topics = self.get_review_topics(current_masteries, day)
                for review_topic in review_topics:
                    if len(daily_topics) < max_topics_today:
                        daily_topics.append(review_topic)
            
            # Get review topics (separate from study topics)
            review_topics = self.get_review_topics(current_masteries, day)
            
            # Allocate time for the daily topics
            min_required_for_topics = 15 * max(1, len(daily_topics))
            tests_time = sum(t.get("time_minutes", 0) for t in tests)
            study_time = effective_daily_time_minutes - (len(review_topics) * 10) - tests_time
            if study_time < min_required_for_topics:
                study_time = min_required_for_topics
            time_allocation = self.calculate_time_allocation(daily_topics, current_masteries, study_time)
            
            # Create the topic study plans for the day
            topic_plans = []
            for topic_code in daily_topics:
                topic_info = next(t for t in PERFECT_LEARNING_FLOW if t['code'] == topic_code)
                current_mastery = current_masteries.get(topic_code, 0)
                study_action = self.determine_study_action(current_mastery)
                
                # Set the target mastery based on the current level
                if current_mastery < 40:
                    target_mastery = 50
                elif current_mastery < 65:
                    target_mastery = 70
                elif current_mastery < 80:
                    target_mastery = 85
                else:
                    target_mastery = min(95, current_mastery + 5)
                
                # Calculate the number of questions and target difficulty
                time_minutes = time_allocation.get(topic_code, 20)
                if current_mastery < 40:
                    questions_recommended = 14
                    target_difficulty = "Easy"
                elif current_mastery < 65:
                    questions_recommended = 12
                    target_difficulty = "Medium"
                elif current_mastery < 80:
                    questions_recommended = 10
                    target_difficulty = "Medium"
                else:
                    questions_recommended = 8
                    target_difficulty = "Hard"

                # Apply recent adjustments if the topic was just assessed
                if topic_code in recent_topic_adjustments:
                    adj = recent_topic_adjustments.get(topic_code, {})
                    q_delta = int(adj.get("questions_delta", 0) or 0)
                    force_diff = adj.get("force_difficulty")
                    questions_recommended = max(5, min(20, questions_recommended + q_delta))
                    if isinstance(force_diff, str) and force_diff in ("Easy", "Medium", "Hard"):
                        target_difficulty = force_diff
                
                # Define focus areas based on the study action
                if study_action == StudyAction.LEARN:
                    focus_areas = ["Basic concepts", "Fundamental skills", "Simple examples"]
                    success_criteria = f"Understand basic concepts, achieve 50% accuracy"
                elif study_action == StudyAction.PRACTICE:
                    focus_areas = ["Skill building", "Practice problems", "Pattern recognition"]
                    success_criteria = f"Build fluency, achieve 70% accuracy"
                elif study_action == StudyAction.REINFORCE:
                    focus_areas = ["Advanced problems", "Edge cases", "Speed improvement"]
                    success_criteria = f"Strengthen skills, achieve 85% accuracy"
                else:
                    focus_areas = ["Challenging problems", "Applications", "Connections"]
                    success_criteria = f"Maintain mastery, 90%+ accuracy"
                
                topic_plan = TopicStudyPlan(
                    day=day,
                    topic_code=topic_code,
                    topic_name=topic_info['name'],
                    current_mastery=current_mastery,
                    target_mastery=target_mastery,
                    target_difficulty=target_difficulty,
                    study_action=study_action,
                    time_minutes=time_minutes,
                    questions_recommended=questions_recommended,
                    focus_areas=focus_areas,
                    success_criteria=success_criteria
                )
                topic_plans.append(topic_plan)
            
            # Determine the daily focus
            if is_full_length_day:
                daily_focus = "Full-Length Assessment"
            elif is_section_test_day:
                daily_focus = "Section Assessment + Study"
            else:
                if topic_plans:
                    primary_action = topic_plans[0].study_action
                    if primary_action == StudyAction.LEARN:
                        daily_focus = "Learning New Concepts"
                    elif primary_action == StudyAction.PRACTICE:
                        daily_focus = "Skill Building & Practice"
                    elif primary_action == StudyAction.REINFORCE:
                        daily_focus = "Strengthening & Mastery"
                    else:
                        daily_focus = "Review & Maintenance"
                else:
                    daily_focus = "Comprehensive Review"
            
            daily_plan = DailyStudyPlan(
                day=day,
                date=current_date,
                topics=topic_plans,
                total_time_minutes=sum(t.time_minutes for t in topic_plans) + len(review_topics) * 10 + tests_time,
                daily_focus=daily_focus,
                review_topics=review_topics,
                tests=tests
            )
            daily_plans.append(daily_plan)
            
            # Simulate progress for planning purposes
            for topic_code in daily_topics:
                current_mastery = current_masteries.get(topic_code, 0)
                if current_mastery < 80:
                    improvement = 3 if study_action == StudyAction.LEARN else 4
                    current_masteries[topic_code] = min(85, current_mastery + improvement)
            
            # Re-evaluate available topics after the progress simulation
            if day < total_days:
                available_topics = self.get_next_available_topics(current_masteries)
                for topic_code in available_topics:
                    if topic_code not in all_topics_to_cover and topic_code not in [t.topic_code for t in topic_plans]:
                        all_topics_to_cover.append(topic_code)
        
        # Ensure all topics are covered in the plan
        daily_plans = self.ensure_comprehensive_coverage(daily_plans, all_topics_to_cover, current_masteries)
        
        # Calculate completion statistics
        total_topics = len(PERFECT_LEARNING_FLOW)
        final_masteries = self.get_student_mastery(student_id)
        mastered_topics = sum(1 for m in final_masteries.values() if m >= 80)
        
        # Calculate coverage statistics
        topics_covered_in_plan = []
        for plan in daily_plans:
            for topic in plan.topics:
                if topic.topic_code not in topics_covered_in_plan:
                    topics_covered_in_plan.append(topic.topic_code)
        
        coverage_percentage = (len(topics_covered_in_plan) / total_topics) * 100
        
        # Estimate when each tier will be completed
        estimated_completion = []
        for tier in range(1, 10):
            tier_topics = [t for t in PERFECT_LEARNING_FLOW if t['tier'] == tier]
            tier_mastery = sum(final_masteries.get(t['code'], 0) for t in tier_topics) / len(tier_topics)
            
            if tier_mastery >= 80:
                estimated_days = 0
            elif tier_mastery >= 60:
                estimated_days = len(tier_topics) * 3
            else:
                estimated_days = len(tier_topics) * 5
            
            estimated_completion.append({
                "tier": tier,
                "tier_name": f"Tier {tier}",
                "topics_count": len(tier_topics),
                "current_avg_mastery": round(tier_mastery, 1),
                "estimated_completion_days": estimated_days
            })
        
        return {
            "success": True,
            "student_id": student_id,
            "plan_duration_days": total_days,
            "daily_time_minutes": effective_daily_time_minutes,
            "plan_start_date": start_date.isoformat(),
            "daily_plans": [
                {
                    "day": plan.day,
                    "date": plan.date.isoformat(),
                    "daily_focus": plan.daily_focus,
                    "total_time_minutes": plan.total_time_minutes,
                    "tests": plan.tests,
                    "topics": [
                        {
                            "topic_code": topic.topic_code,
                            "topic_name": topic.topic_name,
                            "current_mastery": topic.current_mastery,
                            "target_mastery": topic.target_mastery,
                            "target_difficulty": topic.target_difficulty,
                            "study_action": topic.study_action.value,
                            "time_minutes": topic.time_minutes,
                            "questions_recommended": topic.questions_recommended,
                            "focus_areas": topic.focus_areas,
                            "success_criteria": topic.success_criteria
                        } for topic in plan.topics
                    ],
                    "review_topics": plan.review_topics
                } for plan in daily_plans
            ],
            "progress_summary": {
                "total_topics": total_topics,
                "currently_mastered": mastered_topics,
                "mastery_percentage": round((mastered_topics / total_topics) * 100, 1),
                "topics_covered_in_plan": len(topics_covered_in_plan),
                "coverage_percentage": round(coverage_percentage, 1),
                "estimated_tier_completion": estimated_completion
            },
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