This file will contain the documentation for all the APIs in the project.

## Batched Sprint Flow

The batched sprint is designed for focused practice on a specific skill. The flow is as follows:

1.  **Get Questions:** Start a new sprint by getting a batch of questions for a skill.
2.  **Submit Answers:** Submit the student's answers for the batch.
3.  **Get Next Batch:** The server returns the next batch of questions. Repeat until the sprint is complete.
4.  **Complete Session:** End the sprint session.

---

### 1. Get Batched Questions for a Skill

*   **Endpoint:** `GET /sprint/batched/skills/{skill_code}/questions`
*   **Request:**
    *   `skill_code` (string, path parameter)
    *   `student_id` (string, query parameter)
    *   `mastery_level` (integer, optional query parameter, 2-9)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "sprint_token": "sprint-a1b2c3d4",
      "questions": [
        {"question_id": "SKL-001", "topic": "Skill 1", "difficulty": "Easy"},
        {"question_id": "SKL-002", "topic": "Skill 1", "difficulty": "Easy"}
      ],
      "message": "Questions retrieved successfully."
    }
    ```

---

### 2. Submit Answers and Get Next Batch

*   **Endpoint:** `POST /sprint/batched/sessions/{sprint_token}/submit`
*   **Request Body:**
    *   `answers` (list of objects):
        *   `question_id` (string)
        *   `is_correct` (boolean)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "next_batch": [
        {"question_id": "SKL-003", "topic": "Skill 1", "difficulty": "Medium"}
      ],
      "performance_summary": {"correct": 1, "total": 2, "accuracy": 50.0}
    }
    ```

---

### 3. Get Session Status

*   **Endpoint:** `GET /sprint/batched/sessions/{sprint_token}/status`
*   **Request:**
    *   `sprint_token` (string, path parameter)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "status": "in-progress",
      "questions_answered": 2,
      "current_mastery": 0.6
    }
    ```

---

### 4. Complete Session

*   **Endpoint:** `POST /sprint/batched/sessions/{sprint_token}/complete`
*   **Request:**
    *   `sprint_token` (string, path parameter)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "message": "Session completed successfully."
    }
    ```

---

### 5. Get Student Skill Mastery

*   **Endpoint:** `GET /sprint/batched/students/{student_id}/skills/{skill_code}/mastery`
*   **Request:**
    *   `student_id` (string, path parameter)
    *   `skill_code` (string, path parameter)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "skill_code": "MA01",
      "mastery_level": 5,
      "mastery_percentage": 55
    }
    ```

## Diagnostic Test Flow

The diagnostic test is a sequence of API calls designed to assess a student's ability level. The typical flow is as follows:

1.  **Start Session:** Begin a new test session.
2.  **Get Question:** Retrieve the first adaptive question.
3.  **Submit Response:** Submit the student's answer.
4.  **Get Next Question:** Repeat getting questions and submitting responses until the test is complete.
5.  **End Session:** Finalize the test and get a comprehensive analysis.

---

### 1. Start a New Diagnostic Test Session

*   **Endpoint:** `POST /diagnostic/start-session`
*   **Request Body:**
    *   `student_id` (string, optional): The ID of the student. If not provided, a new one is generated.
*   **Sample Response:**
    ```json
    {
      "session_token": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "student_id": "student_20231027_103000",
      "message": "new profile",
      "item_bank_info": {
        "total_items": 150,
        "question_types": ["MCQ", "FillInTheBlank"],
        "sections": ["Algebra", "Geometry"]
      },
      "diagnostic_test_info": {
        "total_questions_answered": 0,
        "current_theta": 0.0,
        "mastery_by_topic": {}
      }
    }
    ```

---

### 2. Get the Next Question

*   **Endpoint:** `POST /diagnostic/get-question`
*   **Request Body:**
    *   `session_token` (string): The token for the current session.
    *   `questionType` (string, optional): Filter for the type of question.
*   **Sample Response (Question):**
    ```json
    {
      "session_complete": false,
      "question_number": 1,
      "question_id": "ALG-001",
      "difficulty": 0.5,
      "questionType": "MCQ",
      "topic": "Linear Equations",
      "options": {"A": "x = 1", "B": "x = 2"},
      "current_theta": 0.1
    }
    ```
*   **Sample Response (Session Complete):**
    ```json
    {
      "session_complete": true,
      "message": "Diagnostic test completed.",
      "final_status": {
        "total_questions_answered": 20,
        "final_theta": 1.2,
        "mastery_by_topic": {
          "Algebra": 0.8,
          "Geometry": 0.6
        }
      }
    }
    ```

---

### 3. Submit a Response

*   **Endpoint:** `POST /diagnostic/submit-response`
*   **Request Body:**
    *   `session_token` (string)
    *   `question_id` (string)
    *   `user_response` (boolean)
    *   `question_number` (integer)
    *   `selected_option` (string, optional)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "message": "Response recorded",
      "is_correct": true,
      "new_theta": 0.25,
      "theta_change": 0.15
    }
    ```

---

### 4. Get Session Status

*   **Endpoint:** `GET /diagnostic/session-status/{session_token}`
*   **Request:**
    *   `session_token` (string, path parameter)
*   **Sample Response:**
    ```json
    {
      "session_token": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "student_id": "student_20231027_103000",
      "status": "in-progress",
      "questions_answered": 5,
      "current_theta": 0.3
    }
    ```

---

### 5. End a Session

*   **Endpoint:** `POST /diagnostic/end-session/{session_token}`
*   **Request:**
    *   `session_token` (string, path parameter)
*   **Sample Response:**
    ```json
    {
      "session_end": {
        "success": true,
        "message": "Session ended."
      },
      "comprehensive_analysis": {
        "student_id": "student_20231027_103000",
        "final_theta": 1.2,
        "mastery_by_topic": {
          "Algebra": {"mastery": 0.8, "questions_answered": 10},
          "Geometry": {"mastery": 0.6, "questions_answered": 10}
        }
      },
      "message": "Session ended successfully and comprehensive analysis saved."
    }
    ```

## Full-Length Test Flow

A full-length test simulates a complete exam and involves the following steps:

1.  **Create Test:** Generate a new full-length test.
2.  **Retrieve Test:** Fetch the test sections, usually one by one.
3.  **Grade Test:** Submit all answers for grading and receive a comprehensive analysis.

---

### 1. Create a New Full-Length Test

*   **Endpoint:** `POST /full-length-test/create`
*   **Request Body:**
    *   `student_id` (string)
    *   `day` (integer, optional)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "test_id": "fl-test-a1b2c3d4",
      "sections": [
        {"section": "Math", "question_ids": ["M01", "M02"], "fetched_count": 2},
        {"section": "Reading", "question_ids": ["R01", "R02"], "fetched_count": 2}
      ],
      "order": ["Math", "Reading"]
    }
    ```

---

### 2. Retrieve a Full-Length Test

*   **Endpoint:** `GET /full-length-test`
*   **Request:**
    *   `student_id` (string, query parameter)
    *   `test_id` (string, optional query parameter)
    *   `page` (integer, optional query parameter, default: 1)
    *   `page_size` (integer, optional query parameter, default: 1)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "total_sections": 2,
      "sections": [{"section": "Math", "questions": [...]}]
    }
    ```

---

### 3. Grade a Full-Length Test

*   **Endpoint:** `POST /full-length-test/grade`
*   **Request Body:**
    *   `test_id` (string)
    *   `answers` (list of strings)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "test_id": "fl-test-a1b2c3d4",
      "graded_count": 50,
      "per_topic": {
        "Algebra": {"correct": 8, "total": 10, "mastery_percentage": 80.0},
        "Geometry": {"correct": 6, "total": 10, "mastery_percentage": 60.0}
      },
      "study_plan_regenerated": true
    }
    ```

## Section Test Flow

Section tests are designed for targeted practice on a specific section of the study plan. The flow is as follows:

1.  **Create Tests:** Generate section tests for a specific day.
2.  **Grade Test:** Submit answers for a single section test to be graded.

---

### 1. Create New Section Tests for a Day

*   **Endpoint:** `POST /section-test`
*   **Request Body:**
    *   `student_id` (string)
    *   `day` (integer)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "day": 1,
      "tests": [
        {"test_id": "sec-test-a1b2", "section": "Algebra", "fetched_count": 5},
        {"test_id": "sec-test-c3d4", "section": "Geometry", "fetched_count": 5}
      ],
      "group_id": "group-xyz"
    }
    ```

---

### 2. Grade a Section Test

*   **Endpoint:** `POST /section-test/grade`
*   **Request Body:**
    *   `test_id` (string)
    *   `answers` (list of strings)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "test_id": "sec-test-a1b2",
      "graded_count": 5,
      "per_topic": {
        "ALG-1": {"correct": 3, "total": 5, "mastery_percentage": 60.0}
      },
      "study_plan_regenerated": false
    }
    ```

## Sprint Flow

Sprints are adaptive, multi-stage practice sessions. The general flow is:

1.  **Get Study Plan Summary & Day Details:** Understand the student's plan.
2.  **Get Adaptive Topic Test:** Start a test for a specific day.
3.  **Grade Answers & Get Next Questions:** Loop through grading and getting new questions.
4.  **Health Check:** Optionally, check if the service is running.

---

### 1. Get Study Plan Summary

*   **Endpoint:** `GET /sprint/study-plan/{student_id}`
*   **Request:**
    *   `student_id` (string, path parameter)
*   **Sample Response:**
    ```json
    {
      "student_id": "student123",
      "total_days": 15,
      "available_days": [1, 2, 3, 4, 5]
    }
    ```

---

### 2. Get Day Details

*   **Endpoint:** `GET /sprint/day-details/{student_id}/{day}`
*   **Request:**
    *   `student_id` (string, path parameter)
    *   `day` (integer, path parameter)
*   **Sample Response:**
    ```json
    {
      "student_id": "student123",
      "day": 1,
      "daily_plan": {"topics": [...], "tests": []},
      "topic_test_allowed": true
    }
    ```

---

### 3. Get Adaptive Topic Test

*   **Endpoint:** `POST /sprint/adaptive-topic-test/{student_id}/{day}`
*   **Request:**
    *   `student_id` (string, path parameter)
    *   `day` (integer, path parameter)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "day": 1,
      "sprint_token": "sprint-xyz",
      "questions": [{"question_id": "Q01"}, {"question_id": "Q02"}]
    }
    ```

---

### 4. Grade Answers

*   **Endpoint:** `POST /sprint/grade-answers/{sprint_token}`
*   **Request Body:**
    *   `answers` (list of objects):
        *   `question_id` (string)
        *   `is_correct` (boolean)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "sprint_token": "sprint-xyz",
      "performance": 80.0,
      "total_questions": 10,
      "correct_questions": 8
    }
    ```

---

### 5. Get Next Questions

*   **Endpoint:** `POST /sprint/next-questions/{sprint_token}`
*   **Request Body:**
    *   `previous_answers` (list of objects)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "sprint_token": "sprint-xyz",
      "questions": [{"question_id": "Q03"}, {"question_id": "Q04"}]
    }
    ```

---

### 6. Get Questions by Skill

*   **Endpoint:** `GET /sprint/skill-questions/{student_id}`
*   **Request:**
    *   `student_id` (string, path parameter)
    *   `topic_code` (string, query parameter)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "topic_code": "ALG-1",
      "questions": [...]
    }
    ```

---

### 7. Health Check

*   **Endpoint:** `GET /sprint/health`
*   **Request:** None
*   **Sample Response:**
    ```json
    {
      "status": "ok",
      "service": "sprint"
    }
    ```

## Student and Study Plan Flow

This set of APIs manages the student's overall study plan and daily activities. The flow includes:

1.  **Create Study Plan:** Generate a new, personalized study plan.
2.  **Get Study Plan:** Retrieve the plan, either by week or by a specific day.
3.  **Get Topic/Section Test:** Get the tests assigned for a particular day.

---

### 1. Create a Study Plan

*   **Endpoint:** `POST /student/study-plan/create`
*   **Request Body:**
    *   `student_id` (string)
    *   `total_days` (integer)
    *   `daily_time_minutes` (integer)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "plan_id": "plan-abc",
      "daily_plans": [...]
    }
    ```

---

### 2. Get a Student's Study Plan

*   **Endpoint:** `GET /student/study-plan`
*   **Request:**
    *   `student_id` (string, query parameter)
    *   `week` (integer, optional query parameter)
    *   `day` (integer, optional query parameter)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "mode": "week",
      "current_week": 1,
      "daily_plans": [...]
    }
    ```

---

### 3. Get a Topic Test for a Day

*   **Endpoint:** `POST /student/topic-test`
*   **Request Body:**
    *   `student_id` (string)
    *   `day` (integer)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "day": 1,
      "sections": [{"topic": "Algebra", "questions": [...]}]
    }
    ```

---

### 4. Get a Section Test for a Day

*   **Endpoint:** `POST /student/section-test`
*   **Request Body:**
    *   `student_id` (string)
    *   `day` (integer)
*   **Sample Response:**
    ```json
    {
      "success": true,
      "student_id": "student123",
      "day": 1,
      "tests": [{"test_id": "sec-test-a1b2", "section": "Algebra"}]
    }
    ```
