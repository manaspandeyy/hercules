"""Analytics — tabbed advanced analytics dashboard.

Top: insights engine, Momentum Score, goal timeline, and export/share actions.
Below: a tab bar switching between Daily, Weekly, Monthly, Comparison,
Leaderboard, Habits, and Course Unit deep-dive views.
"""

import customtkinter as ctk

import theme
from metrics import Metrics
from views.analytics import overview, export
from views.analytics.daily import DailyTab
from views.analytics.weekly import WeeklyTab
from views.analytics.monthly import MonthlyTab
from views.analytics.comparison import ComparisonTab
from views.analytics.leaderboard import LeaderboardTab
from views.analytics.habits import HabitsTab
from views.analytics.unit_deepdive import UnitDeepDiveTab
from views.analytics.jobhunt import JobHuntTab

TABS = [
    ("daily", "Daily", DailyTab),
    ("weekly", "Weekly", WeeklyTab),
    ("monthly", "Monthly", MonthlyTab),
    ("compare", "Comparison", ComparisonTab),
    ("leaderboard", "Leaderboard", LeaderboardTab),
    ("habits", "Habits", HabitsTab),
    ("units", "Unit Deep Dive", UnitDeepDiveTab),
    ("jobhunt", "Job Hunt", JobHuntTab),
]


class AnalyticsView(ctk.CTkFrame):
    _last_tab = "daily"   # remember across rebuilds within a session

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.m = Metrics(app.data)
        self.tab_buttons = {}
        self.active = AnalyticsView._last_tab
        self.tab_view = None
        self._switch_id = None
        self.build()

    @property
    def pal(self):
        return self.app.pal

    def build(self):
        for w in self.winfo_children():
            w.destroy()

        ctk.CTkLabel(self, text="Analytics", font=(theme.FONT, 26, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=4)
        ctk.CTkLabel(self, text="Deep insights into your grind.",
                     font=(theme.FONT, 14), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=4, pady=(2, 8))

        outer = ctk.CTkScrollableFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True)

        # ---- top overview ----
        overview.build_insights(self, outer)
        overview.build_score(self, outer)
        self._export_bar(outer)
        overview.build_timeline(self, outer)

        # ---- tab bar ----
        bar = ctk.CTkFrame(outer, fg_color=self.pal["surface"], corner_radius=12,
                           border_width=1, border_color=self.pal["border"])
        bar.pack(fill="x", pady=(10, 4), padx=4)
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(padx=8, pady=8)
        self.tab_buttons = {}
        for key, label, _ in TABS:
            btn = ctk.CTkButton(inner, text=label, height=34, width=120,
                                font=(theme.FONT, 13, "bold"), corner_radius=9,
                                fg_color="transparent", text_color=self.pal["text_muted"],
                                hover_color=self.pal["surface_2"],
                                command=lambda k=key: self._switch(k))
            btn.pack(side="left", padx=3)
            self.tab_buttons[key] = btn

        # ---- tab content ----
        self.tab_host = ctk.CTkFrame(outer, fg_color="transparent")
        self.tab_host.pack(fill="both", expand=True)
        self._render_tab(animate=False)

    def _export_bar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", pady=(2, 2), padx=4)
        specs = [("⬇ Export CSV", export.export_csv),
                 ("📄 Export PDF", export.export_pdf),
                 ("✦ Share Card", export.share_card)]
        for label, fn in specs:
            ctk.CTkButton(bar, text=label, height=34, width=140, font=(theme.FONT, 12, "bold"),
                          corner_radius=9, fg_color=self.pal["surface_2"],
                          text_color=self.pal["text"], hover_color=self.pal["border"],
                          command=lambda f=fn: self._do_export(f)).pack(side="left", padx=4)
        self.export_status = ctk.CTkLabel(bar, text="", font=(theme.FONT, 12, "bold"),
                                          text_color=theme.SUCCESS)
        self.export_status.pack(side="left", padx=10)

    def _do_export(self, fn):
        try:
            path = fn(self)
        except Exception as e:
            self.export_status.configure(text=f"Export failed: {e}", text_color=theme.DANGER)
            return
        if path:
            import os
            self.export_status.configure(text=f"✓ Saved {os.path.basename(path)}",
                                         text_color=theme.SUCCESS)
            self.after(3000, lambda: self.export_status.configure(text=""))

    def _switch(self, key):
        if key == self.active:
            return
        # Debounce: cancel any pending switch scheduled within the last 80 ms
        if hasattr(self, "_switch_id") and self._switch_id:
            try:
                self.after_cancel(self._switch_id)
            except Exception:
                pass
        self._switch_id = self.after(80, lambda k=key: self._do_switch(k))

    def _do_switch(self, key):
        self._switch_id = None
        self.active = key
        AnalyticsView._last_tab = key
        self._render_tab(animate=True)

    def _render_tab(self, animate):
        if self.tab_view is not None:
            # Free matplotlib figures before destroying the frame
            if hasattr(self.tab_view, "cleanup"):
                self.tab_view.cleanup()
            self.tab_view.destroy()
        cls = next(c for k, _, c in TABS if k == self.active)
        self.tab_view = cls(self.tab_host, self.app)
        self.tab_view.build()
        self.tab_view.pack(fill="both", expand=True)
        # Charts run their own draw animations on load, which supplies the
        # motion — we avoid place()-based slides here to keep the single
        # outer scroll region intact.

        for k, btn in self.tab_buttons.items():
            if k == self.active:
                btn.configure(fg_color=theme.ACCENT, text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color=self.pal["text_muted"])
