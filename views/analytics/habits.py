"""Habit Tracker tab — Apple-Watch-style weekly rings per habit + monthly dot calendar.

Replaces the heavy 365-day contribution grids with two lightweight views:
  • Weekly Rings  — one ring per habit showing % of this week done
  • Dot Calendar  — current month grid, one row per habit, filled dot = done
"""

from datetime import date, timedelta
from calendar import monthrange

import numpy as np
import customtkinter as ctk
import matplotlib.patches as mpatches
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import theme
from metrics import HABITS
from .charts import TabBase

HABIT_COLORS = {
    "Gym": theme.SUCCESS,
    "DSA": theme.ACCENT,
    "Course": theme.TEAL,
    "Badminton": theme.ORANGE,
    "Job Apps": theme.YELLOW,
    "Cold Emails": theme.INFO,
}


class HabitsTab(TabBase):
    def build(self):
        for w in self.winfo_children():
            w.destroy()
        s = self.scroll()
        self._weekly_rings(s)
        self._streak_summary(s)
        self._dot_calendar(s)
        self._best_days(s)

    # ---- weekly activity rings (Apple Watch style) -----------------------
    def _weekly_rings(self, parent):
        card = self.card(parent)
        today = date.today()
        mon = today - timedelta(days=today.weekday())
        days_this_week = [(mon + timedelta(days=i)) for i in range(7)]
        # count done per habit
        counts = []
        for name, kw in HABITS:
            done = sum(1 for d in days_this_week if d <= today and self.m.habit_done(d, kw))
            counts.append(done)

        total_days = (today - mon).days + 1   # days elapsed in this week

        ctk.CTkLabel(card, text="This Week  —  Activity Rings",
                     font=(theme.FONT, 15, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(12, 2))
        ctk.CTkLabel(card,
                     text=f"Day {total_days} of 7  ·  each ring = days completed / days elapsed",
                     font=(theme.FONT, 11), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=18, pady=(0, 4))

        n = len(HABITS)
        fig = Figure(figsize=(6.6, 2.2), dpi=80)
        fig.patch.set_facecolor(self.pal["chart_bg"])

        cols = 3
        rows = (n + cols - 1) // cols
        for i, ((name, _), count) in enumerate(zip(HABITS, counts)):
            ax = fig.add_subplot(rows, cols, i + 1)
            ax.set_facecolor(self.pal["chart_bg"])
            ax.set_aspect("equal")
            ax.axis("off")

            color = HABIT_COLORS.get(name, theme.ACCENT)
            frac = min(1.0, count / max(1, total_days))
            r = 0.80
            thickness = 0.28

            # background ring
            bg = mpatches.Wedge((0, 0), r, 0, 360, width=thickness,
                                facecolor=self.pal["surface_2"], zorder=1)
            ax.add_patch(bg)

            # progress arc (clockwise from top: theta1 = 90 - 360*f, theta2 = 90)
            if frac > 0:
                t1 = 90 - 360 * frac
                t2 = 90
                arc = mpatches.Wedge((0, 0), r, t1, t2, width=thickness,
                                     facecolor=color, zorder=2)
                ax.add_patch(arc)

                # rounded cap at start
                import math
                cap_angle = math.radians(t1)
                cx = (r - thickness / 2) * math.cos(cap_angle)
                cy = (r - thickness / 2) * math.sin(cap_angle)
                cap = mpatches.Circle((cx, cy), thickness / 2,
                                      facecolor=color, zorder=3)
                ax.add_patch(cap)

            # centre text: count / total_days
            ax.text(0, 0.1, str(count), ha="center", va="center",
                    fontsize=14, fontweight="bold",
                    color=color if frac > 0 else self.pal["text_muted"])
            ax.text(0, -0.25, f"/{total_days}", ha="center", va="center",
                    fontsize=8, color=self.pal["chart_text"])
            ax.set_title(name, fontsize=8, color=self.pal["chart_text"], pad=2)
            ax.set_xlim(-1.1, 1.1)
            ax.set_ylim(-1.1, 1.1)

        fig.tight_layout(pad=0.3)
        self._figures.append(fig)
        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=(0, 12))

    # ---- streak summary chips -------------------------------------------
    def _streak_summary(self, parent):
        card = self.card(parent)
        ctk.CTkLabel(card, text="Streaks",
                     font=(theme.FONT, 15, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(12, 8))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 12))
        for name, kw in HABITS:
            cur, longest = self.m.streaks(kw)
            color = HABIT_COLORS.get(name, theme.ACCENT)
            chip = ctk.CTkFrame(row, fg_color=self.pal["surface_2"], corner_radius=10)
            chip.pack(side="left", fill="both", expand=True, padx=(0, 6))
            ctk.CTkLabel(chip, text=name, font=(theme.FONT, 10),
                         text_color=color).pack(pady=(6, 0))
            ctk.CTkLabel(chip, text=str(cur), font=(theme.FONT, 18, "bold"),
                         text_color=color).pack()
            ctk.CTkLabel(chip, text=f"best {longest}", font=(theme.FONT, 9),
                         text_color=self.pal["text_muted"]).pack(pady=(0, 6))

    # ---- dot calendar (current month) -----------------------------------
    def _dot_calendar(self, parent):
        card = self.card(parent)
        today = date.today()
        year, month = today.year, today.month
        num_days = monthrange(year, month)[1]

        ctk.CTkLabel(card,
                     text=f"Dot Calendar  —  {today.strftime('%B %Y')}",
                     font=(theme.FONT, 15, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(12, 2))
        ctk.CTkLabel(card, text="Filled dot = done  ·  faint dot = missed  ·  no dot = future",
                     font=(theme.FONT, 11), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=18, pady=(0, 4))

        habit_names = [name for name, _ in HABITS]
        habit_kws = [kw for _, kw in HABITS]
        colors_list = [HABIT_COLORS.get(n, theme.ACCENT) for n in habit_names]

        fig = Figure(figsize=(6.6, 2.2), dpi=80)
        fig.patch.set_facecolor(self.pal["chart_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.pal["chart_bg"])

        for day in range(1, num_days + 1):
            d = date(year, month, day)
            if d > today:
                continue
            for h_idx, (kw, color) in enumerate(zip(habit_kws, colors_list)):
                done = self.m.habit_done(d, kw)
                y = len(HABITS) - 1 - h_idx
                if done:
                    ax.plot(day, y, "o", color=color, markersize=5.5, zorder=3)
                else:
                    ax.plot(day, y, "o", color=self.pal["chart_grid"],
                            markersize=3, alpha=0.5, zorder=2)

        ax.set_xlim(0.5, num_days + 0.5)
        ax.set_ylim(-0.6, len(HABITS) - 0.4)
        tick_xs = list(range(1, num_days + 1, 3))
        ax.set_xticks(tick_xs)
        ax.set_xticklabels([str(d) for d in tick_xs], fontsize=7,
                           color=self.pal["chart_text"])
        ax.set_yticks(range(len(HABITS)))
        ax.set_yticklabels(list(reversed(habit_names)), fontsize=8,
                           color=self.pal["chart_text"])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(left=False, bottom=False)
        ax.grid(True, axis="x", color=self.pal["chart_grid"],
                lw=0.4, alpha=0.4)
        # today marker
        ax.axvline(today.day, color=theme.ACCENT, lw=1.2, alpha=0.6, ls="--")
        fig.tight_layout()
        self._figures.append(fig)
        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=(0, 12))

    # ---- best day of week text insight ----------------------------------
    def _best_days(self, parent):
        card = self.card(parent)
        ctk.CTkLabel(card, text="Best Days",
                     font=(theme.FONT, 15, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(12, 6))
        verbs = {
            "Gym": "hit the gym", "DSA": "do DSA",
            "Course": "watch lectures", "Badminton": "play badminton",
            "Job Apps": "send applications", "Cold Emails": "send cold emails",
        }
        for name, kw in HABITS:
            _, _, best, worst = self.m.best_day_of_week(kw)
            if best:
                color = HABIT_COLORS.get(name, theme.ACCENT)
                verb = verbs.get(name, "do this")
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=18, pady=2)
                ctk.CTkLabel(row, text=f"● {name}", font=(theme.FONT, 12, "bold"),
                             text_color=color, width=110, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=f"Best: {best}  ·  tends to slip on {worst}s",
                             font=(theme.FONT, 12),
                             text_color=self.pal["text_muted"]).pack(side="left")
        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()
