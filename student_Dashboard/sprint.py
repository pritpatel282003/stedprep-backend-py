# student_Dashboard/sprint.py

import random
import time
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

import numpy as np

@dataclass
class SprintConfig:
    """
    Configuration for the adaptive sprint.
    """
    max_theta: float = 4.0
    min_theta: float = -4.0
    initial_theta: float = 0.0


class SprintAdaptiveSystem:
    """
    Manages an adaptive sprint for a specific topic and a fixed number of questions.
    This class uses the same database and item bank as the main CAT system but is scoped
    to a single topic for a set number of questions.
    """

    def __init__(
        self,
        sprint_token: str,
        student_id: str,
        topic: str,
        num_questions: int,
        db_manager,
        config: SprintConfig | None = None,
    ) -> None:
        """
        Initializes the SprintAdaptiveSystem.

        Args:
            sprint_token (str): A unique token for the sprint session.
            student_id (str): The ID of the student.
            topic (str): The topic of the sprint.
            num_questions (int): The number of questions in the sprint.
            db_manager: The database manager instance.
            config (SprintConfig, optional): Configuration for the sprint. Defaults to None.
        """
        self.sprint_token = sprint_token
        self.student_id = student_id
        self.topic = topic
        self.num_questions = int(num_questions)
        self.db = db_manager
        self.config = config or SprintConfig()
        self.difficulty_bias = 'medium'

        # Initialize database collections
        self._db = getattr(self.db, "db", self.db)
        self.sessions = self._db["sprint_sessions"]
        self.responses = self._db["sprint_responses"]

        # Load or initialize the sprint state
        existing = self.sessions.find_one({"sprint_token": self.sprint_token})
        if existing:
            # Load existing state
            self.current_theta = float(existing.get("current_theta", self.config.initial_theta))
            self.administered_question_ids = [qid for qid in existing.get("administered_question_ids", [])]
            self.current_question_id = existing.get("current_question_id")
            self.awaiting_response = bool(existing.get("awaiting_response", False))
            self.correct_count = int(existing.get("correct_count", 0))
            self.total_answered = int(existing.get("total_answered", 0))
            self.complete = bool(existing.get("complete", False))
            self.difficulty_bias = existing.get("difficulty_bias", 'medium')
            self.start_theta = float(existing.get("start_theta", self.current_theta))
        else:
            # Initialize new state
            self.current_theta = self._get_initial_theta_from_summary() if self.student_id else self.config.initial_theta
            self.administered_question_ids = []
            self.current_question_id = None
            self.awaiting_response = False
            self.correct_count = 0
            self.total_answered = 0
            self.complete = False
            self.start_theta = self.current_theta
            self._persist_state(created=True)

        # Cache the item bank for the topic
        self.item_bank_collection = self.db.item_bank_collection
        self._topic_items_cache = None

    def _persist_state(self, created: bool = False) -> None:
        """
        Saves the current state of the sprint to the database.
        """
        doc = {
            "sprint_token": self.sprint_token,
            "student_id": self.student_id,
            "topic": self.topic,
            "num_questions": self.num_questions,
            "current_theta": float(self.current_theta),
            "administered_question_ids": list(self.administered_question_ids),
            "current_question_id": self.current_question_id,
            "awaiting_response": self.awaiting_response,
            "correct_count": self.correct_count,
            "total_answered": self.total_answered,
            "complete": self.complete,
            "updated_at": datetime.now(),
            "difficulty_bias": self.difficulty_bias,
            "start_theta": float(self.start_theta),
        }
        if created:
            doc["created_at"] = datetime.now()
            self.sessions.insert_one(doc)
        else:
            self.sessions.update_one({"sprint_token": self.sprint_token}, {"$set": doc}, upsert=True)

    def _get_topic_items(self) -> List[Dict[str, Any]]:
        """
        Retrieves and caches all items for the current topic from the item bank.
        """
        if self._topic_items_cache is not None:
            return self._topic_items_cache
        cursor = self.item_bank_collection.find({"topic": self.topic})
        items = []
        for doc in cursor:
            try:
                items.append({
                    "question_id": str(doc.get("question_id")),
                    "a_discrimination": float(doc.get("a_discrimination", 1.0)),
                    "b_difficulty": float(doc.get("b_difficulty", 0.0)),
                    "questionType": doc.get("questionType", "Unknown"),
                    "topic": doc.get("topic", self.topic),
                    "section": doc.get("section", "Unknown"),
                    "subject": doc.get("subject", doc.get("section", "Unknown")),
                    "questionTitle": doc.get("questionTitle", ""),
                    "options": doc.get("options", {}),
                    "correctOption": doc.get("correctOption", ""),
                    "correctAnswer": doc.get("correctAnswer", doc.get("correctOption", "")),
                    "questionImages": doc.get("questionImages", []),
                    "explanation": doc.get("explanation", ""),
                })
            except Exception:
                continue
        self._topic_items_cache = items
        return items

    def _calculate_item_information(self, theta: float, a_param: float, b_param: float) -> float:
        """
        Calculates the Fisher information of an item for a given theta.
        """
        p = 1.0 / (1.0 + np.exp(-a_param * (theta - b_param)))
        return float((a_param ** 2) * p * (1.0 - p))

    def _select_next_item(self) -> Optional[Dict[str, Any]]:
        """
        Selects the next item for the sprint based on the current theta and difficulty bias.
        """
        items = self._get_topic_items()
        if not items:
            return None

        # Filter out already administered questions
        remaining = [it for it in items if it["question_id"] not in set(self.administered_question_ids)]
        if not remaining:
            return None

        # Seed the random number generators for variability
        seed_value = hash(self.sprint_token + str(time.time())) % 10000
        random.seed(seed_value)
        np.random.seed(seed_value)

        # Determine the difficulty bias shift
        bias_shift = 0.0
        if self.difficulty_bias == 'easy':
            bias_shift = -0.5
        elif self.difficulty_bias == 'hard':
            bias_shift = 0.5
        target_theta = self.current_theta + bias_shift

        # Score items based on information and difficulty match
        scored: List[tuple[float, Dict[str, Any]]] = []
        for it in remaining:
            info = self._calculate_item_information(target_theta, it["a_discrimination"], it["b_difficulty"])
            match = 1.0 / (1.0 + abs(it["b_difficulty"] - target_theta))
            score = 0.7 * info + 0.3 * match
            scored.append((score, it))

        # Sort items by score and pick from the top-k to avoid local maxima
        scored.sort(key=lambda x: x[0], reverse=True)
        top_k = scored[: min(5, len(scored))]
        return random.choice(top_k)[1] if top_k else None

    def _plan_next_k_questions(self, k: int) -> List[Dict[str, Any]]:
        """
        Generates a plan of the next k questions without mutating the sprint state.
        This is used to provide the client with a preview of the upcoming questions.
        """
        items = self._get_topic_items()
        if not items:
            return []

        planned: List[Dict[str, Any]] = []
        used_ids = set(self.administered_question_ids)

        # Determine the difficulty bias shift for planning
        bias_shift = 0.0
        if self.difficulty_bias == 'easy':
            bias_shift = -0.5
        elif self.difficulty_bias == 'hard':
            bias_shift = 0.5
        target_theta = self.current_theta + bias_shift

        for _ in range(max(0, k)):
            pool = [it for it in items if it["question_id"] not in used_ids]
            if not pool:
                break

            # Score and select the next question for the plan
            scored: List[tuple[float, Dict[str, Any]]] = []
            for it in pool:
                info = self._calculate_item_information(target_theta, it["a_discrimination"], it["b_difficulty"])
                match = 1.0 / (1.0 + abs(it["b_difficulty"] - target_theta))
                score = 0.7 * info + 0.3 * match
                scored.append((score, it))
            scored.sort(key=lambda x: x[0], reverse=True)
            if not scored:
                break
            candidate = scored[0][1]
            used_ids.add(candidate["question_id"])
            planned.append({
                "question_id": candidate["question_id"],
                "a_discrimination": candidate["a_discrimination"],
                "b_difficulty": candidate["b_difficulty"],
                "theta_snapshot": round(self.current_theta, 3),
                "question_details": candidate,
            })
        return planned

    def _update_theta(self, old_theta: float, correct: bool, a_param: float, b_param: float) -> float:
        """
        Updates the student's ability estimate (theta) based on their response.
        """
        base_adjustment = 0.3 * a_param / 2.0
        if correct:
            if old_theta < b_param:
                adjustment = base_adjustment * (1 + (b_param - old_theta) * 0.5)
            else:
                adjustment = base_adjustment * 0.7
        else:
            if old_theta > b_param:
                adjustment = -base_adjustment * (1 + (old_theta - b_param) * 0.5)
            else:
                adjustment = -base_adjustment * 0.7
        return float(np.clip(old_theta + adjustment, self.config.min_theta, self.config.max_theta))

    def _get_initial_theta_from_summary(self) -> float:
        """
        Maps the mastery percentage for the topic to an initial theta using a logit mapping.
        If no mastery data is available, it returns 0.0.
        """
        try:
            # Find the latest student summary for this student
            coll = self._db["studentSummary"]
            summary = coll.find_one({"student_id": self.student_id}, sort=[("analysis_date", -1), ("created_at", -1), ("updated_at", -1)])
            if not summary:
                return 0.0

            # Get the mastery percentage for the topic
            topic_mastery = (summary.get("individual_mastery") or {}).get("topic_mastery") or {}
            entry = topic_mastery.get(self.topic)
            if not entry:
                return 0.0
            percent = entry.get("mastery_percentage")
            if percent is None:
                return 0.0

            # Convert the percentage to a probability and apply logit transformation
            p = max(0.01, min(0.99, float(percent) / 100.0))
            theta = math.log(p / (1.0 - p))
            return float(np.clip(theta, self.config.min_theta, self.config.max_theta))
        except Exception:
            return 0.0

    def get_next_question(self) -> Dict[str, Any]:
        """
        Gets the next question for the sprint.
        """
        if self.complete:
            return {"session_complete": True, "message": "Sprint already complete"}
        if self.awaiting_response:
            return {"error": True, "message": "Awaiting response for the current question"}

        # Select the next item
        item = self._select_next_item()
        if not item:
            self.complete = True
            self._persist_state()
            return {"session_complete": True, "message": "No more questions available for this topic"}

        # Update the sprint state
        self.current_question_id = item["question_id"]
        self.awaiting_response = True
        self._persist_state()

        # Prepare a plan of the next questions for client visibility
        remaining_after_this = max(0, self.num_questions - self.total_answered)
        planned = self._plan_next_k_questions(remaining_after_this)
        if planned and planned[0]["question_id"] != item["question_id"]:
            planned = [{
                "question_id": item["question_id"],
                "a_discrimination": item["a_discrimination"],
                "b_difficulty": item["b_difficulty"],
                "theta_snapshot": round(self.current_theta, 3),
                "question_details": item,
            }] + [p for p in planned if p["question_id"] != item["question_id"]]

        return {
            "session_complete": False,
            "sprint_token": self.sprint_token,
            "question_id": item["question_id"],
            "question_details": item,
            "current_theta": round(self.current_theta, 3),
            "message": "Question presented successfully",
            "question_number": self.total_answered + 1,
            "remaining": max(0, self.num_questions - self.total_answered),
            "planned_questions": planned,
        }

    def submit_response(self, question_id: str, user_response: bool, question_number: int, selected_option: Optional[str] = None) -> Dict[str, Any]:
        """
        Submits a response to a question in the sprint.
        """
        if self.complete:
            return {"error": True, "message": "Sprint already complete"}
        if not self.awaiting_response:
            return {"error": True, "message": "Not awaiting a response. Please get the next question first."}
        if self.current_question_id != question_id:
            return {"error": True, "message": f"Expected response for {self.current_question_id}, got {question_id}"}

        # Load item details from the database
        item_doc = self.db.get_item_by_question_id(question_id)
        if not item_doc:
            return {"error": True, "message": "Question not found"}

        # Update the student's theta based on their response
        old_theta = self.current_theta
        new_theta = self._update_theta(old_theta, bool(user_response), float(item_doc.get("a_discrimination", 1.0)), float(item_doc.get("b_difficulty", 0.0)))
        theta_change = new_theta - old_theta
        self.current_theta = new_theta

        # Save the response to the database
        self.responses.insert_one({
            "sprint_token": self.sprint_token,
            "student_id": self.student_id,
            "question_number": int(question_number),
            "question_id": str(question_id),
            "user_response": bool(user_response),
            "response_value": int(1 if user_response else 0),
            "selected_option": selected_option,
            "topic": self.topic,
            "item_difficulty": float(item_doc.get("b_difficulty", 0.0)),
            "item_discrimination": float(item_doc.get("a_discrimination", 1.0)),
            "theta_before": float(old_theta),
            "theta_after": float(new_theta),
            "theta_change": float(theta_change),
            "timestamp": datetime.now(),
        })

        # Update the in-memory and session state
        if bool(user_response):
            self.correct_count += 1
        self.total_answered += 1
        self.administered_question_ids.append(question_id)
        self.current_question_id = None
        self.awaiting_response = False
        if self.total_answered >= self.num_questions:
            self.complete = True
        self._persist_state()

        # Finalize the sprint if it is complete
        if self.complete:
            try:
                self._finalize_sprint()
            except Exception:
                pass

        return {
            "success": True,
            "message": "Response recorded",
            "question_id": question_id,
            "question_number": question_number,
            "is_correct": bool(user_response),
            "old_theta": round(old_theta, 3),
            "new_theta": round(new_theta, 3),
            "theta_change": round(theta_change, 3),
            "sprint_complete": self.complete,
            "can_get_next_question": not self.complete,
            "answered": self.total_answered,
            "remaining": max(0, self.num_questions - self.total_answered),
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Gets the current status of the sprint.
        """
        accuracy = (self.correct_count / self.total_answered) if self.total_answered > 0 else 0.0
        status = {
            "sprint_token": self.sprint_token,
            "student_id": self.student_id,
            "topic": self.topic,
            "num_questions": self.num_questions,
            "answered": self.total_answered,
            "correct": self.correct_count,
            "accuracy": round(accuracy, 3),
            "current_theta": round(self.current_theta, 3),
            "awaiting_response": self.awaiting_response,
            "complete": self.complete,
            "administered_question_ids": self.administered_question_ids,
            "next_sprint_plan": None if not self.complete else self._recommend_next_sprint(accuracy),
        }
        if self.complete:
            status["final_summary"] = self._assemble_summary(accuracy)
        return status

    def _recommend_next_sprint(self, accuracy: float) -> Dict[str, Any]:
        """
        Recommends the next sprint based on the student's performance.
        """
        # A simple heuristic to adjust the starting theta and difficulty emphasis based on accuracy
        if accuracy >= 0.85:
            next_start_theta = min(self.current_theta + 0.3, self.config.max_theta)
            mix = [{"difficulty": "Hard", "count": self.num_questions}]
            note = "Strong performance; increase difficulty for mastery consolidation."
        elif accuracy >= 0.6:
            next_start_theta = self.current_theta
            mix = [
                {"difficulty": "Medium", "count": max(1, self.num_questions - 2)},
                {"difficulty": "Hard", "count": 2},
            ]
            note = "Moderate performance; maintain level with some stretch questions."
        else:
            next_start_theta = max(self.current_theta - 0.3, self.config.min_theta)
            mix = [
                {"difficulty": "Easy", "count": max(1, self.num_questions // 2)},
                {"difficulty": "Medium", "count": self.num_questions - max(1, self.num_questions // 2)},
            ]
            note = "Low performance; focus on fundamentals before progressing."
        return {
            "recommended_start_theta": round(next_start_theta, 3),
            "recommended_mix": mix,
            "note": note,
        }

    def _difficulty_bucket(self, b: float) -> str:
        """
        Categorizes a question's difficulty into a bucket (Easy, Medium, Hard).
        """
        if b <= -0.5:
            return 'Easy'
        if b >= 0.5:
            return 'Hard'
        return 'Medium'

    def _assemble_summary(self, accuracy: float) -> Dict[str, Any]:
        """
        Assembles a summary of the sprint's performance.
        """
        # Aggregate the difficulties of the questions in the sprint
        agg = {"Easy": 0, "Medium": 0, "Hard": 0}
        for r in self.responses.find({"sprint_token": self.sprint_token}):
            bucket = self._difficulty_bucket(float(r.get("item_difficulty", 0.0)))
            agg[bucket] = agg.get(bucket, 0) + 1
        return {
            "start_theta": round(self.start_theta, 3),
            "end_theta": round(self.current_theta, 3),
            "accuracy": round(accuracy, 3),
            "difficulty_counts": agg,
            "difficulty_bias": self.difficulty_bias,
        }

    def _finalize_sprint(self) -> None:
        """
        Finalizes the sprint by saving a summary of the run to the database.
        """
        accuracy = (self.correct_count / self.total_answered) if self.total_answered > 0 else 0.0
        summary = self._assemble_summary(accuracy)
        next_plan = self._recommend_next_sprint(accuracy)
        runs = self._db["sprint_runs"]
        doc = {
            "sprint_token": self.sprint_token,
            "student_id": self.student_id,
            "topic": self.topic,
            "num_questions": self.num_questions,
            "answered": self.total_answered,
            "correct": self.correct_count,
            "accuracy": summary["accuracy"],
            "start_theta": summary["start_theta"],
            "end_theta": summary["end_theta"],
            "difficulty_counts": summary["difficulty_counts"],
            "difficulty_bias": self.difficulty_bias,
            "next_sprint_plan": next_plan,
            "created_at": datetime.now(),
            "completed_at": datetime.now(),
        }
        runs.update_one({"sprint_token": self.sprint_token}, {"$set": doc}, upsert=True)


