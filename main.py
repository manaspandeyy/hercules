"""Hercules — a customizable daily tracker desktop app.

Standalone CustomTkinter window with a launch splash, top navigation bar,
an editable daily schedule checklist (with optional auto session popups),
animated analytics, a goals/course planner, mock tracking, a progress-report
analyser, settings, and a weekly self-assessment reminder. All data is stored
locally in JSON under ./data. No terminal needed once launched.

Make it yours: edit your schedule, goals, and standings right inside the app —
nothing here is hard-coded to any one person or course.
"""

from datetime import date, datetime

import customtkinter as ctk

import theme
import icon
import animations as anim
from splash import Splash
from dialogs import SundayReminder
from data_manager import DataManager
from views.schedule_view import ScheduleView
from views.analytics_view import AnalyticsView
from views.goals_view import GoalsView
from views.mocks_view import MocksView
from views.report_view import ReportView
from views.settings_view import SettingsView

# Top-nav order (Check-in removed).
NAV = [
    ("schedule", "📅 Schedule"),
    ("analytics", "📊 Analytics"),
    ("goals", "🎯 Goals & Course"),
    ("mocks", "📝 Mocks & Assessments"),
    ("report", "🧠 Progress Report"),
    ("settings", "⚙ Settings"),
]

WIN_W, WIN_H = 1280, 800
MIN_W, MIN_H = 1200, 700


class HerculesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.data = DataManager()
        self.mode = self.data.settings.get("theme", "dark")
        # restore saved color theme (updates theme.DARK/LIGHT/ACCENT globals)
        saved_color = self.data.settings.get("color_theme", "MIDNIGHT")
        theme.apply_theme(saved_color)

        ctk.set_appearance_mode(self.mode)
        ctk.set_default_color_theme("blue")

        self.title(self._title_text())
        self.minsize(MIN_W, MIN_H)
        anim.center_window(self, WIN_W, WIN_H)
        self._apply_icon()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.current = None
        self.view = None
        self.nav_buttons = {}
        self._views = {}   # cached view instances (everything except schedule)

        self._build_layout()
        self.show("schedule", animate=False)

    # ---- window chrome ---------------------------------------------------
    def _title_text(self):
        today = date.today()
        hour = datetime.now().hour
        greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        return f"{theme.APP_NAME} — {greet}, {today.strftime('%A, %B %d')}"

    def _apply_icon(self):
        try:
            ico_path, png_path = icon.ensure_icon()
            self.iconbitmap(ico_path)
        except Exception:
            try:
                from PIL import Image, ImageTk
                self._tk_icon = ImageTk.PhotoImage(Image.open(png_path))
                self.iconphoto(True, self._tk_icon)
            except Exception:
                pass

    @property
    def pal(self):
        return theme.palette(self.mode)

    # ---- layout (top nav) ------------------------------------------------
    def _build_layout(self):
        self.configure(fg_color=self.pal["bg"])

        topbar = ctk.CTkFrame(self, height=64, corner_radius=0,
                              fg_color=self.pal["sidebar"])
        topbar.pack(side="top", fill="x")
        topbar.pack_propagate(False)

        # brand (left)
        brand = ctk.CTkFrame(topbar, fg_color="transparent")
        brand.pack(side="left", padx=20)
        ctk.CTkLabel(brand, text="⚡", font=(theme.FONT, 20),
                     text_color=theme.ORANGE).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(brand, text=theme.APP_NAME, font=(theme.FONT, 19, "bold"),
                     text_color=self.pal["text"]).pack(side="left")

        # avatar (right of brand)
        self._build_avatar(brand)

        # theme toggle (right)
        self.theme_btn = ctk.CTkButton(
            topbar, text=self._theme_label(), width=110, height=36,
            font=(theme.FONT, 13), corner_radius=10,
            fg_color=self.pal["surface_2"], text_color=self.pal["text"],
            hover_color=self.pal["surface"], command=self.toggle_theme)
        self.theme_btn.pack(side="right", padx=16)

        # nav (centre/left, horizontal)
        nav = ctk.CTkFrame(topbar, fg_color="transparent")
        nav.pack(side="left", padx=8)
        for key, label in NAV:
            btn = ctk.CTkButton(
                nav, text=label, height=38, font=(theme.FONT, 13, "bold"),
                corner_radius=10, fg_color="transparent",
                text_color=self.pal["text_muted"], hover_color=self.pal["surface_2"],
                command=lambda k=key: self.show(k))
            btn.pack(side="left", padx=3)
            self.nav_buttons[key] = btn

        # accent divider under the bar
        ctk.CTkFrame(self, height=2, fg_color=theme.ACCENT, corner_radius=0).pack(
            side="top", fill="x")

        # content stage
        self.content = ctk.CTkFrame(self, fg_color=self.pal["bg"])
        self.content.pack(side="top", fill="both", expand=True)
        self.stage = ctk.CTkFrame(self.content, fg_color="transparent")
        self.stage.pack(fill="both", expand=True, padx=24, pady=20)

    def _build_avatar(self, parent):
        """Add a circular avatar button next to the brand. Click → day-count popup."""
        try:
            from PIL import ImageTk
            img = icon.get_avatar_image(36)
            if img is None:
                raise ValueError("no image")
            self._avatar_img = ImageTk.PhotoImage(img)
            btn = ctk.CTkButton(
                parent, image=self._avatar_img, text="", width=36, height=36,
                corner_radius=18, fg_color="transparent",
                hover_color=self.pal["surface_2"],
                command=self._avatar_popup)
            btn.pack(side="left", padx=(14, 0))
        except Exception:
            pass   # silently skip if PIL/image unavailable

    def _day_number(self):
        """Days since the user's journey start date (settings), min 1."""
        start_str = self.data.settings.get("start_date", "")
        try:
            start = date.fromisoformat(start_str)
        except (ValueError, TypeError):
            start = date.today()
        return max(1, (date.today() - start).days + 1)

    def _avatar_popup(self):
        name = self.data.settings.get("name", "").strip()
        day_num = self._day_number()
        popup = ctk.CTkToplevel(self)
        popup.title("")
        popup.resizable(False, False)
        import animations as _anim
        _anim.center_window(popup, 340, 160)
        popup.configure(fg_color=self.pal["surface"])
        popup.transient(self)
        popup.after(10, lambda: popup.grab_set())
        greeting = f"Hey {name} 👋" if name else "Hey there 👋"
        ctk.CTkLabel(popup, text=greeting,
                     font=(theme.FONT, 22, "bold"),
                     text_color=self.pal["text"]).pack(pady=(24, 4))
        ctk.CTkLabel(popup, text=f"Day {day_num} of your journey.",
                     font=(theme.FONT, 14), text_color=self.pal["text_muted"]).pack()
        ctk.CTkLabel(popup, text="Keep showing up. You're building it. ⚡",
                     font=(theme.FONT, 12), text_color=theme.ACCENT,
                     wraplength=300).pack(pady=(6, 0))
        ctk.CTkButton(popup, text="Let's go", height=36, corner_radius=8,
                      font=(theme.FONT, 13, "bold"), fg_color=theme.ACCENT,
                      hover_color=theme.ACCENT_HOVER,
                      command=popup.destroy).pack(pady=16)

    def _theme_label(self):
        return "☀  Light" if self.mode == "dark" else "🌙  Dark"

    # ---- navigation ------------------------------------------------------
    def _make_view(self, key):
        return {
            "schedule": ScheduleView, "analytics": AnalyticsView,
            "goals": GoalsView, "mocks": MocksView,
            "report": ReportView, "settings": SettingsView,
        }.get(key, ScheduleView)(self.stage, self)

    def show(self, key, animate=True):
        # Hide the current view (don't destroy — reuse on the next visit)
        if self.view is not None:
            try:
                self.view.place_forget()
            except Exception:
                pass

        self.current = key

        # Schedule is always rebuilt (lightweight, needs fresh check-off state).
        # All other views are cached and reused unless invalidated by on_data_changed.
        if key == "schedule" or key not in self._views:
            if key in self._views:
                try:
                    self._views.pop(key).destroy()
                except Exception:
                    pass
            new_view = self._make_view(key)
            if key != "schedule":
                self._views[key] = new_view
            self.view = new_view
        else:
            self.view = self._views[key]

        if animate:
            anim.slide_in(self.view)
        else:
            self.view.place(x=0, y=0, relwidth=1, relheight=1)

        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=theme.ACCENT, text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color=self.pal["text_muted"])

    def on_data_changed(self):
        """Invalidate data-dependent cached views; rebuild if one is currently shown."""
        # Destroy stale cached views so the next visit gets a fresh build.
        for key in ("analytics", "goals", "mocks", "report"):
            if key in self._views:
                try:
                    self._views.pop(key).destroy()
                except Exception:
                    pass
        if self.current in ("analytics", "goals", "mocks"):
            self.view = None   # avoid place_forget on just-destroyed widget
            self.show(self.current, animate=False)

    # ---- theme -----------------------------------------------------------
    def toggle_theme(self):
        self.mode = "light" if self.mode == "dark" else "dark"
        self.data.settings["theme"] = self.mode
        self.data.save_settings()
        ctk.set_appearance_mode(self.mode)

        # Drop cache before destroying children (widgets are about to go away).
        self._views = {}
        for w in self.winfo_children():
            w.destroy()
        self.nav_buttons = {}
        self.view = None
        self._build_layout()
        self.show(self.current or "schedule", animate=False)

    # ---- splash reveal + Sunday reminder --------------------------------
    def _on_close(self):
        """Save window state, close matplotlib figures, quit."""
        try:
            self.attributes("-alpha", 1.0)   # reset before saving state
            self.data.settings["window_state"] = "zoomed"
            self.data.save_settings()
        except Exception:
            pass
        try:
            import matplotlib.pyplot as plt
            plt.close("all")
        except Exception:
            pass
        self.destroy()

    def reveal(self):
        # Maximize FIRST, then make visible — avoids alpha getting stuck on Windows
        try:
            self.state("zoomed")
        except Exception:
            pass
        self.deiconify()
        self.lift()
        self._apply_icon()
        # Ensure fully opaque — skip fade to prevent alpha getting frozen mid-animation
        try:
            self.attributes("-alpha", 1.0)
        except Exception:
            pass
        self.after(900, self._maybe_sunday_reminder)

    def _maybe_sunday_reminder(self):
        from data_manager import today_key
        if date.today().weekday() == 6 and not any(
                a["date"] == today_key() for a in self.data.sunday):
            SundayReminder(self, self.data, on_saved=self.on_data_changed)


def main():
    # Tell Windows this is its own app (not Python) so the taskbar shows our icon
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(theme.APP_ID)
    except Exception:
        pass

    app = HerculesApp()
    app.withdraw()
    Splash(app, on_done=app.reveal)

    from quotes import QuoteNotifier
    QuoteNotifier().start()

    app.mainloop()


if __name__ == "__main__":
    main()
