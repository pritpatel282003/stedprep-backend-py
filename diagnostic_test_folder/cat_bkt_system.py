import numpy as np
import pandas as pd
import random
import time
from datetime import datetime
from typing import Optional, List
from pymongo import MongoClient
import os
from bson import ObjectId

class DiagnosticTestManager:
    """
    Manages the creation, retrieval, and updating of diagnostic test documents in the database.
    """
    def __init__(self, db_manager, student_id: str, session_token: str):
        """
        Initializes the DiagnosticTestManager.

        Args:
            db_manager: The database manager instance.
            student_id (str): The ID of the student.
            session_token (str): The token for the current session.
        """
        self.db = db_manager
        self.student_id = student_id
        self.session_token = session_token
        self.diagnostic_collection = self.db.db.diagnostic_test
        
        # Create indexes for faster queries
        self.diagnostic_collection.create_index("calibrateStudentId")
        self.diagnostic_collection.create_index("student_id")
        
    def create_or_get_diagnostic_test(self, test_type: str = "CALIBRATE", total_questions: int = 55, total_duration: int = 60):
        """
        Creates a new diagnostic test or retrieves an existing one for the student.
        """
        # Check if a diagnostic test already exists for this student
        existing_test = self.diagnostic_collection.find_one({
            "student_id": self.student_id,
            "session_token": self.session_token,
            "testType": test_type,
            "isCompleted": False
        })
        
        if existing_test:
            return existing_test
        
        # Create a new diagnostic test structure
        diagnostic_test = {
            "_id": ObjectId(),
            "calibrateStudentId": ObjectId(self.student_id) if ObjectId.is_valid(self.student_id) else ObjectId(),
            "student_id": self.student_id,
            "session_token": self.session_token,
            "testType": test_type,
            "totalQuestions": total_questions,
            "totalDurationMinutes": total_duration,
            "sections": [
                {"sectionName": "Verbal Reasoning", "durationMinutes": 15, "startTime": None, "endTime": None, "isActive": False, "isCompleted": False, "questions": []},
                {"sectionName": "Quantitative Reasoning", "durationMinutes": 20, "startTime": None, "endTime": None, "isActive": False, "isCompleted": False, "questions": []},
                {"sectionName": "Reading Comprehension", "durationMinutes": 15, "startTime": None, "endTime": None, "isActive": False, "isCompleted": False, "questions": []},
                {"sectionName": "Mathematics Achievement", "durationMinutes": 10, "startTime": None, "endTime": None, "isActive": False, "isCompleted": False, "questions": []}
            ],
            "startTime": None,
            "endTime": None,
            "isCompleted": False,
            "isActive": True,
            "tabSwitch": 0,
            "copyPaste": 0,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
            "__v": 0
        }
        
        # Insert the new diagnostic test into the database
        result = self.diagnostic_collection.insert_one(diagnostic_test)
        diagnostic_test['_id'] = result.inserted_id
        
        print(f"✅ Created new diagnostic test for student: {self.student_id}")
        return diagnostic_test
    
    def add_question_to_diagnostic_test(self, question_data: dict, response_data: dict, section_name: str, saved_response_id: str = None):
        """
        Adds an answered question to the appropriate section in the diagnostic test document.
        """
        try:
            # Get the diagnostic test document
            diagnostic_test = self.create_or_get_diagnostic_test()
            now_ts = datetime.now()
            
            # Ensure the global test start time is set
            if diagnostic_test.get('startTime') is None:
                diagnostic_test['startTime'] = now_ts
                diagnostic_test['isActive'] = True
            
            # Create the question object to be added
            question_obj = {
                "_id": ObjectId(),
                "questionId": ObjectId(question_data['question_id']) if ObjectId.is_valid(question_data['question_id']) else ObjectId(),
                "question_id": str(question_data['question_id']),
                "correctAnswer": question_data.get('correctAnswer', question_data.get('correctOption', 'Unknown')),
                "isCorrect": response_data.get('user_response', False),
                "difficultyLevel": question_data.get('difficultyLevel', 'Lower'),
                "questionType": str(question_data.get('questionType', 'Unknown')),
                "topic": str(question_data.get('topic', 'Unknown')),
                "skillCode": str(question_data.get('skillCode', 'Unknown')),
                "answeredAt": now_ts,
                "crossedOptions": response_data.get('crossedOptions', []),
                "savedResponseId": str(saved_response_id) if saved_response_id else None
            }
            
            # Find the matching section and add the question
            section_updated = False
            for section in diagnostic_test['sections']:
                if section['sectionName'] == section_name:
                    section['questions'].append(question_obj)
                    
                    # Update section start time and status
                    if section.get('startTime') is None:
                        section['startTime'] = now_ts
                        section['isActive'] = True
                    
                    section_updated = True
                    print(f"✅ Added question {question_data['question_id']} to section: {section_name}")
                    break
            
            # If the section is not found, create a new one
            if not section_updated:
                print(f"⚠️ Section '{section_name}' not found, creating new section")
                new_section = {
                    "sectionName": section_name,
                    "durationMinutes": 15,
                    "startTime": now_ts,
                    "endTime": None,
                    "isActive": True,
                    "isCompleted": False,
                    "questions": [question_obj]
                }
                diagnostic_test['sections'].append(new_section)
            
            # Update the diagnostic test in the database
            self.diagnostic_collection.update_one(
                {"_id": diagnostic_test['_id']},
                {
                    "$set": {
                        "sections": diagnostic_test['sections'],
                        "startTime": diagnostic_test.get('startTime'),
                        "isActive": True,
                        "updatedAt": now_ts
                    }
                }
            )
            
            return {
                "success": True,
                "diagnostic_test_id": str(diagnostic_test['_id']),
                "section_added": section_name,
                "question_id": question_data['question_id']
            }
            
        except Exception as e:
            print(f"❌ Error adding question to diagnostic test: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_diagnostic_test_status(self):
        """
        Gets the current status of the diagnostic test.
        """
        try:
            diagnostic_test = self.diagnostic_collection.find_one({
                "student_id": self.student_id,
                "session_token": self.session_token,
                "isCompleted": False
            })
            
            if not diagnostic_test:
                return {"exists": False, "message": "No active diagnostic test found"}
            
            # Calculate statistics for the test
            total_answered = 0
            section_stats = []
            
            for section in diagnostic_test['sections']:
                answered_in_section = len(section['questions'])
                total_answered += answered_in_section
                
                section_stats.append({
                    "sectionName": section['sectionName'],
                    "questions_answered": answered_in_section,
                    "isActive": section.get('isActive', False),
                    "isCompleted": section.get('isCompleted', False),
                    "startTime": section.get('startTime'),
                    "endTime": section.get('endTime')
                })
            
            return {
                "exists": True,
                "diagnostic_test_id": str(diagnostic_test['_id']),
                "testType": diagnostic_test['testType'],
                "totalQuestions": diagnostic_test['totalQuestions'],
                "totalAnswered": total_answered,
                "isCompleted": diagnostic_test['isCompleted'],
                "sections": section_stats,
                "createdAt": diagnostic_test['createdAt'],
                "updatedAt": diagnostic_test['updatedAt']
            }
            
        except Exception as e:
            return {"exists": False, "error": str(e)}

    def end_diagnostic_test(self):
        """
        Marks the diagnostic test as completed and sets the end time.
        """
        try:
            diagnostic_test = self.diagnostic_collection.find_one({
                "student_id": self.student_id,
                "isCompleted": False
            })

            if not diagnostic_test:
                return {"success": False, "message": "No active diagnostic test found"}

            now_ts = datetime.now()
            update_doc = {
                "isActive": False,
                "isCompleted": True,
                "endTime": now_ts,
                "updatedAt": now_ts
            }

            if not diagnostic_test.get('startTime'):
                update_doc['startTime'] = now_ts

            self.diagnostic_collection.update_one(
                {"_id": diagnostic_test['_id']},
                {"$set": update_doc}
            )

            return {"success": True, "diagnostic_test_id": str(diagnostic_test['_id'])}
        except Exception as e:
            return {"success": False, "error": str(e)}

class EnhancedMongoDBManager:
    """
    Manages all interactions with the MongoDB database.
    """
    def __init__(self, connection_string: str = None, database_name: str = "cat_assessment"):
        """
        Initializes the EnhancedMongoDBManager.

        Args:
            connection_string (str, optional): The MongoDB connection string. Defaults to None.
            database_name (str, optional): The name of the database. Defaults to "cat_assessment".
        """
        self.connection_string = connection_string or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.database_name = database_name
        self.client = MongoClient(self.connection_string)
        self.db = self.client[self.database_name]
        
        # Initialize collections
        self.sessions_collection = self.db.sessions
        self.responses_collection = self.db.responses
        self.question_logs_collection = self.db.question_logs
        self.item_bank_collection = self.db.item_bank
        self.assessment_reports_collection = self.db.assessment_reports
        
        # Create indexes for better query performance
        self._create_indexes()
    
    def _create_indexes(self):
        """
        Creates database indexes for better performance on frequently queried fields.
        """
        self.sessions_collection.create_index("session_token", unique=True)
        self.sessions_collection.create_index("student_id")
        self.sessions_collection.create_index("created_at")
        self.responses_collection.create_index("session_token")
        self.responses_collection.create_index("question_id")
        self.question_logs_collection.create_index("session_token")
        self.item_bank_collection.create_index("question_id")
        self.assessment_reports_collection.create_index("student_id")
        self.assessment_reports_collection.create_index("session_token")
    
    def create_session(self, session_data: dict) -> str:
        """
        Creates a new session in the database.
        """
        result = self.sessions_collection.insert_one(session_data)
        return str(result.inserted_id)
    
    def get_session(self, session_token: str) -> Optional[dict]:
        """
        Retrieves session data from the database.
        """
        return self.sessions_collection.find_one({"session_token": session_token})
    
    def update_session(self, session_token: str, update_data: dict):
        """
        Updates session data in the database.
        """
        self.sessions_collection.update_one(
            {"session_token": session_token},
            {"$set": update_data}
        )
    
    def save_detailed_response(self, response_data: dict):
        """
        Saves a detailed student response to the database.
        """
        # Format the response to match the MongoDB document structure
        formatted_response = {
            'session_token': response_data['session_token'],
            'student_id': response_data['student_id'],
            'question_number': int(response_data['question_number']),
            'questionId': response_data['question_id'],
            'question_id': response_data['question_id'],
            'questionType': response_data.get('questionType', 'Unknown'),
            'topic': response_data.get('topic', 'Unknown'),
            'skillCode': response_data.get('skillCode', 'Unknown'),
            'skillDescription': response_data.get('skillDescription', ''),
            'section': response_data.get('section', 'Unknown'),
            'subject': response_data.get('subject', response_data.get('section', 'Unknown')),
            'difficultyLevel': response_data.get('difficultyLevel', 'Unknown'),
            'iseeLevel': response_data.get('iseeLevel', 'Unknown'),
            'part': response_data.get('part', 1),
            'comprehensiveId': response_data.get('comprehensiveId', None),
            'selectedOption': response_data.get('selectedOption', None),
            'correctOption': response_data.get('correctOption', response_data.get('correctAnswer', None)),
            'correctAnswer': response_data.get('correctAnswer', None),
            'user_response': bool(response_data['user_response']),
            'answered': True,
            'isCorrect': bool(response_data['user_response']),
            'isFlaged': False,
            'isWatched': True,
            'response_value': int(1 if response_data['user_response'] else 0),
            'difficulty': float(response_data.get('difficulty', 0.0)),
            'discrimination': float(response_data.get('discrimination', 1.0)),
            'crossedOptions': response_data.get('crossedOptions', []),
            'timestamp': datetime.now(),
            'answeredAt': datetime.now(),
            '_id': ObjectId()
        }
        
        # Save the formatted response to the responses collection
        result = self.responses_collection.insert_one(formatted_response)
        print(f"✅ Saved detailed response for question {response_data['question_id']}")
        return formatted_response
    
    def save_question_log(self, log_data: dict):
        """
        Saves a question log to the database.
        """
        self.question_logs_collection.insert_one(log_data)
    
    def get_student_responses(self, session_token: str) -> List[dict]:
        """
        Gets all responses for a given session.
        """
        return list(self.responses_collection.find({"session_token": session_token}).sort("question_number", 1))
    
    def get_item_bank_as_dataframe(self) -> pd.DataFrame:
        """
        Retrieves the item bank from MongoDB and returns it as a pandas DataFrame.
        """
        try:
            # Get all items from the item_bank collection
            cursor = self.item_bank_collection.find({}, {"_id": 0})
            items = []
            
            # Clean the documents to make them JSON serializable
            for doc in cursor:
                clean_doc = {}
                for key, value in doc.items():
                    if isinstance(value, ObjectId):
                        clean_doc[key] = str(value)
                    elif isinstance(value, dict):
                        clean_doc[key] = {k: str(v) if isinstance(v, ObjectId) else v for k, v in value.items()}
                    elif isinstance(value, list):
                        clean_doc[key] = [str(item) if isinstance(item, ObjectId) else item for item in value]
                    else:
                        clean_doc[key] = value
                items.append(clean_doc)
            
            if not items:
                raise Exception("Item bank is empty. Please load items first using IRT parameter generation.")
            
            # Convert the list of items to a DataFrame
            df = pd.DataFrame(items)
            
            # Ensure question_id exists and set it as the index
            if 'question_id' not in df.columns:
                raise Exception("question_id column not found in item_bank")
            
            df.set_index('question_id', inplace=True, drop=False)
            
            # Ensure required columns exist
            required_cols = ['a_discrimination', 'b_difficulty']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise Exception(f"Missing required columns in item_bank: {missing_cols}")
            
            # Ensure numeric columns have the correct data type
            df['a_discrimination'] = pd.to_numeric(df['a_discrimination'], errors='coerce')
            df['b_difficulty'] = pd.to_numeric(df['b_difficulty'], errors='coerce')
            
            # Check for any NaN values in critical columns
            if df['a_discrimination'].isna().any() or df['b_difficulty'].isna().any():
                raise Exception("Invalid numeric values found in a_discrimination or b_difficulty columns")
            
            return df
            
        except Exception as e:
            raise Exception(f"Failed to load item bank from MongoDB: {str(e)}")
    
    def get_item_by_question_id(self, question_id: str) -> Optional[dict]:
        """
        Gets a specific item from the item bank by its question_id.
        """
        try:
            doc = self.item_bank_collection.find_one({"question_id": question_id}, {"_id": 0})
            if not doc:
                return None
            
            # Clean the document to make it JSON serializable
            clean_doc = {}
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    clean_doc[key] = str(value)
                elif isinstance(value, dict):
                    clean_doc[key] = {k: str(v) if isinstance(v, ObjectId) else v for k, v in value.items()}
                elif isinstance(value, list):
                    clean_doc[key] = [str(item) if isinstance(item, ObjectId) else item for item in value]
                else:
                    clean_doc[key] = value
            
            return clean_doc
        except Exception as e:
            print(f"Error getting item {question_id}: {str(e)}")
            return None
    
    def get_available_question_ids(self) -> List[str]:
        """
        Gets a list of all available question IDs from the item bank.
        """
        try:
            cursor = self.item_bank_collection.find({}, {"question_id": 1, "_id": 0})
            return [str(doc['question_id']) for doc in cursor if 'question_id' in doc]
        except Exception as e:
            print(f"Error getting question IDs: {str(e)}")
            return []
    
    def close_connection(self):
        """
        Closes the MongoDB connection.
        """
        self.client.close()

class BKTTracker:
    """
    Implements the Bayesian Knowledge Tracing (BKT) model to track a student's mastery of a skill.
    """
    def __init__(self, prior_knowledge=0.0, learn_rate=0.08, guess_rate=0.2, slip_rate=0.1):
        self.prior_knowledge = prior_knowledge
        self.learn_rate = learn_rate
        self.guess_rate = guess_rate
        self.slip_rate = slip_rate
        self.prob_known = prior_knowledge
        self.mastery_history = [prior_knowledge]
        self.correct_streak = 0

    def update_mastery(self, response_correct):
        """
        Updates the student's mastery probability based on their response to a question.
        """
        if response_correct:
            # Update mastery based on a correct response
            self.correct_streak += 1
            numerator = self.prob_known * (1 - self.slip_rate)
            denominator = (self.prob_known * (1 - self.slip_rate) + (1 - self.prob_known) * self.guess_rate)
            prob_known_given_correct = numerator / denominator if denominator > 0 else self.prob_known

            # Apply a learning boost for a streak of correct answers
            if self.correct_streak >= 3:
                learning_boost = min(0.05, self.learn_rate * 0.5)
            else:
                learning_boost = 0

            self.prob_known = prob_known_given_correct + (1 - prob_known_given_correct) * (self.learn_rate + learning_boost)
        else:
            # Update mastery based on an incorrect response
            self.correct_streak = 0
            numerator = self.prob_known * self.slip_rate
            denominator = (self.prob_known * self.slip_rate + (1 - self.prob_known) * (1 - self.guess_rate))
            prob_known_given_correct = numerator / denominator if denominator > 0 else self.prob_known

            decay_rate = self.learn_rate * 0.3
            self.prob_known = prob_known_given_correct + (1 - prob_known_given_correct) * decay_rate

        # Ensure the probability is a native Python float and clipped between 0.01 and 0.99
        self.prob_known = float(np.clip(self.prob_known, 0.01, 0.99))
        self.mastery_history.append(self.prob_known)

    def is_mastered(self, threshold=0.8):
        """
        Checks if the student has mastered the skill.
        """
        return bool(self.prob_known >= threshold)

    def is_highly_mastered(self, threshold=0.95):
        """
        Checks if the student has a high level of mastery of the skill.
        """
        return bool(self.prob_known >= threshold)

    def get_mastery_level(self):
        """
        Gets the student's mastery level as a percentage.
        """
        return self.prob_known * 100
    
    def to_dict(self):
        """
        Converts the BKT state to a dictionary for storage in MongoDB.
        """
        return {
            'prior_knowledge': float(self.prior_knowledge),
            'learn_rate': float(self.learn_rate),
            'guess_rate': float(self.guess_rate),
            'slip_rate': float(self.slip_rate),
            'prob_known': float(self.prob_known),
            'mastery_history': [float(x) for x in self.mastery_history],
            'correct_streak': int(self.correct_streak)
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Creates a BKT instance from a dictionary.
        """
        bkt = cls(
            prior_knowledge=data['prior_knowledge'],
            learn_rate=data['learn_rate'],
            guess_rate=data['guess_rate'],
            slip_rate=data['slip_rate']
        )
        bkt.prob_known = data['prob_known']
        bkt.mastery_history = data['mastery_history']
        bkt.correct_streak = data['correct_streak']
        return bkt

class CustomAdaptiveSelector:
    """
    Selects the next question for the student based on their estimated ability (theta).
    """
    def __init__(self):
        self.selection_history = []

    def select_next_item(self, item_bank_df, administered_question_ids, current_theta, question_number, session_token="", question_type_filter=None):
        """
        Selects the next question from the item bank based on the student's ability,
        the questions they have already answered, and any question type filters.
        """
        # Filter out already administered questions
        available_items = item_bank_df[~item_bank_df.index.isin(administered_question_ids)].copy()

        # Apply question type filter if provided
        if question_type_filter:
            if 'questionType' in available_items.columns:
                available_items = available_items[available_items['questionType'] == question_type_filter]
                if len(available_items) == 0:
                    print(f"No available items found for questionType: {question_type_filter}")
                    return None
            else:
                print("questionType column not found in item_bank")
                return None

        if len(available_items) == 0:
            return None

        # Use session token and current time for randomness
        seed_value = hash(session_token + str(time.time())) % 10000
        random.seed(seed_value)
        np.random.seed(seed_value)

        # Set the target difficulty for the next question
        if question_number == 1:
            target_difficulty = 0.0 + np.random.uniform(-0.5, 0.5)
        else:
            target_difficulty = current_theta

        # Calculate item information for each available item
        available_items['target_info'] = available_items.apply(
            lambda row: self._calculate_item_information(
                current_theta, row['a_discrimination'], row['b_difficulty']
            ), axis=1
        )

        # Calculate difficulty match score
        available_items['difficulty_match'] = 1 / (1 + abs(available_items['b_difficulty'] - target_difficulty))

        # Calculate final selection score
        available_items['selection_score'] = (
            0.6 * available_items['target_info'] +
            0.3 * available_items['difficulty_match'] +
            0.1 * np.random.uniform(0, 1, len(available_items))
        )

        # Select from the top candidates
        top_candidates = available_items.nlargest(min(5, len(available_items)), 'selection_score')
        weights = np.exp(top_candidates['selection_score'] * 2)
        weights = weights / weights.sum()

        selected_question_id = np.random.choice(top_candidates.index, p=weights)
        selected_item = available_items.loc[selected_question_id]

        # Log the selection history
        self.selection_history.append({
            'question_number': question_number,
            'selected_question_id': str(selected_question_id),
            'question_type_filter': str(question_type_filter) if question_type_filter else None,
            'target_difficulty': float(target_difficulty),
            'selected_difficulty': float(selected_item['b_difficulty']),
            'selected_discrimination': float(selected_item['a_discrimination']),
            'information_value': float(selected_item['target_info']),
            'difficulty_match': float(selected_item['difficulty_match']),
            'final_score': float(selected_item['selection_score']),
            'session_token': session_token,
            'available_items_count': len(available_items)
        })

        return str(selected_question_id)

    def _calculate_item_information(self, theta, a, b):
        """
        Calculates the Fisher information of an item.
        """
        p = 1 / (1 + np.exp(-a * (theta - b)))
        info = a**2 * p * (1 - p)
        return info

class EnhancedInteractiveCATSystem:
    """
    The main class that orchestrates the diagnostic test. It uses the other classes
    to manage the test flow, update the student's theta and mastery, and save data to the database.
    """
    def __init__(self, session_token: str, student_id: str, db_manager: EnhancedMongoDBManager):
        self.session_token = session_token
        self.student_id = student_id
        self.db = db_manager
        
        # Initialize the diagnostic test manager
        self.diagnostic_manager = DiagnosticTestManager(db_manager, student_id, session_token)
        
        # Define a mapping from different section names to a canonical name
        self.section_mapping = {
            "Verbal Reasoning": "Verbal Reasoning",
            "Quantitative Reasoning": "Quantitative Reasoning", 
            "Reading Comprehension": "Reading Comprehension",
            "Mathematics Achievement": "Mathematics Achievement",
            "Math": "Mathematics Achievement",
            "Reading": "Reading Comprehension",
            "Verbal": "Verbal Reasoning",
            "Quantitative": "Quantitative Reasoning"
        }
        
        # Initialize or load the session state
        session_data = self.db.get_session(session_token)
        
        if session_data:
            # Load the existing session
            self.section_theta = session_data.get('section_theta', {})
            self.section_bkt = {}
            self.section_histories = session_data.get('section_histories', {})
            self.administered_question_ids = session_data['administered_question_ids']
            self.current_question_id = session_data.get('current_question_id', None)
            self.awaiting_response = session_data.get('awaiting_response', False)
            
            # Load BKT trackers for each section
            section_bkt_data = session_data.get('section_bkt', {})
            for section, bkt_data in section_bkt_data.items():
                self.section_bkt[section] = BKTTracker.from_dict(bkt_data)
            
            # Initialize the selector and load the selection history
            self.selector = CustomAdaptiveSelector()
            self.selector.selection_history = session_data.get('selection_history', [])
            
            print(f"📊 Loaded existing session with section-based tracking: {len(self.administered_question_ids)} questions completed")
            print(f"📈 Section thetas: {self.section_theta}")
        else:
            # Create a new session
            self.selector = CustomAdaptiveSelector()
            self.section_theta = {}
            self.section_bkt = {}
            self.section_histories = {}
            self.administered_question_ids = []
            self.current_question_id = None
            self.awaiting_response = False
            
            # Initialize all sections with starting values
            for section_name in self.section_mapping.values():
                self.section_theta[section_name] = 0.0
                self.section_bkt[section_name] = BKTTracker(prior_knowledge=0.0, learn_rate=0.08, guess_rate=0.2, slip_rate=0.1)
                self.section_histories[section_name] = [0.0]
            
            # Save the initial session state
            self._save_session_state()
            print(f"🆕 Created new session with section-based tracking for student: {student_id}")
        
        # Load the item bank from MongoDB
        try:
            self.item_bank_df = self.db.get_item_bank_as_dataframe()
            print(f"✅ Loaded {len(self.item_bank_df)} items from item_bank collection")
        except Exception as e:
            raise Exception(f"Failed to load item bank from MongoDB: {str(e)}")

    def _get_question_section(self, question_data: dict) -> str:
        """
        Determines the canonical section for a question from multiple possible fields.
        """
        def canonicalize(value: str) -> str:
            key = value.strip().lower()
            synonyms = {
                'verbal': 'Verbal Reasoning',
                'verbal reasoning': 'Verbal Reasoning',
                'quant': 'Quantitative Reasoning',
                'quantitative': 'Quantitative Reasoning',
                'quantitative reasoning': 'Quantitative Reasoning',
                'reading': 'Reading Comprehension',
                'reading comprehension': 'Reading Comprehension',
                'math': 'Mathematics Achievement',
                'mathematics': 'Mathematics Achievement',
                'mathematics achievement': 'Mathematics Achievement'
            }
            return synonyms.get(key, None)

        candidates = [
            question_data.get('section'),
            question_data.get('subject'),
            question_data.get('questionType'),
            question_data.get('topic')
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                # Try exact mapping first
                mapped = self.section_mapping.get(candidate, None)
                if mapped:
                    return mapped
                # Try canonicalized synonyms
                canon = canonicalize(candidate)
                if canon:
                    return canon
        return 'Unknown'

    def _save_session_state(self):
        """
        Saves the current session state to MongoDB.
        """
        # Convert section BKT trackers to dictionaries for storage
        section_bkt_data = {}
        for section, bkt_tracker in self.section_bkt.items():
            section_bkt_data[section] = bkt_tracker.to_dict()
        
        session_data = {
            'session_token': self.session_token,
            'student_id': self.student_id,
            'section_theta': {k: float(v) for k, v in self.section_theta.items()},
            'section_bkt': section_bkt_data,
            'section_histories': {k: [float(x) for x in v] for k, v in self.section_histories.items()},
            'administered_question_ids': [str(x) for x in self.administered_question_ids],
            'current_question_id': self.current_question_id,
            'awaiting_response': self.awaiting_response,
            'selection_history': self.selector.selection_history,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'status': 'active'
        }
        
        existing_session = self.db.get_session(self.session_token)
        if existing_session:
            session_data['created_at'] = existing_session['created_at']
            session_data['updated_at'] = datetime.now()
            self.db.update_session(self.session_token, session_data)
        else:
            self.db.create_session(session_data)

    def get_next_question(self, question_type_filter=None):
        """
        Gets the next question for the test, managing section-based theta.
        """
        
        # If we are currently waiting for a response, do not allow a new question
        if self.awaiting_response and self.current_question_id:
            current_item = self.db.get_item_by_question_id(self.current_question_id)
            return {
                'error': True,
                'message': f'You must answer the current question (ID: {self.current_question_id}) before getting the next question',
                'current_question_details': {
                    'question_id': self.current_question_id,
                    'question_number': len(self.administered_question_ids) + 1,
                    'awaiting_response': True,
                    'question_data': current_item
                }
            }
        
        # Check if the assessment is complete
        if self.is_assessment_complete():
            return {
                'error': False,
                'session_complete': True,
                'message': 'Assessment completed',
                'final_status': self.get_current_status()
            }

        # Generate a new question only if not awaiting a response
        question_number = len(self.administered_question_ids) + 1
        
        # Determine the current theta for section-based selection
        current_theta = 0.0
        
        if question_type_filter:
            section_for_filter = self.section_mapping.get(question_type_filter, question_type_filter)
            if section_for_filter in self.section_theta:
                current_theta = self.section_theta[section_for_filter]
                print(f"🎯 Using theta {current_theta:.3f} for section: {section_for_filter}")
        
        selected_question_id = self.selector.select_next_item(
            self.item_bank_df, 
            self.administered_question_ids, 
            current_theta, 
            question_number, 
            self.session_token,
            question_type_filter
        )

        if selected_question_id is None:
            message = f"No more questions available for questionType: {question_type_filter}" if question_type_filter else "No more questions available"
            return {
                'error': False,
                'session_complete': True,
                'message': message,
                'final_status': self.get_current_status()
            }

        # Get the question details from the item bank
        item_data = self.db.get_item_by_question_id(selected_question_id)
        if not item_data:
            return {
                'error': True,
                'message': f'Question data not found for ID: {selected_question_id}'
            }

        # Determine the section for this question
        question_section = self._get_question_section(item_data)
        
        # Get the current theta and mastery for this section
        section_theta = self.section_theta.get(question_section, 0.0)
        section_mastery = self.section_bkt.get(question_section, BKTTracker(prior_knowledge=0.0)).prob_known

        # Set as the current question and mark as awaiting response
        self.current_question_id = selected_question_id
        self.awaiting_response = True
        self._save_session_state()

        print(f"🎯 Question {question_number} presented: {selected_question_id} for section: {question_section}")
        print(f"📈 Section theta: {section_theta:.3f}, Section mastery: {section_mastery:.3f}")

        return {
            'error': False,
            'session_complete': False,
            'question_id': selected_question_id,
            'question_number': question_number,
            'question_details': item_data,
            'current_theta': section_theta,
            'mastery_prob': section_mastery,
            'question_section': question_section,
            'awaiting_response': True,
            'message': f'Question presented successfully for section: {question_section}. Submit your response to continue.'
        }

    def submit_response(self, question_id: str, user_response: bool, question_number: int, selected_option: str = None):
        """
        Submits a student's response with section-based theta and BKT tracking.
        """
        
        # Validate that this is the expected question
        if not self.awaiting_response:
            raise Exception(f"Not currently awaiting a response. Please get a new question first.")
        
        if self.current_question_id != question_id:
            raise Exception(f"Expected response for question {self.current_question_id}, but received for {question_id}")
        
        # Get item details from the item bank
        item_data = self.db.get_item_by_question_id(question_id)
        if not item_data:
            raise Exception(f"Question {question_id} not found in item_bank")

        # Determine the section for this question
        question_section = self._get_question_section(item_data)
        
        # Initialize the section if it doesn't exist
        if question_section not in self.section_theta:
            self.section_theta[question_section] = 0.0
            self.section_bkt[question_section] = BKTTracker(prior_knowledge=0.0, learn_rate=0.08, guess_rate=0.2, slip_rate=0.1)
            self.section_histories[question_section] = [0.0]

        # Get the current section-specific values
        old_section_theta = self.section_theta[question_section]
        old_section_mastery = self.section_bkt[question_section].prob_known

        # Update the section-specific BKT
        self.section_bkt[question_section].update_mastery(user_response)

        # Update the section-specific Theta
        new_section_theta = self._update_theta_custom(
            old_section_theta, user_response,
            item_data['a_discrimination'],
            item_data['b_difficulty']
        )
        
        # Update the section theta and history
        self.section_theta[question_section] = new_section_theta
        self.section_histories[question_section].append(new_section_theta)
        
        theta_change = new_section_theta - old_section_theta

        # Prepare detailed response data
        response_data = {
            'session_token': self.session_token,
            'student_id': self.student_id,
            'question_number': int(question_number),
            'question_id': str(question_id),
            'user_response': bool(user_response),
            'selectedOption': str(selected_option) if selected_option else None,
            'correctAnswer': str(item_data.get('correctOption', item_data.get('correctAnswer', 'Unknown'))),
            'difficulty': float(item_data['b_difficulty']),
            'discrimination': float(item_data['a_discrimination']),
            'questionType': str(item_data.get('questionType', 'Unknown')),
            'topic': str(item_data.get('topic', 'Unknown')),
            'skillCode': str(item_data.get('skillCode', 'Unknown')),
            'skillDescription': str(item_data.get('skillDescription', '')),
            'section': str(item_data.get('section', 'Unknown')),
            'subject': str(item_data.get('subject', item_data.get('section', 'Unknown'))),
            'difficultyLevel': str(item_data.get('difficultyLevel', 'Unknown')),
            'iseeLevel': str(item_data.get('iseeLevel', 'Unknown')),
            'part': item_data.get('part', 1),
            'comprehensiveId': item_data.get('comprehensiveId', None),
            'crossedOptions': []
        }

        # Save the detailed response to the database
        saved_response = self.db.save_detailed_response(response_data)

        # Add the question to the diagnostic test document
        saved_response_id = str(saved_response.get('_id')) if saved_response and '_id' in saved_response else None
        diagnostic_result = self.diagnostic_manager.add_question_to_diagnostic_test(
            item_data, response_data, question_section, saved_response_id=saved_response_id
        )

        # Add to administered questions and clear the current question state
        self.administered_question_ids.append(question_id)
        self.current_question_id = None
        self.awaiting_response = False

        # Save a comprehensive question log for analytics
        question_log = {
            'session_token': self.session_token,
            'student_id': self.student_id,
            'question_number': int(question_number),
            'question_id': str(question_id),
            'item_difficulty': float(item_data['b_difficulty']),
            'item_discrimination': float(item_data['a_discrimination']),
            'questionType': str(item_data.get('questionType', 'Unknown')),
            'topic': str(item_data.get('topic', 'Unknown')),
            'skillCode': str(item_data.get('skillCode', 'Unknown')),
            'section': str(item_data.get('section', 'Unknown')),
            'question_section': question_section,
            'user_response': bool(user_response),
            'response_value': int(1 if user_response else 0),
            'theta_before': float(old_section_theta),
            'theta_after': float(new_section_theta),
            'theta_change': float(theta_change),
            'bkt_mastery_before': float(old_section_mastery),
            'bkt_mastery_after': float(self.section_bkt[question_section].prob_known),
            'bkt_correct_streak': int(self.section_bkt[question_section].correct_streak),
            'timestamp': datetime.now()
        }
        
        # Add all additional item_bank fields safely
        excluded_keys = [
            'question_id', 'a_discrimination', 'b_difficulty', 'questionType', 'section', 'topic', 'skillCode'
        ]
        
        for key, value in item_data.items():
            if key not in excluded_keys:
                if isinstance(value, ObjectId):
                    question_log[key] = str(value)
                elif isinstance(value, (dict, list)):
                    try:
                        question_log[key] = str(value)
                    except:
                        question_log[key] = "complex_object"
                elif isinstance(value, (int, float, str, bool)):
                    question_log[key] = value
                else:
                    question_log[key] = str(value)
        
        self.db.save_question_log(question_log)

        # Update the session state
        self._save_session_state()

        print(f"✅ Response recorded for question {question_id} in section {question_section}: {'Correct' if user_response else 'Incorrect'}")
        print(f"📈 Section {question_section} - Theta: {old_section_theta:.3f} → {new_section_theta:.3f} (Δ{theta_change:+.3f})")
        print(f"🎯 Section {question_section} - Mastery: {old_section_mastery:.3f} → {self.section_bkt[question_section].prob_known:.3f}")

        return {
            'success': True,
            'message': f'Response recorded successfully for section: {question_section}',
            'question_id': question_id,
            'question_number': question_number,
            'question_section': question_section,
            'user_response': user_response,
            'is_correct': user_response,
            'theta_change': round(theta_change, 3),
            'old_theta': round(old_section_theta, 3),
            'new_theta': round(new_section_theta, 3),
            'old_mastery': round(old_section_mastery, 3),
            'new_mastery': round(self.section_bkt[question_section].prob_known, 3),
            'correct_streak': self.section_bkt[question_section].correct_streak,
            'is_assessment_complete': self.is_assessment_complete(),
            'awaiting_response': False,
            'can_get_next_question': True,
            'saved_response_id': saved_response_id,
            'diagnostic_test_update': diagnostic_result,
            'section_theta_status': {k: round(v, 3) for k, v in self.section_theta.items()},
            'section_mastery_status': {k: round(v.prob_known, 3) for k, v in self.section_bkt.items()}
        }

    def _update_theta_custom(self, old_theta, correct_response, a_param, b_param):
        """
        Custom theta update logic.
        """
        expected_prob = 1 / (1 + np.exp(-a_param * (old_theta - b_param)))
        base_adjustment = 0.3 * a_param / 2.0

        if correct_response:
            if old_theta < b_param:
                adjustment = base_adjustment * (1 + (b_param - old_theta) * 0.5)
            else:
                adjustment = base_adjustment * 0.7
        else:
            if old_theta > b_param:
                adjustment = -base_adjustment * (1 + (old_theta - b_param) * 0.5)
            else:
                adjustment = -base_adjustment * 0.7

        new_theta = np.clip(old_theta + adjustment, -4.0, 4.0)
        return new_theta

    def get_current_status(self):
        """
        Gets the current status of the assessment, including section-based data and diagnostic test status.
        """
        responses = self.db.get_student_responses(self.session_token)
        total_questions = len(responses)
        correct_responses = sum(1 for r in responses if r['response_value'] == 1)
        accuracy = correct_responses / total_questions if total_questions > 0 else 0

        # Get the diagnostic test status
        diagnostic_status = self.diagnostic_manager.get_diagnostic_test_status()

        # Calculate section-wise statistics
        section_stats = {}
        for section_name in self.section_theta.keys():
            section_responses = [r for r in responses if self._get_question_section({'section': r.get('section', 'Unknown')}) == section_name]
            section_correct = sum(1 for r in section_responses if r['response_value'] == 1)
            section_total = len(section_responses)
            
            section_stats[section_name] = {
                'theta': round(self.section_theta[section_name], 3),
                'mastery': round(self.section_bkt[section_name].prob_known, 3),
                'questions_answered': section_total,
                'correct_responses': section_correct,
                'accuracy_rate': round(section_correct / section_total, 3) if section_total > 0 else 0,
                'correct_streak': self.section_bkt[section_name].correct_streak,
                'is_mastered': self.section_bkt[section_name].is_mastered(),
                'theta_history': [round(x, 3) for x in self.section_histories[section_name]]
            }

        return {
            'session_token': self.session_token,
            'student_id': self.student_id,
            'total_questions_answered': total_questions,
            'correct_responses': correct_responses,
            'overall_accuracy_rate': round(accuracy, 3),
            'section_statistics': section_stats,
            'available_questions': len(self.item_bank_df) - len(self.administered_question_ids),
            'administered_question_ids': self.administered_question_ids,
            'current_question_id': self.current_question_id,
            'awaiting_response': self.awaiting_response,
            'can_get_next_question': not self.awaiting_response,
            'diagnostic_test_status': diagnostic_status
        }

    def is_assessment_complete(self):
        """
        Checks if the assessment is complete based on section-wise mastery or question limits.
        """
        # Check if any section is highly mastered or if the overall question limit is reached
        any_section_mastered = any(bkt.is_mastered() for bkt in self.section_bkt.values())
        question_limit_reached = len(self.administered_question_ids) >= 50
        no_more_questions = len(self.administered_question_ids) >= len(self.item_bank_df)
        
        return any_section_mastered or question_limit_reached or no_more_questions

    def get_diagnostic_test_summary(self):
        """
        Gets a summary of the current diagnostic test.
        """
        return self.diagnostic_manager.get_diagnostic_test_status()

    def force_next_question_if_stuck(self):
        """
        An emergency function to reset the state if the system is stuck awaiting a response.
        """
        if self.awaiting_response:
            print(f"⚠️ Force resetting awaiting response state for question: {self.current_question_id}")
            self.current_question_id = None
            self.awaiting_response = False
            self._save_session_state()
            return True
        return False

    def end_session(self):
        """
        Ends the assessment session and marks the diagnostic test as complete.
        """
        diag_result = self.diagnostic_manager.end_diagnostic_test()
        self.current_question_id = None
        self.awaiting_response = False
        self._save_session_state()
        
        # Mark the session document as completed
        self.db.update_session(self.session_token, {
            'status': 'completed',
            'updated_at': datetime.now()
        })
        
        return {
            'success': bool(diag_result.get('success', False)),
            'message': 'Session ended successfully' if diag_result.get('success', False) else diag_result.get('message', 'Failed to end session'),
            'diagnostic_test_update': diag_result,
            'final_status': self.get_current_status()
        }

    def get_section_summary(self):
        """
        Gets a detailed summary of all sections.
        """
        summary = {}
        for section_name in self.section_theta.keys():
            summary[section_name] = {
                'current_theta': round(self.section_theta[section_name], 3),
                'current_mastery': round(self.section_bkt[section_name].prob_known, 3),
                'mastery_percentage': round(self.section_bkt[section_name].get_mastery_level(), 1),
                'is_mastered': self.section_bkt[section_name].is_mastered(),
                'correct_streak': self.section_bkt[section_name].correct_streak,
                'theta_history': [round(x, 3) for x in self.section_histories[section_name]],
                'mastery_history': [round(x, 3) for x in self.section_bkt[section_name].mastery_history]
            }
        return summary