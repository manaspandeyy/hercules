"""Goals & Course view — overall donut charts, expandable per-unit cards with
colour-coded progress bars, and an automatic unit-completion planner.

P4 redesign: accordion expand/collapse WITHOUT full rebuild. Body frames are
pre-built once; _toggle() simply pack/pack_forgets them and updates arrow +
badge inline. Inline CTkEntry widgets replace the popup UnitEditDialog.
"""

from datetime import date

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import theme
import animations as anim


class GoalsView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.expanded = set()
        # references updated without rebuild:
        self._arrows = {}       # {i: CTkButton toggle}
        self._pct_labels = {}   # {i: CTkLabel percentage badge}
        self._bodies = {}       # {i: CTkFrame body}
        self._bars = {}         # {i: [(bar_widget, done_key, total_key, unit_index)]}
        self._entries = {}      # {i: {field: (done_var, total_var)}}
        self.build()

    @property
    def pal(self):
        return self.app.pal

    def _card(self, parent):
        c = ctk.CTkFrame(parent, fg_color=self.pal["surface"], corner_radius=14,
                         border_width=1, border_color=self.pal["border"])
        c.pack(fill="x", pady=8, padx=4)
        return c

    def build(self):
        for w in self.winfo_children():
            w.destroy()
        self._arrows.clear()
        self._pct_labels.clear()
        self._bodies.clear()
        self._bars.clear()
        self._entries.clear()

        data = self.app.data

        ctk.CTkLabel(self, text="Goals & Course", font=(theme.FONT, 26, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=4)
        ctk.CTkLabel(self, text="Your progress, unit by unit — and when you'll finish.",
                     font=(theme.FONT, 14), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=4, pady=(2, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._donuts(scroll, data)
        self._planner(scroll, data)

        units_head = ctk.CTkFrame(scroll, fg_color="transparent")
        units_head.pack(fill="x", padx=8, pady=(12, 2))
        ctk.CTkLabel(units_head, text="Units", font=(theme.FONT, 17, "bold"),
                     text_color=self.pal["text"]).pack(side="left")
        ctk.CTkButton(units_head, text="＋ Add unit", height=30, width=110,
                      font=(theme.FONT, 12, "bold"), corner_radius=8,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      text_color="#FFFFFF", command=self._add_unit).pack(side="right")
        for i, u in enumerate(data.goals["course_units"]):
            self._unit_card(scroll, i, u)

    # ---- add / rename / delete units -------------------------------------
    def _add_unit(self):
        self.app.data.add_unit()
        self.app.on_data_changed()

    def _rename_unit(self, index, name_var):
        self.app.data.rename_unit(index, name_var.get())
        self.app.on_data_changed()

    def _delete_unit(self, index):
        from tkinter import messagebox
        name = self.app.data.goals["course_units"][index]["name"]
        if messagebox.askyesno("Delete unit", f"Delete “{name}” and its progress?"):
            self.app.data.delete_unit(index)
            self.app.on_data_changed()

    # ---- overall donuts --------------------------------------------------
    def _donuts(self, parent, data):
        card = self._card(parent)
        ctk.CTkLabel(card, text="Overall progress", font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(14, 4))

        totals = data.course_totals()
        order = [("Assignments", totals["assignments"]),
                 ("Lectures", totals["lectures"]),
                 ("Assessments", totals["assessments"])]

        fig = Figure(figsize=(6.4, 2.3), dpi=80)
        fig.patch.set_facecolor(self.pal["chart_bg"])
        for i, (label, (done, total)) in enumerate(order):
            ax = fig.add_subplot(1, 3, i + 1)
            frac = (done / total) if total else 0
            color = theme.progress_color(frac)
            ax.pie([frac, 1 - frac], colors=[color, self.pal["surface_2"]],
                   startangle=90, counterclock=False,
                   wedgeprops={"width": 0.32, "edgecolor": self.pal["chart_bg"]})
            ax.text(0, 0.12, f"{round(frac*100)}%", ha="center", va="center",
                    fontsize=16, fontweight="bold", color=self.pal["text"])
            ax.text(0, -0.22, f"{done}/{total}", ha="center", va="center",
                    fontsize=9, color=self.pal["chart_text"])
            ax.set_title(label, fontsize=10, color=self.pal["text"], pad=4)
            ax.set_aspect("equal")
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=(0, 12))

    # ---- planner ---------------------------------------------------------
    def _planner(self, parent, data):
        p = data.planner()
        card = self._card(parent)
        ctk.CTkLabel(card, text="🗓 Completion Planner",
                     font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(14, 2))

        per_hours = data.goals.get("study_minutes_per_day", 120) / 60
        ctk.CTkLabel(card, text=f"At {per_hours:g} hrs/day of study:",
                     font=(theme.FONT, 12), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=18)

        on_track = p["on_track"]
        banner = ctk.CTkFrame(card, fg_color=self.pal["surface_2"], corner_radius=10)
        banner.pack(fill="x", padx=18, pady=10)
        proj = p["projected"].strftime("%d %b %Y")
        tgt = p["target"].strftime("%d %b %Y")
        ctk.CTkLabel(banner, text=f"Projected finish:  {proj}",
                     font=(theme.FONT, 15, "bold"),
                     text_color=theme.SUCCESS if on_track else theme.DANGER).pack(
            anchor="w", padx=14, pady=(12, 0))
        msg = (f"On track for the {tgt} target ✓" if on_track
               else f"⚠ Behind the {tgt} target — pick up the pace")
        ctk.CTkLabel(banner, text=msg, font=(theme.FONT, 12),
                     text_color=self.pal["text_muted"]).pack(anchor="w", padx=14)
        ctk.CTkLabel(banner,
                     text=f"Daily lecture target to stay on track: "
                          f"{p['daily_lecture_target']:.1f} lectures/day",
                     font=(theme.FONT, 12, "bold"), text_color=theme.INFO).pack(
            anchor="w", padx=14, pady=(2, 12))

        for u in p["units"]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=2)
            ctk.CTkLabel(row, text=u["name"], font=(theme.FONT, 12),
                         text_color=self.pal["text"], anchor="w", width=240).pack(side="left")
            if u["done"]:
                badge, color = "Complete", theme.SUCCESS
                detail = "—"
            else:
                color = theme.SUCCESS if u["on_track"] else theme.DANGER
                badge = "On track" if u["on_track"] else "Behind"
                detail = f"~{u['days']}d · {u['finish'].strftime('%d %b')}"
            ctk.CTkLabel(row, text=detail, font=(theme.FONT, 11),
                         text_color=self.pal["text_muted"]).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=badge, font=(theme.FONT, 11, "bold"),
                         text_color="#FFFFFF", fg_color=color, corner_radius=8,
                         width=78, height=22).pack(side="right")
        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

    # ---- unit cards (pre-built, no rebuild on toggle) --------------------
    def _unit_card(self, parent, index, u):
        card = self._card(parent)

        done_total = (u["assignments_done"] + u["assessments_done"] + u["lectures_done"])
        all_total = (u["assignments_total"] + u["assessments_total"] + u["lectures_total"])
        frac = (done_total / all_total) if all_total else 0

        # --- header row ---
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=12)

        arrow_btn = ctk.CTkButton(
            head, text=f"  ▸  {u['name']}", anchor="w",
            font=(theme.FONT, 14, "bold"), height=32, corner_radius=8,
            fg_color="transparent", text_color=self.pal["text"],
            hover_color=self.pal["surface_2"],
            command=lambda i=index: self._toggle(i))
        arrow_btn.pack(side="left", fill="x", expand=True)
        self._arrows[index] = arrow_btn

        pct_lbl = ctk.CTkLabel(
            head, text=f"{round(frac*100)}%",
            font=(theme.FONT, 14, "bold"),
            text_color="#FFFFFF", fg_color=theme.progress_color(frac),
            corner_radius=8, width=56, height=26)
        pct_lbl.pack(side="right")
        self._pct_labels[index] = pct_lbl

        # --- body (hidden until expanded) ---
        body = ctk.CTkFrame(card, fg_color="transparent")
        # NOT packed yet — pack on first expand
        self._bodies[index] = body

        self._entries[index] = {}
        self._bars[index] = []

        # --- rename / delete row ---
        manage = ctk.CTkFrame(body, fg_color="transparent")
        manage.pack(fill="x", padx=18, pady=(6, 2))
        name_var = ctk.StringVar(value=u["name"])
        ctk.CTkEntry(manage, textvariable=name_var, height=30, font=(theme.FONT, 12)).pack(
            side="left", fill="x", expand=True)
        ctk.CTkButton(manage, text="Rename", width=74, height=30, font=(theme.FONT, 11),
                      corner_radius=6, fg_color=self.pal["surface_2"],
                      text_color=self.pal["text"], hover_color=self.pal["border"],
                      command=lambda i=index, v=name_var: self._rename_unit(i, v)).pack(
            side="left", padx=6)
        ctk.CTkButton(manage, text="🗑", width=40, height=30, font=(theme.FONT, 13),
                      corner_radius=6, fg_color=self.pal["surface_2"],
                      text_color=theme.DANGER, hover_color=self.pal["border"],
                      command=lambda i=index: self._delete_unit(i)).pack(side="left")

        fields = [
            ("Lectures",    "lectures_done",    "lectures_total"),
            ("Assignments", "assignments_done",  "assignments_total"),
            ("Assessments", "assessments_done",  "assessments_total"),
        ]
        for label, dk, tk_ in fields:
            self._inline_row(body, index, u, label, dk, tk_)

        ctk.CTkFrame(body, fg_color="transparent", height=6).pack()

    def _inline_row(self, parent, unit_idx, u, label, done_key, total_key):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="x", padx=18, pady=4)

        top = ctk.CTkFrame(wrap, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(top, text=label, font=(theme.FONT, 12, "bold"),
                     text_color=self.pal["text"]).pack(side="left")

        # Inline entry pair: done / total
        done_var = ctk.StringVar(value=str(u[done_key]))
        total_var = ctk.StringVar(value=str(u[total_key]))

        entry_done = ctk.CTkEntry(top, textvariable=done_var, width=52, height=24,
                                  font=(theme.FONT, 12), justify="center")
        entry_done.pack(side="right")
        ctk.CTkLabel(top, text="/", font=(theme.FONT, 12),
                     text_color=self.pal["text_muted"]).pack(side="right", padx=2)
        entry_total = ctk.CTkEntry(top, textvariable=total_var, width=52, height=24,
                                   font=(theme.FONT, 12), justify="center")
        entry_total.pack(side="right")

        self._entries[unit_idx][done_key] = done_var
        self._entries[unit_idx][total_key] = total_var

        # progress bar
        frac = (u[done_key] / u[total_key]) if u[total_key] else 0
        bar = ctk.CTkProgressBar(wrap, height=8, corner_radius=4,
                                 progress_color=theme.progress_color(frac),
                                 fg_color=self.pal["surface_2"])
        bar.pack(fill="x", pady=(4, 0))
        bar.set(0)
        anim.animate_progressbar(self, bar, frac, duration=500)
        self._bars[unit_idx].append((bar, done_key, total_key))

        # save on Enter in either entry
        def _save(e=None, i=unit_idx):
            self._save_unit(i)
        entry_done.bind("<Return>", _save)
        entry_total.bind("<Return>", _save)

    # ---- toggle without rebuild ------------------------------------------
    def _toggle(self, index):
        if index in self.expanded:
            self.expanded.discard(index)
            self._bodies[index].pack_forget()
            self._arrows[index].configure(
                text=f"  ▸  {self.app.data.goals['course_units'][index]['name']}")
        else:
            self.expanded.add(index)
            # pack body BEFORE the bottom padding (which doesn't exist as a widget,
            # body just goes right below head inside the card)
            self._bodies[index].pack(fill="x", after=self._arrows[index].master)
            self._arrows[index].configure(
                text=f"  ▾  {self.app.data.goals['course_units'][index]['name']}")

    # ---- inline save (no rebuild) ----------------------------------------
    def _save_unit(self, index):
        data = self.app.data
        u = data.goals["course_units"][index]
        ev = self._entries[index]

        def _int(var, fallback):
            try:
                return max(0, int(var.get()))
            except ValueError:
                return fallback

        u["lectures_done"]    = _int(ev["lectures_done"],    u["lectures_done"])
        u["lectures_total"]   = _int(ev["lectures_total"],   u["lectures_total"])
        u["assignments_done"] = _int(ev["assignments_done"], u["assignments_done"])
        u["assignments_total"]= _int(ev["assignments_total"],u["assignments_total"])
        u["assessments_done"] = _int(ev["assessments_done"], u["assessments_done"])
        u["assessments_total"]= _int(ev["assessments_total"],u["assessments_total"])

        # sync entry vars in case value was clamped to 0
        ev["lectures_done"].set(str(u["lectures_done"]))
        ev["lectures_total"].set(str(u["lectures_total"]))
        ev["assignments_done"].set(str(u["assignments_done"]))
        ev["assignments_total"].set(str(u["assignments_total"]))
        ev["assessments_done"].set(str(u["assessments_done"]))
        ev["assessments_total"].set(str(u["assessments_total"]))

        data.save_goals()
        self.app.on_data_changed()

        # update progress bars inline
        for bar, dk, tk_ in self._bars[index]:
            d2, t2 = u[dk], u[tk_]
            frac = (d2 / t2) if t2 else 0
            bar.configure(progress_color=theme.progress_color(frac))
            anim.animate_progressbar(self, bar, frac, duration=400)

        # update percentage badge
        done_t = u["assignments_done"] + u["assessments_done"] + u["lectures_done"]
        all_t  = u["assignments_total"] + u["assessments_total"] + u["lectures_total"]
        frac_t = (done_t / all_t) if all_t else 0
        self._pct_labels[index].configure(
            text=f"{round(frac_t*100)}%",
            fg_color=theme.progress_color(frac_t))
