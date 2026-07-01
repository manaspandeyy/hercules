"""Local JSON persistence for the Hercules tracker.

Everything lives in a ``data/`` folder next to this file:
  - daily_log.json : per-date schedule check-offs, DSA session, study session
  - goals.json     : course units, leaderboard points + competitors, study settings
  - mocks.json     : mock/practice test attempts
  - sunday.json    : weekly self-assessment entries
  - schedules.json : the per-weekday schedule (see schedules.py)
  - reports.json   : uploaded progress reports
  - settings.json  : UI preferences (theme, name, etc.)

No database, no network. Pure local files so the app is fully portable.
"""

import json
import os
import shutil
from datetime import date, datetime, timedelta
from collections import Counter

import course_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

DAILY_LOG = os.path.join(DATA_DIR, "daily_log.json")
GOALS = os.path.join(DATA_DIR, "goals.json")
MOCKS = os.path.join(DATA_DIR, "mocks.json")
SUNDAY = os.path.join(DATA_DIR, "sunday.json")
REPORTS = os.path.join(DATA_DIR, "reports.json")
SETTINGS = os.path.join(DATA_DIR, "settings.json")

DSA_VALUES = {"0": 0, "1-2": 2, "3-4": 4, "5-6": 6, "7+": 7}
DSA_POINTS = {"easy": 30, "medium": 40, "hard": 50}

DEFAULT_GOALS = {
    "course_units": [],          # seeded from course_data on first run
    "leaderboard": [],           # user-defined competitors [{name, points}]
    "competitor_rate": 0,        # assumed pts/day the leaders gain (for projections)
    "points_start": 0,
    "points_current": 0,
    "points_target": 5000,
    "points_history": [],
    "study_minutes_per_day": course_data.DEFAULT_STUDY_MINUTES_PER_DAY,
    "target_date": course_data.TARGET_DATE,
    "interviews": 0,
    "offers": 0,
}

DEFAULT_SETTINGS = {"theme": "dark"}


def _read(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return json.loads(json.dumps(default))


def _write(path, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def today_key():
    return date.today().isoformat()


def _copy(obj):
    return json.loads(json.dumps(obj))


class DataManager:
    def __init__(self):
        self._version = 0   # incremented on every write; used by Metrics cache
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(REPORTS_DIR, exist_ok=True)
        self.log = _read(DAILY_LOG, {})
        self.goals = {**DEFAULT_GOALS, **_read(GOALS, {})}
        self.mocks = _read(MOCKS, None)
        self.sunday = _read(SUNDAY, [])
        self.reports = _read(REPORTS, [])
        self.settings = {**DEFAULT_SETTINGS, **_read(SETTINGS, {})}

        # Seed course units + mocks the first time.
        if not self.goals.get("course_units"):
            self.goals["course_units"] = _copy(course_data.COURSE_UNITS)
            self.save_goals()
        if not self.mocks:
            self.mocks = _copy(course_data.DEFAULT_MOCKS)
            self.save_mocks()
        if not self.goals["points_history"]:
            self.goals["points_history"] = [
                {"date": today_key(), "points": self.goals["points_current"]}]
            self.save_goals()

    # ---- file writers ----------------------------------------------------
    def save_log(self):
        _write(DAILY_LOG, self.log)
        self._version += 1

    def save_goals(self):
        _write(GOALS, self.goals)
        self._version += 1

    def save_mocks(self):
        _write(MOCKS, self.mocks)
        self._version += 1

    def save_sunday(self):
        _write(SUNDAY, self.sunday)
        self._version += 1

    def save_reports(self):
        _write(REPORTS, self.reports)
        self._version += 1

    def save_settings(self):
        _write(SETTINGS, self.settings)
        self._version += 1

    # ---- daily log -------------------------------------------------------
    def _day(self, key):
        return self.log.setdefault(key, {"tasks": {}})

    def get_tasks(self, key=None):
        return self._day(key or today_key()).get("tasks", {})

    def set_task(self, index, done, key=None):
        self._day(key or today_key()).setdefault("tasks", {})[str(index)] = bool(done)
        self.save_log()

    # ---- DSA session -----------------------------------------------------
    def get_dsa_detail(self, key=None):
        return self._day(key or today_key()).get("dsa_detail",
                                                 {"easy": 0, "medium": 0, "hard": 0})

    def set_dsa_session(self, easy, medium, hard, unit_index=None, key=None):
        key = key or today_key()
        day = self._day(key)
        pts = easy * DSA_POINTS["easy"] + medium * DSA_POINTS["medium"] + hard * DSA_POINTS["hard"]
        old_pts = day.get("dsa_points", 0)
        old_detail = day.get("dsa_detail", {})
        old_unit_idx = old_detail.get("unit_index")
        old_q = (old_detail.get("easy", 0) + old_detail.get("medium", 0)
                 + old_detail.get("hard", 0))

        day["dsa_detail"] = {"easy": easy, "medium": medium, "hard": hard}
        if unit_index is not None:
            day["dsa_detail"]["unit_index"] = unit_index
        day["dsa_points"] = pts
        self.goals["points_current"] += (pts - old_pts)

        units = self.goals.get("course_units", [])
        # undo previous unit contribution (re-edit)
        if old_unit_idx is not None and 0 <= old_unit_idx < len(units):
            u = units[old_unit_idx]
            u["assignments_done"] = max(0, u["assignments_done"] - old_q)

        # apply new unit contribution (capped at remaining capacity)
        new_q = easy + medium + hard
        if unit_index is not None and 0 <= unit_index < len(units):
            u = units[unit_index]
            cap = u["assignments_total"] - u["assignments_done"]
            u["assignments_done"] += min(new_q, max(0, cap))

        self._record_points()
        self.save_log()
        self.save_goals()
        return pts

    # ---- study session (cascades lectures into course units) ------------
    def get_study_detail(self, key=None):
        return self._day(key or today_key()).get("study", {"lectures": 0, "feel": "Okay"})

    def set_study_session(self, lectures, feel, key=None):
        key = key or today_key()
        day = self._day(key)
        old = day.get("study", {}).get("lectures", 0)
        day["study"] = {"lectures": lectures, "feel": feel}
        self._adjust_unit_lectures(lectures - old)
        self.save_log()
        self.save_goals()

    def _adjust_unit_lectures(self, delta):
        units = self.goals["course_units"]
        if delta > 0:
            for u in units:
                cap = u["lectures_total"] - u["lectures_done"]
                take = min(delta, max(0, cap))
                u["lectures_done"] += take
                delta -= take
                if delta <= 0:
                    break
        elif delta < 0:
            delta = -delta
            for u in reversed(units):
                take = min(delta, u["lectures_done"])
                u["lectures_done"] -= take
                delta -= take
                if delta <= 0:
                    break

    # ---- course totals ---------------------------------------------------
    def course_totals(self):
        units = self.goals["course_units"]
        out = {}
        for kind in ("assignments", "assessments", "lectures"):
            done = sum(u[f"{kind}_done"] for u in units)
            total = sum(u[f"{kind}_total"] for u in units)
            out[kind] = (done, total)
        return out

    def update_unit(self, index, field, value):
        try:
            self.goals["course_units"][index][field] = max(0, int(value))
        except (ValueError, IndexError):
            return
        u = self.goals["course_units"][index]
        # keep done within total
        for kind in ("assignments", "assessments", "lectures"):
            u[f"{kind}_done"] = min(u[f"{kind}_done"], u[f"{kind}_total"])
        self.save_goals()

    def add_unit(self, name="New unit"):
        """Append a blank course unit and persist. Returns its index."""
        self.goals["course_units"].append({
            "name": name,
            "assignments_done": 0, "assignments_total": 0,
            "assessments_done": 0, "assessments_total": 0,
            "lectures_done": 0, "lectures_total": 0,
        })
        self.save_goals()
        return len(self.goals["course_units"]) - 1

    def delete_unit(self, index):
        units = self.goals["course_units"]
        if 0 <= index < len(units):
            units.pop(index)
            self.save_goals()

    def rename_unit(self, index, name):
        units = self.goals["course_units"]
        if 0 <= index < len(units):
            units[index]["name"] = name.strip() or units[index]["name"]
            self.save_goals()

    # ---- leaderboard points ---------------------------------------------
    def _record_points(self):
        h = self.goals["points_history"]
        tk = today_key()
        if h and h[-1]["date"] == tk:
            h[-1]["points"] = self.goals["points_current"]
        else:
            h.append({"date": tk, "points": self.goals["points_current"]})

    def update_points(self, points):
        self.goals["points_current"] = int(points)
        self._record_points()
        self.save_goals()

    def daily_avg_points(self):
        h = self.goals["points_history"]
        if len(h) < 2:
            return None
        days = (datetime.fromisoformat(h[-1]["date"]).date()
                - datetime.fromisoformat(h[0]["date"]).date()).days
        gained = h[-1]["points"] - h[0]["points"]
        if days <= 0 or gained <= 0:
            return None
        return gained / days

    def points_eta_days(self):
        rate = self.daily_avg_points()
        if not rate:
            return None
        remaining = self.goals["points_target"] - self.goals["points_current"]
        return 0 if remaining <= 0 else max(1, round(remaining / rate))

    def points_growth(self):
        h = self.goals["points_history"]
        return ([datetime.fromisoformat(x["date"]).strftime("%b %d") for x in h],
                [x["points"] for x in h])

    # ---- mocks -----------------------------------------------------------
    def update_mock(self, index, attempted, date_str, score, total, notes):
        m = self.mocks[index]
        m.update({"attempted": attempted, "date": date_str,
                  "score": score, "total": total, "notes": notes})
        self.save_mocks()

    def mock_scores(self):
        """Return attempted mocks as (name, pct, date) sorted by date."""
        rows = []
        for m in self.mocks:
            if m.get("attempted") and m.get("total"):
                pct = m["score"] / m["total"] * 100
                rows.append((m["name"], pct, m.get("date") or ""))
        rows.sort(key=lambda r: r[2])
        return rows

    # ---- Sunday assessments ---------------------------------------------
    def add_sunday_assessment(self, topic, score, total, difficulty, time_min, notes):
        self.sunday.append({
            "date": today_key(), "topic": topic, "score": score, "total": total,
            "difficulty": difficulty, "time_min": time_min, "notes": notes})
        self.save_sunday()

    def sunday_scores(self):
        rows = sorted(self.sunday, key=lambda a: a["date"])
        labels = [datetime.fromisoformat(a["date"]).strftime("%b %d") for a in rows]
        pcts = [(a["score"] / a["total"] * 100) if a.get("total") else 0 for a in rows]
        return labels, pcts

    def sunday_topic_counts(self):
        c = Counter()
        for a in self.sunday:
            t = (a.get("topic") or "").strip().title()
            if t:
                c[t] += 1
        return c.most_common()

    def sunday_avg_trend(self):
        """Return (avg, direction) where direction is 'up'/'down'/'flat'."""
        _, pcts = self.sunday_scores()
        if not pcts:
            return None, "flat"
        avg = sum(pcts) / len(pcts)
        if len(pcts) < 4:
            return avg, "flat"
        mid = len(pcts) // 2
        first = sum(pcts[:mid]) / mid
        last = sum(pcts[mid:]) / (len(pcts) - mid)
        direction = "up" if last > first + 2 else "down" if last < first - 2 else "flat"
        return avg, direction

    def sunday_streak(self):
        """Consecutive Sundays (ending the most recent past Sunday) with an entry."""
        done = {a["date"] for a in self.sunday}
        # walk back to the most recent Sunday on or before today (Sun == 6)
        d = date.today()
        while d.weekday() != 6:
            d -= timedelta(days=1)
        streak = 0
        while d.isoformat() in done:
            streak += 1
            d -= timedelta(days=7)
        return streak

    # ---- reports ---------------------------------------------------------
    def add_report(self, report, source_path=None):
        if source_path and os.path.exists(source_path):
            os.makedirs(REPORTS_DIR, exist_ok=True)
            ext = os.path.splitext(source_path)[1]
            stored = os.path.join(REPORTS_DIR, f"report_{len(self.reports)+1}{ext}")
            try:
                shutil.copy2(source_path, stored)
                report["stored_file"] = os.path.relpath(stored, BASE_DIR)
            except OSError:
                report["stored_file"] = None
        self.reports.append(report)
        self.save_reports()

    # ---- completion planner ---------------------------------------------
    def _unit_remaining_minutes(self, u):
        m = course_data.ITEM_MINUTES
        return ((u["lectures_total"] - u["lectures_done"]) * m["lecture"]
                + (u["assignments_total"] - u["assignments_done"]) * m["assignment"]
                + (u["assessments_total"] - u["assessments_done"]) * m["assessment"])

    def planner(self):
        """Per-unit + overall completion projection at the configured pace."""
        per_day = max(30, self.goals.get("study_minutes_per_day", 120))
        target = datetime.fromisoformat(self.goals["target_date"]).date()
        cursor = date.today()
        units_out = []
        for u in self.goals["course_units"]:
            rem = self._unit_remaining_minutes(u)
            days = 0 if rem <= 0 else max(1, -(-rem // per_day))  # ceil
            finish = cursor + timedelta(days=days)
            units_out.append({
                "name": u["name"], "days": days,
                "finish": finish, "on_track": finish <= target,
                "done": rem <= 0,
            })
            cursor = finish
        projected = cursor
        days_to_target = (target - date.today()).days
        lec_total = self.course_totals()["lectures"]
        remaining_lec = lec_total[1] - lec_total[0]
        daily_lecture_target = (remaining_lec / days_to_target) if days_to_target > 0 else remaining_lec
        return {
            "units": units_out,
            "projected": projected,
            "target": target,
            "on_track": projected <= target,
            "daily_lecture_target": daily_lecture_target,
            "days_to_target": days_to_target,
        }

    # ---- analytics helpers ----------------------------------------------
    def _last_n_dates(self, n):
        today = date.today()
        return [(today - timedelta(days=i)) for i in range(n - 1, -1, -1)]

    def _task_done_on(self, d, keyword):
        from schedules import get_schedule_for_date
        sched = get_schedule_for_date(d)[1]
        tasks = self.log.get(d.isoformat(), {}).get("tasks", {})
        for i, item in enumerate(sched):
            if keyword in item["task"].lower():
                return tasks.get(str(i), False)
        return False

    def completion_last_7(self):
        from schedules import get_schedule_for_date
        labels, pcts = [], []
        for d in self._last_n_dates(7):
            sched = get_schedule_for_date(d)[1]
            tasks = self.log.get(d.isoformat(), {}).get("tasks", {})
            done = sum(1 for v in tasks.values() if v)
            pcts.append(round(done / len(sched) * 100) if sched else 0)
            labels.append(d.strftime("%a"))
        return labels, pcts

    def completion_frac(self, d):
        """Completion fraction for a date, or None when nothing was logged."""
        from schedules import get_schedule_for_date
        sched = get_schedule_for_date(d)[1]
        tasks = self.log.get(d.isoformat(), {}).get("tasks", {})
        if not tasks:
            return None
        done = sum(1 for v in tasks.values() if v)
        return done / len(sched) if sched else 0

    def dsa_last_30(self):
        labels, vals = [], []
        for d in self._last_n_dates(30):
            day = self.log.get(d.isoformat(), {})
            det = day.get("dsa_detail")
            vals.append((det["easy"] + det["medium"] + det["hard"]) if det else 0)
            labels.append(d.strftime("%d"))
        return labels, vals

    def dsa_points_last_n(self, n=14):
        labels, vals = [], []
        for d in self._last_n_dates(n):
            vals.append(self.log.get(d.isoformat(), {}).get("dsa_points", 0))
            labels.append(d.strftime("%d"))
        return labels, vals

    def lectures_last_30(self):
        labels, vals = [], []
        for d in self._last_n_dates(30):
            vals.append(self.log.get(d.isoformat(), {}).get("study", {}).get("lectures", 0))
            labels.append(d.strftime("%d"))
        return labels, vals

    def jobs_per_week(self, weeks=6):
        """Completed portal/referral tasks per week from the schedule."""
        today = date.today()
        labels, totals = [], []
        for w in range(weeks - 1, -1, -1):
            week_start = today - timedelta(days=7 * w + 6)
            total = 0
            for i in range(7):
                d = week_start + timedelta(days=i)
                from schedules import get_schedule_for_date
                sched = get_schedule_for_date(d)[1]
                tasks = self.log.get(d.isoformat(), {}).get("tasks", {})
                for idx, item in enumerate(sched):
                    t = item["task"].lower()
                    if ("portal" in t or "referral" in t or "job application" in t) and tasks.get(str(idx)):
                        total += 1
            labels.append(week_start.strftime("%b %d"))
            totals.append(total)
        return labels, totals

    # ---- portal applications (counter window) ----------------------------
    def get_portal_session(self, key=None):
        return self._day(key or today_key()).get("portal_apps", {"count": 0, "time_min": 0})

    def set_portal_session(self, count, time_min, key=None):
        self._day(key or today_key())["portal_apps"] = {
            "count": max(0, count), "time_min": max(0, time_min)}
        self.save_log()

    # ---- referral requests -----------------------------------------------
    def get_referral_session(self, key=None):
        return self._day(key or today_key()).get("referrals",
                                                  {"sent": 0, "responses": 0, "notes": ""})

    def set_referral_session(self, sent, responses, notes="", key=None):
        self._day(key or today_key())["referrals"] = {
            "sent": max(0, sent), "responses": max(0, responses),
            "notes": str(notes).strip()}
        self.save_log()

    # ---- cold emails -------------------------------------------------------
    def get_cold_email_session(self, key=None):
        return self._day(key or today_key()).get("cold_emails",
                                                  {"sent": 0, "source": "Telegram",
                                                   "replies": 0, "notes": ""})

    def set_cold_email_session(self, sent, source, replies, notes="", key=None):
        self._day(key or today_key())["cold_emails"] = {
            "sent": max(0, sent), "source": str(source),
            "replies": max(0, replies), "notes": str(notes).strip()}
        self.save_log()

    # ---- interviews & offers (funnel, updated manually) ------------------
    def update_interviews_offers(self, interviews, offers):
        self.goals["interviews"] = max(0, int(interviews))
        self.goals["offers"] = max(0, int(offers))
        self.save_goals()

    # ---- job hunt analytics series ---------------------------------------
    def portal_apps_last_n(self, n=30):
        days = self._last_n_dates(n)
        labels = [d.strftime("%d") for d in days]
        vals = [self.log.get(d.isoformat(), {}).get("portal_apps", {}).get("count", 0)
                for d in days]
        return labels, vals

    def referrals_last_n(self, n=30):
        days = self._last_n_dates(n)
        labels = [d.strftime("%d") for d in days]
        sent = [self.log.get(d.isoformat(), {}).get("referrals", {}).get("sent", 0)
                for d in days]
        responses = [self.log.get(d.isoformat(), {}).get("referrals", {}).get("responses", 0)
                     for d in days]
        return labels, sent, responses

    def cold_emails_last_n(self, n=30):
        days = self._last_n_dates(n)
        labels = [d.strftime("%d") for d in days]
        sent = [self.log.get(d.isoformat(), {}).get("cold_emails", {}).get("sent", 0)
                for d in days]
        replies = [self.log.get(d.isoformat(), {}).get("cold_emails", {}).get("replies", 0)
                   for d in days]
        return labels, sent, replies

    def weekly_completion_rate(self, weeks=6):
        """Average daily schedule-completion % per week."""
        today = date.today()
        labels, rates = [], []
        for w in range(weeks - 1, -1, -1):
            week_start = today - timedelta(days=7 * w + 6)
            fracs = []
            for i in range(7):
                d = week_start + timedelta(days=i)
                f = self.completion_frac(d)
                if f is not None:
                    fracs.append(f)
            rates.append(round(sum(fracs) / len(fracs) * 100) if fracs else 0)
            labels.append(week_start.strftime("%b %d"))
        return labels, rates

    def unit_progress(self):
        """Per-unit overall % (across all item types) for the comparison chart."""
        names, pcts = [], []
        for u in self.goals["course_units"]:
            done = u["assignments_done"] + u["assessments_done"] + u["lectures_done"]
            total = u["assignments_total"] + u["assessments_total"] + u["lectures_total"]
            pcts.append(round(done / total * 100) if total else 0)
            names.append(u["name"])
        return names, pcts

    def activity_grid(self, weeks=14):
        """Return list of (date, frac_or_None) for the last `weeks` weeks,
        aligned so each row of 7 starts on Monday."""
        today = date.today()
        # end on the Sunday of this week so columns are full weeks
        end = today + timedelta(days=(6 - today.weekday()))
        start = end - timedelta(days=weeks * 7 - 1)
        cells = []
        d = start
        while d <= end:
            frac = None if d > today else self.completion_frac(d)
            cells.append((d, frac))
            d += timedelta(days=1)
        return cells

    # ---- streaks (derived from schedule task check-offs) ----------------
    def _streak(self, predicate):
        streak = 0
        d = date.today()
        if not self.log.get(d.isoformat(), {}).get("tasks"):
            d -= timedelta(days=1)
        while True:
            if d.isoformat() not in self.log or not predicate(d):
                break
            streak += 1
            d -= timedelta(days=1)
        return streak

    def gym_streak(self):
        return self._streak(lambda d: self._task_done_on(d, "gym"))

    def badminton_streak(self):
        return self._streak(lambda d: self._task_done_on(d, "badminton"))

    def dsa_streak(self):
        def did(d):
            det = self.log.get(d.isoformat(), {}).get("dsa_detail")
            if det:
                return (det["easy"] + det["medium"] + det["hard"]) > 0
            return self._task_done_on(d, "dsa")
        return self._streak(did)

    def daily_streak(self):
        """Consecutive days where at least 50% of tasks were completed."""
        def half_done(d):
            tasks = self.log.get(d.isoformat(), {}).get("tasks", {})
            if not tasks:
                return False
            done = sum(1 for v in tasks.values() if v)
            return done / max(1, len(tasks)) >= 0.5
        return self._streak(half_done)
