"""Daily view tab — per-day series for the last 30 days."""

from datetime import date, timedelta

import theme
from .charts import TabBase, ChartCard


class DailyTab(TabBase):
    N = 30

    def _dates(self):
        return [date.today() - timedelta(days=i) for i in range(self.N - 1, -1, -1)]

    def _detail(self, dates):
        def fn(idx):
            if not (0 <= idx < len(dates)):
                return None
            d = dates[idx]
            day = self.m.day(d)
            return (d.strftime("%a, %d %b"), [
                ("Schedule", f"{round(day['completion']*100)}%", theme.INFO),
                ("DSA solved", day["dsa"], theme.ACCENT),
                ("Lectures", day["lectures"], theme.TEAL),
                ("Points", day["points"], theme.ORANGE),
                ("Job apps", day["jobs"], theme.SUCCESS),
                (theme.SCORE_NAME, f"{self.m.day_score(d)}/100", theme.ACCENT),
            ])
        return fn

    def build(self):
        for w in self.winfo_children():
            w.destroy()
        s = self.scroll()
        dates = self._dates()
        labels = [d.strftime("%d") for d in dates]
        xs = list(range(self.N))
        detail = self._detail(dates)

        # 1. completion bar
        _, comp = self.m.series("completion", self.N)
        comp = [round(c * 100) for c in comp]
        cc = ChartCard(self, s, "Schedule Completion % — last 30 days")
        bars = cc.ax.bar(xs, [0] * self.N, color=theme.ACCENT, width=0.7, zorder=3)
        cc.ax.set_ylim(0, 100); cc.ax.set_ylabel("% done")
        cc.ax.set_xticks(xs[::5]); cc.ax.set_xticklabels(labels[::5])
        cc.finish(animate=("bars", bars, comp),
                  hover=("bar", xs, comp, labels, lambda v: f"{v:g}%"), detail=detail)

        # 2. DSA line + target
        _, dsa = self.m.series("dsa", self.N)
        cc = ChartCard(self, s, "DSA Questions Solved — daily")
        (ln,) = cc.ax.plot([], [], color=theme.ACCENT, lw=2, marker="o", ms=3, zorder=3,
                           label="Solved")
        cc.ax.axhline(7, color=theme.SUCCESS, ls="--", lw=1.4, label="Target 7/day")
        cc.ax.set_xlim(-0.3, self.N - 0.7); cc.ax.set_ylim(0, max(dsa + [8]) + 1)
        cc.ax.set_ylabel("questions")
        cc.ax.set_xticks(xs[::5]); cc.ax.set_xticklabels(labels[::5]); cc.legend()
        cc.finish(animate=("line", ln, xs, dsa),
                  hover=("line", xs, dsa, labels), detail=detail)

        # 3. lectures line
        _, lec = self.m.series("lectures", self.N)
        cc = ChartCard(self, s, "Lectures Watched — daily")
        (ln,) = cc.ax.plot([], [], color=theme.TEAL, lw=2, marker="o", ms=3, zorder=3,
                           label="Lectures")
        cc.ax.set_xlim(-0.3, self.N - 0.7); cc.ax.set_ylim(0, max(lec + [4]) + 1)
        cc.ax.set_ylabel("lectures")
        cc.ax.set_xticks(xs[::5]); cc.ax.set_xticklabels(labels[::5]); cc.legend()
        cc.finish(animate=("line", ln, xs, lec),
                  hover=("line", xs, lec, labels), detail=detail)

        # 4. points bar
        _, pts = self.m.series("points", self.N)
        cc = ChartCard(self, s, "Points Earned — daily (leaderboard)")
        bars = cc.ax.bar(xs, [0] * self.N, color=theme.ORANGE, width=0.7, zorder=3)
        cc.ax.set_ylim(0, max(pts + [10]) * 1.2); cc.ax.set_ylabel("points")
        cc.ax.set_xticks(xs[::5]); cc.ax.set_xticklabels(labels[::5])
        cc.finish(animate=("bars", bars, pts),
                  hover=("bar", xs, pts, labels, lambda v: f"{v:g} pts"), detail=detail)

        # 5. job apps bar
        _, jobs = self.m.series("jobs", self.N)
        cc = ChartCard(self, s, "Job Applications — daily")
        bars = cc.ax.bar(xs, [0] * self.N, color=theme.SUCCESS, width=0.7, zorder=3)
        cc.ax.set_ylim(0, max(jobs + [2]) + 1); cc.ax.set_ylabel("applications")
        cc.ax.set_xticks(xs[::5]); cc.ax.set_xticklabels(labels[::5])
        cc.finish(animate=("bars", bars, jobs),
                  hover=("bar", xs, jobs, labels), detail=detail)

        # 6. cumulative points area
        clabels, cum = self.m.cumulative_points()
        cxs = list(range(len(cum)))
        cc = ChartCard(self, s, "Cumulative Leaderboard Points", zoom=True)
        (ln,) = cc.ax.plot([], [], color=theme.ACCENT, lw=2.2, zorder=3, label="Total")
        cc.ax.fill_between(cxs, cum, color=theme.ACCENT, alpha=0.18)
        if cum:
            cc.ax.set_xlim(-0.3, max(1, len(cum) - 1) + 0.3)
            cc.ax.set_ylim(min(cum) * 0.98, max(cum) * 1.03)
        step = max(1, len(clabels) // 6)
        cc.ax.set_xticks(cxs[::step]); cc.ax.set_xticklabels(clabels[::step])
        cc.ax.set_ylabel("total pts"); cc.legend()
        cc.finish(animate=("line", ln, cxs, cum),
                  hover=("line", cxs, cum, clabels, lambda v: f"{v:,.0f} pts"))
