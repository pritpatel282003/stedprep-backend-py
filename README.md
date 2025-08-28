# STEDPrep API

The STEDPrep API is a FastAPI-based application that provides a comprehensive platform for adaptive learning and assessment. It includes features for diagnostic tests, personalized study plans, and various types of practice tests (topic, section, and full-length).

## Project Overview

The core of the application is an adaptive learning system that uses Item Response Theory (IRT) and Bayesian Knowledge Tracing (BKT) to tailor the learning experience to each student's needs. The system is designed to assess a student's knowledge, identify their strengths and weaknesses, and generate a personalized study plan to help them improve.

### Key Features

- **Diagnostic Test:** A computerized adaptive test (CAT) that accurately assesses a student's ability level (theta) in various subjects.
- **Personalized Study Plans:** The system generates a personalized study plan for each student based on their performance in the diagnostic test. The study plan includes daily tasks, practice tests, and review sessions.
- **Adaptive Sprints:** Short, focused practice sessions on specific topics.
- **Topic, Section, and Full-Length Tests:** Various types of practice tests to help students prepare for their exams.
- **Performance Analysis:** The system provides detailed performance analysis to help students track their progress and identify areas for improvement.

## Project Structure

The project is organized into the following directories:

- **`routes/`:** Contains the FastAPI routers for the different API endpoints.
- **`models/`:** Contains the Pydantic models used for request and response validation.
- **`student_Dashboard/`:** Contains the core logic for the student dashboard features, including study plan generation and practice test creation.
- **`diagnostic_test_folder/`:** Contains the core logic for the diagnostic test system, including the CAT engine and BKT model.

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd STEDPrep-API
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**

    Create a `.env` file in the root directory of the project and add the following environment variables:

    ```
    MONGODB_URI="mongodb://localhost:27017/"
    DATABASE_NAME="cat_assessment"
    ```

4.  **Run the application:**

    ```bash
    uvicorn adaptive_server:app --reload
    ```

    The application will be available at `http://127.0.0.1:8000`.

## API Endpoints

The API documentation is available at `http://127.0.0.1:8000/docs` when the application is running.

Here is a summary of the main API endpoints:

### Diagnostic Test

-   **`POST /diagnostic/start-session`**: Starts a new diagnostic test session.
-   **`POST /diagnostic/get-question`**: Gets the next question in the diagnostic test.
-   **`POST /diagnostic/submit-response`**: Submits a student's response to a question.
-   **`GET /diagnostic/session-status/{session_token}`**: Gets the current status of a diagnostic test session.
-   **`POST /diagnostic/end-session/{session_token}`**: Ends a diagnostic test session and performs a comprehensive analysis.

### Student Dashboard

-   **`POST /student/study-plan/create`**: Creates a new study plan for a student.
-   **`GET /student/study-plan`**: Retrieves a student's study plan.
-   **`POST /student/topic-test`**: Retrieves a topic test for a specific day.
-   **`POST /student/section-test`**: Retrieves a section test for a specific day.

### Full-Length Test

-   **`POST /full-length-test/create`**: Creates a new full-length test.
-   **`GET /full-length-test`**: Retrieves a full-length test.
-   **`POST /full-length-test/grade`**: Grades a full-length test.

### Utility

-   **`POST /util/upload-irt-csv`**: Uploads a CSV file with student responses to calculate IRT parameters.

## Workflow

1.  **Upload IRT Data:** Before starting a diagnostic test, the item bank must be populated with IRT parameters. This can be done by uploading a CSV file with student responses to the `/util/upload-irt-csv` endpoint.

2.  **Start a Diagnostic Test:** A student starts a new diagnostic test session by calling the `/diagnostic/start-session` endpoint.

3.  **Take the Test:** The student gets questions and submits responses using the `/diagnostic/get-question` and `/diagnostic/submit-response` endpoints. The system uses a CAT engine to select the next question based on the student's ability level.

4.  **End the Test:** The student ends the test by calling the `/diagnostic/end-session` endpoint. The system then performs a comprehensive analysis of the student's performance.

5.  **Create a Study Plan:** A study plan is created for the student based on their performance in the diagnostic test by calling the `/student/study-plan/create` endpoint.

6.  **Follow the Study Plan:** The student can retrieve their study plan and take practice tests (topic, section, and full-length) using the corresponding endpoints.

7.  **Track Progress:** The system tracks the student's progress and updates their mastery levels as they complete practice tests. The study plan is regenerated periodically to adapt to the student's progress.
