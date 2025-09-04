# models/learning_flow.py

# This file defines the complete learning flow for all topics, including verbal, reading comprehension, and math.
# It is the single source of truth for the entire application.

COMPLETE_LEARNING_FLOW = [
    {
        "code": "VR-01",
        "name": "Abstract & Philosophical Concepts",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-02",
        "name": "Actions, Verbs & Emotions",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-03",
        "name": "Nature & Environment",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-04",
        "name": "Numbers, Time & Measurements",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-05",
        "name": "Objects & Materials",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-06",
        "name": "People & Relationships",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-07",
        "name": "Places & Geography",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-08",
        "name": "Qualities & Descriptions",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-09",
        "name": "Science & Technology",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-10",
        "name": "Society, Government & Law",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-11",
        "name": "Cause-and-Effect Connector",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-12",
        "name": "Character Trait / Emotion Inference",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-13",
        "name": "Contextual Academic Vocabulary",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-14",
        "name": "Continuation / Similarity Connector",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-15",
        "name": "Contrast / Concession Connector",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-16",
        "name": "Definition by Restatement",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-17",
        "name": "Degree / Intensity Calibration",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-18",
        "name": "Figurative / Idiomatic Meaning",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-19",
        "name": "Multi-Clue Synthesis",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-20",
        "name": "Real-World Context Inference",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "VR-21",
        "name": "Tone & Connotation Match",
        "tier": 0,
        "section": "Verbal",
        "prerequisites": []
    },
    {
        "code": "RC-01",
        "name": "Social Studies",
        "tier": 0,
        "section": "Reading Comprehension",
        "prerequisites": []
    },
    {
        "code": "RC-02",
        "name": "History",
        "tier": 0,
        "section": "Reading Comprehension",
        "prerequisites": []
    },
    {
        "code": "RC-03",
        "name": "Science",
        "tier": 0,
        "section": "Reading Comprehension",
        "prerequisites": []
    },
    {
        "code": "RC-04",
        "name": "Contemporary Life",
        "tier": 0,
        "section": "Reading Comprehension",
        "prerequisites": []
    },
    {
        "code": "RC-05",
        "name": "Arts",
        "tier": 0,
        "section": "Reading Comprehension",
        "prerequisites": []
    },
    {
        "code": "RC-06",
        "name": "Biography",
        "tier": 0,
        "section": "Reading Comprehension",
        "prerequisites": []
    },
    {
        "code": "RC-07",
        "name": "Technology",
        "tier": 0,
        "section": "Reading Comprehension",
        "prerequisites": []
    },
    {
        "code": "MS01",
        "name": "Whole-number operations & order of operations",
        "tier": 1,
        "section": "Math",
        "prerequisites": []
    },
    {
        "code": "MS02",
        "name": "Prime factors, GCF & LCM",
        "tier": 1,
        "section": "Math",
        "prerequisites": [
            "MS01"
        ]
    },
    {
        "code": "QC03",
        "name": "GCF & LCM Reasoning",
        "tier": 1,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS02"
        ]
    },
    {
        "code": "MS03",
        "name": "Integer operations & absolute value",
        "tier": 1,
        "section": "Math",
        "prerequisites": [
            "MS01"
        ]
    },
    {
        "code": "QC01",
        "name": "Signed Integers & Absolute Value",
        "tier": 1,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS03"
        ]
    },
    {
        "code": "MS04",
        "name": "Fraction & mixed-number operations",
        "tier": 2,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS02",
            "MS03"
        ]
    },
    {
        "code": "QC02",
        "name": "Fractions & Mixed Numbers",
        "tier": 2,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04"
        ]
    },
    {
        "code": "MS05",
        "name": "Decimal & percent reasoning",
        "tier": 2,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04"
        ]
    },
    {
        "code": "QC04",
        "name": "Decimals & Percents",
        "tier": 2,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS05"
        ]
    },
    {
        "code": "MS06",
        "name": "Ratios, unit rates, scale drawings & proportions",
        "tier": 3,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS05"
        ]
    },
    {
        "code": "QC05",
        "name": "Ratios & Unit Rates",
        "tier": 3,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS05",
            "MS06"
        ]
    },
    {
        "code": "MS07",
        "name": "Exponents, squares & square roots",
        "tier": 4,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS03"
        ]
    },
    {
        "code": "QC06",
        "name": "Exponents & Roots",
        "tier": 4,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS03",
            "MS07"
        ]
    },
    {
        "code": "QC19",
        "name": "Scientific Notation & Order of Magnitude",
        "tier": 4,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS05",
            "MS07"
        ]
    },
    {
        "code": "MS08",
        "name": "Evaluating & simplifying algebraic expressions",
        "tier": 5,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS03",
            "MS07"
        ]
    },
    {
        "code": "QC07a",
        "name": "Variable Expressions (Fixed Order)",
        "tier": 5,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS03",
            "MS08"
        ]
    },
    {
        "code": "QC07b",
        "name": "Variable Expressions (Indeterminate)",
        "tier": 5,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS03",
            "MS08",
            "QC07a"
        ]
    },
    {
        "code": "MS09",
        "name": "One-variable linear equations & inequalities",
        "tier": 6,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS03",
            "MS08"
        ]
    },
    {
        "code": "MS10",
        "name": "Coordinate-plane basics",
        "tier": 6,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS03"
        ]
    },
    {
        "code": "QC13",
        "name": "Coordinate Plane Slope & Distance",
        "tier": 6,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS03",
            "MS10"
        ]
    },
    {
        "code": "MS11",
        "name": "Patterns, sequences & basic function rules",
        "tier": 6,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS08",
            "MS09"
        ]
    },
    {
        "code": "QC08",
        "name": "Sequences & Patterns",
        "tier": 6,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS08",
            "MS11"
        ]
    },
    {
        "code": "MS12",
        "name": "Angle relationships & polygon properties",
        "tier": 7,
        "section": "Math",
        "prerequisites": [
            "MS01"
        ]
    },
    {
        "code": "QC09",
        "name": "Angle & Segment Relations",
        "tier": 7,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS12"
        ]
    },
    {
        "code": "MS13",
        "name": "Perimeter, area & circumference of 2-D shapes",
        "tier": 7,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS12"
        ]
    },
    {
        "code": "QC11",
        "name": "Area & Perimeter Reasoning",
        "tier": 7,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS12",
            "MS13"
        ]
    },
    {
        "code": "QC12",
        "name": "Circle Measures",
        "tier": 7,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS05",
            "MS13"
        ]
    },
    {
        "code": "QC10",
        "name": "Similar Figures & Scale",
        "tier": 7,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS06",
            "MS12"
        ]
    },
    {
        "code": "MS14",
        "name": "Surface area & volume of 3-D solids",
        "tier": 7,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS13"
        ]
    },
    {
        "code": "QC16",
        "name": "Volume & Surface Area",
        "tier": 7,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS13",
            "MS14"
        ]
    },
    {
        "code": "MS16",
        "name": "Measurement units, tools & conversions",
        "tier": 8,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS05"
        ]
    },
    {
        "code": "QC14",
        "name": "Unit Conversion",
        "tier": 8,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS05",
            "MS16"
        ]
    },
    {
        "code": "QC15",
        "name": "Rate/Time/Distance & Density",
        "tier": 8,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS05",
            "MS06"
        ]
    },
    {
        "code": "MS17",
        "name": "Data representation & statistics",
        "tier": 9,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS05"
        ]
    },
    {
        "code": "QC17",
        "name": "Data Displays & Central Tendency",
        "tier": 9,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS05",
            "MS17"
        ]
    },
    {
        "code": "MS18",
        "name": "Probability of simple & compound events",
        "tier": 9,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS05"
        ]
    },
    {
        "code": "QC18",
        "name": "Probability Comparisons",
        "tier": 9,
        "section": "Math",
        "prerequisites": [
            "MS01",
            "MS04",
            "MS05",
            "MS18"
        ]
    }
]

# A lookup dictionary for prerequisites
TOPIC_PREREQUISITES = {topic['code']: topic.get('prerequisites', []) for topic in COMPLETE_LEARNING_FLOW}

# A lookup dictionary for topic names
TOPIC_NAMES = {topic['code']: topic.get('name', '') for topic in COMPLETE_LEARNING_FLOW}
