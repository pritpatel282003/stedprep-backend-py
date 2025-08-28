# student_Dashboard/learning_flow.py

from typing import Set, List

# This file defines the learning flow for all topics, including verbal, reading comprehension, and math.
# It provides a curated order of topics, a complete list of all topics with their codes, names, tiers, and sections,
# and the prerequisites for each topic.

# A set of all allowed topic names for study plans.
# Only topics from this list will be considered when generating study plans.
ALLOWED_TOPICS: Set[str] = {
    # Tier 0 - Verbal & Reading Comprehension
    "Abstract & Philosophical Concepts",
    "Actions, Verbs & Emotions",
    "Nature & Environment",
    "Numbers, Time & Measurements",
    "Objects & Materials",
    "People & Relationships",
    "Places & Geography",
    "Qualities & Descriptions",
    "Science & Technology",
    "Society, Government & Law",
    "Cause-and-Effect Connector",
    "Character Trait / Emotion Inference",
    "Contextual Academic Vocabulary",
    "Continuation / Similarity Connector",
    "Contrast / Concession Connector",
    "Definition by Restatement",
    "Degree / Intensity Calibration",
    "Figurative / Idiomatic Meaning",
    "Multi-Clue Synthesis",
    "Real-World Context Inference",
    "Tone & Connotation Match",
    "Social Studies",
    "History",
    "Science",
    "Contemporary Life",
    "Arts",
    "Biography",
    "Technology",

    # Math topics
    "Whole-number operations & order of operations",
    "Prime factors, GCF & LCM",
    "GCF & LCM Reasoning",
    "Integer operations & absolute value",
    "Signed Integers & Absolute Value",
    "Fraction & mixed-number operations",
    "Fractions & Mixed Numbers",
    "Decimal & percent reasoning",
    "Decimals & Percents",
    "Ratios, unit rates, scale drawings & proportions",
    "Ratios & Unit Rates",
    "Exponents, squares & square roots",
    "Exponents & Roots",
    "Scientific Notation & Order of Magnitude",
    "Evaluating & simplifying algebraic expressions",
    "Variable Expressions (Fixed Order)",
    "Variable Expressions (Indeterminate)",
    "One-variable linear equations & inequalities",
    "Coordinate-plane basics",
    "Coordinate Plane Slope & Distance",
    "Patterns, sequences & basic function rules",
    "Sequences & Patterns",
    "Angle relationships & polygon properties",
    "Angle & Segment Relations",
    "Perimeter, area & circumference of 2-D shapes",
    "Area & Perimeter Reasoning",
    "Circle Measures",
    "Similar Figures & Scale",
    "Surface area & volume of 3-D solids",
    "Volume & Surface Area",
    "Measurement units, tools & conversions",
    "Unit Conversion",
    "Rate/Time/Distance & Density",
    "Data representation & statistics",
    "Probability of simple & compound events",
    "Data Displays & Central Tendency",
    "Probability Comparisons",
}

# A curated order of topics to guide the learning path.
CURATED_FLOW_ORDER: List[str] = [
    # Tier 0 - Verbal & Reading Comprehension
    # Synonyms - Vocabulary Building
    "Abstract & Philosophical Concepts",
    "Actions, Verbs & Emotions",
    "Nature & Environment",
    "Numbers, Time & Measurements",
    "Objects & Materials",
    "People & Relationships",
    "Places & Geography",
    "Qualities & Descriptions",
    "Science & Technology",
    "Society, Government & Law",
    # Sentence Completion - Advanced Verbal
    "Cause-and-Effect Connector",
    "Character Trait / Emotion Inference",
    "Contextual Academic Vocabulary",
    "Continuation / Similarity Connector",
    "Contrast / Concession Connector",
    "Definition by Restatement",
    "Degree / Intensity Calibration",
    "Figurative / Idiomatic Meaning",
    "Multi-Clue Synthesis",
    "Real-World Context Inference",
    "Tone & Connotation Match",
    # Reading Comprehension - Domains
    "Social Studies",
    "History",
    "Science",
    "Contemporary Life",
    "Arts",
    "Biography",
    "Technology",

    # Math sequence
    # Tier 1
    "Whole-number operations & order of operations",
    "Prime factors, GCF & LCM",
    "GCF & LCM Reasoning",
    "Integer operations & absolute value",
    "Signed Integers & Absolute Value",
    # Tier 2
    "Fraction & mixed-number operations",
    "Fractions & Mixed Numbers",
    "Decimal & percent reasoning",
    "Decimals & Percents",
    # Tier 3
    "Ratios, unit rates, scale drawings & proportions",
    "Ratios & Unit Rates",
    # Tier 4
    "Exponents, squares & square roots",
    "Exponents & Roots",
    "Scientific Notation & Order of Magnitude",
    # Tier 5
    "Evaluating & simplifying algebraic expressions",
    "Variable Expressions (Fixed Order)",
    "Variable Expressions (Indeterminate)",
    # Tier 6
    "One-variable linear equations & inequalities",
    "Coordinate-plane basics",
    "Coordinate Plane Slope & Distance",
    "Patterns, sequences & basic function rules",
    "Sequences & Patterns",
    # Tier 7
    "Angle relationships & polygon properties",
    "Angle & Segment Relations",
    "Perimeter, area & circumference of 2-D shapes",
    "Area & Perimeter Reasoning",
    "Circle Measures",
    "Similar Figures & Scale",
    "Surface area & volume of 3-D solids",
    "Volume & Surface Area",
    # Tier 8
    "Measurement units, tools & conversions",
    "Unit Conversion",
    "Rate/Time/Distance & Density",
    # Tier 9
    "Data representation & statistics",
    "Probability of simple & compound events",
    "Data Displays & Central Tendency",
    "Probability Comparisons",
]

# A complete catalog of all topics with their codes, names, tiers, and sections.
COMPLETE_LEARNING_FLOW = [
    # TIER 0: VERBAL & READING COMPREHENSION (No Prerequisites)
    # Synonyms Section - Vocabulary Building
    {"code": "VR-01", "name": "Abstract & Philosophical Concepts", "tier": 0, "section": "Verbal"},
    {"code": "VR-02", "name": "Actions, Verbs & Emotions", "tier": 0, "section": "Verbal"},
    {"code": "VR-03", "name": "Nature & Environment", "tier": 0, "section": "Verbal"},
    {"code": "VR-04", "name": "Numbers, Time & Measurements", "tier": 0, "section": "Verbal"},
    {"code": "VR-05", "name": "Objects & Materials", "tier": 0, "section": "Verbal"},
    {"code": "VR-06", "name": "People & Relationships", "tier": 0, "section": "Verbal"},
    {"code": "VR-07", "name": "Places & Geography", "tier": 0, "section": "Verbal"},
    {"code": "VR-08", "name": "Qualities & Descriptions", "tier": 0, "section": "Verbal"},
    {"code": "VR-09", "name": "Science & Technology", "tier": 0, "section": "Verbal"},
    {"code": "VR-10", "name": "Society, Government & Law", "tier": 0, "section": "Verbal"},
    # Sentence Completion Section - Advanced Verbal Skills
    {"code": "VR-11", "name": "Cause-and-Effect Connector", "tier": 0, "section": "Verbal"},
    {"code": "VR-12", "name": "Character Trait / Emotion Inference", "tier": 0, "section": "Verbal"},
    {"code": "VR-13", "name": "Contextual Academic Vocabulary", "tier": 0, "section": "Verbal"},
    {"code": "VR-14", "name": "Continuation / Similarity Connector", "tier": 0, "section": "Verbal"},
    {"code": "VR-15", "name": "Contrast / Concession Connector", "tier": 0, "section": "Verbal"},
    {"code": "VR-16", "name": "Definition by Restatement", "tier": 0, "section": "Verbal"},
    {"code": "VR-17", "name": "Degree / Intensity Calibration", "tier": 0, "section": "Verbal"},
    {"code": "VR-18", "name": "Figurative / Idiomatic Meaning", "tier": 0, "section": "Verbal"},
    {"code": "VR-19", "name": "Multi-Clue Synthesis", "tier": 0, "section": "Verbal"},
    {"code": "VR-20", "name": "Real-World Context Inference", "tier": 0, "section": "Verbal"},
    {"code": "VR-21", "name": "Tone & Connotation Match", "tier": 0, "section": "Verbal"},
    # Reading Comprehension Section - Domain Knowledge
    {"code": "RC-01", "name": "Social Studies", "tier": 0, "section": "Reading Comprehension"},
    {"code": "RC-02", "name": "History", "tier": 0, "section": "Reading Comprehension"},
    {"code": "RC-03", "name": "Science", "tier": 0, "section": "Reading Comprehension"},
    {"code": "RC-04", "name": "Contemporary Life", "tier": 0, "section": "Reading Comprehension"},
    {"code": "RC-05", "name": "Arts", "tier": 0, "section": "Reading Comprehension"},
    {"code": "RC-06", "name": "Biography", "tier": 0, "section": "Reading Comprehension"},
    {"code": "RC-07", "name": "Technology", "tier": 0, "section": "Reading Comprehension"},

    # TIER 1: MATH FOUNDATIONAL
    {"code": "MS01", "name": "Whole-number operations & order of operations", "tier": 1, "section": "Math"},
    {"code": "MS02", "name": "Prime factors, GCF & LCM", "tier": 1, "section": "Math"},
    {"code": "QC03", "name": "GCF & LCM Reasoning", "tier": 1, "section": "Math"},
    {"code": "MS03", "name": "Integer operations & absolute value", "tier": 1, "section": "Math"},
    {"code": "QC01", "name": "Signed Integers & Absolute Value", "tier": 1, "section": "Math"},

    # TIER 2: MATH NUMBER SYSTEMS
    {"code": "MS04", "name": "Fraction & mixed-number operations", "tier": 2, "section": "Math"},
    {"code": "QC02", "name": "Fractions & Mixed Numbers", "tier": 2, "section": "Math"},
    {"code": "MS05", "name": "Decimal & percent reasoning", "tier": 2, "section": "Math"},
    {"code": "QC04", "name": "Decimals & Percents", "tier": 2, "section": "Math"},

    # TIER 3: MATH PROPORTIONAL REASONING
    {"code": "MS06", "name": "Ratios, unit rates, scale drawings & proportions", "tier": 3, "section": "Math"},
    {"code": "QC05", "name": "Ratios & Unit Rates", "tier": 3, "section": "Math"},

    # TIER 4: MATH EXPONENTIAL
    {"code": "MS07", "name": "Exponents, squares & square roots", "tier": 4, "section": "Math"},
    {"code": "QC06", "name": "Exponents & Roots", "tier": 4, "section": "Math"},
    {"code": "QC19", "name": "Scientific Notation & Order of Magnitude", "tier": 4, "section": "Math"},

    # TIER 5: MATH ALGEBRAIC BASIC
    {"code": "MS08", "name": "Evaluating & simplifying algebraic expressions", "tier": 5, "section": "Math"},
    {"code": "QC07a", "name": "Variable Expressions (Fixed Order)", "tier": 5, "section": "Math"},
    {"code": "QC07b", "name": "Variable Expressions (Indeterminate)", "tier": 5, "section": "Math"},

    # TIER 6: MATH ALGEBRAIC ADVANCED
    {"code": "MS09", "name": "One-variable linear equations & inequalities", "tier": 6, "section": "Math"},
    {"code": "MS10", "name": "Coordinate-plane basics", "tier": 6, "section": "Math"},
    {"code": "QC13", "name": "Coordinate Plane Slope & Distance", "tier": 6, "section": "Math"},
    {"code": "MS11", "name": "Patterns, sequences & basic function rules", "tier": 6, "section": "Math"},
    {"code": "QC08", "name": "Sequences & Patterns", "tier": 6, "section": "Math"},

    # TIER 7: MATH GEOMETRIC
    {"code": "MS12", "name": "Angle relationships & polygon properties", "tier": 7, "section": "Math"},
    {"code": "QC09", "name": "Angle & Segment Relations", "tier": 7, "section": "Math"},
    {"code": "MS13", "name": "Perimeter, area & circumference of 2-D shapes", "tier": 7, "section": "Math"},
    {"code": "QC11", "name": "Area & Perimeter Reasoning", "tier": 7, "section": "Math"},
    {"code": "QC12", "name": "Circle Measures", "tier": 7, "section": "Math"},
    {"code": "QC10", "name": "Similar Figures & Scale", "tier": 7, "section": "Math"},
    {"code": "MS14", "name": "Surface area & volume of 3-D solids", "tier": 7, "section": "Math"},
    {"code": "QC16", "name": "Volume & Surface Area", "tier": 7, "section": "Math"},

    # TIER 8: MATH MEASUREMENT
    {"code": "MS16", "name": "Measurement units, tools & conversions", "tier": 8, "section": "Math"},
    {"code": "QC14", "name": "Unit Conversion", "tier": 8, "section": "Math"},
    {"code": "QC15", "name": "Rate/Time/Distance & Density", "tier": 8, "section": "Math"},

    # TIER 9: MATH DATA ANALYSIS
    {"code": "MS17", "name": "Data representation & statistics", "tier": 9, "section": "Math"},
    {"code": "QC17", "name": "Data Displays & Central Tendency", "tier": 9, "section": "Math"},
    {"code": "MS18", "name": "Probability of simple & compound events", "tier": 9, "section": "Math"},
    {"code": "QC18", "name": "Probability Comparisons", "tier": 9, "section": "Math"},
]

# A mapping of topic codes to their prerequisites.
COMPLETE_PREREQUISITES = {
    # TIER 0 - Verbal & Reading Comprehension (NO PREREQUISITES)
    # All Synonyms skills
    "VR-01": [],  # Abstract & Philosophical Concepts
    "VR-02": [],  # Actions, Verbs & Emotions
    "VR-03": [],  # Nature & Environment
    "VR-04": [],  # Numbers, Time & Measurements
    "VR-05": [],  # Objects & Materials
    "VR-06": [],  # People & Relationships
    "VR-07": [],  # Places & Geography
    "VR-08": [],  # Qualities & Descriptions
    "VR-09": [],  # Science & Technology
    "VR-10": [],  # Society, Government & Law

    # All Sentence Completion skills
    "VR-11": [],  # Cause-and-Effect Connector
    "VR-12": [],  # Character Trait / Emotion Inference
    "VR-13": [],  # Contextual Academic Vocabulary
    "VR-14": [],  # Continuation / Similarity Connector
    "VR-15": [],  # Contrast / Concession Connector
    "VR-16": [],  # Definition by Restatement
    "VR-17": [],  # Degree / Intensity Calibration
    "VR-18": [],  # Figurative / Idiomatic Meaning
    "VR-19": [],  # Multi-Clue Synthesis
    "VR-20": [],  # Real-World Context Inference
    "VR-21": [],  # Tone & Connotation Match

    # All Reading Comprehension skills
    "RC-01": [],  # Social Studies
    "RC-02": [],  # History
    "RC-03": [],  # Science
    "RC-04": [],  # Contemporary Life
    "RC-05": [],  # Arts
    "RC-06": [],  # Biography
    "RC-07": [],  # Technology
}


