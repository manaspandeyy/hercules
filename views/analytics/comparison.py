"""Comparison tab — pick any two periods and see which won each metric."""

import customtkinter as ctk

import theme
from .charts import TabBase


class ComparisonTab(TabBase):
    def __init__(self, master, app):
        super().__init__(master, app)
        self.a = "This week"
        self.b = "Last week"

    def build(self):
        for w in self.winfo_children():
            w.destroy()
        s = self.scroll()

        # selectors
        sel = self.card(s)
        row = ctk.CTkFrame(sel, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=16)
        opts = self.m.PERIODS
        ctk.CTkLabel(row, text="Period A", font=(theme.FONT, 13, "bold"),
                     text_color=theme.ACCENT).pack(side="left")
        ma = ctk.CTkOptionMenu(row, values=opts, width=150, font=(theme.FONT, 13),
                               fg_color=self.pal["surface_2"], button_color=theme.ACCENT,
                               button_hover_color=theme.ACCENT_HOVER,
                               command=lambda v: self._set("a", v))
        ma.set(self.a); ma.pack(side="left", padx=(8, 20))
        ctk.CTkLabel(row, text="vs", font=(theme.FONT, 13),
                     text_color=self.pal["text_muted"]).pack(side="left")
        ctk.CTkLabel(row, text="Period B", font=(theme.FONT, 13, "bold"),
                     text_color=theme.INFO).pack(side="left", padx=(20, 0))
        mb = ctk.CTkOptionMenu(row, values=opts, width=150, font=(theme.FONT, 13),
                               fg_color=self.pal["surface_2"], button_color=theme.INFO,
                               button_hover_color=theme.ACCENT_HOVER,
                               command=lambda v: self._set("b", v))
        mb.set(self.b); mb.pack(side="left", padx=8)

        rows, na, nb = self.m.compare(self.a, self.b)

        # header
        head = self.card(s)
        hr = ctk.CTkFrame(head, fg_color="transparent")
        hr.pack(fill="x", padx=18, pady=12)
        ctk.CTkLabel(hr, text="Metric", font=(theme.FONT, 12, "bold"),
                     text_color=self.pal["text_muted"], width=180, anchor="w").pack(side="left")
        ctk.CTkLabel(hr, text=na, font=(theme.FONT, 12, "bold"),
                     text_color=theme.ACCENT, width=90).pack(side="left")
        ctk.CTkLabel(hr, text=nb, font=(theme.FONT, 12, "bold"),
                     text_color=theme.INFO, width=90).pack(side="left")
        ctk.CTkLabel(hr, text="Change", font=(theme.FONT, 12, "bold"),
                     text_color=self.pal["text_muted"]).pack(side="left", padx=10)

        for r in rows:
            self._row(head, r, na, nb)

        # auto summary
        summ = self.card(s)
        ctk.CTkLabel(summ, text="📋 Auto summary", font=(theme.FONT, 15, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(12, 4))
        ctk.CTkLabel(summ, text=self.m.compare_summary(rows, na, nb),
                     font=(theme.FONT, 13), text_color=self.pal["text"],
                     wraplength=640, justify="left").pack(anchor="w", padx=18, pady=(0, 16))

    def _row(self, parent, r, na, nb):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=2)
        ctk.CTkLabel(row, text=r["label"], font=(theme.FONT, 12),
                     text_color=self.pal["text"], width=180, anchor="w").pack(side="left")
        a_color = theme.SUCCESS if r["winner"] == "a" else self.pal["text"]
        b_color = theme.SUCCESS if r["winner"] == "b" else self.pal["text"]
        ctk.CTkLabel(row, text=str(r["a"]), font=(theme.FONT, 12, "bold"),
                     text_color=a_color, width=90).pack(side="left")
        ctk.CTkLabel(row, text=str(r["b"]), font=(theme.FONT, 12, "bold"),
                     text_color=b_color, width=90).pack(side="left")
        pct = r["pct"]
        col = theme.SUCCESS if pct > 0 else theme.DANGER if pct < 0 else self.pal["text_muted"]
        arrow = "▲" if pct > 0 else "▼" if pct < 0 else "■"
        ctk.CTkLabel(row, text=f"{arrow} {pct:+d}%  (A vs B)", font=(theme.FONT, 12, "bold"),
                     text_color=col).pack(side="left", padx=10)

    def _set(self, which, value):
        setattr(self, which, value)
        self.build()
