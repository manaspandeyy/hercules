"""Floating always-on-top portal applications counter.

A small semi-transparent window that stays above all other apps so the user
can click +1 while browsing job portals. Space/Enter also adds +1. Celebrates
with a colour flash when the 50-application target is hit.
"""

import time

import customtkinter as ctk

import theme
import animations as anim


class PortalCounter(ctk.CTkToplevel):
    TARGET = 50
    IDLE_TIMEOUT_MS = 30_000   # fade to semi-transparent after 30 s of no interaction

    def __init__(self, app, data, on_saved=None):
        super().__init__(app)
        self.app = app
        self.data = data
        self.on_saved = on_saved
        self.pal = theme.palette(app.mode)

        self._count = data.get_portal_session().get("count", 0)
        self._start = time.time()
        self._idle_id = None
        self._dimmed = False
        self._celebrated = False
        self._drag_x = self._drag_y = 0

        # ---- window chrome ----
        self.title("Portal Applications")
        self.resizable(False, False)
        self.wm_attributes("-topmost", True)
        self.attributes("-alpha", 0.88)

        # ---- default position: bottom-right corner ----
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"300x290+{sw - 320}+{sh - 330}")

        self._build()
        self._tick()
        self._reset_idle()

        self.bind("<space>", lambda _e: self._add(1))
        self.bind("<Return>", lambda _e: self._add(1))
        self.after(50, self.focus_force)

    # ---- build UI --------------------------------------------------------
    def _build(self):
        self.configure(fg_color=self.pal["sidebar"])

        # drag-handle header
        hdr = ctk.CTkFrame(self, fg_color=self.pal["surface_2"],
                           corner_radius=0, height=36)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Portal Applications 🚀",
                     font=(theme.FONT, 12, "bold"),
                     text_color=self.pal["text"]).pack(side="left", padx=12)
        ctk.CTkButton(hdr, text="✕", width=30, height=28,
                      font=(theme.FONT, 14), corner_radius=4,
                      fg_color="transparent", text_color=self.pal["text_muted"],
                      hover_color=theme.DANGER,
                      command=self.destroy).pack(side="right", padx=4)
        hdr.bind("<Button-1>", self._drag_start)
        hdr.bind("<B1-Motion>", self._drag_move)
        for child in hdr.winfo_children():
            child.bind("<Button-1>", self._drag_start)
            child.bind("<B1-Motion>", self._drag_move)

        # timer + target
        self.timer_lbl = ctk.CTkLabel(self, text="0:00  ·  Target: 50",
                                       font=(theme.FONT, 11),
                                       text_color=self.pal["text_muted"])
        self.timer_lbl.pack(pady=(6, 0))

        # progress bar
        self.prog = ctk.CTkProgressBar(self, height=7, corner_radius=4,
                                        progress_color=theme.ACCENT,
                                        fg_color=self.pal["surface_2"])
        self.prog.pack(fill="x", padx=16, pady=(2, 0))
        self.prog.set(min(1.0, self._count / self.TARGET))

        # big count number
        self.count_lbl = ctk.CTkLabel(self, text=str(self._count),
                                       font=(theme.FONT, 56, "bold"),
                                       text_color=theme.ACCENT)
        self.count_lbl.pack(pady=(2, 0))

        self.status_lbl = ctk.CTkLabel(self, text=self._status_text(),
                                        font=(theme.FONT, 11),
                                        text_color=self.pal["text_muted"])
        self.status_lbl.pack()

        # +/- / +5 row
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(8, 2))
        for label, delta, color in (("−1", -1, self.pal["surface_2"]),
                                     ("+1", 1, theme.ACCENT),
                                     ("+5", 5, theme.TEAL)):
            ctk.CTkButton(btn_row, text=label, width=62, height=38,
                          font=(theme.FONT, 15, "bold"), corner_radius=9,
                          fg_color=color,
                          text_color="#FFFFFF" if color != self.pal["surface_2"] else self.pal["text"],
                          hover_color=theme.ACCENT_HOVER if color == theme.ACCENT else
                          ("#24B0A0" if color == theme.TEAL else self.pal["border"]),
                          command=lambda d=delta: self._add(d)).pack(side="left", padx=3)

        # custom input row
        inp_row = ctk.CTkFrame(self, fg_color="transparent")
        inp_row.pack(pady=(2, 8))
        self.custom_ent = ctk.CTkEntry(inp_row, width=62, height=32,
                                        font=(theme.FONT, 13),
                                        fg_color=self.pal["surface_2"],
                                        border_color=self.pal["border"],
                                        placeholder_text="n")
        self.custom_ent.pack(side="left", padx=(0, 4))
        self.custom_ent.bind("<Return>", lambda _e: self._add_custom())
        ctk.CTkButton(inp_row, text="Add ▶", width=76, height=32,
                      font=(theme.FONT, 12, "bold"), corner_radius=8,
                      fg_color=self.pal["surface_2"], text_color=self.pal["text"],
                      hover_color=self.pal["border"],
                      command=self._add_custom).pack(side="left")

        # done button
        ctk.CTkButton(self, text="Done — Save & Close", height=38, corner_radius=8,
                      font=(theme.FONT, 13, "bold"),
                      fg_color=theme.SUCCESS, hover_color="#18A84E",
                      command=self._save_and_close).pack(fill="x", padx=14, pady=(0, 12))

    # ---- actions ---------------------------------------------------------
    def _add(self, n):
        self._count = max(0, self._count + n)
        self._update_display()
        self._reset_idle()
        if self._count >= self.TARGET and not self._celebrated:
            self._celebrate()

    def _add_custom(self):
        try:
            n = int(self.custom_ent.get().strip())
            self._add(n)
            self.custom_ent.delete(0, "end")
        except ValueError:
            pass

    def _update_display(self):
        if not self.winfo_exists():
            return
        self.count_lbl.configure(text=str(self._count))
        self.prog.set(min(1.0, self._count / self.TARGET))
        remaining = max(0, self.TARGET - self._count)
        col = theme.SUCCESS if remaining == 0 else self.pal["text_muted"]
        self.status_lbl.configure(text=self._status_text(), text_color=col)

    def _status_text(self):
        remaining = max(0, self.TARGET - self._count)
        return "🎉 Target reached!" if remaining == 0 else f"{remaining} to go"

    # ---- celebration flash -----------------------------------------------
    def _celebrate(self):
        self._celebrated = True
        try:
            self.bell()
        except Exception:
            pass
        self._flash(4, theme.SUCCESS)

    def _flash(self, n, color):
        if not self.winfo_exists():
            return
        if n <= 0:
            self.configure(fg_color=self.pal["sidebar"])
            return
        self.configure(fg_color=color)
        self.after(160, lambda: self._flash_off(n, color))

    def _flash_off(self, n, color):
        if not self.winfo_exists():
            return
        self.configure(fg_color=self.pal["sidebar"])
        self.after(160, lambda: self._flash(n - 1, color))

    # ---- timer -----------------------------------------------------------
    def _tick(self):
        if not self.winfo_exists():
            return
        elapsed = int(time.time() - self._start)
        m, s = divmod(elapsed, 60)
        h, m = divmod(m, 60)
        t = f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"
        if self.timer_lbl.winfo_exists():
            self.timer_lbl.configure(text=f"{t}  ·  Target: {self.TARGET}")
        self.after(1000, self._tick)

    # ---- idle dim --------------------------------------------------------
    def _reset_idle(self):
        if self._idle_id:
            try:
                self.after_cancel(self._idle_id)
            except Exception:
                pass
        if self._dimmed:
            self._dimmed = False
            self.attributes("-alpha", 0.88)
        self._idle_id = self.after(self.IDLE_TIMEOUT_MS, self._dim)

    def _dim(self):
        if self.winfo_exists():
            self._dimmed = True
            self.attributes("-alpha", 0.45)

    # ---- drag ------------------------------------------------------------
    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()
        self._reset_idle()

    def _drag_move(self, event):
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    # ---- save & close ----------------------------------------------------
    def _save_and_close(self):
        elapsed_min = max(0, int((time.time() - self._start) / 60))
        self.data.set_portal_session(self._count, elapsed_min)
        if self.on_saved:
            self.on_saved()
        self.destroy()
