import pandas as pd
import numpy as np
from datetime import datetime
from pymongo import MongoClient
from girth import twopl_mml

def generate_irt_parameters_for_item_bank(
    csv_file_path: str,
    mongo_uri: str,
    db_name: str,
    question_bank_collection: str = "question_bank",
    item_bank_collection: str = "item_bank"
) -> pd.DataFrame:
    """
    Calculate IRT a and b parameters from CSV response data and store in item_bank 
    with question_id and questionType from question_bank collection.
    """

    try:
        # --- MongoDB connection ---
        client = MongoClient(mongo_uri)
        db = client[db_name]

        # --- Load CSV data ---
        df = pd.read_csv(csv_file_path)
        
        if df.shape[1] < 2:
            raise ValueError("CSV must have at least one question column after question_id.")

        # Get question IDs from first column and response data from remaining columns
        question_ids = df.iloc[:, 0].tolist()  # q1, q2, q3, etc.
        
        # Response matrix: questions × students (transpose of CSV structure)
        response_matrix = df.iloc[:, 1:].to_numpy(dtype=float)

        # --- IRT Parameter Estimation ---
        try:
            # Try 2PL model first
            discrimination, difficulty = twopl_mml(response_matrix)
            print("✅ Used 2PL model for parameter estimation")
        except Exception as e:
            print(f"⚠️ 2PL failed ({e}), trying Rasch model...")
            try:
                # Fall back to Rasch (1PL) model
                from girth import rasch_mml
                difficulty = rasch_mml(response_matrix)
                discrimination = np.ones(len(question_ids))  # All discrimination = 1.0
                print("✅ Used Rasch model for parameter estimation")
            except Exception as e2:
                print(f"⚠️ Rasch failed ({e2}), using fallback correlation method...")
                # --- Fallback: Point-biserial correlation method ---
                discrimination, difficulty = [], []
                
                for j in range(len(question_ids)):
                    # Calculate total score for each student (excluding current question)
                    other_questions = np.delete(response_matrix, j, axis=0)
                    total_scores = np.nansum(other_questions, axis=0)
                    
                    question_scores = response_matrix[j, :]
                    
                    # Remove NaN values
                    valid_idx = ~(np.isnan(question_scores) | np.isnan(total_scores))
                    
                    if np.sum(valid_idx) > 1:
                        q_clean = question_scores[valid_idx]
                        t_clean = total_scores[valid_idx]
                        
                        # Calculate point-biserial correlation
                        if np.std(q_clean) > 0 and np.std(t_clean) > 0:
                            corr = np.corrcoef(q_clean, t_clean)[0, 1]
                        else:
                            corr = 0.5
                    else:
                        corr = 0.5
                    
                    # Convert correlation to discrimination parameter
                    a_param = max(0.1, abs(corr) * 2)
                    
                    # Calculate difficulty from proportion correct
                    prop_correct = np.nanmean(question_scores)
                    prop_correct = max(0.01, min(0.99, prop_correct))  # Bound between 0.01 and 0.99
                    b_param = -np.log(prop_correct / (1 - prop_correct))  # Logit transformation
                    
                    discrimination.append(a_param)
                    difficulty.append(b_param)
                
                discrimination = np.array(discrimination)
                difficulty = np.array(difficulty)
                print("✅ Used fallback correlation method for parameter estimation")

        # --- Ensure matching lengths ---
        min_len = min(len(question_ids), len(discrimination), len(difficulty))
        question_ids = question_ids[:min_len]
        discrimination = discrimination[:min_len]
        difficulty = difficulty[:min_len]

        # --- Fetch ALL data from question_bank ---
        question_bank_data = {}
        question_docs = db[question_bank_collection].find(
            {"question_id": {"$in": question_ids}},
            {"_id": 0}  # Exclude only MongoDB's _id field, get everything else
        )
        
        for doc in question_docs:
            question_bank_data[doc["question_id"]] = doc

        # --- Prepare results for item_bank ---
        run_id = datetime.utcnow().isoformat()
        timestamp = datetime.utcnow()
        results = []
        
        for i in range(min_len):
            qid = question_ids[i]
            # Get all question bank data for this question_id
            question_data = question_bank_data.get(qid, {})
            
            # Create the final document with IRT parameters + all question bank data
            item_document = {
                "run_id": run_id,
                "timestamp": timestamp,
                "question_id": qid,
                "a_discrimination": round(float(discrimination[i]), 3),
                "b_difficulty": round(float(difficulty[i]), 3),
                **question_data  # Merge ALL fields from question_bank
            }
            
            results.append(item_document)

        # --- Store to item_bank collection ---
        item_collection = db[item_bank_collection]
        
        # Clear existing data and insert new results
        item_collection.delete_many({})
        item_collection.insert_many(results)

        print(f"✅ Successfully stored {len(results)} items in '{item_bank_collection}' collection")
        print(f"   Each item contains: question_id, a_discrimination, b_difficulty + ALL question_bank fields")
        
        # Print summary of fields stored
        if results:
            sample_keys = list(results[0].keys())
            print(f"   Total fields per item: {len(sample_keys)}")
            print(f"   Fields: {', '.join(sample_keys[:10])}{'...' if len(sample_keys) > 10 else ''}")

        # Close MongoDB connection
        client.close()

        return pd.DataFrame(results)

    except Exception as e:
        print(f"❌ Error: {e}")
        if 'client' in locals():
            client.close()
        raise

