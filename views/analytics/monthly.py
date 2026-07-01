"""Monthly view tab — month-over-month totals, comparison, and a month heatmap."""

from calendar import monthrange
from datetime import date

import customtkinter as ctk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import theme
from .charts import TabBase, ChartCard


class MonthlyTab(TabBase):
    def __init__(self, master, app):
        super().__init__(master, app)
        self.sel = None  # selected (label, year, month)

    def build(self):
        for w in self.winfo_children():
            w.destroy()
        s = self.scroll()
        months = self.m.months()
        if self.sel is None:
            today = date.today()
            self.sel = next((m for m in months if m[1] == today.year and m[2] == today.month),
                            months[-1])

        # selector
        sel_card = self.card(s)
        row = ctk.CTkFrame(sel_card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=14)
        ctk.CTkLabel(row, text="Month", font=(theme.FONT, 14, "bold"),
                     text_color=self.pal["text"]).pack(side="left")
        labels = [f"{lbl} {yr}" for lbl, yr, mo in months]
        cur_label = f"{self.sel[0]} {self.sel[1]}"
        menu = ctk.CTkOptionMenu(row, values=labels, width=160,
                                 font=(theme.FONT, 13), fg_color=self.pal["surface_2"],
                                 button_color=theme.ACCENT, button_hover_color=theme.ACCENT_HOVER,
                                 command=lambda v: self._pick(months, v))
        menu.set(cur_label)
        menu.pack(side="left", padx=12)

        self._big_numbers(s, self.sel)
        self._comparison(s, months)
        self._mock_months(s, months)
        self._heatmap(s, self.sel)

    def _pick(self, months, value):
        for lbl, yr, mo in months:
            if f"{lbl} {yr}" == value:
                self.sel = (lbl, yr, mo)
                break
        self.build()

    def _big_numbers(self, parent, sel):
        lbl, yr, mo = sel
        mm = self.m.month_metrics(yr, mo)
        card = self.card(parent)
        ctk.CTkLabel(card, text=f"{lbl} {yr} — totals", font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(14, 6))
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 14))
        cards = [
            ("DSA solved", mm["dsa"], theme.ACCENT),
            ("Lectures", mm["lectures"], theme.TEAL),
            ("Points", mm["points"], theme.ORANGE),
            ("Job apps", mm["jobs"], theme.SUCCESS),
            ("Gym", mm["gym"], theme.INFO),
            ("Badminton", mm["badminton"], theme.YELLOW),
        ]
        for i, (label, val, color) in enumerate(cards):
            cell = ctk.CTkFrame(grid, fg_color=self.pal["surface_2"], corner_radius=12)
            cell.grid(row=i // 3, column=i % 3, padx=6, pady=6, sticky="nsew")
            grid.grid_columnconfigure(i % 3, weight=1)
            ctk.CTkLabel(cell, text=f"{val:,}", font=(theme.FONT, 26, "bold"),
                         text_color=color).pack(pady=(14, 0))
            ctk.CTkLabel(cell, text=label, font=(theme.FONT, 11),
                         text_color=self.pal["text_muted"]).pack(pady=(0, 14))

    def _comparison(self, parent, months):
        mlabels = [m[0] for m in months]
        mm = [self.m.month_metrics(y, mo) for _, y, mo in months]
        cc = ChartCard(self, parent, "Month-over-Month — DSA · Lectures · Points",
                       subtitle="June → September", height=3.0)
        x = np.arange(len(months))
        series = [("DSA", "dsa", theme.ACCENT), ("Lectures", "lectures", theme.TEAL),
                  ("Job apps", "jobs", theme.SUCCESS)]
        width = 0.8 / len(series)
        for si, (name, key, color) in enumerate(series):
            vals = [m[key] for m in mm]
            cc.ax.bar(x + si * width - 0.4 + width / 2, vals, width, label=name,
                      color=color, zorder=3)
        cc.ax.set_xticks(x); cc.ax.set_xticklabels(mlabels)
        cc.ax.set_ylabel("count"); cc.legend()
        cc.finish()

    def _mock_months(self, parent, months):
        rows = self.app.data.mock_scores()
        if not rows:
            return
        from collections import defaultdict
        buckets = defaultdict(list)
        for name, pct, dstr in rows:
            if dstr:
                buckets[dstr[:7]].append(pct)
        labels = sorted(buckets.keys())
        vals = [sum(buckets[k]) / len(buckets[k]) for k in labels]
        cc = ChartCard(self, parent, "Monthly Mock Average")
        xs = list(range(len(vals)))
        bars = cc.ax.bar(xs, [0] * len(vals), color=theme.ACCENT, width=0.5, zorder=3)
        cc.ax.axhline(60, color=theme.ORANGE, ls="--", lw=1.2)
        cc.ax.set_ylim(0, 100); cc.ax.set_xticks(xs); cc.ax.set_xticklabels(labels, fontsize=7)
        cc.finish(animate=("bars", bars, vals),
                  hover=("bar", xs, vals, labels, lambda v: f"{v:.0f}%"))

    def _heatmap(self, parent, sel):
        lbl, yr, mo = sel
        card = self.card(parent)
        ctk.CTkLabel(card, text=f"{lbl} {yr} — daily productivity ({theme.SCORE_NAME})",
                     font=(theme.FONT, 15, "bold"), text_color=self.pal["text"]).pack(
            anchor="w", padx=18, pady=(12, 0))
        ndays = monthrange(yr, mo)[1]
        first = date(yr, mo, 1)
        start_wd = first.weekday()  # Mon=0

        fig = Figure(figsize=(5.2, 3.2), dpi=100)
        fig.patch.set_facecolor(self.pal["chart_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.pal["chart_bg"])

        def color(score, has):
            if not has:
                return self.pal["surface_2"]
            if score <= 40:
                return theme.DANGER
            if score <= 70:
                return theme.ORANGE
            if score <= 85:
                return theme.YELLOW
            return theme.SUCCESS

        for day in range(1, ndays + 1):
            d = date(yr, mo, day)
            idx = start_wd + (day - 1)
            col = idx % 7
            row = idx // 7
            has = bool(self.app.data.log.get(d.isoformat()))
            sc = self.m.day_score(d) if has else 0
            ax.add_patch(mpatches.Rectangle((col, -row), 0.9, 0.9,
                                            facecolor=color(sc, has),
                                            edgecolor=self.pal["chart_bg"], lw=1.5))
            ax.text(col + 0.45, -row + 0.45, str(day), ha="center", va="center",
                    fontsize=6, color=self.pal["text"])
        ax.set_xlim(0, 7); ax.set_ylim(-(6), 1)
        ax.set_xticks([i + 0.45 for i in range(7)])
        ax.set_xticklabels(["M", "T", "W", "T", "F", "S", "S"], fontsize=8,
                           color=self.pal["chart_text"])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_aspect("equal")
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)
