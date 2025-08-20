from typing import List, Dict, Any

from student_Dashboard.section_test import fetch_section_questions


SECTION_ORDER_DEFAULT: List[str] = [
    "quantitative reasoning",
    "verbal reasoning",
    "reading comprehension",
    "mathematics achievement",
]


def build_full_length_test(db_manager, sections_order: List[str] = None, per_section: int = 25) -> List[Dict[str, Any]]:
    """Build a full-length test packet: 25 questions per each section in order.

    Returns a list of section dicts: { section, fetched_count, questions }
    """
    sections_order = sections_order or SECTION_ORDER_DEFAULT
    results: List[Dict[str, Any]] = []
    for section_name in sections_order:
        questions = fetch_section_questions(db_manager, section_name=section_name.lower(), num_questions=per_section)
        results.append({
            "section": section_name.lower(),
            "questions_recommended": per_section,
            "fetched_count": len(questions),
            "questions": questions,
            "no_questions": len(questions) == 0,
            "message": (f"No questions found for section {section_name}" if len(questions) == 0 else "")
        })
    return results


