"""Mocks & Assessments view — track mock tests (score, pass/fail) plus a
performance chart with scores per mock and an improvement trend line.
"""

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import theme
from dialogs import MockDialog


class MocksView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
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
        data = self.app.data

        ctk.CTkLabel(self, text="Mocks & Assessments", font=(theme.FONT, 26, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=4)
        ctk.CTkLabel(self, text="Track your mock tests — pass is 60%+.",
                     font=(theme.FONT, 14), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=4, pady=(2, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for i, m in enumerate(data.mocks):
            self._mock_card(scroll, i, m)

        if data.mock_scores():
            self._chart(scroll, data)

    def _mock_card(self, parent, index, m):
        card = self._card(parent)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=14)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(left, text=m["name"], font=(theme.FONT, 15, "bold"),
                     text_color=self.pal["text"], anchor="w").pack(fill="x")

        if m.get("attempted") and m.get("total"):
            pct = m["score"] / m["total"] * 100
            passed = pct >= 60
            sub = f"{m['score']}/{m['total']}  ·  {pct:.0f}%  ·  {m.get('date', '')}"
            ctk.CTkLabel(left, text=sub, font=(theme.FONT, 12),
                         text_color=self.pal["text_muted"], anchor="w").pack(fill="x")
            if m.get("notes"):
                ctk.CTkLabel(left, text=f"Notes: {m['notes']}", font=(theme.FONT, 11),
                             text_color=self.pal["text_muted"], anchor="w",
                             wraplength=420, justify="left").pack(fill="x", pady=(2, 0))
            status, color = ("PASS ✅", theme.SUCCESS) if passed else ("FAIL ❌", theme.DANGER)
        else:
            ctk.CTkLabel(left, text="Not attempted", font=(theme.FONT, 12),
                         text_color=self.pal["text_muted"], anchor="w").pack(fill="x")
            status, color = ("Pending", theme.ORANGE)

        ctk.CTkLabel(row, text=status, font=(theme.FONT, 12, "bold"),
                     text_color="#FFFFFF", fg_color=color, corner_radius=8,
                     width=90, height=28).pack(side="right", padx=(8, 8))
        ctk.CTkButton(row, text="Log / Edit", height=36, width=110,
                      font=(theme.FONT, 13, "bold"), corner_radius=8,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=lambda i=index: MockDialog(
                          self.app, self.app.data, i, on_saved=self.build)).pack(side="right")

    def _chart(self, parent, data):
        card = self._card(parent)
        ctk.CTkLabel(card, text="Mock performance", font=(theme.FONT, 16, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(14, 0))

        rows = data.mock_scores()
        names = [r[0].replace(" Mock", "").replace(" (Mid Course)", "")
                 .replace(" (Full Course)", "") for r in rows]
        pcts = [r[1] for r in rows]

        fig = Figure(figsize=(5, 2.8), dpi=100)
        fig.patch.set_facecolor(self.pal["chart_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.pal["chart_bg"])
        for s in ax.spines.values():
            s.set_color(self.pal["chart_grid"])
        ax.tick_params(colors=self.pal["chart_text"], labelsize=8)
        ax.grid(True, axis="y", color=self.pal["chart_grid"], linewidth=0.5, alpha=0.6)

        colors = [theme.SUCCESS if p >= 60 else theme.DANGER for p in pcts]
        x = range(len(pcts))
        ax.bar(x, pcts, color=colors, width=0.55, zorder=3)
        if len(pcts) >= 2:                       # improvement trend line
            ax.plot(x, pcts, color=theme.INFO, linewidth=2, marker="o",
                    markersize=4, zorder=4, label="Trend")
            ax.legend(facecolor=self.pal["chart_bg"], edgecolor=self.pal["chart_grid"],
                      labelcolor=self.pal["chart_text"], fontsize=8)
        ax.axhline(60, color=theme.ORANGE, linestyle="--", linewidth=1.2)
        ax.set_ylim(0, 100)
        ax.set_ylabel("% score")
        ax.set_xticks(list(x))
        ax.set_xticklabels(names, fontsize=7, rotation=15, ha="right")
        ax.set_title("", color=self.pal["text"])
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)
