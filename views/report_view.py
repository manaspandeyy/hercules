"""Progress Report view — upload a performance summary (PDF/image), confirm the
parsed metrics, then see analysis, report-over-report comparison, coaching
recommendations, and full history.

Nothing here is tied to a specific course or report format: the parser pre-fills
what it can recognise, and you can always type the numbers in yourself.
"""

import os
from datetime import date
from tkinter import filedialog

import customtkinter as ctk

import theme
import report_parser as rp


class ReportView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.pending = None       # parsed dict awaiting confirmation
        self.preview_img = None    # keep a ref so CTkImage isn't GC'd
        self.fields = {}
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

        ctk.CTkLabel(self, text="Progress Report", font=(theme.FONT, 26, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=4)
        ctk.CTkLabel(self, text="Upload a progress report (or just type the numbers) "
                                "to see where you stand.",
                     font=(theme.FONT, 14), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=4, pady=(2, 12))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self._upload_card()
        self._entry_card()
        reports = self.app.data.reports
        if reports:
            self._analysis_card(reports[-1])
            if len(reports) >= 2:
                self._comparison_card(reports[-1], reports[-2])
            self._recommendations_card(reports[-1],
                                       reports[-2] if len(reports) >= 2 else None)
            self._history_card(reports)

    # ---- upload ----------------------------------------------------------
    def _upload_card(self):
        card = self._card(self.scroll)
        ctk.CTkLabel(card, text="📤 Upload report (PDF or image)",
                     font=(theme.FONT, 15, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(14, 8))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkButton(row, text="Choose File…", height=40, width=160,
                      font=(theme.FONT, 14, "bold"), corner_radius=10,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self._choose).pack(side="left")
        self.upload_status = ctk.CTkLabel(row, text="No file selected",
                                          font=(theme.FONT, 12),
                                          text_color=self.pal["text_muted"])
        self.upload_status.pack(side="left", padx=12)
        self.preview_holder = ctk.CTkFrame(card, fg_color="transparent")
        self.preview_holder.pack(fill="x", padx=18, pady=(0, 12))

    def _choose(self):
        path = filedialog.askopenfilename(
            title="Select report",
            filetypes=[("Reports", "*.pdf *.png *.jpg *.jpeg *.bmp *.webp"),
                       ("All files", "*.*")])
        if not path:
            return
        self.pending_path = path
        name = os.path.basename(path)
        self.upload_status.configure(text=f"Selected: {name}", text_color=theme.SUCCESS)

        # PDF → try auto-extract and pre-fill the form.
        if rp.is_pdf(path):
            parsed = rp.extract_from_pdf(path)
            self._prefill(parsed)
            self.upload_status.configure(
                text=f"Parsed: {name} — review the numbers below")
        elif rp.is_image(path):
            self._show_preview(path)
            self.upload_status.configure(
                text=f"Image loaded: {name} — enter the numbers below")

    def _show_preview(self, path):
        for w in self.preview_holder.winfo_children():
            w.destroy()
        try:
            from PIL import Image
            img = Image.open(path)
            img.thumbnail((220, 220))
            self.preview_img = ctk.CTkImage(light_image=img, dark_image=img,
                                            size=img.size)
            ctk.CTkLabel(self.preview_holder, image=self.preview_img, text="").pack(anchor="w")
        except Exception:
            pass

    # ---- manual entry / confirm -----------------------------------------
    def _entry_card(self):
        card = self._card(self.scroll)
        ctk.CTkLabel(card, text="✍️ Confirm metrics", font=(theme.FONT, 15, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(14, 8))

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=14, pady=(0, 6))

        self.fields = {}
        specs = [
            ("assignments", "Assignments done (period)"),
            ("assessments", "Assessments done (period)"),
            ("lectures", "Lectures watched (period)"),
            ("avg_score", "Avg assessment score %"),
            ("time_spent", "Time spent"), ("topics", "Topics (comma-sep)"),
            ("weak_areas", "Weak areas (comma-sep)"),
            ("strong_areas", "Strong areas (comma-sep)"),
        ]
        for i, (key, label) in enumerate(specs):
            r, c = divmod(i, 2)
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=r, column=c, sticky="ew", padx=6, pady=6)
            grid.grid_columnconfigure(c, weight=1)
            ctk.CTkLabel(cell, text=label, font=(theme.FONT, 12),
                         text_color=self.pal["text_muted"], anchor="w").pack(fill="x")
            ent = ctk.CTkEntry(cell, height=34, font=(theme.FONT, 13),
                               fg_color=self.pal["surface_2"],
                               border_color=self.pal["border"])
            ent.pack(fill="x")
            self.fields[key] = ent

        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=(6, 16))
        ctk.CTkButton(bar, text="Save Report", height=42, width=180,
                      font=(theme.FONT, 14, "bold"), corner_radius=10,
                      fg_color=theme.SUCCESS, hover_color="#00997A",
                      command=self._save).pack(side="left")
        self.save_status = ctk.CTkLabel(bar, text="", font=(theme.FONT, 13, "bold"),
                                        text_color=theme.SUCCESS)
        self.save_status.pack(side="left", padx=12)

    def _prefill(self, parsed):
        mapping = {
            "assignments": parsed.get("assignments", ""),
            "assessments": parsed.get("assessments", ""),
            "lectures": parsed.get("lectures", ""),
            "avg_score": parsed.get("avg_score", ""),
            "time_spent": parsed.get("time_spent", ""),
            "topics": ", ".join(parsed.get("topics", [])),
            "weak_areas": ", ".join(parsed.get("weak_areas", [])),
            "strong_areas": ", ".join(parsed.get("strong_areas", [])),
        }
        for key, val in mapping.items():
            ent = self.fields.get(key)
            if ent is not None:
                ent.delete(0, "end")
                if val not in ("", 0, 0.0):
                    ent.insert(0, str(val))

    def _save(self):
        def to_int(v):
            try:
                return int(float(v))
            except (ValueError, TypeError):
                return 0

        def to_float(v):
            try:
                return float(str(v).replace("%", "").strip())
            except (ValueError, TypeError):
                return 0.0

        def to_list(v):
            return [s.strip() for s in v.split(",") if s.strip()]

        report = {
            "label": f"Progress report · {date.today().strftime('%b %d, %Y')}",
            "date": date.today().isoformat(),
            "assignments": to_int(self.fields["assignments"].get()),
            "assessments": to_int(self.fields["assessments"].get()),
            "lectures": to_int(self.fields["lectures"].get()),
            "avg_score": to_float(self.fields["avg_score"].get()),
            "time_spent": self.fields["time_spent"].get().strip(),
            "topics": to_list(self.fields["topics"].get()),
            "weak_areas": to_list(self.fields["weak_areas"].get()),
            "strong_areas": to_list(self.fields["strong_areas"].get()),
            "source_file": os.path.basename(getattr(self, "pending_path", "") or "manual entry"),
        }
        self.app.data.add_report(report, getattr(self, "pending_path", None))
        self.save_status.configure(text="✓ Saved")
        self.after(400, self.build)   # rebuild to show analysis

    # ---- analysis --------------------------------------------------------
    def _metric(self, parent, label, value, color=None):
        cell = ctk.CTkFrame(parent, fg_color=self.pal["surface_2"], corner_radius=10)
        ctk.CTkLabel(cell, text=str(value), font=(theme.FONT, 22, "bold"),
                     text_color=color or self.pal["text"]).pack(pady=(12, 0))
        ctk.CTkLabel(cell, text=label, font=(theme.FONT, 11),
                     text_color=self.pal["text_muted"]).pack(pady=(0, 12))
        return cell

    def _chips(self, parent, items, color):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="x", padx=18, pady=(0, 4))
        if not items:
            ctk.CTkLabel(wrap, text="—", text_color=self.pal["text_muted"],
                         font=(theme.FONT, 12)).pack(anchor="w")
            return
        for it in items:
            ctk.CTkLabel(wrap, text=f"  {it}  ", font=(theme.FONT, 12, "bold"),
                         text_color="#FFFFFF", fg_color=color, corner_radius=8,
                         height=26).pack(side="left", padx=3, pady=2)

    def _analysis_card(self, r):
        card = self._card(self.scroll)
        ctk.CTkLabel(card, text=f"📊 Latest — {r['label']}",
                     font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(14, 8))

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 10))
        metrics = [
            ("Assignments", r.get("assignments", 0), theme.ACCENT),
            ("Assessments", r.get("assessments", 0), theme.TEAL),
            ("Lectures", r.get("lectures", 0), theme.INFO),
            ("Avg score", f"{r.get('avg_score', 0):.0f}%", theme.SUCCESS),
            ("Time", r.get("time_spent") or "—", self.pal["text"]),
        ]
        for i, (label, val, color) in enumerate(metrics):
            self._metric(grid, label, val, color).grid(
                row=0, column=i, padx=5, pady=4, sticky="nsew")
            grid.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(card, text="Strong areas", font=(theme.FONT, 13, "bold"),
                     text_color=theme.SUCCESS).pack(anchor="w", padx=18, pady=(6, 0))
        self._chips(card, r.get("strong_areas", []), theme.SUCCESS)
        ctk.CTkLabel(card, text="Weak areas", font=(theme.FONT, 13, "bold"),
                     text_color=theme.DANGER).pack(anchor="w", padx=18, pady=(8, 0))
        self._chips(card, r.get("weak_areas", []), theme.DANGER)
        if r.get("topics"):
            ctk.CTkLabel(card, text="Topics covered: " + ", ".join(r["topics"]),
                         font=(theme.FONT, 12), text_color=self.pal["text_muted"],
                         wraplength=640, justify="left").pack(anchor="w", padx=18, pady=(8, 14))
        else:
            ctk.CTkFrame(card, fg_color="transparent", height=6).pack()

    def _comparison_card(self, cur, prev):
        card = self._card(self.scroll)
        ctk.CTkLabel(card, text="📈 This report vs previous report",
                     font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(14, 8))

        def delta_row(label, c, p, suffix=""):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=3)
            ctk.CTkLabel(row, text=label, font=(theme.FONT, 13),
                         text_color=self.pal["text"], width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{p}{suffix} → {c}{suffix}", font=(theme.FONT, 13),
                         text_color=self.pal["text_muted"]).pack(side="left", padx=10)
            d = c - p
            color = theme.SUCCESS if d > 0 else theme.DANGER if d < 0 else self.pal["text_muted"]
            arrow = "▲" if d > 0 else "▼" if d < 0 else "■"
            ctk.CTkLabel(row, text=f"{arrow} {d:+}{suffix}", font=(theme.FONT, 13, "bold"),
                         text_color=color).pack(side="left")

        delta_row("Assignments", cur.get("assignments", 0), prev.get("assignments", 0))
        delta_row("Assessments", cur.get("assessments", 0), prev.get("assessments", 0))
        delta_row("Lectures", cur.get("lectures", 0), prev.get("lectures", 0))
        delta_row("Avg score", round(cur.get("avg_score", 0)), round(prev.get("avg_score", 0)), "%")
        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

    def _recommendations_card(self, cur, prev):
        card = self._card(self.scroll)
        ctk.CTkLabel(card, text="🤖 Recommendations", font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(14, 8))
        for tip in rp.generate_recommendations(cur, prev, self.app.data.goals["course_units"]):
            row = ctk.CTkFrame(card, fg_color=self.pal["surface_2"], corner_radius=10)
            row.pack(fill="x", padx=18, pady=4)
            ctk.CTkLabel(row, text="→", font=(theme.FONT, 14, "bold"),
                         text_color=theme.ACCENT).pack(side="left", padx=(14, 8), pady=10)
            ctk.CTkLabel(row, text=tip, font=(theme.FONT, 13), text_color=self.pal["text"],
                         wraplength=600, justify="left", anchor="w").pack(
                side="left", fill="x", expand=True, pady=10, padx=(0, 12))
        ctk.CTkFrame(card, fg_color="transparent", height=6).pack()

    def _history_card(self, reports):
        card = self._card(self.scroll)
        ctk.CTkLabel(card, text="🗂 Report history", font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(14, 8))
        for r in reversed(reports):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=2)
            ctk.CTkLabel(row, text=r["label"], font=(theme.FONT, 12, "bold"),
                         text_color=self.pal["text"], anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{r.get('assignments', 0)} assign · {r.get('lectures', 0)} lec · "
                                   f"{r.get('avg_score', 0):.0f}% avg · {r.get('source_file', '')}",
                         font=(theme.FONT, 11), text_color=self.pal["text_muted"]).pack(side="right")
        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()
