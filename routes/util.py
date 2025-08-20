from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import os
from diagnostic_test_folder.irt_helper import generate_irt_parameters_for_item_bank
from app_context import get_db

router = APIRouter(prefix="/util", tags=["util"])


@router.post("/upload-irt-csv")
async def upload_irt_csv(file: UploadFile = File(...), db = Depends(get_db)):
    try:
        responses_path = f"temp_{file.filename}"
        with open(responses_path, "wb") as f:
            f.write(await file.read())

        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("DATABASE_NAME", "cat_assessment")

        generate_irt_parameters_for_item_bank(
            csv_file_path=responses_path,
            mongo_uri=mongo_uri,
            db_name=db_name,
            question_bank_collection="question_bank",
            item_bank_collection="item_bank"
        )

        os.remove(responses_path)
        return {"message": "IRT parameters calculated and stored in item_bank"}
    except Exception as e:
        if 'responses_path' in locals() and os.path.exists(responses_path):
            os.remove(responses_path)
        raise HTTPException(status_code=500, detail=str(e))


