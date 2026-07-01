"""Schedule view — today's checklist with greeting, stat pills, category-colour
task rows, quote banner, and a live Momentum Score.

P6: time-based greeting, coloured left border per category, stat pills
    (Done / Remaining / Streak / Score), daily quote banner between morning and
    afternoon blocks, completed tasks dim + strikethrough.
P8: Sunday assessment banner (shown only on Sundays when no assessment logged).
"""

from datetime import date, datetime

import customtkinter as ctk

import theme
from schedules import get_schedule_for_date
from dialogs import DSADialog, StudyDialog, ReferralsDialog, ColdEmailsDialog
from views.portal_counter import PortalCounter
from quotes import get_daily_quote

# --- category colour map (task keyword → hex colour) --------------------
CATEGORY_COLORS = {
    "wake":        "#F5A623",
    "freshen":     "#F5A623",
    "gym":         "#27AE60",
    "portal":      "#E74C3C",
    "breakfast":   "#1ABC9C",
    "meal":        "#1ABC9C",
    "lunch":       "#1ABC9C",
    "dinner":      "#1ABC9C",
    "java":        "#8E44AD",
    "spring":      "#8E44AD",
    "course":      "#8E44AD",
    "dsa":         "#2980B9",
    "coding":      "#2980B9",
    "internship":  "#1F6FEB",
    "badminton":   "#E91E8C",
    "break":       "#7F8C8D",
    "rest":        "#7F8C8D",
    "free":        "#7F8C8D",
    "referral":    "#CD853F",
    "cold email":  "#F39C12",
    "hr cold":     "#F39C12",
    "sleep":       "#2C3E6B",
    "home":        "#7F8C8D",
}

# --- time-based greeting slots -------------------------------------------
def _greeting(name=""):
    who = f", {name}" if name else ""
    h = datetime.now().hour
    if 6 <= h < 9:
        return f"Rise and grind{who}. Let's make it count. ⚡"
    if 9 <= h < 12:
        return "Morning session — execute with precision."
    if 12 <= h < 15:
        return "Keep the momentum going. Afternoon focus mode."
    if 15 <= h < 19:
        return "Push through. The evening belongs to those who don't stop."
    if 19 <= h < 22:
        return "Final stretch of the day. Finish strong."
    return "Late night grind. Champions work when others sleep."

def _task_color(task_text):
    """Return a left-border colour for a task based on keyword matching."""
    t = task_text.lower()
    for kw, color in CATEGORY_COLORS.items():
        if kw in t:
            return color
    return theme.ACCENT

# index in schedule where afternoon starts (after 12:00 PM)
def _afternoon_index(schedule):
    for i, item in enumerate(schedule):
        h = item["time"]
        if "12" in h and "PM" in h:
            return i
        if "PM" in h:
            return i
    return len(schedule) // 2


class ScheduleView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.checks = []
        self._score_label = None
        self._stat_pills = {}    # key → CTkLabel
        self._quote_banner = None
        self.build()

    @property
    def pal(self):
        return self.app.pal

    def build(self):
        for w in self.winfo_children():
            w.destroy()
        self.checks = []
        self._stat_pills = {}
        self._score_label = None

        today = date.today()
        label, schedule = get_schedule_for_date(today)
        self.schedule = schedule

        saved = self.app.data.get_tasks()

        # ---- P8: Sunday assessment banner --------------------------------
        if today.weekday() == 6:
            from data_manager import today_key
            no_assessment = not any(
                a.get("date") == today_key() for a in self.app.data.sunday)
            if no_assessment:
                self._sunday_banner()

        # ---- header -------------------------------------------------------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=4, pady=(0, 10))

        ctk.CTkLabel(header, text="Today's Schedule",
                     font=(theme.FONT, 26, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w")
        ctk.CTkLabel(header,
                     text=f"{today.strftime('%A, %d %B %Y')}  ·  {label} plan",
                     font=(theme.FONT, 14),
                     text_color=self.pal["text_muted"]).pack(anchor="w", pady=(2, 0))

        # greeting
        name = self.app.data.settings.get("name", "").strip()
        ctk.CTkLabel(header, text=_greeting(name),
                     font=(theme.FONT, 13, "italic"),
                     text_color=theme.ACCENT).pack(anchor="w", pady=(4, 0))

        # ---- stat pills row -----------------------------------------------
        pills_row = ctk.CTkFrame(self, fg_color="transparent")
        pills_row.pack(fill="x", padx=4, pady=(6, 6))
        for key, icon in [("done", "✓ Done"), ("remaining", "⏳ Left"),
                           ("streak", "🔥 Streak"), ("score", "⚡ Score")]:
            pill = ctk.CTkFrame(pills_row, fg_color=self.pal["surface"],
                                corner_radius=10,
                                border_width=1, border_color=self.pal["border"])
            pill.pack(side="left", fill="both", expand=True, padx=(0, 8))
            ctk.CTkLabel(pill, text=icon, font=(theme.FONT, 10),
                         text_color=self.pal["text_muted"]).pack(pady=(6, 0))
            val_lbl = ctk.CTkLabel(pill, text="—", font=(theme.FONT, 17, "bold"),
                                   text_color=theme.ACCENT)
            val_lbl.pack(pady=(0, 6))
            self._stat_pills[key] = val_lbl

        # ---- progress bar card -------------------------------------------
        prog_card = ctk.CTkFrame(self, fg_color=self.pal["surface"], corner_radius=14)
        prog_card.pack(fill="x", padx=4, pady=(0, 10))

        row = ctk.CTkFrame(prog_card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=12)

        self.pct_label = ctk.CTkLabel(row, text="0%",
                                      font=(theme.FONT, 32, "bold"),
                                      text_color=theme.ACCENT)
        self.pct_label.pack(side="left")

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True, padx=(20, 0))

        self.count_label = ctk.CTkLabel(right, text="0 of 0 tasks done",
                                        font=(theme.FONT, 13),
                                        text_color=self.pal["text_muted"], anchor="w")
        self.count_label.pack(fill="x", anchor="w")

        self.progress = ctk.CTkProgressBar(right, height=14, corner_radius=8,
                                           progress_color=theme.ACCENT,
                                           fg_color=self.pal["surface_2"])
        self.progress.pack(fill="x", pady=(8, 0))
        self.progress.set(0)

        # live Momentum Score
        self._score_label = ctk.CTkLabel(right, text=f"{theme.SCORE_NAME}: —",
                                         font=(theme.FONT, 11),
                                         text_color=self.pal["text_muted"], anchor="w")
        self._score_label.pack(anchor="w", pady=(4, 0))

        # ---- quick-launch buttons (open trackers without marking task done) -
        ql = ctk.CTkFrame(self, fg_color=self.pal["surface"], corner_radius=12)
        ql.pack(fill="x", padx=4, pady=(0, 8))
        ctk.CTkLabel(ql, text="Quick Launch", font=(theme.FONT, 11),
                     text_color=self.pal["text_muted"]).pack(anchor="w", padx=14, pady=(8, 4))
        ql_row = ctk.CTkFrame(ql, fg_color="transparent")
        ql_row.pack(fill="x", padx=10, pady=(0, 10))

        _ql_btns = [
            ("🖥  Portal Counter",  "#E74C3C", lambda: PortalCounter(self.app, self.app.data, on_saved=self.app.on_data_changed)),
            ("🤝  Referrals",       "#CD853F", lambda: ReferralsDialog(self.app, self.app.data, on_saved=self.app.on_data_changed)),
            ("📧  Cold Emails",     "#F39C12", lambda: ColdEmailsDialog(self.app, self.app.data, on_saved=self.app.on_data_changed)),
            ("🧠  DSA Session",     "#2980B9", lambda: DSADialog(self.app, self.app.data, on_saved=self.app.on_data_changed)),
        ]
        for label, color, cmd in _ql_btns:
            ctk.CTkButton(ql_row, text=label, height=34,
                          font=(theme.FONT, 12, "bold"),
                          fg_color=color, hover_color=color,
                          text_color="#FFFFFF", corner_radius=8,
                          command=cmd).pack(side="left", padx=(0, 8), fill="x", expand=True)

        # ---- checklist (with quote banner in the middle) -----------------
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        split = _afternoon_index(schedule)
        quote_inserted = False

        for i, item in enumerate(schedule):
            if i == split and not quote_inserted:
                self._quote_banner_widget(scroll)
                quote_inserted = True
            done = saved.get(str(i), False)
            self._task_row(scroll, i, item, done)

        self.refresh_progress()

    # ---- Sunday banner ---------------------------------------------------
    def _sunday_banner(self):
        from dialogs import SundayReminder
        banner = ctk.CTkFrame(self, fg_color="#2C1E6B", corner_radius=12,
                              border_width=2, border_color="#6C5CE7")
        banner.pack(fill="x", padx=4, pady=(0, 8))
        ctk.CTkLabel(banner, text="📋  Sunday Assessment Due",
                     font=(theme.FONT, 15, "bold"),
                     text_color="#FFFFFF").pack(side="left", padx=18, pady=14)
        ctk.CTkButton(banner, text="Fill it in →", height=34, width=120,
                      font=(theme.FONT, 13, "bold"),
                      fg_color="#6C5CE7", hover_color="#5A50D4",
                      text_color="#FFFFFF",
                      command=lambda: SundayReminder(
                          self.app, self.app.data,
                          on_saved=self.app.on_data_changed)).pack(
            side="right", padx=18, pady=14)

    # ---- daily quote banner ----------------------------------------------
    def _quote_banner_widget(self, parent):
        q = get_daily_quote()
        frame = ctk.CTkFrame(parent, fg_color=self.pal["surface_2"],
                             corner_radius=10)
        frame.pack(fill="x", padx=4, pady=8)
        ctk.CTkLabel(frame, text=f'"{q}"',
                     font=(theme.FONT, 13, "italic"),
                     text_color=theme.ACCENT,
                     wraplength=580, justify="center").pack(
            padx=20, pady=12)

    # ---- task row with coloured left border + strikethrough on done ------
    def _task_row(self, parent, index, item, done):
        color = _task_color(item["task"])

        outer = ctk.CTkFrame(parent, fg_color="transparent")
        outer.pack(fill="x", pady=3, padx=4)

        # coloured left border strip
        ctk.CTkFrame(outer, width=5, fg_color=color,
                     corner_radius=3).pack(side="left", fill="y", padx=(0, 0))

        card = ctk.CTkFrame(outer, fg_color=self.pal["surface"], corner_radius=12)
        card.pack(side="left", fill="x", expand=True)

        var = ctk.BooleanVar(value=done)

        time_lbl = ctk.CTkLabel(card, text=item["time"], width=82, anchor="w",
                                font=(theme.FONT, 13, "bold"),
                                text_color=color if not done else self.pal["text_muted"])
        time_lbl.pack(side="left", padx=(16, 8), pady=12)

        # strikethrough font when done
        if done:
            strike_font = ctk.CTkFont(family=theme.FONT, size=14, overstrike=True)
            task_lbl = ctk.CTkLabel(card, text=item["task"],
                                    font=strike_font,
                                    text_color=self.pal["text_muted"])
            task_lbl.pack(side="left", fill="x", expand=True, pady=12)
            chk = ctk.CTkCheckBox(card, text="", variable=var, width=28,
                                  fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                                  checkmark_color="#FFFFFF", corner_radius=6,
                                  command=lambda i=index, v=var: self._toggle(i, v))
            chk.pack(side="right", padx=12, pady=12)
        else:
            chk = ctk.CTkCheckBox(card, text=item["task"], variable=var,
                                  font=(theme.FONT, 14),
                                  text_color=self.pal["text"],
                                  fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                                  checkmark_color="#FFFFFF", corner_radius=6,
                                  command=lambda i=index, v=var: self._toggle(i, v))
            chk.pack(side="left", fill="x", expand=True, pady=12)

        self.checks.append((index, var))

    def _toggle(self, index, var, task_lbl=None, time_lbl=None):
        done = var.get()
        self.app.data.set_task(index, done)
        self.refresh_progress()
        if done:
            task = self.schedule[index]["task"].lower()
            if "dsa" in task:
                DSADialog(self.app, self.app.data, on_saved=self.app.on_data_changed)
            elif "java" in task and "spring" in task:
                StudyDialog(self.app, self.app.data, on_saved=self.app.on_data_changed)
            elif "portal" in task:
                PortalCounter(self.app, self.app.data, on_saved=self.app.on_data_changed)
            elif "referral" in task:
                ReferralsDialog(self.app, self.app.data, on_saved=self.app.on_data_changed)
            elif "cold email" in task or "hr cold" in task:
                ColdEmailsDialog(self.app, self.app.data, on_saved=self.app.on_data_changed)

    def refresh_progress(self):
        total = len(self.schedule)
        done_count = sum(1 for _, v in self.checks if v.get())
        pct = round(done_count / total * 100) if total else 0
        self.progress.set(pct / 100)
        self.pct_label.configure(text=f"{pct}%")
        self.count_label.configure(text=f"{done_count} of {total} tasks done")

        # stat pills
        remaining = total - done_count
        streak = self.app.data.daily_streak()
        self._stat_pills["done"].configure(text=str(done_count))
        self._stat_pills["remaining"].configure(text=str(remaining))
        self._stat_pills["streak"].configure(text=f"{streak}d")

        # live Momentum Score
        try:
            from metrics import Metrics
            m = Metrics(self.app.data)
            score = m.day_score(date.today())
            self._stat_pills["score"].configure(text=str(score))
            if self._score_label:
                self._score_label.configure(
                    text=f"{theme.SCORE_NAME} today: {score} / 100",
                    text_color=theme.progress_color(score / 100))
        except Exception:
            pass
