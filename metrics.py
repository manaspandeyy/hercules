"""Analytics engine for Hercules.

A thin computation layer over DataManager that produces all the aggregated
series the advanced analytics tabs need: per-day metrics, weekly/monthly
roll-ups, habit streaks, the daily "Momentum Score", day-of-week analysis,
period comparison, leaderboard projection, unit priority, and insights.

Nothing here draws — views consume these plain numbers.
"""

from datetime import date, datetime, timedelta
from calendar import monthrange

import leaderboard_data as lb

DSA_TARGET = 7          # questions/day for full DSA score
LECTURE_TARGET = 3      # lectures/day for full lecture score

# The six tracked habits and the schedule keyword that marks each done.
HABITS = [
    ("Gym", "gym"),
    ("DSA", "dsa"),
    ("Course", "course"),
    ("Badminton", "badminton"),
    ("Job Apps", "portal"),        # matches "Portal Applications" task
    ("Cold Emails", "cold email"), # matches "HR Cold Emails" task
]


def _d(iso):
    return datetime.fromisoformat(iso).date()


class Metrics:
    def __init__(self, dm):
        self.dm = dm
        self._cache = {}
        self._cache_ver = -1

    def _invalidate_if_stale(self):
        if self.dm._version != self._cache_ver:
            self._cache = {}
            self._cache_ver = self.dm._version

    def _cached(self, key, fn):
        self._invalidate_if_stale()
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    # ---- primitive per-day numbers --------------------------------------
    def dsa_count(self, d):
        det = self.dm.log.get(d.isoformat(), {}).get("dsa_detail")
        return (det["easy"] + det["medium"] + det["hard"]) if det else 0

    def lectures(self, d):
        return self.dm.log.get(d.isoformat(), {}).get("study", {}).get("lectures", 0)

    def points(self, d):
        return self.dm.log.get(d.isoformat(), {}).get("dsa_points", 0)

    def portal_count(self, d):
        """Portal applications submitted (from counter session log)."""
        return self.dm.log.get(d.isoformat(), {}).get("portal_apps", {}).get("count", 0)

    def referrals_sent(self, d):
        return self.dm.log.get(d.isoformat(), {}).get("referrals", {}).get("sent", 0)

    def cold_emails_sent(self, d):
        return self.dm.log.get(d.isoformat(), {}).get("cold_emails", {}).get("sent", 0)

    def job_apps(self, d):
        """Checks portal + referral task completion from the schedule (0-2 per day)."""
        from schedules import get_schedule_for_date
        sched = get_schedule_for_date(d)[1]
        tasks = self.dm.log.get(d.isoformat(), {}).get("tasks", {})
        return sum(1 for i, it in enumerate(sched)
                   if ("portal" in it["task"].lower() or "referral" in it["task"].lower()
                       or "job application" in it["task"].lower())
                   and tasks.get(str(i)))

    def completion(self, d):
        f = self.dm.completion_frac(d)
        return 0.0 if f is None else f

    def habit_done(self, d, keyword):
        if keyword == "dsa":
            return self.dsa_count(d) > 0 or self.dm._task_done_on(d, "dsa")
        if keyword == "course":
            return self.lectures(d) > 0
        if keyword in ("portal", "job application"):
            return self.job_apps(d) > 0 or self.portal_count(d) > 0
        return self.dm._task_done_on(d, keyword)

    def day(self, d):
        return self._cached(f"day_{d.isoformat()}", lambda: self._day_impl(d))

    def _day_impl(self, d):
        return {
            "completion": self.completion(d),
            "dsa": self.dsa_count(d),
            "lectures": self.lectures(d),
            "points": self.points(d),
            "jobs": self.job_apps(d),
            "gym": 1 if self.habit_done(d, "gym") else 0,
            "badminton": 1 if self.habit_done(d, "badminton") else 0,
            "cold": 1 if self.habit_done(d, "cold email") else 0,
            "portal": self.portal_count(d),
            "referrals": self.referrals_sent(d),
            "cold_sent": self.cold_emails_sent(d),
            "cold_replies": self.dm.log.get(d.isoformat(), {}).get(
                "cold_emails", {}).get("replies", 0),
            "referral_responses": self.dm.log.get(d.isoformat(), {}).get(
                "referrals", {}).get("responses", 0),
        }

    # ---- Momentum Score --------------------------------------------------
    def day_score(self, d):
        day = self.day(d)
        score = 30 * day["completion"]
        score += 20 * min(1.0, day["dsa"] / DSA_TARGET)
        score += 20 * min(1.0, day["lectures"] / LECTURE_TARGET)
        score += 10 if day["gym"] else 0
        score += 10 * min(1.0, day["jobs"] / 2)
        score += 10 if day["cold"] else 0
        return round(score)

    def score_history(self, n=30):
        days = [date.today() - timedelta(days=i) for i in range(n - 1, -1, -1)]
        return [d.strftime("%d") for d in days], [self.day_score(d) for d in days]

    def score_stats(self, n=30):
        days = [date.today() - timedelta(days=i) for i in range(n)]
        logged = [(d, self.day_score(d)) for d in days
                  if self.dm.log.get(d.isoformat())]
        if not logged:
            return None
        best = max(logged, key=lambda x: x[1])
        worst = min(logged, key=lambda x: x[1])
        avg = sum(s for _, s in logged) / len(logged)
        return {"best": best, "worst": worst, "avg": avg, "today": self.day_score(date.today())}

    # ---- series ----------------------------------------------------------
    def series(self, key, n=30):
        days = [date.today() - timedelta(days=i) for i in range(n - 1, -1, -1)]
        return [d.strftime("%d") for d in days], [self.day(d)[key] for d in days]

    def cumulative_points(self):
        """Running leaderboard total from the earliest logged day to today."""
        start = self.dm.goals["points_start"]
        first = date.today() - timedelta(days=29)
        if self.dm.log:
            try:
                first = min(_d(k) for k in self.dm.log)
            except ValueError:
                pass
        days, vals, run = [], [], start
        d = first
        while d <= date.today():
            run += self.points(d)
            days.append(d.strftime("%b %d"))
            vals.append(run)
            d += timedelta(days=1)
        return days, vals

    # ---- weeks / months --------------------------------------------------
    def last_weeks(self, n=4):
        """Return [(label, start, end)] for the last n Mon-Sun weeks."""
        today = date.today()
        this_mon = today - timedelta(days=today.weekday())
        out = []
        for i in range(n - 1, -1, -1):
            start = this_mon - timedelta(days=7 * i)
            end = start + timedelta(days=6)
            out.append((f"Week {n - i}", start, end))
        return out

    def range_metrics(self, start, end):
        k = f"range_{start.isoformat()}_{end.isoformat()}"
        return self._cached(k, lambda: self._range_impl(start, end))

    def _range_impl(self, start, end):
        agg = {"dsa": 0, "lectures": 0, "jobs": 0, "points": 0,
               "gym": 0, "badminton": 0, "cold": 0, "completion": 0.0,
               "portal": 0, "referrals": 0, "cold_sent": 0}
        days = 0
        d = start
        while d <= end:
            m = self.day(d)
            for key in ("dsa", "lectures", "jobs", "points", "gym",
                        "badminton", "cold", "portal", "referrals", "cold_sent"):
                agg[key] += m[key]
            agg["completion"] += m["completion"]
            days += 1
            d += timedelta(days=1)
        agg["completion"] = round(agg["completion"] / days * 100) if days else 0
        agg["assignments"] = agg["dsa"]
        return agg

    def months(self, n=4):
        """The last `n` months (oldest first), ending with the current month."""
        today = date.today()
        base = []
        y, m = today.year, today.month
        for _ in range(n):
            base.append((y, m))
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        base.reverse()
        return [(datetime(yy, mm, 1).strftime("%b"), yy, mm) for yy, mm in base]

    def month_metrics(self, year, month):
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
        return self.range_metrics(start, end)

    # ---- habits ----------------------------------------------------------
    def contribution(self, keyword, days=365):
        """List of (date, intensity 0..1) for the last `days` days."""
        return self._cached(f"contrib_{keyword}_{days}", lambda: self._contrib_impl(keyword, days))

    def _contrib_impl(self, keyword, days):
        out = []
        today = date.today()
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            if keyword == "dsa":
                inten = min(1.0, self.dsa_count(d) / DSA_TARGET)
                if inten == 0 and self.dm._task_done_on(d, "dsa"):
                    inten = 0.5
            elif keyword == "course":
                inten = min(1.0, self.lectures(d) / LECTURE_TARGET)
            elif keyword in ("portal", "job application"):
                inten = min(1.0, (self.portal_count(d) + self.job_apps(d)) / 2)
            else:
                inten = 1.0 if self.dm._task_done_on(d, keyword) else 0.0
            out.append((d, inten))
        return out

    def streaks(self, keyword):
        """(current_streak, longest_streak) of consecutive days the habit was done."""
        today = date.today()
        cur = longest = run = 0
        # scan last 365 days oldest→newest for longest
        days = [today - timedelta(days=i) for i in range(364, -1, -1)]
        for d in days:
            if self.habit_done(d, keyword):
                run += 1
                longest = max(longest, run)
            else:
                run = 0
        # current streak ending today (or yesterday)
        d = today
        if not self.dm.log.get(d.isoformat()):
            d -= timedelta(days=1)
        while self.dm.log.get(d.isoformat()) and self.habit_done(d, keyword):
            cur += 1
            d -= timedelta(days=1)
        return cur, longest

    def best_day_of_week(self, keyword, days=120):
        """Return per-weekday completion rate + best/worst weekday names."""
        today = date.today()
        totals = [0] * 7
        counts = [0] * 7
        for i in range(days):
            d = today - timedelta(days=i)
            if not self.dm.log.get(d.isoformat()):
                continue
            wd = d.weekday()
            counts[wd] += 1
            if self.habit_done(d, keyword):
                totals[wd] += 1
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        rates = [(totals[i] / counts[i]) if counts[i] else 0 for i in range(7)]
        if not any(counts):
            return names, rates, None, None
        best = names[max(range(7), key=lambda i: rates[i])]
        worst = names[min(range(7), key=lambda i: rates[i])]
        return names, rates, best, worst

    # ---- comparison periods ---------------------------------------------
    PERIODS = ["This week", "Last week", "This month", "Last month"]

    def resolve_period(self, name):
        today = date.today()
        if name == "This week":
            s = today - timedelta(days=today.weekday())
            return s, today, name
        if name == "Last week":
            this_mon = today - timedelta(days=today.weekday())
            return this_mon - timedelta(days=7), this_mon - timedelta(days=1), name
        if name == "This month":
            return today.replace(day=1), today, name
        if name == "Last month":
            first = today.replace(day=1)
            last_prev = first - timedelta(days=1)
            return last_prev.replace(day=1), last_prev, name
        return today - timedelta(days=6), today, name

    def compare(self, name_a, name_b):
        sa, ea, _ = self.resolve_period(name_a)
        sb, eb, _ = self.resolve_period(name_b)
        a = self.range_metrics(sa, ea)
        b = self.range_metrics(sb, eb)
        keys = [("dsa", "DSA questions"), ("lectures", "Lectures"),
                ("jobs", "Job applications"), ("points", "Points earned"),
                ("completion", "Schedule completion %"), ("gym", "Gym sessions")]
        rows = []
        for k, label in keys:
            va, vb = a[k], b[k]
            if vb == 0 and va == 0:
                pct = 0
            elif vb == 0:
                pct = 100
            else:
                pct = round((va - vb) / vb * 100)
            rows.append({"label": label, "a": va, "b": vb, "pct": pct,
                         "winner": "a" if va > vb else "b" if vb > va else "tie"})
        return rows, name_a, name_b

    def compare_summary(self, rows, name_a, name_b):
        a_wins = sum(1 for r in rows if r["winner"] == "a")
        b_wins = sum(1 for r in rows if r["winner"] == "b")
        best = name_a if a_wins >= b_wins else name_b
        ups = [r["label"] for r in rows if r["winner"] == "a"]
        downs = [r["label"] for r in rows if r["winner"] == "b"]
        parts = [f"Your stronger period was {best}."]
        if ups:
            parts.append(f"{name_a} led on {', '.join(ups[:2]).lower()}.")
        if downs:
            parts.append(f"{name_b} led on {', '.join(downs[:2]).lower()}.")
        parts.append("Focus on consistency to keep every metric trending up.")
        return " ".join(parts)

    # ---- leaderboard -----------------------------------------------------
    def my_points(self):
        return self.dm.goals["points_current"]

    def my_rate(self):
        r = self.dm.daily_avg_points()
        return r if r else 0

    def overtake_projection(self):
        """Days/date to overtake rank 1, accounting for competitor growth."""
        you = self.my_points()
        rate = self.my_rate()
        comp_rate = lb.competitor_rate(self.dm)
        gap = lb.rank1_points(self.dm) - you
        if gap <= 0:
            return 0, date.today()
        if rate <= comp_rate:
            return None, None
        days = gap / (rate - comp_rate)
        return round(days), date.today() + timedelta(days=round(days))

    def points_to_ranks(self):
        """For each competitor above you, points needed to overtake."""
        you = self.my_points()
        out = []
        for rank, row in enumerate(lb.board_competitors(self.dm), start=1):
            if row["points"] > you:
                out.append((rank, row["name"], row["points"], row["points"] - you + 1))
        return out

    # ---- course units ----------------------------------------------------
    def unit_priority(self):
        """Priority score per unit: more remaining + closer deadline = higher."""
        plan = self.dm.planner()
        target = plan["target"]
        out = []
        for u, pu in zip(self.dm.goals["course_units"], plan["units"]):
            done = u["assignments_done"] + u["assessments_done"] + u["lectures_done"]
            total = u["assignments_total"] + u["assessments_total"] + u["lectures_total"]
            remaining = (1 - done / total) if total else 0
            days_left = max(1, (target - date.today()).days)
            # behind units score higher; weight by remaining workload
            urgency = 1.4 if not pu["on_track"] and not pu["done"] else 1.0
            score = round(remaining * 100 * urgency)
            out.append({"name": u["name"], "remaining": remaining,
                        "finish": pu["finish"], "on_track": pu["on_track"],
                        "done": pu["done"], "priority": score})
        out_sorted = sorted(out, key=lambda x: x["priority"], reverse=True)
        return out, out_sorted

    # ---- job hunt analytics ----------------------------------------------
    def job_hunt_series(self, n=30):
        """Per-day (portal, referrals, cold_emails) for last n days."""
        days = [date.today() - timedelta(days=i) for i in range(n - 1, -1, -1)]
        labels = [d.strftime("%b %d") for d in days]
        portals = [self.portal_count(d) for d in days]
        refs = [self.referrals_sent(d) for d in days]
        colds = [self.cold_emails_sent(d) for d in days]
        return labels, portals, refs, colds

    def job_hunt_totals(self, n=30):
        """Running totals and response rates for last n days."""
        days = [date.today() - timedelta(days=i) for i in range(n - 1, -1, -1)]
        total_portal = sum(self.portal_count(d) for d in days)
        total_refs = sum(self.referrals_sent(d) for d in days)
        total_ref_resp = sum(self.dm.log.get(d.isoformat(), {}).get(
            "referrals", {}).get("responses", 0) for d in days)
        total_cold = sum(self.cold_emails_sent(d) for d in days)
        total_cold_rep = sum(self.dm.log.get(d.isoformat(), {}).get(
            "cold_emails", {}).get("replies", 0) for d in days)
        ref_rate = (total_ref_resp / total_refs * 100) if total_refs > 0 else 0
        cold_rate = (total_cold_rep / total_cold * 100) if total_cold > 0 else 0
        return {
            "portal": total_portal, "referrals": total_refs,
            "ref_responses": total_ref_resp, "ref_rate": ref_rate,
            "cold": total_cold, "cold_replies": total_cold_rep, "cold_rate": cold_rate,
            "total_outreach": total_portal + total_refs + total_cold,
        }

    def job_hunt_funnel(self):
        """Funnel: applications → responses → interviews → offers."""
        totals = self.job_hunt_totals(n=90)
        interviews = self.dm.goals.get("interviews", 0)
        offers = self.dm.goals.get("offers", 0)
        applications = totals["portal"] + totals["referrals"] + totals["cold"]
        responses = totals["ref_responses"] + totals["cold_replies"]
        return [
            ("Applications", applications),
            ("Responses", responses),
            ("Interviews", interviews),
            ("Offers", offers),
        ]

    def job_hunt_weekly(self, weeks=8):
        """Per-week portal + referral + cold email totals."""
        wks = self.last_weeks(weeks)
        labels, portals, refs, colds = [], [], [], []
        for lbl, start, end in wks:
            d = start
            p = r = c = 0
            while d <= end:
                p += self.portal_count(d)
                r += self.referrals_sent(d)
                c += self.cold_emails_sent(d)
                d += timedelta(days=1)
            labels.append(lbl)
            portals.append(p)
            refs.append(r)
            colds.append(c)
        return labels, portals, refs, colds

    def job_hunt_insights(self):
        totals = self.job_hunt_totals(30)
        out = []
        if totals["portal"] > 0:
            avg = totals["portal"] / 30
            out.append(("📨", f"You've submitted {totals['portal']} portal apps in 30 days "
                               f"({avg:.1f}/day avg)"))
        if totals["ref_rate"] > 0:
            out.append(("🤝", f"Referral response rate: {totals['ref_rate']:.1f}% "
                               f"({totals['ref_responses']}/{totals['referrals']})"))
        if totals["cold_rate"] > 0:
            out.append(("📧", f"Cold email reply rate: {totals['cold_rate']:.1f}% "
                               f"({totals['cold_replies']}/{totals['cold']})"))
        if totals["total_outreach"] == 0:
            out.append(("💡", "Start tracking portal apps, referrals & cold emails to see insights"))
        return out

    # ---- insights engine -------------------------------------------------
    def insights(self):
        out = []
        # DSA streak
        cur, _ = self.streaks("dsa")
        if cur >= 2:
            out.append(("🔥", f"You're on a {cur}-day DSA streak — keep it going!"))
        # lectures week over week
        weeks = self.last_weeks(2)
        if len(weeks) == 2:
            w_prev = self.range_metrics(weeks[0][1], weeks[0][2])["lectures"]
            w_cur = self.range_metrics(weeks[1][1], weeks[1][2])["lectures"]
            if w_prev > 0:
                ch = round((w_cur - w_prev) / w_prev * 100)
                if ch <= -20:
                    out.append(("⚠️", f"Lectures watched dropped {abs(ch)}% this week vs last week"))
                elif ch >= 20:
                    out.append(("📈", f"Lectures watched up {ch}% this week — great momentum"))
        # planner — a behind unit
        _, prio = self.unit_priority()
        for u in prio:
            if not u["done"] and not u["on_track"]:
                tgt = self.dm.planner()["target"]
                behind = (u["finish"] - tgt).days
                short = u["name"].split("&")[0].strip()
                out.append(("📅", f"At current pace you'll finish {short} by "
                                  f"{u['finish'].strftime('%b %d')} — {behind} days behind target"))
                break
        # best day
        names, rates, best, _ = self.best_day_of_week("dsa")
        if best and any(rates):
            out.append(("💪", f"Your best DSA day is {best} — schedule harder problems then"))
        # leaderboard (only when the user has set a target / competitors)
        you = self.my_points()
        gap = lb.rank1_points(self.dm) - you
        rate = self.my_rate()
        if gap > 0 and lb.board_competitors(self.dm):
            if rate > 0:
                out.append(("🎯", f"You need {gap:,} more points to reach the top — "
                                  f"at {rate:.0f} pts/day that's {round(gap / rate)} days"))
            else:
                out.append(("🎯", f"You need {gap:,} more points to reach the top — "
                                  f"log DSA sessions to set your pace"))
        if not out:
            out.append(("✨", "Log a few days of activity to unlock personalised insights."))
        return out
