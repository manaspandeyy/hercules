"""Export & share — CSV backup, PDF summary report, and a Wrapped-style card."""

import csv
import os
from datetime import date, timedelta
from tkinter import filedialog

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure

import theme
import leaderboard_data as lb


def export_csv(view):
    """Dump per-day metrics (last 120 days) to a CSV the user picks."""
    path = filedialog.asksaveasfilename(
        defaultextension=".csv", filetypes=[("CSV", "*.csv")],
        initialfile="hercules_backup.csv", title="Export data as CSV")
    if not path:
        return None
    m = view.m
    cols = ["date", "completion_pct", "dsa", "lectures", "points", "jobs",
            "gym", "badminton", "cold_emails", "day_score"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i in range(119, -1, -1):
            d = date.today() - timedelta(days=i)
            if not view.app.data.log.get(d.isoformat()):
                continue
            day = m.day(d)
            w.writerow([d.isoformat(), round(day["completion"] * 100), day["dsa"],
                        day["lectures"], day["points"], day["jobs"], day["gym"],
                        day["badminton"], day["cold"], m.day_score(d)])
    return path


def export_pdf(view):
    """One-page PDF summary of this week + this month."""
    path = filedialog.asksaveasfilename(
        defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
        initialfile="hercules_summary.pdf", title="Export summary as PDF")
    if not path:
        return None
    m = view.m
    pal = view.pal
    weeks = m.last_weeks(1)[0]
    wk = m.range_metrics(weeks[1], weeks[2])
    months = m.months()
    mm = m.month_metrics(months[-1][1], months[-1][2])

    fig = Figure(figsize=(8.3, 11.7), dpi=120)
    fig.patch.set_facecolor("#FFFFFF")
    ax = fig.add_subplot(111); ax.axis("off")
    y = 0.96
    ax.text(0.5, y, theme.APP_NAME, ha="center", fontsize=26, fontweight="bold",
            color=theme.ACCENT); y -= 0.04
    ax.text(0.5, y, f"Performance Summary · {date.today().strftime('%d %B %Y')}",
            ha="center", fontsize=11, color="#555"); y -= 0.06

    def section(title, rows):
        nonlocal y
        ax.text(0.08, y, title, fontsize=14, fontweight="bold", color="#111"); y -= 0.035
        for label, val in rows:
            ax.text(0.10, y, label, fontsize=11, color="#333")
            ax.text(0.90, y, str(val), fontsize=11, fontweight="bold", color="#111", ha="right")
            y -= 0.028
        y -= 0.02

    section("This Week", [
        ("DSA questions", wk["dsa"]), ("Lectures watched", wk["lectures"]),
        ("Points earned", wk["points"]), ("Job applications", wk["jobs"]),
        ("Schedule completion", f"{wk['completion']}%"),
        ("Gym sessions", wk["gym"]), ("Badminton", wk["badminton"])])
    section(f"This Month ({months[-1][0]})", [
        ("DSA questions", mm["dsa"]), ("Lectures watched", mm["lectures"]),
        ("Points earned", mm["points"]), ("Job applications", mm["jobs"])])
    section("Leaderboard", [
        ("Current points", f"{m.my_points():,}"),
        ("Points to the top", f"{max(0, lb.rank1_points(view.app.data) - m.my_points()):,}"),
        (f"Today's {theme.SCORE_NAME}", f"{m.day_score(date.today())}/100")])

    fig.savefig(path, facecolor="#FFFFFF", bbox_inches="tight")
    return path


def share_card(view):
    """Spotify-Wrapped-style PNG summarising the week."""
    path = filedialog.asksaveasfilename(
        defaultextension=".png", filetypes=[("PNG", "*.png")],
        initialfile="hercules_week_card.png", title="Save share card")
    if not path:
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    m = view.m
    wk = m.last_weeks(1)[0]
    s = m.range_metrics(wk[1], wk[2])
    score = m.day_score(date.today())

    W = H = 1080
    img = Image.new("RGB", (W, H), "#0E1016")
    d = ImageDraw.Draw(img)

    def font(sz, bold=True):
        for name in (("arialbd.ttf" if bold else "arial.ttf"), "arial.ttf"):
            try:
                return ImageFont.truetype(name, sz)
            except OSError:
                continue
        return ImageFont.load_default()

    # accent header band
    d.rectangle([0, 0, W, 150], fill="#6366F1")
    d.text((60, 44), theme.APP_NAME, font=font(58), fill="#FFFFFF")
    d.text((62, 178), "YOUR WEEK IN NUMBERS", font=font(30), fill="#8B90A3")
    d.text((62, 222), f"{wk[1].strftime('%d %b')} – {wk[2].strftime('%d %b %Y')}",
           font=font(26, False), fill="#8B90A3")

    rows = [
        ("DSA questions solved", str(s["dsa"]), "#6366F1"),
        ("Lectures watched", str(s["lectures"]), "#2DD4BF"),
        ("Leaderboard points", f"{s['points']:,}", "#F97316"),
        ("Job applications", str(s["jobs"]), "#22C55E"),
        ("Schedule completion", f"{s['completion']}%", "#38BDF8"),
        ("Gym sessions", str(s["gym"]), "#EAB308"),
    ]
    y = 320
    for label, val, color in rows:
        d.text((62, y), label, font=font(34, False), fill="#ECEEF4")
        d.text((W - 62, y - 6), val, font=font(54), fill=color, anchor="ra")
        y += 110

    # score footer
    d.rectangle([0, H - 150, W, H], fill="#171A23")
    sc_color = "#22C55E" if score > 70 else "#F97316" if score > 40 else "#EF4444"
    d.text((62, H - 120), theme.SCORE_NAME, font=font(30, False), fill="#8B90A3")
    d.text((W - 62, H - 128), f"{score}/100", font=font(64), fill=sc_color, anchor="ra")

    img.save(path)
    return path
