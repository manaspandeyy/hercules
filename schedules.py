"""User-editable daily schedules.

The schedule is no longer hard-coded — each day of the week has its own plan,
stored in ``data/schedules.json`` and edited from Settings → Daily Schedule
(or Schedule tab). A fresh install is seeded with the generic template below,
which the user is meant to replace with their own routine.

Each plan is a list of ``{"time": "7:00 AM", "task": "..."}`` entries.
``get_schedule_for_date(date)`` returns ``(weekday_label, plan)`` for any date.
"""

import json
import os
from datetime import date

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_SCHED_PATH = os.path.join(_DATA_DIR, "schedules.json")

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday",
        "saturday", "sunday"]
DAY_LABELS = {d: d.capitalize() for d in DAYS}

# ---- generic starter template (edit in-app) -----------------------------
_DEFAULT_WEEKDAY = [
    {"time": "7:00 AM", "task": "Wake up & morning routine"},
    {"time": "7:30 AM", "task": "Exercise / workout (1 hr)"},
    {"time": "8:30 AM", "task": "Breakfast"},
    {"time": "9:00 AM", "task": "Deep work / study block 1 (2 hrs)"},
    {"time": "11:00 AM", "task": "Short break"},
    {"time": "11:30 AM", "task": "Deep work / study block 2 (1.5 hrs)"},
    {"time": "1:00 PM", "task": "Lunch & rest"},
    {"time": "2:00 PM", "task": "Learning / course (2 hrs)"},
    {"time": "4:00 PM", "task": "Focused project work (2 hrs)"},
    {"time": "6:00 PM", "task": "Walk / exercise"},
    {"time": "7:00 PM", "task": "Dinner"},
    {"time": "8:00 PM", "task": "Reading / personal project (1.5 hrs)"},
    {"time": "10:00 PM", "task": "Wind down"},
    {"time": "10:30 PM", "task": "Sleep"},
]

_DEFAULT_WEEKEND = [
    {"time": "8:00 AM", "task": "Wake up & morning routine"},
    {"time": "8:30 AM", "task": "Exercise / workout (1 hr)"},
    {"time": "9:30 AM", "task": "Breakfast"},
    {"time": "10:00 AM", "task": "Study / catch-up block (2 hrs)"},
    {"time": "12:00 PM", "task": "Free time"},
    {"time": "1:00 PM", "task": "Lunch"},
    {"time": "2:00 PM", "task": "Personal project / hobby (2 hrs)"},
    {"time": "4:00 PM", "task": "Rest & recharge"},
    {"time": "6:00 PM", "task": "Walk / social time"},
    {"time": "7:30 PM", "task": "Dinner"},
    {"time": "9:00 PM", "task": "Plan the week / reflect"},
    {"time": "11:00 PM", "task": "Sleep"},
]


def default_schedules():
    """A fresh weekly template: Mon–Fri weekday plan, Sat/Sun weekend plan."""
    out = {}
    for d in DAYS:
        base = _DEFAULT_WEEKEND if d in ("saturday", "sunday") else _DEFAULT_WEEKDAY
        out[d] = [dict(item) for item in base]
    return out


# ---- persistence --------------------------------------------------------

def load_schedules():
    """Return the full weekly dict, seeding the file on first run."""
    try:
        with open(_SCHED_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = default_schedules()
        save_schedules(data)
        return data
    # make sure every weekday exists (in case the file is partial)
    changed = False
    for d in DAYS:
        if d not in data or not isinstance(data[d], list):
            data[d] = default_schedules()[d]
            changed = True
    if changed:
        save_schedules(data)
    return data


def save_schedules(data):
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_SCHED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---- lookup -------------------------------------------------------------

def get_schedule_for_date(d):
    """Return ``(weekday_label, plan)`` for a given ``datetime.date``."""
    dayname = DAYS[d.weekday()]
    plan = load_schedules().get(dayname, [])
    return DAY_LABELS[dayname], plan
