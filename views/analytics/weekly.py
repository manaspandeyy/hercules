"""Weekly view tab — Week 1-4 comparisons, habit radar, time distribution."""

from datetime import date, timedelta

import numpy as np
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import theme
from .charts import TabBase, ChartCard

# Schedule activity → hours/day, for the weekly time-distribution stack.
ACTIVITY_HOURS = [
    ("Gym", "gym", 2.0, theme.SUCCESS),
    ("DSA", "dsa", 2.0, theme.ACCENT),
    ("Course", "java", 2.0, theme.TEAL),
    ("Internship", "internship", 3.0, theme.INFO),
    ("Badminton", "badminton", 1.0, theme.ORANGE),
    ("Jobs", "job application", 1.0, theme.YELLOW),
]


class WeeklyTab(TabBase):
    def build(self):
        for w in self.winfo_children():
            w.destroy()
        s = self.scroll()
        weeks = self.m.last_weeks(4)
        wlabels = [w[0] for w in weeks]
        wm = [self.m.range_metrics(w[1], w[2]) for w in weeks]

        self._grouped(s, wlabels, wm)
        self._single(s, "Points Earned per Week", wlabels,
                     [m["points"] for m in wm], theme.ORANGE, " pts")
        self._single(s, "Schedule Completion % per Week", wlabels,
                     [m["completion"] for m in wm], theme.INFO, "%", ymax=100)
        self._mock_trend(s)
        self._radar(s, weeks[-1])
        self._stacked(s, weeks, wlabels)

    # grouped: x = metric, 4 week-bars each
    def _grouped(self, parent, wlabels, wm):
        metrics = [("DSA", "dsa"), ("Lectures", "lectures"),
                   ("Assignments", "assignments"), ("Jobs", "jobs")]
        cc = ChartCard(self, parent, "Weekly Comparison — counts per metric",
                       subtitle="Week 1 → Week 4 side by side", height=3.0)
        x = np.arange(len(metrics))
        nb = len(wm)
        width = 0.8 / nb
        colors = [theme.ACCENT_SOFT, theme.TEAL, theme.INFO, theme.ACCENT]
        for wi, m in enumerate(wm):
            vals = [m[k] for _, k in metrics]
            cc.ax.bar(x + wi * width - 0.4 + width / 2, vals, width,
                      label=wlabels[wi], color=colors[wi % len(colors)], zorder=3)
        cc.ax.set_xticks(x); cc.ax.set_xticklabels([m[0] for m in metrics])
        cc.ax.set_ylabel("count"); cc.legend()
        cc.finish()

    def _single(self, parent, title, labels, vals, color, suffix="", ymax=None):
        cc = ChartCard(self, parent, title)
        xs = list(range(len(vals)))
        bars = cc.ax.bar(xs, [0] * len(vals), color=color, width=0.55, zorder=3)
        cc.ax.set_ylim(0, ymax or (max(vals + [1]) * 1.2))
        cc.ax.set_xticks(xs); cc.ax.set_xticklabels(labels)
        cc.finish(animate=("bars", bars, vals),
                  hover=("bar", xs, vals, labels, lambda v: f"{v:g}{suffix}"))

    def _mock_trend(self, parent):
        rows = self.app.data.mock_scores()
        if not rows:
            return
        # average score per ISO week
        from collections import OrderedDict
        buckets = OrderedDict()
        for name, pct, dstr in rows:
            wk = dstr[:7] if dstr else "—"
            buckets.setdefault(wk, []).append(pct)
        labels = list(buckets.keys())
        vals = [sum(v) / len(v) for v in buckets.values()]
        cc = ChartCard(self, parent, "Weekly Average Mock Score")
        xs = list(range(len(vals)))
        (ln,) = cc.ax.plot([], [], color=theme.ACCENT, lw=2.2, marker="o", ms=4,
                           zorder=3, label="Avg %")
        cc.ax.axhline(60, color=theme.ORANGE, ls="--", lw=1.2)
        cc.ax.set_ylim(0, 100); cc.ax.set_xlim(-0.3, max(1, len(vals) - 1) + 0.3)
        cc.ax.set_xticks(xs); cc.ax.set_xticklabels(labels, fontsize=7); cc.legend()
        cc.finish(animate=("line", ln, xs, vals),
                  hover=("line", xs, vals, labels, lambda v: f"{v:.0f}%"))

    # radar of the 6 habits for the current week
    def _radar(self, parent, week):
        _, start, end = week
        from metrics import HABITS
        days = [(start + timedelta(days=i)) for i in range(7)]
        today = date.today()
        labels, values = [], []
        for name, kw in HABITS:
            done = sum(1 for d in days if d <= today and self.m.habit_done(d, kw))
            labels.append(name)
            values.append(done / 7)

        card = self.card(parent)
        ctk.CTkLabel(card, text="Habit Radar — this week",
                     font=(theme.FONT, 15, "bold"), text_color=self.pal["text"]).pack(
            anchor="w", padx=18, pady=(12, 0))
        ctk.CTkLabel(card, text="How consistent each habit was (full = every day)",
                     font=(theme.FONT, 11), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=18)

        fig = Figure(figsize=(4.6, 3.4), dpi=100)
        fig.patch.set_facecolor(self.pal["chart_bg"])
        ax = fig.add_subplot(111, polar=True)
        ax.set_facecolor(self.pal["chart_bg"])
        ang = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        vals = values + values[:1]
        ang2 = ang + ang[:1]
        ax.plot(ang2, vals, color=theme.ACCENT, lw=2)
        ax.fill(ang2, vals, color=theme.ACCENT, alpha=0.25)
        ax.set_xticks(ang); ax.set_xticklabels(labels, fontsize=8,
                                               color=self.pal["chart_text"])
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(["25", "50", "75", "100"], fontsize=6,
                           color=self.pal["chart_text"])
        ax.set_ylim(0, 1)
        ax.grid(color=self.pal["chart_grid"])
        ax.spines["polar"].set_color(self.pal["chart_grid"])
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)

    # stacked time distribution per week
    def _stacked(self, parent, weeks, wlabels):
        cc = ChartCard(self, parent, "Weekly Time Distribution (hours)",
                       subtitle="Estimated from completed schedule blocks", height=3.0)
        x = np.arange(len(weeks))
        bottoms = np.zeros(len(weeks))
        for name, kw, hrs, color in ACTIVITY_HOURS:
            series = []
            for _, start, end in weeks:
                tot = 0.0
                for i in range(7):
                    d = start + timedelta(days=i)
                    if self.app.data._task_done_on(d, kw):
                        tot += hrs
                series.append(tot)
            cc.ax.bar(x, series, 0.55, bottom=bottoms, label=name, color=color, zorder=3)
            bottoms += np.array(series)
        cc.ax.set_xticks(x); cc.ax.set_xticklabels(wlabels)
        cc.ax.set_ylabel("hours"); cc.legend()
        cc.finish()
