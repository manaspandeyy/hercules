"""Leaderboard analytics tab — standings table, speedometer gauge, growth-vs-
competitor projection, and points-per-day this week.
"""

from datetime import date, timedelta

import numpy as np
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.patches import Wedge
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import theme
import leaderboard_data as lb
from .charts import TabBase, ChartCard


class LeaderboardTab(TabBase):
    def build(self):
        for w in self.winfo_children():
            w.destroy()
        s = self.scroll()
        you = self.m.my_points()

        self._gauge(s, you)
        self._projection(s, you)
        self._points_week(s)
        self._table(s, you)

    # speedometer 1920 → 15000
    def _gauge(self, parent, you):
        start, target = self.app.data.goals["points_start"], self.app.data.goals["points_target"]
        frac = max(0.0, min(1.0, (you - start) / (target - start)))
        card = self.card(parent)
        ctk.CTkLabel(card, text="🏁 Distance to Rank 1", font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(12, 0))

        fig = Figure(figsize=(4.8, 2.6), dpi=100)
        fig.patch.set_facecolor(self.pal["chart_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.pal["chart_bg"])
        bands = [(0, 0.5, theme.DANGER), (0.5, 0.75, theme.ORANGE),
                 (0.75, 0.9, theme.YELLOW), (0.9, 1.0, theme.SUCCESS)]
        for lo, hi, color in bands:
            ax.add_patch(Wedge((0, 0), 1.0, 180 * (1 - hi), 180 * (1 - lo),
                               width=0.32, facecolor=color))
        ang = np.pi * (1 - frac)
        ax.plot([0, 0.82 * np.cos(ang)], [0, 0.82 * np.sin(ang)],
                color=self.pal["text"], lw=3, zorder=5)
        ax.add_patch(Wedge((0, 0), 0.06, 0, 360, facecolor=self.pal["text"]))
        ax.text(0, -0.18, f"{you:,} pts", ha="center", fontsize=15, fontweight="bold",
                color=self.pal["text"])
        ax.text(0, -0.40, f"{round(frac*100)}% of the way to {target:,}", ha="center",
                fontsize=9, color=self.pal["chart_text"])
        ax.set_xlim(-1.15, 1.15); ax.set_ylim(-0.5, 1.15)
        ax.set_aspect("equal"); ax.axis("off")
        fig.tight_layout()
        c = FigureCanvasTkAgg(fig, master=card); c.draw()
        c.get_tk_widget().pack(fill="x", padx=10, pady=10)

    # your growth vs competitor projection
    def _projection(self, parent, you):
        rate = self.m.my_rate()
        if rate <= 0:                     # fall back to recent daily points average
            recent = [self.m.points(date.today() - timedelta(days=i)) for i in range(14)]
            logged = [p for p in recent if p > 0]
            rate = (sum(logged) / len(logged)) if logged else 150
        horizon = 120
        days = list(range(horizon + 1))
        r1 = lb.rank1_points(self.app.data)
        crate = lb.competitor_rate(self.app.data)
        you_line = [you + rate * t for t in days]
        comp = [r1 + crate * t for t in days]
        eta_days, eta_date = self.m.overtake_projection()

        sub = (f"Overtake the leader around {eta_date.strftime('%d %b %Y')} "
               f"(~{eta_days} days)" if eta_days else
               "At current pace you don't overtake the leader — raise your daily points")
        cc = ChartCard(self, parent, "Your Growth vs Leader (projected)",
                       subtitle=sub, height=3.0, zoom=True)
        cc.ax.plot(days, you_line, color=theme.ACCENT, lw=2.2, label="You")
        cc.ax.plot(days, comp, color=theme.DANGER, lw=2.2, ls="--",
                   label=f"Leader (~{crate}/day)")
        cc.ax.axhline(self.app.data.goals["points_target"], color=theme.SUCCESS,
                      lw=1, ls=":", label="Safe target")
        if eta_days and eta_days <= horizon:
            cc.ax.axvline(eta_days, color=theme.YELLOW, lw=1.2)
        cc.ax.set_xlabel("days from today"); cc.ax.set_ylabel("points")
        cc.ax.xaxis.label.set_color(self.pal["chart_text"])
        cc.legend()
        cc.finish()

    def _points_week(self, parent):
        days = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
        labels = [d.strftime("%a") for d in days]
        vals = [self.m.points(d) for d in days]
        cc = ChartCard(self, parent, "Points per Day — this week")
        xs = list(range(7))
        bars = cc.ax.bar(xs, [0] * 7, color=theme.ORANGE, width=0.6, zorder=3)
        cc.ax.set_ylim(0, max(vals + [10]) * 1.2); cc.ax.set_ylabel("points")
        cc.ax.set_xticks(xs); cc.ax.set_xticklabels(labels)
        cc.finish(animate=("bars", bars, vals),
                  hover=("bar", xs, vals, labels, lambda v: f"{v:g} pts"))

    def _edit_board(self):
        from dialogs import LeaderboardEditorDialog
        LeaderboardEditorDialog(self.app, self.app.data,
                                on_saved=self.app.on_data_changed)

    def _table(self, parent, you):
        card = self.card(parent)
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(12, 6))
        ctk.CTkLabel(head, text="🏆 Standings", font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(side="left")
        ctk.CTkButton(head, text="✏ Edit standings", height=30, width=130,
                      font=(theme.FONT, 12), corner_radius=8,
                      fg_color=self.pal["surface_2"], text_color=self.pal["text"],
                      hover_color=self.pal["border"],
                      command=self._edit_board).pack(side="right")

        board = sorted(lb.board_with_you(self.app.data), key=lambda r: r["points"], reverse=True)
        for i, r in enumerate(board):
            is_you = r["you"]
            rowf = ctk.CTkFrame(card, fg_color=theme.ACCENT if is_you else self.pal["surface_2"],
                                corner_radius=10)
            rowf.pack(fill="x", padx=14, pady=2)
            tcol = "#FFFFFF" if is_you else self.pal["text"]
            ctk.CTkLabel(rowf, text=f"#{i+1}", font=(theme.FONT, 13, "bold"),
                         text_color=tcol, width=44).pack(side="left", padx=(12, 0), pady=8)
            ctk.CTkLabel(rowf, text=r["name"], font=(theme.FONT, 13,
                         "bold" if is_you else "normal"),
                         text_color=tcol, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(rowf, text=f"{r['points']:,}", font=(theme.FONT, 13, "bold"),
                         text_color=tcol, width=80).pack(side="right", padx=12)

        # points needed to overtake those above
        need = self.m.points_to_ranks()
        if need:
            ctk.CTkLabel(card, text="Points to overtake those above you:",
                         font=(theme.FONT, 12, "bold"), text_color=self.pal["text"]).pack(
                anchor="w", padx=18, pady=(12, 4))
            for rank, name, pts, gap in need:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=18, pady=1)
                ctk.CTkLabel(row, text=f"Rank {rank} · {name}", font=(theme.FONT, 12),
                             text_color=self.pal["text_muted"], anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=f"+{gap:,} pts", font=(theme.FONT, 12, "bold"),
                             text_color=theme.ORANGE).pack(side="right")
        ctk.CTkFrame(card, fg_color="transparent", height=10).pack()
