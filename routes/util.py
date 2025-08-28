# routes/util.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import os
from diagnostic_test_folder.irt_helper import generate_irt_parameters_for_item_bank
from app_context import get_db

# Create a new router for utility endpoints
router = APIRouter(prefix="/util", tags=["util"])


@router.post("/upload-irt-csv")
async def upload_irt_csv(file: UploadFile = File(...), db=Depends(get_db)):
    """
    Uploads a CSV file with student responses, calculates Item Response Theory (IRT)
    parameters, and stores them in the item_bank collection in the database.

    This is a utility endpoint for populating the item bank for the diagnostic test.
    """
    try:
        # Save the uploaded file temporarily
        responses_path = f"temp_{file.filename}"
        with open(responses_path, "wb") as f:
            f.write(await file.read())

        # Get MongoDB connection details from environment variables or use defaults
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("DATABASE_NAME", "cat_assessment")

        # Generate IRT parameters for the item bank using the uploaded CSV
        generate_irt_parameters_for_item_bank(
            csv_file_path=responses_path,
            mongo_uri=mongo_uri,
            db_name=db_name,
            question_bank_collection="question_bank",
            item_bank_collection="item_bank"
        )

        # Clean up the temporary file
        os.remove(responses_path)

        return {"message": "IRT parameters calculated and stored in item_bank"}
    except Exception as e:
        # Ensure the temporary file is removed even if an error occurs
        if 'responses_path' in locals() and os.path.exists(responses_path):
            os.remove(responses_path)
        raise HTTPException(status_code=500, detail=str(e))


