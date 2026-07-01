"""Best-effort parsing of a progress report (PDF/image) + recommendations.

PDFs are scanned for common period metrics (assignments / assessments /
lectures / average assessment score) with regex via pdfplumber. Images can't
be read without OCR, so the view always lets the user confirm/edit the numbers
— the parser just pre-fills what it can find. Works with any report that uses
those words; otherwise just type the numbers in.
"""

import os
import re


def _num(pattern, text, cast=int, default=None):
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return default
    try:
        return cast(m.group(1))
    except (ValueError, IndexError):
        return default


def extract_from_pdf(path):
    """Return a dict of any metrics found in the PDF. Zero-ish on failure."""
    result = {
        "assignments": 0, "assessments": 0, "lectures": 0, "avg_score": 0.0,
        "time_spent": "", "topics": [], "weak_areas": [], "strong_areas": [],
    }
    try:
        import pdfplumber
    except ImportError:
        return result
    try:
        parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        text = "\n".join(parts)
    except Exception:
        return result

    result["assignments"] = _num(r"assignment[s]?\D*?(\d+)", text, int, 0)
    result["assessments"] = _num(r"assessment[s]?\D*?(\d+)", text, int, 0)
    result["lectures"] = _num(r"lecture[s]?\D*?(\d+)", text, int, 0)
    result["avg_score"] = _num(r"(?:average|avg)[^\d]*?([\d.]+)\s*%?", text, float, 0.0)
    tm = re.search(r"time\s*(?:spent)?[:\s]*([\d.]+\s*(?:h|hr|hrs|hours|min|mins))",
                   text, re.IGNORECASE)
    if tm:
        result["time_spent"] = tm.group(1).strip()
    return result


def generate_recommendations(report, previous=None, course_units=None):
    """Specific, action-oriented coaching from a report (+ optional prior one
    and current course state)."""
    tips = []

    # period-over-period deltas
    if previous:
        d_assign = report.get("assignments", 0) - previous.get("assignments", 0)
        if d_assign < 0:
            tips.append(f"Assignment volume dropped {abs(d_assign)} this period — "
                        f"add 30 min extra DSA/practice daily to recover.")
        elif d_assign > 0:
            tips.append(f"Assignments up {d_assign} vs last period — strong momentum, "
                        f"keep the daily block sacred.")
        d_score = report.get("avg_score", 0) - previous.get("avg_score", 0)
        if d_score < -3:
            tips.append(f"Average assessment score fell {abs(d_score):.0f}% — slow down "
                        f"and revise weak topics before the next assessment.")
        elif d_score > 3:
            tips.append(f"Average score improved {d_score:.0f}% — the revision is working.")

    # absolute signals
    avg = report.get("avg_score", 0) or 0
    if avg and avg < 60:
        tips.append(f"Average assessment score is {avg:.0f}% (below the 60% pass bar) — "
                    f"prioritise revision over new lectures this week.")
    if (report.get("lectures", 0) or 0) < 5:
        tips.append(f"Only {report.get('lectures', 0)} lectures watched in the period — "
                    f"protect your study block to keep the course on schedule.")

    # course-state awareness — surface the first unit that hasn't been started
    if course_units:
        for u in course_units:
            if u.get("lectures_total") and u.get("lectures_done", 0) == 0:
                tips.append(f"“{u['name']}” hasn't been started yet — "
                            f"begin it this week to stay on schedule.")
                break

    # weak areas
    weak = report.get("weak_areas") or []
    if weak:
        tips.append(f"You're weak on {' and '.join(weak[:2])} — add 2 extra "
                    f"{weak[0]} questions daily this week.")

    if not tips:
        tips.append("Balanced, steady performance — keep the rhythm and gradually "
                    "shift toward medium/hard problems.")
    return tips


def is_pdf(path):
    return os.path.splitext(path)[1].lower() == ".pdf"


def is_image(path):
    return os.path.splitext(path)[1].lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
