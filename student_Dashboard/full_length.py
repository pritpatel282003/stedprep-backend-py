# student_Dashboard/full_length.py

from typing import List, Dict, Any
from student_Dashboard.section_test import fetch_section_questions

# The default order of sections in a full-length test.
SECTION_ORDER_DEFAULT: List[str] = [
    "quantitative reasoning",
    "verbal reasoning",
    "reading comprehension",
    "mathematics achievement",
]


def build_full_length_test(db_manager, sections_order: List[str] = None, per_section: int = 25) -> List[Dict[str, Any]]:
    """
    Builds a full-length test packet with a specified number of questions per section.

    This function fetches a set number of questions for each section in the specified order
    and compiles them into a list of section dictionaries.

    Args:
        db_manager: The database manager instance.
        sections_order (List[str], optional): The order of sections in the test.
            Defaults to SECTION_ORDER_DEFAULT.
        per_section (int, optional): The number of questions to fetch for each section.
            Defaults to 25.

    Returns:
        A list of dictionaries, where each dictionary represents a section and contains
        the section name, the number of questions recommended, the number of questions fetched,
        and the list of questions.
    """
    # Use the default section order if none is provided
    sections_order = sections_order or SECTION_ORDER_DEFAULT

    results: List[Dict[str, Any]] = []

    # Fetch questions for each section in the specified order
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


