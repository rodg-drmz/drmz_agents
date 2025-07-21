# 🚦 classifier.py
# Improved: More flexible file classifier for syllabus vs assignment

def classify_file_type(text: str) -> str:
    """
    Classify a document's type based on common educational phrases.

    Returns:
        "syllabus" | "assignment" | "unknown"
    """
    lower = text.lower()

    syllabus_markers = [
        "student learning outcome", "course description", "grading policy",
        "academic integrity", "class schedule", "office hours", "required texts",
        "withdrawal policy", "institutional learning outcomes"
    ]

    assignment_markers = [
        "submit your work", "assignment instructions", "grading rubric", "final draft",
        "write a paper", "write an essay", "develop a project", "due date",
        "you are expected to", "you will write", "complete the following", 
        "respond to the following", "your task is to", "analyze the following", 
        "assignment overview", "turnitin", "word count", "rubric", "peer review"
    ]

    if any(phrase in lower for phrase in syllabus_markers):
        return "syllabus"
    elif any(phrase in lower for phrase in assignment_markers):
        return "assignment"
    elif len(lower) > 1000:
        # Fallback: assume longer documents are likely assignments
        return "assignment"
    else:
        return "unknown"
