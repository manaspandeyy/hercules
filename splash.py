"""Launch splash screen."""

import customtkinter as ctk

import theme
import animations as anim

W, H = 460, 320


class Splash(ctk.CTkToplevel):
    def __init__(self, master, on_done):
        super().__init__(master)
        self.on_done = on_done
        self.pal = theme.palette(master.mode)

        self.overrideredirect(True)
        self.configure(fg_color=self.pal["sidebar"])
        anim.center_window(self, W, H)
        try:
            self.attributes("-topmost", True)
            self.attributes("-alpha", 0.0)
        except Exception:
            pass

        self._build()
        anim.fade_in(self, duration=450, on_done=self._start_loading)

    def _build(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(wrap, text="⚡", font=(theme.FONT, 46),
                     text_color=theme.WARNING).pack()
        ctk.CTkLabel(wrap, text=theme.APP_NAME, font=(theme.FONT, 44, "bold"),
                     text_color=self.pal["text"]).pack(pady=(2, 0))
        ctk.CTkLabel(wrap, text=theme.APP_TAGLINE.upper(), font=(theme.FONT, 13),
                     text_color=theme.ACCENT).pack(pady=(2, 18))

        self.bar = ctk.CTkProgressBar(wrap, width=260, height=8, corner_radius=4,
                                      progress_color=theme.ACCENT,
                                      fg_color=self.pal["surface_2"])
        self.bar.pack()
        self.bar.set(0)

        self.status = ctk.CTkLabel(wrap, text="Loading…", font=(theme.FONT, 11),
                                   text_color=self.pal["text_muted"])
        self.status.pack(pady=(10, 0))

        # "Let's Go" button — hidden until loading completes
        self.go_btn = ctk.CTkButton(
            wrap, text="Let's Go →",
            font=(theme.FONT, 15, "bold"),
            text_color="#FFFFFF",
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            width=160, height=42,
            corner_radius=10,
            command=self._finish,
        )
        # not packed yet — shown in _on_ready

    def _start_loading(self):
        anim.animate_progressbar(self, self.bar, 1.0, duration=1400, steps=40)
        self.after(1500, self._on_ready)

    def _on_ready(self):
        self.status.configure(text="Ready ✓", text_color=theme.SUCCESS)
        self.go_btn.pack(pady=(14, 0))

    def _finish(self):
        anim.fade_out(self, duration=320, on_done=self._close)

    def _close(self):
        cb = self.on_done
        if self.winfo_exists():
            self.destroy()
        if cb:
            cb()
