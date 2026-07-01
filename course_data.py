"""Example course/goal structure used to seed goals.json on first run.

These are generic placeholder modules — rename them, change the counts, or add
and delete units right inside the app (Goals & Course tab). Once seeded, the
user's edited numbers live in goals.json and this file is only a fallback.
"""

from datetime import date

# Each unit: done/total for assignments, assessments, lectures.
# Replace these with your own course modules, project milestones, or goals.
COURSE_UNITS = [
    {"name": "Module 1 — Fundamentals",
     "assignments_done": 0, "assignments_total": 20,
     "assessments_done": 0, "assessments_total": 2,
     "lectures_done": 0, "lectures_total": 10},
    {"name": "Module 2 — Core Skills",
     "assignments_done": 0, "assignments_total": 25,
     "assessments_done": 0, "assessments_total": 3,
     "lectures_done": 0, "lectures_total": 12},
    {"name": "Module 3 — Advanced Topics",
     "assignments_done": 0, "assignments_total": 20,
     "assessments_done": 0, "assessments_total": 3,
     "lectures_done": 0, "lectures_total": 10},
]

# Pre-loaded practice tests (rename / edit in the Mocks tab).
DEFAULT_MOCKS = [
    {"name": "Practice Test 1", "attempted": False, "date": None,
     "score": 0, "total": 0, "notes": ""},
    {"name": "Practice Test 2", "attempted": False, "date": None,
     "score": 0, "total": 0, "notes": ""},
    {"name": "Mid-course Mock", "attempted": False, "date": None,
     "score": 0, "total": 0, "notes": ""},
    {"name": "Final Mock", "attempted": False, "date": None,
     "score": 0, "total": 0, "notes": ""},
]

# Default course completion target: end of the current year (edit in Settings).
TARGET_DATE = date(date.today().year, 12, 31).isoformat()

# Rough time budget per item (minutes) used by the completion planner.
ITEM_MINUTES = {"lecture": 20, "assignment": 12, "assessment": 25}
DEFAULT_STUDY_MINUTES_PER_DAY = 120  # 2 hours
