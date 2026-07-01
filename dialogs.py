"""Auto-triggered check-in popups and in-app editors.

DSADialog   — fired when a task containing "dsa" is checked off. Logs
              easy/medium/hard counts, computes points (30/40/50) and rolls
              them into the leaderboard total.
StudyDialog — fired when a study/course task is checked off. Logs lectures
              watched + completion feel and bumps your course lectures.
ScheduleEditorDialog   — edit the per-weekday schedule.
LeaderboardEditorDialog — add/edit/remove leaderboard competitors.
"""

import copy

import customtkinter as ctk

import theme
import animations as anim
from data_manager import DSA_POINTS


class _BaseDialog(ctk.CTkToplevel):
    """Shared modal scaffolding: centred, fades in, grabs focus."""

    def __init__(self, master, width=420, height=420):
        super().__init__(master)
        self.pal = theme.palette(master.mode)
        self.configure(fg_color=self.pal["surface"])
        self.resizable(False, False)
        anim.center_window(self, width, height)
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass
        self.transient(master)
        self.after(10, self._grab)
        anim.fade_in(self, duration=260)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _stepper(self, parent, label, color, initial=0, minimum=0):
        """A row: label on the left, [-]  N  [+] on the right. Returns getter."""
        row = ctk.CTkFrame(parent, fg_color=self.pal["surface_2"], corner_radius=12)
        row.pack(fill="x", pady=6, padx=4)

        ctk.CTkLabel(
            row, text=label, font=(theme.FONT, 14, "bold"),
            text_color=color, anchor="w",
        ).pack(side="left", padx=16, pady=14)

        state = {"value": initial}
        count = ctk.CTkLabel(row, text=str(initial), width=44,
                             font=(theme.FONT, 18, "bold"),
                             text_color=self.pal["text"])

        def render():
            count.configure(text=str(state["value"]))
            if self.on_change:
                self.on_change()

        def bump(delta):
            state["value"] = max(minimum, state["value"] + delta)
            render()

        plus = ctk.CTkButton(row, text="+", width=38, height=34,
                             font=(theme.FONT, 18, "bold"), corner_radius=8,
                             fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                             command=lambda: bump(1))
        minus = ctk.CTkButton(row, text="−", width=38, height=34,
                              font=(theme.FONT, 18, "bold"), corner_radius=8,
                              fg_color=self.pal["surface"], hover_color=self.pal["border"],
                              text_color=self.pal["text"],
                              command=lambda: bump(-1))
        plus.pack(side="right", padx=(4, 14), pady=12)
        count.pack(side="right")
        minus.pack(side="right", padx=(14, 4), pady=12)
        return lambda: state["value"]

    def _close(self):
        anim.fade_out(self, duration=180, on_done=self.destroy)


class DSADialog(_BaseDialog):
    _NO_UNIT = "— No unit sync —"

    def __init__(self, master, data, on_saved=None):
        self.on_change = None
        super().__init__(master, 440, 540)
        self.data = data
        self.on_saved = on_saved
        saved = data.get_dsa_detail()

        ctk.CTkLabel(self, text="DSA Session Done 🧠",
                     font=(theme.FONT, 22, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=24, pady=(22, 2))
        ctk.CTkLabel(self, text="Log what you solved — points auto-add to the leaderboard.",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=24, pady=(0, 14))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=20)
        self.get_easy = self._stepper(body, f"Easy  ·  {DSA_POINTS['easy']} pts",
                                      theme.SUCCESS, saved.get("easy", 0))
        self.get_medium = self._stepper(body, f"Medium  ·  {DSA_POINTS['medium']} pts",
                                        theme.WARNING, saved.get("medium", 0))
        self.get_hard = self._stepper(body, f"Hard  ·  {DSA_POINTS['hard']} pts",
                                      theme.DANGER, saved.get("hard", 0))

        self.points_lbl = ctk.CTkLabel(self, text="", font=(theme.FONT, 15, "bold"),
                                       text_color=theme.ACCENT)
        self.points_lbl.pack(pady=(10, 2))
        self.on_change = self._recalc
        self._recalc()

        # ---- unit selector (P7) ----
        units = data.goals.get("course_units", [])
        self._unit_names = [self._NO_UNIT] + [u["name"] for u in units]
        saved_idx = saved.get("unit_index")
        default_unit = (self._unit_names[saved_idx + 1]
                        if saved_idx is not None and saved_idx + 1 < len(self._unit_names)
                        else self._NO_UNIT)
        ctk.CTkLabel(self, text="Sync questions to unit assignments:",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=24, pady=(8, 2))
        self.unit_var = ctk.StringVar(value=default_unit)
        ctk.CTkOptionMenu(self, values=self._unit_names, variable=self.unit_var,
                          font=(theme.FONT, 13),
                          fg_color=self.pal["surface_2"],
                          button_color=theme.ACCENT,
                          button_hover_color=theme.ACCENT_HOVER,
                          dropdown_fg_color=self.pal["surface"],
                          text_color=self.pal["text"],
                          height=36).pack(fill="x", padx=24, pady=(0, 4))

        self._buttons()

    def _recalc(self):
        e, m, h = self.get_easy(), self.get_medium(), self.get_hard()
        pts = e * DSA_POINTS["easy"] + m * DSA_POINTS["medium"] + h * DSA_POINTS["hard"]
        self.points_lbl.configure(
            text=f"Today's points:  {e}E + {m}M + {h}H = {pts} pts")

    def _selected_unit_index(self):
        """Return int index into course_units, or None if no unit selected."""
        name = self.unit_var.get()
        if name == self._NO_UNIT:
            return None
        try:
            return self._unit_names.index(name) - 1   # -1 because index 0 is NO_UNIT
        except ValueError:
            return None

    def _buttons(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(8, 18), side="bottom")
        ctk.CTkButton(bar, text="Cancel", height=42, width=120,
                      font=(theme.FONT, 14), corner_radius=10,
                      fg_color=self.pal["surface_2"], text_color=self.pal["text"],
                      hover_color=self.pal["border"], command=self._close).pack(side="left")
        ctk.CTkButton(bar, text="Confirm", height=42, corner_radius=10,
                      font=(theme.FONT, 14, "bold"),
                      fg_color=theme.SUCCESS, hover_color="#00997A",
                      command=self._confirm).pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _confirm(self):
        self.data.set_dsa_session(
            self.get_easy(), self.get_medium(), self.get_hard(),
            unit_index=self._selected_unit_index())
        if self.on_saved:
            self.on_saved()
        self._close()


class StudyDialog(_BaseDialog):
    FEELS = ["Struggled", "Okay", "Confident"]

    def __init__(self, master, data, on_saved=None):
        self.on_change = None
        super().__init__(master, 440, 400)
        self.data = data
        self.on_saved = on_saved
        saved = data.get_study_detail()

        ctk.CTkLabel(self, text="Study Session Done 📖",
                     font=(theme.FONT, 22, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=24, pady=(22, 2))
        ctk.CTkLabel(self, text="Lectures auto-add to your course progress.",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=24, pady=(0, 14))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=20)
        self.get_lectures = self._stepper(body, "Lectures watched today",
                                          theme.INFO, saved.get("lectures", 0))

        ctk.CTkLabel(self, text="Completion feel?", font=(theme.FONT, 14, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=24, pady=(16, 6))
        self.feel = ctk.StringVar(value=saved.get("feel", "Okay"))
        ctk.CTkSegmentedButton(self, values=self.FEELS, variable=self.feel,
                               font=(theme.FONT, 13),
                               selected_color=theme.ACCENT,
                               selected_hover_color=theme.ACCENT_HOVER,
                               unselected_color=self.pal["surface_2"],
                               fg_color=self.pal["surface_2"],
                               text_color=self.pal["text"]).pack(padx=24, anchor="w")

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(8, 18), side="bottom")
        ctk.CTkButton(bar, text="Cancel", height=42, width=120,
                      font=(theme.FONT, 14), corner_radius=10,
                      fg_color=self.pal["surface_2"], text_color=self.pal["text"],
                      hover_color=self.pal["border"], command=self._close).pack(side="left")
        ctk.CTkButton(bar, text="Confirm", height=42, corner_radius=10,
                      font=(theme.FONT, 14, "bold"),
                      fg_color=theme.SUCCESS, hover_color="#00997A",
                      command=self._confirm).pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _confirm(self):
        self.data.set_study_session(self.get_lectures(), self.feel.get())
        if self.on_saved:
            self.on_saved()
        self._close()


def _labeled_entry(parent, pal, label, default="", width=120):
    """Vertical label + entry; returns the CTkEntry."""
    col = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(col, text=label, font=(theme.FONT, 12), anchor="w",
                 text_color=pal["text_muted"]).pack(fill="x")
    ent = ctk.CTkEntry(col, height=34, width=width, font=(theme.FONT, 13),
                       fg_color=pal["surface_2"], border_color=pal["border"])
    if default not in ("", None):
        ent.insert(0, str(default))
    ent.pack(fill="x")
    return col, ent


class SundayAssessmentDialog(_BaseDialog):
    """Weekly self-assessment logger. Multiple entries can be saved per Sunday."""

    DIFF = ["Easy", "Medium", "Hard"]

    def __init__(self, master, data, on_saved=None):
        self.on_change = None
        super().__init__(master, 460, 540)
        self.data = data
        self.on_saved = on_saved
        self.saved_count = 0

        ctk.CTkLabel(self, text="Weekly Self-Assessment 📝",
                     font=(theme.FONT, 22, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=24, pady=(22, 2))
        ctk.CTkLabel(self, text="Log one or more papers you tested yourself on today.",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=24, pady=(0, 12))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=24)

        col, self.topic = _labeled_entry(body, self.pal, "Topic tested", width=400)
        col.pack(fill="x", pady=6)

        score_row = ctk.CTkFrame(body, fg_color="transparent")
        score_row.pack(fill="x", pady=6)
        c1, self.score = _labeled_entry(score_row, self.pal, "Score", "0", width=120)
        c1.pack(side="left")
        ctk.CTkLabel(score_row, text="/", font=(theme.FONT, 20),
                     text_color=self.pal["text_muted"]).pack(side="left", padx=8, pady=(18, 0))
        c2, self.total = _labeled_entry(score_row, self.pal, "Out of", "20", width=120)
        c2.pack(side="left")
        c3, self.time = _labeled_entry(score_row, self.pal, "Time (min)", "", width=120)
        c3.pack(side="right")

        ctk.CTkLabel(body, text="Difficulty", font=(theme.FONT, 12),
                     text_color=self.pal["text_muted"]).pack(anchor="w", pady=(8, 2))
        self.diff = ctk.StringVar(value="Medium")
        ctk.CTkSegmentedButton(body, values=self.DIFF, variable=self.diff,
                               font=(theme.FONT, 13), selected_color=theme.ACCENT,
                               selected_hover_color=theme.ACCENT_HOVER,
                               unselected_color=self.pal["surface_2"],
                               fg_color=self.pal["surface_2"],
                               text_color=self.pal["text"]).pack(anchor="w")

        col, self.notes = _labeled_entry(body, self.pal, "Notes / weak areas", width=400)
        col.pack(fill="x", pady=(8, 4))

        self.status = ctk.CTkLabel(self, text="", font=(theme.FONT, 12, "bold"),
                                   text_color=theme.SUCCESS)
        self.status.pack(pady=(4, 0))

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(8, 18), side="bottom")
        ctk.CTkButton(bar, text="Done", height=42, width=110, font=(theme.FONT, 14),
                      corner_radius=10, fg_color=self.pal["surface_2"],
                      text_color=self.pal["text"], hover_color=self.pal["border"],
                      command=self._close).pack(side="left")
        ctk.CTkButton(bar, text="Save & Add Another", height=42, corner_radius=10,
                      font=(theme.FONT, 13, "bold"), fg_color=self.pal["surface_2"],
                      text_color=self.pal["text"], hover_color=self.pal["border"],
                      command=lambda: self._save(keep_open=True)).pack(side="left", padx=8)
        ctk.CTkButton(bar, text="Save", height=42, corner_radius=10,
                      font=(theme.FONT, 14, "bold"), fg_color=theme.SUCCESS,
                      hover_color="#16A34A",
                      command=lambda: self._save(keep_open=False)).pack(
            side="right", fill="x", expand=True, padx=(8, 0))

    def _save(self, keep_open):
        def i(e, d=0):
            try:
                return int(float(e.get()))
            except (ValueError, TypeError):
                return d
        topic = self.topic.get().strip() or "Untitled"
        self.data.add_sunday_assessment(topic, i(self.score), i(self.total, 1) or 1,
                                        self.diff.get(), i(self.time), self.notes.get().strip())
        self.saved_count += 1
        if self.on_saved:
            self.on_saved()
        if keep_open:
            self.status.configure(text=f"✓ Saved ({self.saved_count}) — add another")
            for e in (self.topic, self.score, self.time, self.notes):
                e.delete(0, "end")
            self.score.insert(0, "0")
            self.topic.focus_set()
        else:
            self._close()


class MockDialog(_BaseDialog):
    """Edit a single mock test attempt."""

    def __init__(self, master, data, index, on_saved=None):
        self.on_change = None
        super().__init__(master, 440, 470)
        self.data = data
        self.index = index
        self.on_saved = on_saved
        m = data.mocks[index]

        ctk.CTkLabel(self, text=m["name"], font=(theme.FONT, 20, "bold"),
                     text_color=self.pal["text"], wraplength=380, justify="left").pack(
            anchor="w", padx=24, pady=(22, 2))
        ctk.CTkLabel(self, text="Log your attempt — pass is 60%+.",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=24, pady=(0, 12))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=24)

        self.attempted = ctk.BooleanVar(value=m.get("attempted", False))
        ctk.CTkSwitch(body, text="Attempted", variable=self.attempted,
                      font=(theme.FONT, 14), progress_color=theme.SUCCESS,
                      text_color=self.pal["text"], command=self._recalc).pack(anchor="w", pady=(0, 6))

        from datetime import date as _date
        col, self.date = _labeled_entry(body, self.pal, "Date (YYYY-MM-DD)",
                                        m.get("date") or _date.today().isoformat(), width=400)
        col.pack(fill="x", pady=6)

        score_row = ctk.CTkFrame(body, fg_color="transparent")
        score_row.pack(fill="x", pady=6)
        c1, self.score = _labeled_entry(score_row, self.pal, "Score", m.get("score", 0), 150)
        c1.pack(side="left")
        ctk.CTkLabel(score_row, text="/", font=(theme.FONT, 20),
                     text_color=self.pal["text_muted"]).pack(side="left", padx=8, pady=(18, 0))
        c2, self.total = _labeled_entry(score_row, self.pal, "Total marks", m.get("total", 0), 150)
        c2.pack(side="left")
        for e in (self.score, self.total):
            e.bind("<KeyRelease>", lambda _e: self._recalc())

        col, self.notes = _labeled_entry(body, self.pal, "Notes / weak areas",
                                         m.get("notes", ""), width=400)
        col.pack(fill="x", pady=6)

        self.result = ctk.CTkLabel(self, text="", font=(theme.FONT, 15, "bold"))
        self.result.pack(pady=(8, 0))
        self._recalc()

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(8, 18), side="bottom")
        ctk.CTkButton(bar, text="Cancel", height=42, width=120, font=(theme.FONT, 14),
                      corner_radius=10, fg_color=self.pal["surface_2"],
                      text_color=self.pal["text"], hover_color=self.pal["border"],
                      command=self._close).pack(side="left")
        ctk.CTkButton(bar, text="Save", height=42, corner_radius=10,
                      font=(theme.FONT, 14, "bold"), fg_color=theme.SUCCESS,
                      hover_color="#16A34A", command=self._save).pack(
            side="right", fill="x", expand=True, padx=(10, 0))

    def _nums(self):
        def i(e):
            try:
                return int(float(e.get()))
            except (ValueError, TypeError):
                return 0
        return i(self.score), i(self.total)

    def _recalc(self):
        s, t = self._nums()
        if not self.attempted.get():
            self.result.configure(text="Not attempted yet", text_color=self.pal["text_muted"])
            return
        if t <= 0:
            self.result.configure(text="Enter total marks", text_color=self.pal["text_muted"])
            return
        pct = s / t * 100
        passed = pct >= 60
        self.result.configure(
            text=f"{pct:.0f}%  ·  {'PASS ✅' if passed else 'FAIL ❌'}",
            text_color=theme.SUCCESS if passed else theme.DANGER)

    def _save(self):
        s, t = self._nums()
        self.data.update_mock(self.index, self.attempted.get(), self.date.get().strip(),
                              s, t, self.notes.get().strip())
        if self.on_saved:
            self.on_saved()
        self._close()


class UnitEditDialog(_BaseDialog):
    """Edit the done/total counts for one course unit."""

    def __init__(self, master, data, index, on_saved=None):
        self.on_change = None
        super().__init__(master, 460, 420)
        self.data = data
        self.index = index
        self.on_saved = on_saved
        u = data.goals["course_units"][index]

        ctk.CTkLabel(self, text=u["name"], font=(theme.FONT, 19, "bold"),
                     text_color=self.pal["text"], wraplength=400, justify="left").pack(
            anchor="w", padx=24, pady=(22, 12))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=24)
        self.entries = {}
        for kind, color in (("lectures", theme.INFO), ("assignments", theme.ACCENT),
                            ("assessments", theme.TEAL)):
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=8)
            ctk.CTkLabel(row, text=kind.capitalize(), font=(theme.FONT, 14, "bold"),
                         text_color=color, width=120, anchor="w").pack(side="left")
            c1, done = _labeled_entry(row, self.pal, "Done", u[f"{kind}_done"], 110)
            c1.pack(side="left", padx=(0, 8))
            c2, total = _labeled_entry(row, self.pal, "Total", u[f"{kind}_total"], 110)
            c2.pack(side="left")
            self.entries[kind] = (done, total)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(8, 18), side="bottom")
        ctk.CTkButton(bar, text="Cancel", height=42, width=120, font=(theme.FONT, 14),
                      corner_radius=10, fg_color=self.pal["surface_2"],
                      text_color=self.pal["text"], hover_color=self.pal["border"],
                      command=self._close).pack(side="left")
        ctk.CTkButton(bar, text="Save", height=42, corner_radius=10,
                      font=(theme.FONT, 14, "bold"), fg_color=theme.SUCCESS,
                      hover_color="#16A34A", command=self._save).pack(
            side="right", fill="x", expand=True, padx=(10, 0))

    def _save(self):
        for kind, (done_e, total_e) in self.entries.items():
            self.data.update_unit(self.index, f"{kind}_total", total_e.get())
            self.data.update_unit(self.index, f"{kind}_done", done_e.get())
        if self.on_saved:
            self.on_saved()
        self._close()


class ReferralsDialog(_BaseDialog):
    """Referral Requests check-in — how many sent, any responses, notes."""

    def __init__(self, master, data, on_saved=None):
        self.on_change = None
        super().__init__(master, 440, 440)
        self.data = data
        self.on_saved = on_saved
        saved = data.get_referral_session()
        self._sent = saved.get("sent", 0)
        self._sent_btns = []

        ctk.CTkLabel(self, text="Referral Requests 🤝",
                     font=(theme.FONT, 22, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=24, pady=(22, 2))
        ctk.CTkLabel(self, text="Quality over quantity — max 3/day. Who did you reach out to?",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=24, pady=(0, 14))

        # ---- sent count (0 / 1 / 2 / 3 buttons) ----
        ctk.CTkLabel(self, text="Referral requests sent today:",
                     font=(theme.FONT, 14, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=24)
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(anchor="w", padx=24, pady=(6, 0))
        for n in (0, 1, 2, 3):
            b = ctk.CTkButton(btn_row, text=str(n), width=64, height=44,
                              font=(theme.FONT, 18, "bold"), corner_radius=10,
                              command=lambda v=n: self._set_sent(v))
            b.pack(side="left", padx=(0, 8))
            self._sent_btns.append(b)
        self._refresh_sent_btns()

        # ---- responses ----
        self.on_change = None  # _stepper needs this attribute
        ctk.CTkLabel(self, text="Positive responses received?",
                     font=(theme.FONT, 14, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=24, pady=(16, 4))
        resp_row = ctk.CTkFrame(self, fg_color="transparent")
        resp_row.pack(fill="x", padx=20)
        self.get_responses = self._stepper(resp_row, "Responses",
                                           theme.SUCCESS, saved.get("responses", 0))

        # ---- notes ----
        ctk.CTkLabel(self, text="Notes  (who / company / outcome):",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=24, pady=(12, 2))
        self.notes_ent = ctk.CTkEntry(self, height=34, font=(theme.FONT, 13),
                                       fg_color=self.pal["surface_2"],
                                       border_color=self.pal["border"])
        self.notes_ent.pack(fill="x", padx=24)
        if saved.get("notes"):
            self.notes_ent.insert(0, saved["notes"])

        # ---- buttons ----
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(16, 18), side="bottom")
        ctk.CTkButton(bar, text="Cancel", height=42, width=120,
                      font=(theme.FONT, 14), corner_radius=10,
                      fg_color=self.pal["surface_2"], text_color=self.pal["text"],
                      hover_color=self.pal["border"], command=self._close).pack(side="left")
        ctk.CTkButton(bar, text="Save", height=42, corner_radius=10,
                      font=(theme.FONT, 14, "bold"), fg_color=theme.SUCCESS,
                      hover_color="#16A34A", command=self._save).pack(
            side="right", fill="x", expand=True, padx=(10, 0))

    def _set_sent(self, v):
        self._sent = v
        self._refresh_sent_btns()

    def _refresh_sent_btns(self):
        for i, b in enumerate(self._sent_btns):
            if i == self._sent:
                b.configure(fg_color=theme.ACCENT, text_color="#FFFFFF")
            else:
                b.configure(fg_color=self.pal["surface_2"], text_color=self.pal["text"])

    def _save(self):
        self.data.set_referral_session(self._sent, self.get_responses(),
                                       self.notes_ent.get().strip())
        if self.on_saved:
            self.on_saved()
        self._close()


class ColdEmailsDialog(_BaseDialog):
    """HR Cold Emails check-in — how many sent, source, replies, notes."""

    SOURCES = ["Telegram", "LinkedIn", "Other"]

    def __init__(self, master, data, on_saved=None):
        self.on_change = None
        super().__init__(master, 440, 480)
        self.data = data
        self.on_saved = on_saved
        saved = data.get_cold_email_session()
        self._source = saved.get("source", "Telegram")
        self._src_btns = []

        ctk.CTkLabel(self, text="Cold Emails Done 📧",
                     font=(theme.FONT, 22, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=24, pady=(22, 2))
        ctk.CTkLabel(self, text="Log tonight's outreach — sourced from Telegram, LinkedIn, or other.",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=24, pady=(0, 12))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=20)

        # ---- sent count (stepper, no upper limit) ----
        self.get_sent = self._stepper(body, "Cold emails sent tonight",
                                      theme.ACCENT, saved.get("sent", 0))

        # ---- source ----
        ctk.CTkLabel(self, text="Source:", font=(theme.FONT, 14, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=24, pady=(14, 4))
        src_row = ctk.CTkFrame(self, fg_color="transparent")
        src_row.pack(anchor="w", padx=24)
        for s in self.SOURCES:
            b = ctk.CTkButton(src_row, text=s, width=100, height=36,
                              font=(theme.FONT, 13, "bold"), corner_radius=8,
                              command=lambda v=s: self._set_source(v))
            b.pack(side="left", padx=(0, 6))
            self._src_btns.append(b)
        self._refresh_source_btns()

        # ---- replies ----
        body2 = ctk.CTkFrame(self, fg_color="transparent")
        body2.pack(fill="x", padx=20)
        self.get_replies = self._stepper(body2, "Replies / callbacks received today",
                                         theme.SUCCESS, saved.get("replies", 0))

        # ---- notes ----
        ctk.CTkLabel(self, text="Notes  (optional):",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=24, pady=(12, 2))
        self.notes_ent = ctk.CTkEntry(self, height=34, font=(theme.FONT, 13),
                                       fg_color=self.pal["surface_2"],
                                       border_color=self.pal["border"])
        self.notes_ent.pack(fill="x", padx=24)
        if saved.get("notes"):
            self.notes_ent.insert(0, saved["notes"])

        # ---- buttons ----
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(16, 18), side="bottom")
        ctk.CTkButton(bar, text="Cancel", height=42, width=120,
                      font=(theme.FONT, 14), corner_radius=10,
                      fg_color=self.pal["surface_2"], text_color=self.pal["text"],
                      hover_color=self.pal["border"], command=self._close).pack(side="left")
        ctk.CTkButton(bar, text="Save", height=42, corner_radius=10,
                      font=(theme.FONT, 14, "bold"), fg_color=theme.SUCCESS,
                      hover_color="#16A34A", command=self._save).pack(
            side="right", fill="x", expand=True, padx=(10, 0))

    def _set_source(self, v):
        self._source = v
        self._refresh_source_btns()

    def _refresh_source_btns(self):
        for b in self._src_btns:
            active = b.cget("text") == self._source
            b.configure(
                fg_color=theme.TEAL if active else self.pal["surface_2"],
                text_color="#FFFFFF" if active else self.pal["text"])

    def _save(self):
        self.data.set_cold_email_session(self.get_sent(), self._source,
                                         self.get_replies(), self.notes_ent.get().strip())
        if self.on_saved:
            self.on_saved()
        self._close()


class SundayReminder(_BaseDialog):
    """Small nudge shown on Sundays; opens the assessment logger."""

    def __init__(self, master, data, on_saved=None):
        self.on_change = None
        super().__init__(master, 420, 240)
        self.data = data
        self.on_saved = on_saved

        ctk.CTkLabel(self, text="📝", font=(theme.FONT, 40)).pack(pady=(28, 4))
        ctk.CTkLabel(self, text="Time for your weekly self assessment!",
                     font=(theme.FONT, 16, "bold"), text_color=self.pal["text"],
                     wraplength=360).pack(padx=20)
        ctk.CTkLabel(self, text="Test yourself on this week's topics and log the result.",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"],
                     wraplength=360).pack(padx=20, pady=(4, 16))

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(0, 18), side="bottom")
        ctk.CTkButton(bar, text="Later", height=42, width=110, font=(theme.FONT, 14),
                      corner_radius=10, fg_color=self.pal["surface_2"],
                      text_color=self.pal["text"], hover_color=self.pal["border"],
                      command=self._close).pack(side="left")
        ctk.CTkButton(bar, text="Log Now", height=42, corner_radius=10,
                      font=(theme.FONT, 14, "bold"), fg_color=theme.ACCENT,
                      hover_color=theme.ACCENT_HOVER, command=self._open).pack(
            side="right", fill="x", expand=True, padx=(10, 0))

    def _open(self):
        master = self.master
        self._close()
        SundayAssessmentDialog(master, self.data, on_saved=self.on_saved)


class ScheduleEditorDialog(_BaseDialog):
    """Edit the daily schedule for each day of the week."""

    def __init__(self, master, data, on_saved=None):
        self.on_change = None
        super().__init__(master, 660, 720)
        self.data = data
        self.on_saved = on_saved

        from datetime import date
        import schedules as sched
        self._sched = sched
        self.work = copy.deepcopy(sched.load_schedules())
        self.current_day = sched.DAYS[date.today().weekday()]
        self._row_vars = []   # [(time_var, task_var)] for the visible day

        ctk.CTkLabel(self, text="Edit Schedule", font=(theme.FONT, 22, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self, text="Set your plan for each weekday. Use times like \"7:00 AM\".",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=24, pady=(0, 10))

        # ---- day selector ----
        day_row = ctk.CTkFrame(self, fg_color="transparent")
        day_row.pack(fill="x", padx=20, pady=(0, 8))
        self._day_btns = {}
        for d in sched.DAYS:
            b = ctk.CTkButton(day_row, text=sched.DAY_LABELS[d][:3], width=60, height=32,
                              font=(theme.FONT, 12, "bold"), corner_radius=8,
                              command=lambda dd=d: self._switch_day(dd))
            b.pack(side="left", padx=2, expand=True, fill="x")
            self._day_btns[d] = b

        # ---- scrollable rows area ----
        self.rows_scroll = ctk.CTkScrollableFrame(
            self, fg_color=self.pal["surface_2"], corner_radius=10, height=360)
        self.rows_scroll.pack(fill="both", expand=True, padx=20, pady=6)

        # ---- add / copy buttons ----
        tools = ctk.CTkFrame(self, fg_color="transparent")
        tools.pack(fill="x", padx=20, pady=(2, 4))
        ctk.CTkButton(tools, text="＋ Add slot", height=34, width=120,
                      font=(theme.FONT, 13, "bold"), corner_radius=8,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      text_color="#FFFFFF", command=self._add_slot).pack(side="left")
        ctk.CTkButton(tools, text="Copy this day to all weekdays", height=34,
                      font=(theme.FONT, 12), corner_radius=8,
                      fg_color=self.pal["surface_2"], text_color=self.pal["text"],
                      hover_color=self.pal["border"],
                      command=self._copy_weekdays).pack(side="left", padx=8)

        # ---- save / cancel ----
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(4, 16))
        ctk.CTkButton(bar, text="Cancel", height=42, width=120, font=(theme.FONT, 14),
                      corner_radius=10, fg_color=self.pal["surface_2"],
                      text_color=self.pal["text"], hover_color=self.pal["border"],
                      command=self._close).pack(side="left")
        ctk.CTkButton(bar, text="Save Schedule", height=42, corner_radius=10,
                      font=(theme.FONT, 14, "bold"), fg_color=theme.SUCCESS,
                      hover_color="#16A34A", command=self._save).pack(
            side="right", fill="x", expand=True, padx=(10, 0))

        self._render()

    # ---- helpers ---------------------------------------------------------
    def _collect(self):
        """Read the visible rows back into self.work[current_day]."""
        plan = []
        for time_var, task_var in self._row_vars:
            t = time_var.get().strip()
            task = task_var.get().strip()
            if t or task:
                plan.append({"time": t, "task": task})
        self.work[self.current_day] = plan

    def _switch_day(self, day):
        self._collect()
        self.current_day = day
        self._render()

    def _render(self):
        for w in self.rows_scroll.winfo_children():
            w.destroy()
        self._row_vars = []

        # highlight active day button
        for d, b in self._day_btns.items():
            if d == self.current_day:
                b.configure(fg_color=theme.ACCENT, text_color="#FFFFFF")
            else:
                b.configure(fg_color=self.pal["surface"], text_color=self.pal["text"])

        plan = self.work.get(self.current_day, [])
        if not plan:
            ctk.CTkLabel(self.rows_scroll,
                         text="No slots yet — click “＋ Add slot” to start this day.",
                         font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
                pady=20)
        for i, item in enumerate(plan):
            self._row(i, item)

    def _row(self, index, item):
        row = ctk.CTkFrame(self.rows_scroll, fg_color=self.pal["surface"],
                           corner_radius=8)
        row.pack(fill="x", pady=3, padx=4)

        time_var = ctk.StringVar(value=item.get("time", ""))
        task_var = ctk.StringVar(value=item.get("task", ""))
        self._row_vars.append((time_var, task_var))

        ctk.CTkEntry(row, textvariable=time_var, width=84, height=30,
                     font=(theme.FONT, 12), justify="center",
                     placeholder_text="7:00 AM").pack(side="left", padx=(8, 4), pady=6)
        ctk.CTkEntry(row, textvariable=task_var, height=30, font=(theme.FONT, 12),
                     placeholder_text="Task").pack(
            side="left", fill="x", expand=True, padx=4, pady=6)

        ctk.CTkButton(row, text="✕", width=30, height=30, font=(theme.FONT, 13, "bold"),
                      corner_radius=6, fg_color=self.pal["surface_2"],
                      text_color=theme.DANGER, hover_color=self.pal["border"],
                      command=lambda i=index: self._delete(i)).pack(side="right", padx=(2, 8))
        ctk.CTkButton(row, text="▼", width=28, height=30, font=(theme.FONT, 11),
                      corner_radius=6, fg_color=self.pal["surface_2"],
                      text_color=self.pal["text"], hover_color=self.pal["border"],
                      command=lambda i=index: self._move(i, 1)).pack(side="right", padx=1)
        ctk.CTkButton(row, text="▲", width=28, height=30, font=(theme.FONT, 11),
                      corner_radius=6, fg_color=self.pal["surface_2"],
                      text_color=self.pal["text"], hover_color=self.pal["border"],
                      command=lambda i=index: self._move(i, -1)).pack(side="right", padx=1)

    def _add_slot(self):
        self._collect()
        self.work[self.current_day].append({"time": "", "task": ""})
        self._render()

    def _delete(self, index):
        self._collect()
        plan = self.work[self.current_day]
        if 0 <= index < len(plan):
            plan.pop(index)
        self._render()

    def _move(self, index, delta):
        self._collect()
        plan = self.work[self.current_day]
        j = index + delta
        if 0 <= index < len(plan) and 0 <= j < len(plan):
            plan[index], plan[j] = plan[j], plan[index]
        self._render()

    def _copy_weekdays(self):
        self._collect()
        plan = self.work[self.current_day]
        for d in ("monday", "tuesday", "wednesday", "thursday", "friday"):
            self.work[d] = copy.deepcopy(plan)
        self._render()

    def _save(self):
        self._collect()
        self._sched.save_schedules(self.work)
        if self.on_saved:
            self.on_saved()
        self._close()


class LeaderboardEditorDialog(_BaseDialog):
    """Add, edit and remove leaderboard competitors (stored in goals)."""

    def __init__(self, master, data, on_saved=None):
        self.on_change = None
        super().__init__(master, 480, 560)
        self.data = data
        self.on_saved = on_saved
        self.work = [dict(r) for r in data.goals.get("leaderboard", [])]
        self._row_vars = []   # [(name_var, points_var)]

        ctk.CTkLabel(self, text="Edit Standings", font=(theme.FONT, 22, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self, text="Add the people (or targets) you're competing with. "
                                "Your own row updates automatically.",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"],
                     wraplength=420, justify="left").pack(anchor="w", padx=24, pady=(0, 10))

        self.rows_scroll = ctk.CTkScrollableFrame(
            self, fg_color=self.pal["surface_2"], corner_radius=10, height=300)
        self.rows_scroll.pack(fill="both", expand=True, padx=20, pady=6)

        ctk.CTkButton(self, text="＋ Add competitor", height=34, width=160,
                      font=(theme.FONT, 13, "bold"), corner_radius=8,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      text_color="#FFFFFF", command=self._add).pack(anchor="w", padx=20, pady=4)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(4, 16))
        ctk.CTkButton(bar, text="Cancel", height=42, width=120, font=(theme.FONT, 14),
                      corner_radius=10, fg_color=self.pal["surface_2"],
                      text_color=self.pal["text"], hover_color=self.pal["border"],
                      command=self._close).pack(side="left")
        ctk.CTkButton(bar, text="Save", height=42, corner_radius=10,
                      font=(theme.FONT, 14, "bold"), fg_color=theme.SUCCESS,
                      hover_color="#16A34A", command=self._save).pack(
            side="right", fill="x", expand=True, padx=(10, 0))

        self._render()

    def _collect(self):
        rows = []
        for name_var, pts_var in self._row_vars:
            name = name_var.get().strip()
            try:
                pts = max(0, int(float(pts_var.get())))
            except (ValueError, TypeError):
                pts = 0
            if name:
                rows.append({"name": name, "points": pts})
        self.work = rows

    def _render(self):
        for w in self.rows_scroll.winfo_children():
            w.destroy()
        self._row_vars = []
        if not self.work:
            ctk.CTkLabel(self.rows_scroll,
                         text="No competitors yet — add one to build your board.",
                         font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(pady=20)
        for i, r in enumerate(self.work):
            self._row(i, r)

    def _row(self, index, r):
        row = ctk.CTkFrame(self.rows_scroll, fg_color=self.pal["surface"], corner_radius=8)
        row.pack(fill="x", pady=3, padx=4)
        name_var = ctk.StringVar(value=r.get("name", ""))
        pts_var = ctk.StringVar(value=str(r.get("points", 0)))
        self._row_vars.append((name_var, pts_var))
        ctk.CTkEntry(row, textvariable=name_var, height=30, font=(theme.FONT, 12),
                     placeholder_text="Name").pack(side="left", fill="x", expand=True,
                                                    padx=(8, 4), pady=6)
        ctk.CTkEntry(row, textvariable=pts_var, width=80, height=30, font=(theme.FONT, 12),
                     justify="center", placeholder_text="pts").pack(side="left", padx=4, pady=6)
        ctk.CTkButton(row, text="✕", width=30, height=30, font=(theme.FONT, 13, "bold"),
                      corner_radius=6, fg_color=self.pal["surface_2"],
                      text_color=theme.DANGER, hover_color=self.pal["border"],
                      command=lambda i=index: self._delete(i)).pack(side="right", padx=(2, 8))

    def _add(self):
        self._collect()
        self.work.append({"name": "", "points": 0})
        self._render()

    def _delete(self, index):
        self._collect()
        if 0 <= index < len(self.work):
            self.work.pop(index)
        self._render()

    def _save(self):
        self._collect()
        self.data.goals["leaderboard"] = self.work
        self.data.save_goals()
        if self.on_saved:
            self.on_saved()
        self._close()
