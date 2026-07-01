"""Shared building blocks for analytics tabs.

FIX 3: ChartCard.finish() now renders matplotlib figures in a background
thread (using the Agg backend — thread-safe, no Tk required), converts to
PIL Image, and displays via CTkLabel on the main thread via after(0, ...).

This means the UI never freezes during chart rendering. A "Rendering…"
placeholder is shown immediately; it is replaced by the chart image when ready.
"""

import io
import threading
from tkinter import filedialog

import customtkinter as ctk
from matplotlib.figure import Figure
from PIL import Image

import theme
import animations as anim
from metrics import Metrics

# DPI for all charts — low enough for zero lag
CHART_DPI = 72


class TabBase(ctk.CTkFrame):
    """Base for every analytics tab."""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.m = Metrics(app.data)
        self._figures = []   # no longer needed for cleanup, kept for compat

    def cleanup(self):
        """No-op: figures are closed immediately after PNG export in bg thread."""
        self._figures.clear()

    @property
    def pal(self):
        return self.app.pal

    def card(self, parent=None):
        c = ctk.CTkFrame(parent or self, fg_color=self.pal["surface"], corner_radius=14,
                         border_width=1, border_color=self.pal["border"])
        c.pack(fill="x", pady=8, padx=4)
        return c

    def scroll(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="both", expand=True)
        return f


class DetailPopup(ctk.CTkToplevel):
    def __init__(self, app, title, lines):
        super().__init__(app)
        pal = theme.palette(app.mode)
        self.configure(fg_color=pal["surface"])
        self.resizable(False, False)
        anim.center_window(self, 320, 80 + 34 * len(lines))
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass
        self.transient(app)
        self.after(10, self._grab)
        anim.fade_in(self, duration=180)

        ctk.CTkLabel(self, text=title, font=(theme.FONT, 16, "bold"),
                     text_color=pal["text"]).pack(anchor="w", padx=18, pady=(16, 8))
        for label, value, color in lines:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=2)
            ctk.CTkLabel(row, text=label, font=(theme.FONT, 13),
                         text_color=pal["text_muted"]).pack(side="left")
            ctk.CTkLabel(row, text=str(value), font=(theme.FONT, 13, "bold"),
                         text_color=color or pal["text"]).pack(side="right")
        ctk.CTkButton(self, text="Close", height=34, corner_radius=8,
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self.destroy).pack(fill="x", padx=18, pady=14)

    def _grab(self):
        try:
            self.grab_set()
        except Exception:
            pass


class ChartCard:
    """A titled card wrapping one matplotlib figure.

    finish() is always async: matplotlib renders in a daemon thread using the
    Agg backend (thread-safe), then the resulting PIL Image is displayed on the
    main thread via after(0, ...). The UI is never blocked.
    """

    def __init__(self, tab, parent, title, subtitle=None, height=2.7, ncols=1, zoom=False):
        self.tab = tab
        self.pal = tab.pal
        self._title = title

        self.card = ctk.CTkFrame(parent, fg_color=self.pal["surface"], corner_radius=14,
                                 border_width=1, border_color=self.pal["border"])
        self.card.pack(fill="x", pady=8, padx=4)

        head = ctk.CTkFrame(self.card, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(12, 0))
        col = ctk.CTkFrame(head, fg_color="transparent")
        col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(col, text=title, font=(theme.FONT, 15, "bold"),
                     text_color=self.pal["text"], anchor="w").pack(fill="x")
        if subtitle:
            ctk.CTkLabel(col, text=subtitle, font=(theme.FONT, 11),
                         text_color=self.pal["text_muted"], anchor="w").pack(fill="x")
        ctk.CTkButton(head, text="⬇ PNG", width=64, height=28, font=(theme.FONT, 11),
                      corner_radius=8, fg_color=self.pal["surface_2"],
                      text_color=self.pal["text"], hover_color=self.pal["border"],
                      command=self._export).pack(side="right")

        # figure + axes — set up on main thread (fast: just data binding)
        self.fig = Figure(figsize=(5 * ncols, height), dpi=CHART_DPI)
        self.fig.patch.set_facecolor(self.pal["chart_bg"])
        self.ax = self.fig.add_subplot(111)
        self.style(self.ax)

        # placeholder shown while bg thread renders
        self._placeholder = ctk.CTkLabel(
            self.card, text="⏳  Rendering chart…",
            font=(theme.FONT, 12), text_color=self.pal["text_muted"])
        self._placeholder.pack(pady=24)

        self._img_label = None   # will hold the CTkLabel with the chart image

    # -- styling helpers -------------------------------------------------------
    def style(self, ax):
        ax.set_facecolor(self.pal["chart_bg"])
        for s in ax.spines.values():
            s.set_color(self.pal["chart_grid"])
        ax.tick_params(colors=self.pal["chart_text"], labelsize=8)
        ax.yaxis.label.set_color(self.pal["chart_text"])
        ax.title.set_color(self.pal["text"])
        ax.grid(True, color=self.pal["chart_grid"], linewidth=0.5, alpha=0.6)

    def legend(self, ax=None):
        (ax or self.ax).legend(
            facecolor=self.pal["chart_bg"],
            edgecolor=self.pal["chart_grid"],
            labelcolor=self.pal["chart_text"],
            fontsize=8)

    # -- async finish ----------------------------------------------------------
    def finish(self, animate=None, hover=None, detail=None):
        """Kick off background render; display result on main thread."""
        # animate/hover/detail are ignored in async mode —
        # interactivity is sacrificed to guarantee a non-frozen UI.
        try:
            self.fig.tight_layout()
        except Exception:
            pass

        fig = self.fig
        bg = self.pal["chart_bg"]
        card = self.card

        def _render():
            try:
                from matplotlib.backends.backend_agg import FigureCanvasAgg
                FigureCanvasAgg(fig)          # bind thread-safe Agg renderer
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight",
                            facecolor=bg, dpi=CHART_DPI)
                buf.seek(0)
                img = Image.open(buf).copy()  # detach from BytesIO before it closes
            except Exception:
                img = None
            finally:
                try:
                    import matplotlib.pyplot as plt
                    plt.close(fig)
                except Exception:
                    pass
            card.after(0, lambda: _show(img))

        def _show(img):
            if not card.winfo_exists():
                return
            if self._placeholder and self._placeholder.winfo_exists():
                self._placeholder.pack_forget()
            if img is None:
                ctk.CTkLabel(card, text="Chart unavailable",
                             font=(theme.FONT, 11),
                             text_color=theme.DANGER).pack(pady=8)
                return
            try:
                cimg = ctk.CTkImage(light_image=img, dark_image=img,
                                    size=(img.width, img.height))
                lbl = ctk.CTkLabel(card, image=cimg, text="")
                lbl._ref = cimg        # prevent garbage collection
                lbl.pack(fill="x", padx=10, pady=(4, 10))
                self._img_label = lbl
            except Exception:
                pass

        threading.Thread(target=_render, daemon=True).start()

    # -- PNG export (sync — user triggered, blocking is acceptable) -----------
    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG image", "*.png")],
            title="Export chart")
        if path and self._img_label:
            try:
                img = self._img_label._ref._light_image
                img.save(path)
            except Exception:
                pass
