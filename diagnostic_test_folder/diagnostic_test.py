import pandas as pd
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from fastapi import HTTPException
from bson import ObjectId

# Define the complete learning flow with prerequisites
PERFECT_LEARNING_FLOW = [
    # TIER 1: FOUNDATIONAL
    {'code': 'MS01', 'name': 'Whole-number operations & order of operations', 'prerequisites': []},
    {'code': 'MS02', 'name': 'Prime factors, GCF & LCM', 'prerequisites': ['MS01']},
    {'code': 'QC03', 'name': 'GCF & LCM Reasoning', 'prerequisites': ['MS01', 'MS02']},
    {'code': 'MS03', 'name': 'Integer operations & absolute value', 'prerequisites': ['MS01']},
    {'code': 'QC01', 'name': 'Signed Integers & Absolute Value', 'prerequisites': ['MS01', 'MS03']},
    
    # TIER 2: NUMBER SYSTEMS
    {'code': 'MS04', 'name': 'Fraction & mixed-number operations', 'prerequisites': ['MS01', 'MS02', 'MS03']},
    {'code': 'QC02', 'name': 'Fractions & Mixed Numbers', 'prerequisites': ['MS01', 'MS04']},
    {'code': 'MS05', 'name': 'Decimal & percent reasoning', 'prerequisites': ['MS01', 'MS04']},
    {'code': 'QC04', 'name': 'Decimals & Percents', 'prerequisites': ['MS01', 'MS04', 'MS05']},
    
    # TIER 3: PROPORTIONAL REASONING
    {'code': 'MS06', 'name': 'Ratios, unit rates, scale drawings & proportions', 'prerequisites': ['MS01', 'MS04', 'MS05']},
    {'code': 'QC05', 'name': 'Ratios & Unit Rates', 'prerequisites': ['MS01', 'MS04', 'MS05', 'MS06']},
    
    # TIER 4: EXPONENTIAL
    {'code': 'MS07', 'name': 'Exponents, squares & square roots', 'prerequisites': ['MS01', 'MS03']},
    {'code': 'QC06', 'name': 'Exponents & Roots', 'prerequisites': ['MS01', 'MS03', 'MS07']},
    {'code': 'QC19', 'name': 'Scientific Notation & Order of Magnitude', 'prerequisites': ['MS01', 'MS05', 'MS07']},
    
    # TIER 5: ALGEBRAIC BASIC
    {'code': 'MS08', 'name': 'Evaluating & simplifying algebraic expressions', 'prerequisites': ['MS01', 'MS03', 'MS07']},
    {'code': 'QC07a', 'name': 'Variable Expressions (Fixed Order)', 'prerequisites': ['MS01', 'MS03', 'MS08']},
    {'code': 'QC07b', 'name': 'Variable Expressions (Indeterminate)', 'prerequisites': ['MS01', 'MS03', 'MS08', 'QC07a']},
    
    # TIER 6: ALGEBRAIC ADVANCED
    {'code': 'MS09', 'name': 'One-variable linear equations & inequalities', 'prerequisites': ['MS01', 'MS03', 'MS08']},
    {'code': 'MS10', 'name': 'Coordinate-plane basics', 'prerequisites': ['MS01', 'MS03']},
    {'code': 'QC13', 'name': 'Coordinate Plane Slope & Distance', 'prerequisites': ['MS01', 'MS03', 'MS10']},
    {'code': 'MS11', 'name': 'Patterns, sequences & basic function rules', 'prerequisites': ['MS01', 'MS08', 'MS09']},
    {'code': 'QC08', 'name': 'Sequences & Patterns', 'prerequisites': ['MS01', 'MS08', 'MS11']},
    
    # TIER 7: GEOMETRIC
    {'code': 'MS12', 'name': 'Angle relationships & polygon properties', 'prerequisites': ['MS01']},
    {'code': 'QC09', 'name': 'Angle & Segment Relations', 'prerequisites': ['MS01', 'MS12']},
    {'code': 'MS13', 'name': 'Perimeter, area & circumference of 2-D shapes', 'prerequisites': ['MS01', 'MS04', 'MS12']},
    {'code': 'QC11', 'name': 'Area & Perimeter Reasoning', 'prerequisites': ['MS01', 'MS04', 'MS12', 'MS13']},
    {'code': 'QC12', 'name': 'Circle Measures', 'prerequisites': ['MS01', 'MS05', 'MS13']},
    {'code': 'QC10', 'name': 'Similar Figures & Scale', 'prerequisites': ['MS01', 'MS04', 'MS06', 'MS12']},
    {'code': 'MS14', 'name': 'Surface area & volume of 3-D solids', 'prerequisites': ['MS01', 'MS04', 'MS13']},
    {'code': 'QC16', 'name': 'Volume & Surface Area', 'prerequisites': ['MS01', 'MS04', 'MS13', 'MS14']},
    
    # TIER 8: MEASUREMENT
    {'code': 'MS16', 'name': 'Measurement units, tools & conversions', 'prerequisites': ['MS01', 'MS04', 'MS05']},
    {'code': 'QC14', 'name': 'Unit Conversion', 'prerequisites': ['MS01', 'MS04', 'MS05', 'MS16']},
    {'code': 'QC15', 'name': 'Rate/Time/Distance & Density', 'prerequisites': ['MS01', 'MS04', 'MS05', 'MS06']},
    
    # TIER 9: DATA ANALYSIS
    {'code': 'MS17', 'name': 'Data representation & statistics', 'prerequisites': ['MS01', 'MS04', 'MS05']},
    {'code': 'QC17', 'name': 'Data Displays & Central Tendency', 'prerequisites': ['MS01', 'MS04', 'MS05', 'MS17']},
    {'code': 'MS18', 'name': 'Probability of simple & compound events', 'prerequisites': ['MS01', 'MS04', 'MS05']},
    {'code': 'QC18', 'name': 'Probability Comparisons', 'prerequisites': ['MS01', 'MS04', 'MS05', 'MS18']}
]

# Create a lookup dictionary for prerequisites
TOPIC_PREREQUISITES = {topic['code']: topic['prerequisites'] for topic in PERFECT_LEARNING_FLOW}
TOPIC_NAMES = {topic['code']: topic['name'] for topic in PERFECT_LEARNING_FLOW}

def apply_prerequisite_logic(topic_mastery, minimum_implied_mastery=40):
    """
    Apply prerequisite logic: if a student performs well on advanced topics,
    they must have some mastery of prerequisite topics.
    
    Args:
        topic_mastery: Dictionary of current topic mastery data
        minimum_implied_mastery: Minimum mastery percentage to assign to prerequisites
    
    Returns:
        Updated topic_mastery with implied mastery for prerequisites
    """
    updated_mastery = topic_mastery.copy()
    
    # Sort topics by tier (advanced topics first to propagate prerequisites)
    assessed_topics = [(code, data) for code, data in topic_mastery.items() 
                      if data.get('total_questions', 0) > 0]
    
    # Process each assessed topic
    for topic_code, topic_data in assessed_topics:
        current_mastery = topic_data.get('mastery_percentage', 0)
        
        # If student shows competency in this topic (>=60%), 
        # ensure prerequisites have minimum implied mastery
        if current_mastery >= 60:
            prerequisites = TOPIC_PREREQUISITES.get(topic_code, [])
            
            for prereq_code in prerequisites:
                if prereq_code in updated_mastery:
                    prereq_data = updated_mastery[prereq_code]
                    current_prereq_mastery = prereq_data.get('mastery_percentage', 0)
                    
                    # Only update if prerequisite hasn't been assessed or has very low score
                    if prereq_data.get('total_questions', 0) == 0 or current_prereq_mastery < minimum_implied_mastery:
                        # Calculate implied mastery based on advanced topic performance
                        implied_mastery = min(current_mastery * 0.7, 80)  # Cap at 80%
                        implied_mastery = max(implied_mastery, minimum_implied_mastery)
                        
                        updated_mastery[prereq_code].update({
                            'mastery_percentage': round(implied_mastery, 2),
                            'implied_from': topic_code,
                            'assessment_type': 'inferred' if prereq_data.get('total_questions', 0) == 0 else 'confirmed_low',
                            'note': f"Inferred from performance in {TOPIC_NAMES.get(topic_code, topic_code)}"
                        })
    
    return updated_mastery

def get_complete_topic_mastery_with_prerequisites():
    """Initialize all topics with zero mastery and prerequisite structure"""
    complete_mastery = {}
    for topic in PERFECT_LEARNING_FLOW:
        complete_mastery[topic['code']] = {
            "section": "Not Assessed",
            "topic": topic['name'],
            "correct_answers": 0,
            "total_questions": 0,
            "mastery_percentage": 0.0,
            "prerequisites": topic['prerequisites'],
            "assessment_type": "not_assessed",
            "implied_from": None,
            "note": ""
        }
    return complete_mastery

def analyze_session_performance(session_data):
    """Enhanced analyze function with prerequisite logic"""
    try:
        # Extract all questions from nested structure
        question_records = []
        for section in session_data.get("sections", []):
            section_name = section.get("sectionName")
            for question in section.get("questions", []):
                # If selectedOption is null, it means not answered = incorrect
                selected_option = question.get("selectedOption")
                if selected_option is None:
                    is_correct = False
                else:
                    is_correct = selected_option == question.get("correctAnswer")
                
                question_records.append({
                    "subject": section_name,
                    "difficulty": question.get("difficultyLevel", "Lower"),
                    "skillCode": question.get("skillCode", "Unknown"),
                    "topic": question.get("topic", section_name),
                    "questionType": question.get("questionType", section_name),
                    "isCorrect": is_correct
                })

        if not question_records:
            raise HTTPException(status_code=404, detail=f"No questions found for session {session_data.get('session_token')}")

        df = pd.DataFrame(question_records)

        # Subject performance
        subject_perf = df.groupby("subject")["isCorrect"].agg(["mean", "count"]).reset_index()
        
        # Subtopic/Skill mastery analysis
        skill_perf = df.groupby("skillCode")["isCorrect"].agg(["mean", "count"]).reset_index()
        skill_perf["accuracy_percent"] = (skill_perf["mean"] * 100).round(2)
        
        # Topic-level analysis
        topic_perf = df.groupby("topic")["isCorrect"].agg(["mean", "count"]).reset_index()
        topic_perf["accuracy_percent"] = (topic_perf["mean"] * 100).round(2)
        
        # Difficulty-level analysis
        difficulty_perf = df.groupby("difficulty")["isCorrect"].agg(["mean", "count"]).reset_index()
        difficulty_perf["accuracy_percent"] = (difficulty_perf["mean"] * 100).round(2)
        
        def classify_strength(acc):
            return "Strong" if acc >= 0.75 else "Average" if acc >= 0.5 else "Weak"

        subject_perf["strength"] = subject_perf["mean"].apply(classify_strength)
        subject_perf["accuracy_percent"] = (subject_perf["mean"] * 100).round(2)

        # Identify weak skills that need more practice
        weak_skills = skill_perf[skill_perf["mean"] < 0.6]
        improvement_needed = []
        for _, skill in weak_skills.iterrows():
            improvement_needed.append({
                "skill": skill["skillCode"],
                "current_accuracy": skill["accuracy_percent"],
                "questions_attempted": int(skill["count"]),
                "importance_level": "High" if skill["count"] >= 2 else "Medium"
            })

        # Subject-wise detailed breakdown
        subject_breakdown = []
        for subject in df["subject"].unique():
            subject_data = df[df["subject"] == subject]
            subject_skills = subject_data.groupby("skillCode")["isCorrect"].agg(["mean", "count"]).reset_index()
            
            weak_skills_in_subject = subject_skills[subject_skills["mean"] < 0.6]
            strong_skills_in_subject = subject_skills[subject_skills["mean"] >= 0.8]
            
            subject_breakdown.append({
                "subject": subject,
                "overall_accuracy": round(subject_data["isCorrect"].mean() * 100, 2),
                "total_questions": len(subject_data),
                "weak_skills": [
                    {
                        "skill": row["skillCode"], 
                        "accuracy": round(row["mean"] * 100, 2),
                        "questions": int(row["count"])
                    } 
                    for _, row in weak_skills_in_subject.iterrows()
                ],
                "strong_skills": [
                    {
                        "skill": row["skillCode"], 
                        "accuracy": round(row["mean"] * 100, 2),
                        "questions": int(row["count"])
                    } 
                    for _, row in strong_skills_in_subject.iterrows()
                ]
            })

        # Final conclusion
        strength_groups = {"Strong": [], "Average": [], "Weak": []}
        for _, row in subject_perf.iterrows():
            strength_groups[row["strength"]].append(row["subject"])

        conclusion_parts = [f"{level} in {', '.join(subjects)}" 
                           for level, subjects in strength_groups.items() if subjects]
        final_conclusion = ", ".join(conclusion_parts)

        # Feature importance (simplified)
        feature_importance = []
        model_accuracy = None
        
        if len(df) >= 10 and len(df["isCorrect"].unique()) > 1:
            try:
                enc = OneHotEncoder(sparse_output=False)
                X = enc.fit_transform(df[["subject", "difficulty", "skillCode"]])
                y = df["isCorrect"]
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
                model = LogisticRegression(max_iter=1000)
                model.fit(X_train, y_train)
                model_accuracy = round(model.score(X_test, y_test), 4)
                
                feature_importance = [{"feature": feat, "importance": round(imp, 4)} 
                                    for feat, imp in zip(enc.get_feature_names_out(), model.coef_[0])]
            except:
                pass

        return {
            "date": datetime.now().isoformat(),
            "session_token": session_data.get("session_token"),
            "student_id": session_data.get("student_id"),
            "total_questions_analyzed": len(df),
            "subject_performance": subject_perf.rename(columns={"mean": "accuracy_percent", "count": "total_questions"}).to_dict(orient="records"),
            "skill_mastery": {
                "detailed_skills": skill_perf.rename(columns={"mean": "accuracy_rate", "count": "questions_attempted"}).to_dict(orient="records"),
                "improvement_needed": improvement_needed,
                "subject_breakdown": subject_breakdown
            },
            "topic_performance": topic_perf.rename(columns={"mean": "accuracy_rate", "count": "questions_attempted"}).to_dict(orient="records"),
            "difficulty_analysis": difficulty_perf.rename(columns={"mean": "accuracy_rate", "count": "questions_attempted"}).to_dict(orient="records"),
            "model_accuracy": model_accuracy,
            "feature_importance": feature_importance,
            "final_conclusion": final_conclusion
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

def analyze_student_strength_by_session(session_token: str, db_manager):
    """Analyze strengths and weaknesses for a student using session_token."""
    try:
        # Access your collection
        database = db_manager.client[db_manager.database_name]
        collection = database["diagnostic_test"] 
        
        # Query for session data using session_token
        session_data = collection.find_one({"session_token": session_token})
        
        if not session_data:
            raise HTTPException(status_code=404, detail=f"No test data found for session {session_token}")

        # Use the analyze_session_performance function
        return analyze_session_performance(session_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

def get_mastery_level(percentage):
    """Determine mastery level based on percentage"""
    if percentage >= 90:
        return "Expert"
    elif percentage >= 80:
        return "Proficient"
    elif percentage >= 70:
        return "Developing"
    elif percentage >= 60:
        return "Basic"
    elif percentage > 0:
        return "Needs Improvement"
    else:
        return "Not Assessed"

def get_section_wise_summary(diagnostic_test):
    """Generate section-wise performance summary"""
    section_summary = {}
    
    for section in diagnostic_test.get("sections", []):
        section_name = section.get("sectionName")
        questions = section.get("questions", [])
        
        if not questions:
            continue
        
        total_questions = len(questions)
        correct_answers = sum(1 for q in questions if q.get("isCorrect", False))
        accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Difficulty breakdown
        difficulty_breakdown = {}
        for question in questions:
            diff = question.get("difficultyLevel", "Unknown")
            if diff not in difficulty_breakdown:
                difficulty_breakdown[diff] = {"correct": 0, "total": 0}
            difficulty_breakdown[diff]["total"] += 1
            if question.get("isCorrect", False):
                difficulty_breakdown[diff]["correct"] += 1
        
        section_summary[section_name] = {
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "accuracy_percentage": round(accuracy, 2),
            "performance_level": get_mastery_level(accuracy),
            "difficulty_breakdown": {
                diff: {
                    "accuracy": round((perf["correct"] / perf["total"]) * 100, 2) if perf["total"] > 0 else 0,
                    "questions_attempted": perf["total"],
                    "correct_answers": perf["correct"]
                } for diff, perf in difficulty_breakdown.items()
            },
            "start_time": section.get("startTime"),
            "end_time": section.get("endTime"),
            "duration_minutes": section.get("durationMinutes")
        }
    
    return section_summary

def generate_study_recommendations(topic_mastery, skill_mastery):
    """Generate personalized study recommendations with prerequisite awareness"""
    recommendations = {
        "priority_areas": [],
        "study_suggestions": [],
        "strengths": [],
        "not_assessed": [],
        "inferred_skills": []  # New: Skills inferred from prerequisites
    }
    
    # Separate assessed, inferred, and not assessed topics
    assessed_topics = [t for t in topic_mastery.values() if t.get("total_questions", 0) > 0]
    inferred_topics = [t for t in topic_mastery.values() if t.get("assessment_type") == "inferred"]
    not_assessed_topics = [t for t in topic_mastery.values() if t.get("total_questions", 0) == 0 and t.get("assessment_type") != "inferred"]
    
    # Identify weak areas that need immediate attention
    weak_topics = [t for t in assessed_topics if t["mastery_percentage"] < 60]
    weak_skills = [s for s in skill_mastery.values() if s.get("mastery_percentage", 0) < 60 and s.get("total_questions", 0) > 0]
    
    # Priority areas (lowest performing)
    if weak_topics:
        worst_topic = min(weak_topics, key=lambda x: x["mastery_percentage"])
        recommendations["priority_areas"].append({
            "area": f"{worst_topic['topic']}",
            "skill_code": worst_topic.get('skill_code', ''),
            "current_performance": f"{worst_topic['mastery_percentage']}%",
            "focus": "Immediate review needed",
            "type": "assessed"
        })
    
    if weak_skills:
        worst_skill = min(weak_skills, key=lambda x: x["mastery_percentage"])
        recommendations["priority_areas"].append({
            "area": f"Skill: {worst_skill.get('skill_code', '')}",
            "skill_code": worst_skill.get('skill_code', ''),
            "current_performance": f"{worst_skill['mastery_percentage']}%",
            "focus": "Practice exercises recommended",
            "type": "assessed"
        })
    
    # Study suggestions
    if len(weak_topics) > 0:
        recommendations["study_suggestions"].append(
            f"Focus on {len(weak_topics)} topics that scored below 60%"
        )
    
    if len(weak_skills) > 0:
        recommendations["study_suggestions"].append(
            f"Practice {len(weak_skills)} specific skills that need improvement"
        )
    
    if len(inferred_topics) > 0:
        recommendations["study_suggestions"].append(
            f"Confirm understanding of {len(inferred_topics)} foundational skills inferred from advanced performance"
        )
    
    if len(not_assessed_topics) > 0:
        recommendations["study_suggestions"].append(
            f"Complete assessment for {len(not_assessed_topics)} topics that haven't been evaluated"
        )
    
    # Identify strengths
    strong_topics = [t for t in assessed_topics if t["mastery_percentage"] >= 80]
    if strong_topics:
        best_topic = max(strong_topics, key=lambda x: x["mastery_percentage"])
        recommendations["strengths"].append({
            "area": f"{best_topic['topic']}",
            "skill_code": best_topic.get('skill_code', ''),
            "performance": f"{best_topic['mastery_percentage']}%",
            "note": "Excellent performance - maintain this level",
            "type": "assessed"
        })
    
    # Inferred skills
    for topic in inferred_topics:
        recommendations["inferred_skills"].append({
            "area": topic["topic"],
            "skill_code": topic.get("skill_code", ""),
            "inferred_mastery": f"{topic['mastery_percentage']}%",
            "inferred_from": topic.get("note", ""),
            "suggestion": "Consider taking a quick assessment to confirm this level"
        })
    
    # Not assessed areas
    recommendations["not_assessed"] = [
        {
            "area": topic["topic"],
            "skill_code": topic.get("skill_code", ""),
            "note": "Assessment needed to determine mastery level"
        }
        for topic in not_assessed_topics[:10]  # Limit to first 10 for readability
    ]
    
    return recommendations

def analyze_comprehensive_performance(session_token: str, db_manager):
    """
    Enhanced comprehensive analysis with prerequisite logic
    """
    try:
        # Get diagnostic test data
        database = db_manager.client[db_manager.database_name]
        diagnostic_collection = database["diagnostic_test"]
        student_summary_collection = database["studentSummary"]
        
        diagnostic_test = diagnostic_collection.find_one({"session_token": session_token})
        
        if not diagnostic_test:
            raise HTTPException(status_code=404, detail=f"No diagnostic test data found for session {session_token}")
        
        # Get basic performance analysis
        performance_analysis = analyze_session_performance(diagnostic_test)
        
        # Initialize complete topic mastery with prerequisites
        complete_topic_mastery = get_complete_topic_mastery_with_prerequisites()
        
        # Process each section to update mastery based on skillCode match
        for section in diagnostic_test.get("sections", []):
            section_name = section.get("sectionName")
            section_questions = section.get("questions", [])
            
            # Track skill performance by skill code
            skill_performance = {}
            
            for question in section_questions:
                skill_code = question.get("skillCode", "Unknown")
                is_correct = question.get("isCorrect", False)
                topic_name = question.get("topic", "Unknown")
                
                # Track skill performance by skill code
                if skill_code not in skill_performance:
                    skill_performance[skill_code] = {
                        "correct": 0, 
                        "total": 0,
                        "section": section_name,
                        "topic": topic_name
                    }
                skill_performance[skill_code]["total"] += 1
                if is_correct:
                    skill_performance[skill_code]["correct"] += 1
            
            # Update complete_topic_mastery only for matching skill codes
            for skill_code, perf in skill_performance.items():
                if skill_code in complete_topic_mastery:
                    mastery_percent = (perf["correct"] / perf["total"]) * 100 if perf["total"] > 0 else 0
                    
                    # Update existing topic entry with actual performance
                    complete_topic_mastery[skill_code].update({
                        "section": perf["section"],
                        "topic": perf["topic"],  # Use actual topic from question
                        "correct_answers": perf["correct"],
                        "total_questions": perf["total"],
                        "mastery_percentage": round(mastery_percent, 2),
                        "assessment_type": "assessed"
                    })
        
        # Apply prerequisite logic
        complete_topic_mastery = apply_prerequisite_logic(complete_topic_mastery)
        
        # Get section-wise summary
        section_summary = get_section_wise_summary(diagnostic_test)
        
        # Generate recommendations with prerequisite awareness
        recommendations = generate_study_recommendations(complete_topic_mastery, {})
        
        # Count different types of assessments
        assessment_stats = {
            "directly_assessed": len([t for t in complete_topic_mastery.values() if t.get("assessment_type") == "assessed"]),
            "inferred_from_prerequisites": len([t for t in complete_topic_mastery.values() if t.get("assessment_type") == "inferred"]),
            "not_assessed": len([t for t in complete_topic_mastery.values() if t.get("assessment_type") == "not_assessed"])
        }
        
        # Create comprehensive student summary document
        student_summary = {
            "student_id": diagnostic_test.get("student_id"),
            "session_token": session_token,
            "assessment_date": diagnostic_test.get("createdAt", datetime.now()),
            "analysis_date": datetime.now(),
            
            # Complete mastery data with prerequisite logic applied
            "complete_topic_mastery": complete_topic_mastery,
            "assessment_statistics": assessment_stats,
            "recommendations": recommendations,
            
            # Metadata
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "analysis_version": "3.0_with_prerequisites"
        }
        
        # Store in studentSummary collection (upsert based on student_id and session_token)
        filter_criteria = {
            "student_id": diagnostic_test.get("student_id"),
            "session_token": session_token
        }
        
        result = student_summary_collection.replace_one(
            filter_criteria,
            student_summary,
            upsert=True
        )
        
        # Create response with summary ID
        if result.upserted_id:
            student_summary["_id"] = str(result.upserted_id)
        else:
            existing_doc = student_summary_collection.find_one(filter_criteria)
            student_summary["_id"] = str(existing_doc["_id"]) if existing_doc else None
        
        print(f"✅ Student summary with prerequisite logic saved for student: {diagnostic_test.get('student_id')}")
        print(f"📊 Assessment Stats: {assessment_stats}")
        
        return {
            "success": True,
            "message": "Analysis completed with prerequisite logic applied",
            "student_summary_id": student_summary.get("_id"),
            "assessment_statistics": assessment_stats,
            "analysis_data": student_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comprehensive analysis error: {str(e)}")

# Example usage function to demonstrate the prerequisite logic
def demonstrate_prerequisite_logic():
    """
    Example to show how prerequisite logic works
    """
    # Sample scenario: Student answers ratio questions correctly but hasn't been tested on whole numbers
    sample_mastery = {
        'MS01': {'mastery_percentage': 0, 'total_questions': 0, 'assessment_type': 'not_assessed', 'topic': 'Whole-number operations', 'prerequisites': []},
        'MS04': {'mastery_percentage': 0, 'total_questions': 0, 'assessment_type': 'not_assessed', 'topic': 'Fraction operations', 'prerequisites': ['MS01']},
        'MS05': {'mastery_percentage': 0, 'total_questions': 0, 'assessment_type': 'not_assessed', 'topic': 'Decimal reasoning', 'prerequisites': ['MS01']},
        'MS06': {'mastery_percentage': 85, 'total_questions': 5, 'assessment_type': 'assessed', 'topic': 'Ratios and proportions', 'prerequisites': ['MS01', 'MS04', 'MS05']},
        'QC05': {'mastery_percentage': 75, 'total_questions': 4, 'assessment_type': 'assessed', 'topic': 'Ratios & Unit Rates', 'prerequisites': ['MS01', 'MS04', 'MS05', 'MS06']}
    }
    
    print("BEFORE applying prerequisite logic:")
    for code, data in sample_mastery.items():
        print(f"{code}: {data['mastery_percentage']}% ({data['assessment_type']})")
    
    # Apply prerequisite logic
    updated_mastery = apply_prerequisite_logic(sample_mastery)
    
    print("\nAFTER applying prerequisite logic:")
    for code, data in updated_mastery.items():
        status = f"({data['assessment_type']})"
        if data.get('implied_from'):
            status += f" - inferred from {data['implied_from']}"
        print(f"{code}: {data['mastery_percentage']}% {status}")
    
    return updated_mastery

def get_prerequisite_chain(topic_code, max_depth=3):
    """
    Get the prerequisite chain for a given topic code
    
    Args:
        topic_code: The topic code to analyze
        max_depth: Maximum depth to traverse (prevents infinite loops)
    
    Returns:
        List of prerequisite chains
    """
    def get_chain_recursive(code, current_chain, depth):
        if depth > max_depth or code in current_chain:  # Prevent infinite loops
            return [current_chain]
        
        prerequisites = TOPIC_PREREQUISITES.get(code, [])
        if not prerequisites:
            return [current_chain + [code]]
        
        all_chains = []
        for prereq in prerequisites:
            chains = get_chain_recursive(prereq, current_chain + [code], depth + 1)
            all_chains.extend(chains)
        
        return all_chains
    
    chains = get_chain_recursive(topic_code, [], 0)
    return chains

def analyze_learning_path_gaps(topic_mastery):
    """
    Identify gaps in learning path where prerequisites are missing
    
    Args:
        topic_mastery: Dictionary of topic mastery data
        
    Returns:
        Dictionary with gap analysis
    """
    gaps = {
        "critical_gaps": [],  # Strong performance with weak prerequisites
        "learning_path_violations": [],  # Advanced topics mastered before basics
        "suggested_assessments": []  # Prerequisites that should be tested
    }
    
    for topic_code, topic_data in topic_mastery.items():
        if topic_data.get('assessment_type') == 'assessed' and topic_data.get('mastery_percentage', 0) >= 70:
            # Student performed well on this topic
            prerequisites = TOPIC_PREREQUISITES.get(topic_code, [])
            
            for prereq_code in prerequisites:
                if prereq_code in topic_mastery:
                    prereq_data = topic_mastery[prereq_code]
                    prereq_mastery = prereq_data.get('mastery_percentage', 0)
                    prereq_assessed = prereq_data.get('total_questions', 0) > 0
                    
                    # Check for critical gaps
                    if prereq_assessed and prereq_mastery < 50:
                        gaps["critical_gaps"].append({
                            "advanced_topic": topic_code,
                            "advanced_performance": topic_data.get('mastery_percentage'),
                            "weak_prerequisite": prereq_code,
                            "prerequisite_performance": prereq_mastery,
                            "gap_severity": "High" if prereq_mastery < 30 else "Medium"
                        })
                    
                    # Check for learning path violations
                    if prereq_assessed and topic_data.get('mastery_percentage', 0) > prereq_mastery + 20:
                        gaps["learning_path_violations"].append({
                            "advanced_topic": topic_code,
                            "prerequisite": prereq_code,
                            "performance_gap": topic_data.get('mastery_percentage', 0) - prereq_mastery,
                            "note": "Student may have skipped foundational concepts"
                        })
                    
                    # Suggest assessments for unassessed prerequisites
                    if not prereq_assessed and prereq_data.get('assessment_type') != 'inferred':
                        gaps["suggested_assessments"].append({
                            "prerequisite": prereq_code,
                            "prerequisite_topic": prereq_data.get('topic'),
                            "needed_for": topic_code,
                            "priority": "High" if topic_data.get('mastery_percentage', 0) >= 80 else "Medium"
                        })
    
    return gaps

def generate_adaptive_study_plan(topic_mastery, student_goals=None):
    """
    Generate an adaptive study plan based on current mastery and prerequisite logic
    
    Args:
        topic_mastery: Dictionary of current topic mastery
        student_goals: List of target topics the student wants to master
        
    Returns:
        Structured study plan
    """
    study_plan = {
        "immediate_priorities": [],
        "foundation_building": [],
        "skill_advancement": [],
        "assessment_recommendations": [],
        "estimated_study_time": {}
    }
    
    # Analyze gaps
    gaps = analyze_learning_path_gaps(topic_mastery)
    
    # Immediate priorities - fix critical gaps
    for gap in gaps["critical_gaps"]:
        study_plan["immediate_priorities"].append({
            "topic_code": gap["weak_prerequisite"],
            "topic_name": TOPIC_NAMES.get(gap["weak_prerequisite"], gap["weak_prerequisite"]),
            "current_level": gap["prerequisite_performance"],
            "target_level": 70,
            "reason": f"Required for {TOPIC_NAMES.get(gap['advanced_topic'], gap['advanced_topic'])}",
            "urgency": gap["gap_severity"]
        })
    
    # Foundation building - strengthen prerequisites for inferred skills
    inferred_topics = [code for code, data in topic_mastery.items() 
                      if data.get('assessment_type') == 'inferred']
    
    for topic_code in inferred_topics:
        topic_data = topic_mastery[topic_code]
        if topic_data.get('mastery_percentage', 0) < 60:  # Low inferred mastery
            study_plan["foundation_building"].append({
                "topic_code": topic_code,
                "topic_name": topic_data.get('topic'),
                "inferred_level": topic_data.get('mastery_percentage'),
                "target_level": 70,
                "reason": topic_data.get('note', 'Foundational skill'),
                "confidence": "Low - needs assessment"
            })
    
    # Skill advancement - topics ready for next level
    ready_for_advancement = []
    for topic_code, topic_data in topic_mastery.items():
        if (topic_data.get('assessment_type') == 'assessed' and 
            topic_data.get('mastery_percentage', 0) >= 80):
            
            # Find topics that have this as a prerequisite
            dependent_topics = [code for code, prereqs in TOPIC_PREREQUISITES.items() 
                              if topic_code in prereqs and code in topic_mastery]
            
            for dep_code in dependent_topics:
                dep_data = topic_mastery[dep_code]
                if dep_data.get('total_questions', 0) == 0:  # Not assessed yet
                    ready_for_advancement.append({
                        "topic_code": dep_code,
                        "topic_name": dep_data.get('topic'),
                        "prerequisite_strength": topic_data.get('mastery_percentage'),
                        "readiness": "High" if topic_data.get('mastery_percentage', 0) >= 85 else "Medium"
                    })
    
    study_plan["skill_advancement"] = ready_for_advancement[:5]  # Top 5 recommendations
    
    # Assessment recommendations
    study_plan["assessment_recommendations"] = gaps["suggested_assessments"][:8]  # Top 8
    
    # Estimate study time (simplified)
    for priority in study_plan["immediate_priorities"]:
        current = priority["current_level"]
        target = priority["target_level"]
        gap = target - current
        estimated_hours = max(2, gap * 0.1)  # Rough estimate: 6 minutes per percentage point
        study_plan["estimated_study_time"][priority["topic_code"]] = {
            "hours": round(estimated_hours, 1),
            "sessions": max(1, round(estimated_hours / 2))  # Assuming 2-hour study sessions
        }
    
    return study_plan

def create_prerequisite_visualization_data(topic_mastery):
    """
    Create data structure for visualizing prerequisite relationships and mastery levels
    
    Returns:
        Dictionary suitable for frontend visualization
    """
    nodes = []
    edges = []
    
    for topic_code, topic_data in topic_mastery.items():
        # Create node for each topic
        mastery_level = topic_data.get('mastery_percentage', 0)
        assessment_type = topic_data.get('assessment_type', 'not_assessed')
        
        # Determine node color based on mastery and assessment type
        if assessment_type == 'assessed':
            color = '#22c55e' if mastery_level >= 70 else '#ef4444' if mastery_level < 50 else '#f59e0b'
        elif assessment_type == 'inferred':
            color = '#8b5cf6'  # Purple for inferred
        else:
            color = '#6b7280'  # Gray for not assessed
        
        nodes.append({
            'id': topic_code,
            'label': topic_data.get('topic', topic_code)[:30] + '...' if len(topic_data.get('topic', '')) > 30 else topic_data.get('topic', topic_code),
            'mastery': mastery_level,
            'assessment_type': assessment_type,
            'color': color,
            'size': max(20, mastery_level * 0.5),  # Size based on mastery
            'details': {
                'full_name': topic_data.get('topic'),
                'correct_answers': topic_data.get('correct_answers', 0),
                'total_questions': topic_data.get('total_questions', 0),
                'note': topic_data.get('note', '')
            }
        })
        
        # Create edges for prerequisites
        prerequisites = TOPIC_PREREQUISITES.get(topic_code, [])
        for prereq in prerequisites:
            edges.append({
                'from': prereq,
                'to': topic_code,
                'type': 'prerequisite'
            })
    
    return {
        'nodes': nodes,
        'edges': edges,
        'stats': {
            'total_topics': len(nodes),
            'assessed': len([n for n in nodes if n['assessment_type'] == 'assessed']),
            'inferred': len([n for n in nodes if n['assessment_type'] == 'inferred']),
            'not_assessed': len([n for n in nodes if n['assessment_type'] == 'not_assessed']),
            'mastery_above_70': len([n for n in nodes if n['mastery'] >= 70])
        }
    }

# Enhanced main analysis function that includes all new features
def analyze_comprehensive_performance_with_full_features(session_token: str, db_manager):
    """
    Most comprehensive analysis with all prerequisite features
    """
    try:
        # Run the standard comprehensive analysis first
        standard_result = analyze_comprehensive_performance(session_token, db_manager)
        
        if not standard_result["success"]:
            return standard_result
        
        topic_mastery = standard_result["analysis_data"]["complete_topic_mastery"]
        
        # Add advanced analyses
        gap_analysis = analyze_learning_path_gaps(topic_mastery)
        study_plan = generate_adaptive_study_plan(topic_mastery)
        visualization_data = create_prerequisite_visualization_data(topic_mastery)
        
        # Enhance the result with additional analyses
        enhanced_result = standard_result.copy()
        enhanced_result["analysis_data"].update({
            "gap_analysis": gap_analysis,
            "adaptive_study_plan": study_plan,
            "visualization_data": visualization_data,
            "prerequisite_chains": {
                code: get_prerequisite_chain(code) 
                for code, data in topic_mastery.items() 
                if data.get('assessment_type') == 'assessed' and data.get('mastery_percentage', 0) >= 70
            }
        })
        
        enhanced_result["message"] = "Complete analysis with prerequisite logic, gap analysis, and study planning"
        enhanced_result["analysis_version"] = "4.0_full_prerequisite_analysis"
        
        # Update the database record
        database = db_manager.client[db_manager.database_name]
        student_summary_collection = database["studentSummary"]
        
        filter_criteria = {
            "student_id": enhanced_result["analysis_data"].get("student_id"),
            "session_token": session_token
        }
        
        student_summary_collection.replace_one(
            filter_criteria,
            enhanced_result["analysis_data"],
            upsert=True
        )
        
        return enhanced_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced analysis error: {str(e)}")

