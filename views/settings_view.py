"""Settings view — FIX 5: 5 sections (Color Scheme, Profile, Notifications,
Performance, Data).
"""

import json
import os
import shutil
import threading
from datetime import date
from tkinter import filedialog, messagebox

import customtkinter as ctk

import theme
import icon as icon_mod


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.build()

    @property
    def pal(self):
        return self.app.pal

    def _card(self, parent, title):
        c = ctk.CTkFrame(parent, fg_color=self.pal["surface"], corner_radius=14,
                         border_width=1, border_color=self.pal["border"])
        c.pack(fill="x", pady=8, padx=4)
        ctk.CTkLabel(c, text=title, font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(14, 8))
        return c

    def build(self):
        for w in self.winfo_children():
            w.destroy()
        data = self.app.data

        ctk.CTkLabel(self, text="Settings", font=(theme.FONT, 26, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=4)
        ctk.CTkLabel(self, text=f"Customize {theme.APP_NAME} to your liking.",
                     font=(theme.FONT, 14), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=4, pady=(2, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._color_scheme(scroll, data)
        self._profile_section(scroll, data)
        self._schedule_section(scroll, data)
        self._goals_section(scroll, data)
        self._notifications_section(scroll, data)
        self._performance_section(scroll, data)
        self._data_section(scroll, data)

    # ---- 1. Color scheme -------------------------------------------------
    def _color_scheme(self, parent, data):
        card = self._card(parent, "🎨  Color Scheme")
        active = theme.current_theme_name()

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=18, pady=(0, 16))

        for col_i, (name, t) in enumerate(theme.THEMES.items()):
            col = col_i % 4
            row = col_i // 4
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=row, column=col, padx=8, pady=6, sticky="nsew")
            grid.columnconfigure(col, weight=1)

            accent = t["accent"]
            is_active = (name == active)

            swatch = ctk.CTkButton(
                cell,
                text="✓" if is_active else "",
                font=(theme.FONT, 16, "bold"),
                text_color="#FFFFFF",
                fg_color=accent,
                hover_color=t["accent_hover"],
                width=44, height=44,
                corner_radius=22,
                border_width=3 if is_active else 0,
                border_color="#FFFFFF" if is_active else accent,
                command=lambda n=name: self._apply_theme(n),
            )
            swatch.pack()
            ctk.CTkLabel(cell, text=name, font=(theme.FONT, 10),
                         text_color=self.pal["text_muted"]).pack(pady=(3, 0))

        # dark/light mode toggle
        row_w = ctk.CTkFrame(card, fg_color="transparent")
        row_w.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkLabel(row_w, text="Mode", font=(theme.FONT, 13),
                     text_color=self.pal["text"]).pack(side="left")
        seg = ctk.CTkSegmentedButton(
            row_w, values=["Dark", "Light"],
            font=(theme.FONT, 13),
            selected_color=theme.ACCENT, selected_hover_color=theme.ACCENT_HOVER,
            unselected_color=self.pal["surface_2"], fg_color=self.pal["surface_2"],
            text_color=self.pal["text"],
            command=self._set_mode)
        seg.set("Dark" if self.app.mode == "dark" else "Light")
        seg.pack(side="right")

    def _apply_theme(self, name):
        theme.apply_theme(name, self.app)

    def _set_mode(self, value):
        want = "dark" if value == "Dark" else "light"
        if want != self.app.mode:
            self.app.toggle_theme()

    # ---- 2. Profile -------------------------------------------------------
    def _profile_section(self, parent, data):
        card = self._card(parent, "👤  Profile")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 16))

        # avatar preview
        try:
            from PIL import ImageTk
            img = icon_mod.get_avatar_image(52)
            if img:
                self._avatar_img = ctk.CTkImage(light_image=img, dark_image=img, size=(52, 52))
                av_lbl = ctk.CTkLabel(body, image=self._avatar_img, text="")
                av_lbl.pack(side="left", padx=(0, 18))
        except Exception:
            pass

        fields = ctk.CTkFrame(body, fg_color="transparent")
        fields.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(fields, text="Name", font=(theme.FONT, 12),
                     text_color=self.pal["text_muted"]).pack(anchor="w")
        self._name_ent = ctk.CTkEntry(fields, height=34, font=(theme.FONT, 13),
                                      fg_color=self.pal["surface_2"],
                                      border_color=self.pal["border"],
                                      placeholder_text="Your name")
        self._name_ent.insert(0, data.settings.get("name", ""))
        self._name_ent.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(fields, text="Journey start date (YYYY-MM-DD)",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(anchor="w")
        self._start_ent = ctk.CTkEntry(fields, height=34, font=(theme.FONT, 13),
                                       fg_color=self.pal["surface_2"],
                                       border_color=self.pal["border"])
        self._start_ent.insert(0, data.settings.get("start_date", date.today().isoformat()))
        self._start_ent.pack(fill="x", pady=(2, 8))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkButton(btn_row, text="📷  Change Photo", height=36, width=160,
                      font=(theme.FONT, 13), corner_radius=8,
                      fg_color=self.pal["surface_2"], text_color=self.pal["text"],
                      hover_color=self.pal["border"],
                      command=self._change_photo).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_row, text="Save", height=36, width=100,
                      font=(theme.FONT, 13, "bold"), corner_radius=8,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      text_color="#FFFFFF",
                      command=self._save_profile).pack(side="left")
        self._profile_status = ctk.CTkLabel(btn_row, text="",
                                            font=(theme.FONT, 12, "bold"),
                                            text_color=theme.SUCCESS)
        self._profile_status.pack(side="left", padx=10)

    def _change_photo(self):
        path = filedialog.askopenfilename(
            title="Select profile photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")])
        if not path:
            return
        dest = os.path.join(os.path.dirname(os.path.abspath(icon_mod.__file__)), "profile.jpg")
        try:
            from PIL import Image
            img = Image.open(path).convert("RGB")
            img.save(dest, "JPEG", quality=92)
            # clear cached icons
            for f in (icon_mod.ICO_PATH, icon_mod.PNG_PATH):
                try:
                    os.remove(f)
                except Exception:
                    pass
            self._profile_status.configure(text="✓ Photo saved — restart to see in taskbar")
        except Exception as e:
            self._profile_status.configure(
                text=f"Failed: {e}", text_color=theme.DANGER)

    def _save_profile(self):
        self.app.data.settings["name"] = self._name_ent.get().strip()
        self.app.data.settings["start_date"] = self._start_ent.get().strip()
        self.app.data.save_settings()
        self._profile_status.configure(text="✓ Saved", text_color=theme.SUCCESS)
        self.after(2000, lambda: self._profile_status.configure(text=""))

    # ---- 2b. Daily schedule editor --------------------------------------
    def _schedule_section(self, parent, data):
        card = self._card(parent, "📅  Daily Schedule")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkLabel(body,
                     text="Build your own plan for each day of the week — add, edit, "
                          "reorder and delete time slots. This is what shows on the "
                          "Schedule tab and drives your analytics.",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"],
                     wraplength=580, justify="left").pack(anchor="w", pady=(0, 10))
        ctk.CTkButton(body, text="✏  Edit Schedule", height=38, width=180,
                      font=(theme.FONT, 13, "bold"), corner_radius=8,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      text_color="#FFFFFF",
                      command=self._open_schedule_editor).pack(anchor="w")

    def _open_schedule_editor(self):
        from dialogs import ScheduleEditorDialog
        ScheduleEditorDialog(self.app, self.app.data,
                             on_saved=self.app.on_data_changed)

    # ---- 2c. Goals (target date / study pace / points target) -----------
    def _goals_section(self, parent, data):
        card = self._card(parent, "🎯  Goals")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 16))

        def field(label, value):
            ctk.CTkLabel(body, text=label, font=(theme.FONT, 12),
                         text_color=self.pal["text_muted"]).pack(anchor="w")
            ent = ctk.CTkEntry(body, height=34, font=(theme.FONT, 13),
                               fg_color=self.pal["surface_2"],
                               border_color=self.pal["border"])
            ent.insert(0, str(value))
            ent.pack(fill="x", pady=(2, 8))
            return ent

        hrs = round(data.goals.get("study_minutes_per_day", 120) / 60, 2)
        self._target_ent = field("Target completion date (YYYY-MM-DD)",
                                  data.goals.get("target_date", ""))
        self._hours_ent = field("Study hours per day", hrs)
        self._points_target_ent = field("Points target (leaderboard goal)",
                                         data.goals.get("points_target", 0))

        ctk.CTkButton(body, text="Save Goals", height=36, width=120,
                      font=(theme.FONT, 13, "bold"), corner_radius=8,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      text_color="#FFFFFF",
                      command=self._save_goals).pack(anchor="w")
        self._goals_status = ctk.CTkLabel(body, text="", font=(theme.FONT, 12, "bold"),
                                          text_color=theme.SUCCESS)
        self._goals_status.pack(anchor="w", pady=4)

    def _save_goals(self):
        g = self.app.data.goals
        td = self._target_ent.get().strip()
        if td:
            g["target_date"] = td
        try:
            g["study_minutes_per_day"] = max(30, int(float(self._hours_ent.get()) * 60))
        except (ValueError, TypeError):
            pass
        try:
            g["points_target"] = max(0, int(float(self._points_target_ent.get())))
        except (ValueError, TypeError):
            pass
        self.app.data.save_goals()
        self.app.on_data_changed()
        self._goals_status.configure(text="✓ Saved", text_color=theme.SUCCESS)
        self.after(2000, lambda: self._goals_status.configure(text=""))

    # ---- 3. Notifications -------------------------------------------------
    def _notifications_section(self, parent, data):
        card = self._card(parent, "🔔  Notifications")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 16))

        # toggle on/off
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="Motivational quote notifications",
                     font=(theme.FONT, 13), text_color=self.pal["text"]).pack(side="left")
        self._notif_var = ctk.BooleanVar(
            value=data.settings.get("quotes_enabled", True))
        ctk.CTkSwitch(row, variable=self._notif_var, text="",
                      progress_color=theme.ACCENT,
                      command=self._save_notif).pack(side="right")

        # min interval
        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(row2, text="Min interval (minutes)", font=(theme.FONT, 12),
                     text_color=self.pal["text_muted"]).pack(side="left")
        self._min_lbl = ctk.CTkLabel(row2, font=(theme.FONT, 12, "bold"),
                                     text_color=theme.ACCENT,
                                     text=str(data.settings.get("quotes_min_min", 15)))
        self._min_lbl.pack(side="right")
        self._min_slider = ctk.CTkSlider(body, from_=15, to=120, number_of_steps=21,
                                         progress_color=theme.ACCENT,
                                         button_color=theme.ACCENT,
                                         command=lambda v: self._min_lbl.configure(
                                             text=str(int(v))))
        self._min_slider.set(data.settings.get("quotes_min_min", 15))
        self._min_slider.pack(fill="x", pady=(2, 8))

        # max interval
        row3 = ctk.CTkFrame(body, fg_color="transparent")
        row3.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(row3, text="Max interval (minutes)", font=(theme.FONT, 12),
                     text_color=self.pal["text_muted"]).pack(side="left")
        self._max_lbl = ctk.CTkLabel(row3, font=(theme.FONT, 12, "bold"),
                                     text_color=theme.ACCENT,
                                     text=str(data.settings.get("quotes_max_min", 120)))
        self._max_lbl.pack(side="right")
        self._max_slider = ctk.CTkSlider(body, from_=60, to=240, number_of_steps=30,
                                         progress_color=theme.ACCENT,
                                         button_color=theme.ACCENT,
                                         command=lambda v: self._max_lbl.configure(
                                             text=str(int(v))))
        self._max_slider.set(data.settings.get("quotes_max_min", 120))
        self._max_slider.pack(fill="x", pady=(2, 8))

        # test button
        test_row = ctk.CTkFrame(body, fg_color="transparent")
        test_row.pack(fill="x", pady=4)
        ctk.CTkButton(test_row, text="🔔 Test — show a quote now",
                      height=36, font=(theme.FONT, 13), corner_radius=8,
                      fg_color=self.pal["surface_2"], text_color=self.pal["text"],
                      hover_color=self.pal["border"],
                      command=self._test_quote).pack(side="left")
        ctk.CTkButton(test_row, text="Save", height=36, width=80,
                      font=(theme.FONT, 13, "bold"), corner_radius=8,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      text_color="#FFFFFF",
                      command=self._save_notif).pack(side="left", padx=10)

    def _save_notif(self):
        s = self.app.data.settings
        s["quotes_enabled"] = self._notif_var.get()
        s["quotes_min_min"] = int(self._min_slider.get())
        s["quotes_max_min"] = int(self._max_slider.get())
        self.app.data.save_settings()

    def _test_quote(self):
        try:
            from quotes import _next_quote
            from plyer import notification
            q = _next_quote()
            notification.notify(title=theme.APP_NAME, message=q,
                                app_name=theme.APP_NAME, timeout=8)
        except Exception as e:
            messagebox.showinfo("Quote test", str(e))

    # ---- 4. Performance --------------------------------------------------
    def _performance_section(self, parent, data):
        card = self._card(parent, "⚡  Performance")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 16))

        # animations toggle
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="UI Animations", font=(theme.FONT, 13),
                     text_color=self.pal["text"]).pack(side="left")
        self._anim_var = ctk.BooleanVar(
            value=data.settings.get("animations", True))
        ctk.CTkSwitch(row, variable=self._anim_var, text="",
                      progress_color=theme.ACCENT).pack(side="right")

        # chart quality
        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(8, 4))
        ctk.CTkLabel(row2, text="Chart quality  (DPI: Low=60  Medium=72  High=90)",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(side="left")
        self._quality_var = ctk.StringVar(
            value=data.settings.get("chart_quality", "Medium"))
        ctk.CTkSegmentedButton(body, values=["Low", "Medium", "High"],
                               variable=self._quality_var,
                               font=(theme.FONT, 13),
                               selected_color=theme.ACCENT,
                               selected_hover_color=theme.ACCENT_HOVER,
                               unselected_color=self.pal["surface_2"],
                               fg_color=self.pal["surface_2"],
                               text_color=self.pal["text"]).pack(anchor="w", pady=(2, 8))

        ctk.CTkButton(body, text="Save Performance Settings", height=36,
                      font=(theme.FONT, 13, "bold"), corner_radius=8,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      text_color="#FFFFFF",
                      command=self._save_perf).pack(anchor="w")

    def _save_perf(self):
        s = self.app.data.settings
        s["animations"] = self._anim_var.get()
        q = self._quality_var.get()
        s["chart_quality"] = q
        dpi_map = {"Low": 60, "Medium": 72, "High": 90}
        import views.analytics.charts as cc
        cc.CHART_DPI = dpi_map.get(q, 72)
        self.app.data.save_settings()

    # ---- 5. Data ---------------------------------------------------------
    def _data_section(self, parent, data):
        card = self._card(parent, "💾  Data")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 16))

        def btn(parent, text, command, color=None):
            ctk.CTkButton(parent, text=text, height=36, font=(theme.FONT, 13),
                          corner_radius=8,
                          fg_color=color or self.pal["surface_2"],
                          hover_color=self.pal["border"] if not color else color,
                          text_color="#FFFFFF" if color else self.pal["text"],
                          command=command).pack(
                side="left", padx=(0, 10), pady=4)

        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x")
        btn(row1, "⬇  Export backup JSON", self._export_backup)
        btn(row1, "⬆  Import backup JSON", self._import_backup)

        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(4, 0))
        btn(row2, "🗑  Clear today's data", self._clear_today, color=theme.ORANGE)
        btn(row2, "⚠  Reset ALL data", self._reset_all, color=theme.DANGER)

        self._data_status = ctk.CTkLabel(body, text="", font=(theme.FONT, 12, "bold"),
                                         text_color=theme.SUCCESS)
        self._data_status.pack(anchor="w", pady=4)

    def _export_backup(self):
        from data_manager import BASE_DIR, DATA_DIR
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON backup", "*.json")],
            title=f"Export {theme.APP_NAME} backup")
        if not path:
            return
        combined = {}
        for fname in ("daily_log.json", "goals.json", "mocks.json",
                      "sunday.json", "schedules.json", "settings.json"):
            fp = os.path.join(DATA_DIR, fname)
            if os.path.exists(fp):
                with open(fp, encoding="utf-8") as f:
                    combined[fname] = json.load(f)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2)
        self._data_status.configure(text="✓ Backup exported")
        self.after(3000, lambda: self._data_status.configure(text=""))

    def _import_backup(self):
        from data_manager import DATA_DIR
        path = filedialog.askopenfilename(
            filetypes=[("JSON backup", "*.json")],
            title=f"Import {theme.APP_NAME} backup")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                combined = json.load(f)
            for fname, content in combined.items():
                dest = os.path.join(DATA_DIR, fname)
                with open(dest, "w", encoding="utf-8") as f2:
                    json.dump(content, f2, indent=2)
            self._data_status.configure(text="✓ Imported — restart to apply")
        except Exception as e:
            self._data_status.configure(
                text=f"Import failed: {e}", text_color=theme.DANGER)

    def _clear_today(self):
        from data_manager import today_key
        if not messagebox.askyesno("Clear today",
                                   "Delete today's check-offs and sessions?"):
            return
        key = today_key()
        if key in self.app.data.log:
            del self.app.data.log[key]
            self.app.data.save_log()
            self.app.on_data_changed()
        self._data_status.configure(text="✓ Today's data cleared")
        self.after(2500, lambda: self._data_status.configure(text=""))

    def _reset_all(self):
        if not messagebox.askyesno(
                "Reset ALL data",
                "This permanently deletes ALL history, goals, and progress.\n"
                "This cannot be undone. Are you sure?"):
            return
        from data_manager import DATA_DIR, DAILY_LOG, GOALS, MOCKS, SUNDAY
        for fp in (DAILY_LOG, GOALS, MOCKS, SUNDAY):
            try:
                os.remove(fp)
            except Exception:
                pass
        messagebox.showinfo("Reset complete", "All data cleared. Restart the app.")
