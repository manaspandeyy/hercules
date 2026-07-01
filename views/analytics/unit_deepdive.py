"""Course Unit Deep Dive tab — per-unit detail, side-by-side unit compare,
and an auto priority ranking based on remaining work and the Sept 2026 deadline.
"""

import numpy as np
import customtkinter as ctk

import theme
from .charts import TabBase, ChartCard


class UnitDeepDiveTab(TabBase):
    def __init__(self, master, app):
        super().__init__(master, app)
        self.sel_a = 0
        self.sel_b = 1

    def _units(self):
        return self.app.data.goals["course_units"]

    def build(self):
        for w in self.winfo_children():
            w.destroy()
        s = self.scroll()
        units = self._units()
        names = [u["name"] for u in units]

        # selectors
        sel = self.card(s)
        row = ctk.CTkFrame(sel, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(row, text="Unit A", font=(theme.FONT, 13, "bold"),
                     text_color=theme.ACCENT).pack(side="left")
        ma = ctk.CTkOptionMenu(row, values=names, width=240, font=(theme.FONT, 12),
                               fg_color=self.pal["surface_2"], button_color=theme.ACCENT,
                               button_hover_color=theme.ACCENT_HOVER,
                               command=lambda v: self._set("sel_a", names.index(v)))
        ma.set(names[self.sel_a]); ma.pack(side="left", padx=8)
        ctk.CTkLabel(row, text="vs", font=(theme.FONT, 13),
                     text_color=self.pal["text_muted"]).pack(side="left", padx=4)
        mb = ctk.CTkOptionMenu(row, values=names, width=240, font=(theme.FONT, 12),
                               fg_color=self.pal["surface_2"], button_color=theme.INFO,
                               button_hover_color=theme.ACCENT_HOVER,
                               command=lambda v: self._set("sel_b", names.index(v)))
        mb.set(names[self.sel_b]); mb.pack(side="left", padx=8)

        self._detail(s, self.sel_a)
        self._compare(s, self.sel_a, self.sel_b)
        self._priority(s)

    def _set(self, which, idx):
        setattr(self, which, idx)
        self.build()

    def _detail(self, parent, idx):
        u = self._units()[idx]
        _, prio = self.m.unit_priority()
        pu = next(p for p in self.m.unit_priority()[0] if p["name"] == u["name"])

        card = self.card(parent)
        ctk.CTkLabel(card, text=u["name"], font=(theme.FONT, 17, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(12, 6))

        for kind, color in (("lectures", theme.INFO), ("assignments", theme.ACCENT),
                            ("assessments", theme.TEAL)):
            done, total = u[f"{kind}_done"], u[f"{kind}_total"]
            frac = (done / total) if total else 0
            wrap = ctk.CTkFrame(card, fg_color="transparent")
            wrap.pack(fill="x", padx=18, pady=4)
            top = ctk.CTkFrame(wrap, fg_color="transparent"); top.pack(fill="x")
            ctk.CTkLabel(top, text=kind.capitalize(), font=(theme.FONT, 12, "bold"),
                         text_color=color).pack(side="left")
            ctk.CTkLabel(top, text=f"{done}/{total}", font=(theme.FONT, 12),
                         text_color=self.pal["text_muted"]).pack(side="right")
            bar = ctk.CTkProgressBar(wrap, height=10, corner_radius=5,
                                     progress_color=theme.progress_color(frac),
                                     fg_color=self.pal["surface_2"])
            bar.pack(fill="x", pady=(3, 0)); bar.set(frac)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=18, pady=12)
        badge = "Complete" if pu["done"] else ("On track" if pu["on_track"] else "Behind")
        bcol = theme.SUCCESS if (pu["done"] or pu["on_track"]) else theme.DANGER
        for label, val, color in [
            ("Est. completion", pu["finish"].strftime("%d %b %Y"), self.pal["text"]),
            ("Priority score", f"{pu['priority']}/100", theme.ORANGE),
            ("Status", badge, bcol)]:
            cell = ctk.CTkFrame(info, fg_color=self.pal["surface_2"], corner_radius=10)
            cell.pack(side="left", expand=True, fill="x", padx=4)
            ctk.CTkLabel(cell, text=val, font=(theme.FONT, 14, "bold"),
                         text_color=color).pack(pady=(8, 0))
            ctk.CTkLabel(cell, text=label, font=(theme.FONT, 10),
                         text_color=self.pal["text_muted"]).pack(pady=(0, 8))

    def _compare(self, parent, ia, ib):
        ua, ub = self._units()[ia], self._units()[ib]
        cc = ChartCard(self, parent, "Unit A vs Unit B — % complete by category",
                       height=2.8)
        cats = ["lectures", "assignments", "assessments"]
        x = np.arange(len(cats))

        def pcts(u):
            return [round(u[f"{k}_done"] / u[f"{k}_total"] * 100) if u[f"{k}_total"] else 0
                    for k in cats]
        cc.ax.bar(x - 0.2, pcts(ua), 0.4, label=ua["name"][:16], color=theme.ACCENT, zorder=3)
        cc.ax.bar(x + 0.2, pcts(ub), 0.4, label=ub["name"][:16], color=theme.INFO, zorder=3)
        cc.ax.set_ylim(0, 100); cc.ax.set_xticks(x)
        cc.ax.set_xticklabels([c.capitalize() for c in cats]); cc.ax.set_ylabel("% done")
        cc.legend()
        cc.finish()

    def _priority(self, parent):
        _, ranked = self.m.unit_priority()
        card = self.card(parent)
        ctk.CTkLabel(card, text="🚨 Priority Ranking", font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(12, 2))
        urgent = next((u for u in ranked if not u["done"]), None)
        if urgent:
            ctk.CTkLabel(card, text=f"Most urgent: {urgent['name']} — start here.",
                         font=(theme.FONT, 12, "bold"), text_color=theme.DANGER).pack(
                anchor="w", padx=18, pady=(0, 6))
        for u in ranked:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=2)
            ctk.CTkLabel(row, text=u["name"], font=(theme.FONT, 12),
                         text_color=self.pal["text"], anchor="w", width=260).pack(side="left")
            ctk.CTkLabel(row, text=f"{round(u['remaining']*100)}% left",
                         font=(theme.FONT, 11), text_color=self.pal["text_muted"]).pack(side="left")
            bar = ctk.CTkProgressBar(row, height=10, corner_radius=5, width=140,
                                     progress_color=theme.ORANGE if u["priority"] > 50 else theme.INFO,
                                     fg_color=self.pal["surface_2"])
            bar.pack(side="right", padx=6); bar.set(u["priority"] / 100)
            ctk.CTkLabel(row, text=f"{u['priority']}", font=(theme.FONT, 12, "bold"),
                         text_color=theme.ORANGE).pack(side="right")
        ctk.CTkFrame(card, fg_color="transparent", height=10).pack()
