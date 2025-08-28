# diagnostic_test_folder/irt_helper.py

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
    Calculates Item Response Theory (IRT) parameters (discrimination 'a' and difficulty 'b')
    from a CSV file of student responses. The results are then stored in a MongoDB
    collection, merging them with existing question data from a question bank.

    Args:
        csv_file_path (str): The path to the CSV file containing response data.
        mongo_uri (str): The MongoDB connection URI.
        db_name (str): The name of the database.
        question_bank_collection (str, optional): The name of the collection containing question metadata.
            Defaults to "question_bank".
        item_bank_collection (str, optional): The name of the collection where the IRT parameters
            will be stored. Defaults to "item_bank".

    Returns:
        pd.DataFrame: A DataFrame containing the calculated IRT parameters and merged question data.
    """
    try:
        # Establish a connection to the MongoDB database
        client = MongoClient(mongo_uri)
        db = client[db_name]

        # Load the response data from the CSV file
        df = pd.read_csv(csv_file_path)
        
        if df.shape[1] < 2:
            raise ValueError("CSV must have at least one question column after question_id.")

        # Extract question IDs and the response matrix
        question_ids = df.iloc[:, 0].tolist()
        response_matrix = df.iloc[:, 1:].to_numpy(dtype=float)

        # Estimate IRT parameters using a 2PL model, with fallbacks
        try:
            # Attempt to use the 2-Parameter Logistic (2PL) model
            discrimination, difficulty = twopl_mml(response_matrix)
            print("✅ Used 2PL model for parameter estimation")
        except Exception as e:
            print(f"⚠️ 2PL failed ({e}), trying Rasch model...")
            try:
                # Fall back to the Rasch (1PL) model if 2PL fails
                from girth import rasch_mml
                difficulty = rasch_mml(response_matrix)
                discrimination = np.ones(len(question_ids))
                print("✅ Used Rasch model for parameter estimation")
            except Exception as e2:
                print(f"⚠️ Rasch failed ({e2}), using fallback correlation method...")
                # Fall back to a point-biserial correlation method if Rasch also fails
                discrimination, difficulty = [], []
                
                for j in range(len(question_ids)):
                    # Calculate total score for each student, excluding the current question
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
                    
                    # Calculate difficulty from the proportion of correct answers
                    prop_correct = np.nanmean(question_scores)
                    prop_correct = max(0.01, min(0.99, prop_correct))
                    b_param = -np.log(prop_correct / (1 - prop_correct))
                    
                    discrimination.append(a_param)
                    difficulty.append(b_param)
                
                discrimination = np.array(discrimination)
                difficulty = np.array(difficulty)
                print("✅ Used fallback correlation method for parameter estimation")

        # Ensure that the lengths of all lists match
        min_len = min(len(question_ids), len(discrimination), len(difficulty))
        question_ids = question_ids[:min_len]
        discrimination = discrimination[:min_len]
        difficulty = difficulty[:min_len]

        # Fetch all data from the question bank for the relevant questions
        question_bank_data = {}
        question_docs = db[question_bank_collection].find(
            {"question_id": {"$in": question_ids}},
            {"_id": 0}
        )
        
        for doc in question_docs:
            question_bank_data[doc["question_id"]] = doc

        # Prepare the results to be inserted into the item_bank collection
        run_id = datetime.utcnow().isoformat()
        timestamp = datetime.utcnow()
        results = []
        
        for i in range(min_len):
            qid = question_ids[i]
            question_data = question_bank_data.get(qid, {})
            
            # Create the final document with IRT parameters and all question bank data
            item_document = {
                "run_id": run_id,
                "timestamp": timestamp,
                "question_id": qid,
                "a_discrimination": round(float(discrimination[i]), 3),
                "b_difficulty": round(float(difficulty[i]), 3),
                **question_data
            }
            
            results.append(item_document)

        # Store the results in the item_bank collection, clearing any existing data
        item_collection = db[item_bank_collection]
        item_collection.delete_many({})
        item_collection.insert_many(results)

        print(f"✅ Successfully stored {len(results)} items in '{item_bank_collection}' collection")
        print(f"   Each item contains: question_id, a_discrimination, b_difficulty + ALL question_bank fields")
        
        # Print a summary of the fields stored
        if results:
            sample_keys = list(results[0].keys())
            print(f"   Total fields per item: {len(sample_keys)}")
            print(f"   Fields: {', '.join(sample_keys[:10])}{'...' if len(sample_keys) > 10 else ''}")

        # Close the MongoDB connection
        client.close()

        return pd.DataFrame(results)

    except Exception as e:
        print(f"❌ Error: {e}")
        if 'client' in locals():
            client.close()
        raise

