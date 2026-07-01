"""Top-of-Analytics components shared across tabs:
insights engine card, the daily Momentum Score card, and the goal timeline.
"""

import random
from datetime import date

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import theme
import animations as anim


def _milestones(view):
    """Build the goal timeline from the user's data (today + their target date)."""
    goals = view.app.data.goals
    out = [("Today", date.today().isoformat(), "marker")]
    target = goals.get("target_date")
    if target:
        out.append(("Goal completion", target, "course"))
    return out


def score_color(s):
    return theme.DANGER if s <= 40 else theme.ORANGE if s <= 70 else theme.SUCCESS


def build_insights(view, parent):
    card = ctk.CTkFrame(parent, fg_color=view.pal["surface"], corner_radius=14,
                        border_width=1, border_color=theme.ACCENT)
    card.pack(fill="x", pady=8, padx=4)
    head = ctk.CTkFrame(card, fg_color="transparent")
    head.pack(fill="x", padx=18, pady=(14, 6))
    ctk.CTkLabel(head, text="💡 Insights", font=(theme.FONT, 16, "bold"),
                 text_color=view.pal["text"]).pack(side="left")
    ctk.CTkButton(head, text="⟳ Refresh", width=92, height=30, font=(theme.FONT, 12),
                  corner_radius=8, fg_color=view.pal["surface_2"],
                  text_color=view.pal["text"], hover_color=view.pal["border"],
                  command=lambda: _refresh_insights(view, body)).pack(side="right")

    body = ctk.CTkFrame(card, fg_color="transparent")
    body.pack(fill="x", padx=18, pady=(0, 14))
    _refresh_insights(view, body)


def _refresh_insights(view, body):
    for w in body.winfo_children():
        w.destroy()
    pool = view.m.insights()
    random.shuffle(pool)
    for icon, text in pool[:3]:
        row = ctk.CTkFrame(body, fg_color=view.pal["surface_2"], corner_radius=10)
        row.pack(fill="x", pady=3)
        ctk.CTkLabel(row, text=icon, font=(theme.FONT, 16)).pack(side="left", padx=(14, 8), pady=10)
        ctk.CTkLabel(row, text=text, font=(theme.FONT, 13), text_color=view.pal["text"],
                     wraplength=620, justify="left", anchor="w").pack(
            side="left", fill="x", expand=True, pady=10, padx=(0, 12))


def build_score(view, parent):
    stats = view.m.score_stats()
    today = view.m.day_score(date.today())
    card = ctk.CTkFrame(parent, fg_color=view.pal["surface"], corner_radius=14,
                        border_width=1, border_color=view.pal["border"])
    card.pack(fill="x", pady=8, padx=4)

    top = ctk.CTkFrame(card, fg_color="transparent")
    top.pack(fill="x", padx=18, pady=(14, 4))
    left = ctk.CTkFrame(top, fg_color="transparent")
    left.pack(side="left")
    ctk.CTkLabel(left, text=f"{theme.SCORE_NAME} — today", font=(theme.FONT, 14, "bold"),
                 text_color=view.pal["text"]).pack(anchor="w")
    big = ctk.CTkLabel(left, text="0", font=(theme.FONT, 46, "bold"),
                       text_color=score_color(today))
    big.pack(anchor="w")
    anim.animate_count(card, big, 0, today, duration=900, fmt=lambda v: f"{int(round(v))}/100")

    if stats:
        right = ctk.CTkFrame(top, fg_color="transparent")
        right.pack(side="right")
        for label, val in [("Best", f"{stats['best'][1]} ({stats['best'][0].strftime('%d %b')})"),
                           ("Average", f"{stats['avg']:.0f}"),
                           ("Worst", f"{stats['worst'][1]} ({stats['worst'][0].strftime('%d %b')})")]:
            r = ctk.CTkFrame(right, fg_color="transparent")
            r.pack(anchor="e")
            ctk.CTkLabel(r, text=f"{label}: ", font=(theme.FONT, 11),
                         text_color=view.pal["text_muted"]).pack(side="left")
            ctk.CTkLabel(r, text=val, font=(theme.FONT, 11, "bold"),
                         text_color=view.pal["text"]).pack(side="left")

    # score history mini chart
    labels, hist = view.m.score_history(30)
    fig = Figure(figsize=(6.2, 1.8), dpi=100)
    fig.patch.set_facecolor(view.pal["chart_bg"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(view.pal["chart_bg"])
    xs = list(range(len(hist)))
    ax.plot(xs, hist, color=theme.ACCENT, lw=2, zorder=3)
    ax.fill_between(xs, hist, color=theme.ACCENT, alpha=0.15)
    ax.axhline(70, color=theme.SUCCESS, ls="--", lw=1)
    ax.set_ylim(0, 100)
    ax.set_xticks(xs[::5]); ax.set_xticklabels(labels[::5], fontsize=7,
                                               color=view.pal["chart_text"])
    ax.tick_params(colors=view.pal["chart_text"], labelsize=7)
    for sp in ax.spines.values():
        sp.set_color(view.pal["chart_grid"])
    ax.grid(True, color=view.pal["chart_grid"], lw=0.5, alpha=0.6)
    fig.tight_layout()
    c = FigureCanvasTkAgg(fig, master=card); c.draw()
    c.get_tk_widget().pack(fill="x", padx=10, pady=(6, 12))


def build_timeline(view, parent):
    card = ctk.CTkFrame(parent, fg_color=view.pal["surface"], corner_radius=14,
                        border_width=1, border_color=view.pal["border"])
    card.pack(fill="x", pady=8, padx=4)
    ctk.CTkLabel(card, text="🗺 Goal Timeline", font=(theme.FONT, 16, "bold"),
                 text_color=view.pal["text"]).pack(anchor="w", padx=18, pady=(14, 6))

    today = date.today()
    # course completion % drives the "in progress" state of the first milestone
    totals = view.app.data.course_totals()
    course_pct = round(sum(d for d, t in totals.values()) /
                       max(1, sum(t for d, t in totals.values())) * 100)

    for name, dstr, key in _milestones(view):
        try:
            d = date.fromisoformat(dstr)
        except (ValueError, TypeError):
            continue
        days = (d - today).days
        if key == "marker":
            status, color = "You are here", theme.ACCENT
            extra = today.strftime("%B %Y")
        elif days < 0:
            status, color, extra = "Done", theme.SUCCESS, "completed"
        elif key == "course":
            status, color = "In Progress", theme.INFO
            extra = f"{course_pct}% complete · {days} days left"
        else:
            status, color = "Upcoming", view.pal["text_muted"]
            extra = f"{days} days left"

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=4)
        dot = ctk.CTkLabel(row, text="●", font=(theme.FONT, 18), text_color=color)
        dot.pack(side="left", padx=(0, 10))
        col = ctk.CTkFrame(row, fg_color="transparent")
        col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(col, text=f"{name}  ·  {d.strftime('%b %Y')}",
                     font=(theme.FONT, 13, "bold"), text_color=view.pal["text"],
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(col, text=extra, font=(theme.FONT, 11),
                     text_color=view.pal["text_muted"], anchor="w").pack(fill="x")
        ctk.CTkLabel(row, text=status, font=(theme.FONT, 11, "bold"), text_color="#FFFFFF",
                     fg_color=color, corner_radius=8, width=110, height=26).pack(side="right")
    ctk.CTkFrame(card, fg_color="transparent", height=10).pack()
