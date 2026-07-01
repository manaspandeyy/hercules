"""User-defined leaderboard standings.

The board is fully optional and lives in the user's data (goals["leaderboard"]),
so anyone can add the people (or targets) they're competing with and edit their
points anytime from the Leaderboard tab. Your own row's points are kept live
from DSA check-ins via DataManager (goals["points_current"]).

Nothing here is hard-coded to any one person — a fresh install starts with an
empty board and just your own row.
"""

# A brand-new install seeds this (empty). Add competitors in-app.
DEFAULT_COMPETITORS = []          # e.g. [{"name": "Alex", "points": 3000}]
DEFAULT_COMPETITOR_RATE = 0       # assumed points/day competitors gain (0 = static)


def _you_name(dm):
    name = (dm.settings.get("name") or "").strip()
    return f"{name} (You)" if name else "You"


def board_competitors(dm):
    """Return the saved competitor rows (list of {name, points}), sorted high→low."""
    rows = [dict(r) for r in dm.goals.get("leaderboard", [])]
    rows.sort(key=lambda r: r.get("points", 0), reverse=True)
    return rows


def board_with_you(dm):
    """Return the full board (competitors + your live row), each flagged you=True/False."""
    rows = []
    for r in board_competitors(dm):
        rows.append({"name": r.get("name", "—"),
                     "points": r.get("points", 0), "you": False})
    rows.append({"name": _you_name(dm),
                 "points": dm.goals.get("points_current", 0), "you": True})
    return rows


def rank1_points(dm):
    """Points held by the current #1. Falls back to your target when no competitors."""
    comps = board_competitors(dm)
    if comps:
        return max(r.get("points", 0) for r in comps)
    return dm.goals.get("points_target", 0)


def competitor_rate(dm):
    """Assumed daily points the leaders keep adding (used for projections)."""
    return dm.goals.get("competitor_rate", DEFAULT_COMPETITOR_RATE)
