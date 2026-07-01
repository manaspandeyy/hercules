"""Small, dependency-free animation helpers built on Tk's ``after`` loop.

Everything here degrades gracefully — if a widget is destroyed mid-animation
the callbacks simply stop. Used for: window centering, fading toplevels,
animating progress bars, counting numbers up, and sliding views in.
"""


def ease_out(t):
    """Cubic ease-out: fast start, gentle finish. t in [0, 1]."""
    return 1 - (1 - t) ** 3


def center_window(win, w, h):
    """Place a window of size w×h dead centre on the screen."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = max(0, (sw - w) // 2)
    y = max(0, (sh - h) // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")


def fade_in(win, duration=280, steps=14, target=1.0, on_done=None):
    """Animate a toplevel's alpha from 0 → target."""
    try:
        win.attributes("-alpha", 0.0)
    except Exception:
        if on_done:
            on_done()
        return
    delay = max(1, int(duration / steps))

    def step(i):
        if not win.winfo_exists():
            return
        t = ease_out(i / steps)
        win.attributes("-alpha", target * t)
        if i < steps:
            win.after(delay, lambda: step(i + 1))
        elif on_done:
            on_done()
    step(1)


def fade_out(win, duration=210, steps=13, on_done=None):
    """Animate a toplevel's alpha from current → 0, then call on_done."""
    try:
        start = float(win.attributes("-alpha"))
    except Exception:
        if on_done:
            on_done()
        return
    delay = max(1, int(duration / steps))

    def step(i):
        if not win.winfo_exists():
            return
        t = i / steps
        win.attributes("-alpha", max(0.0, start * (1 - t)))
        if i < steps:
            win.after(delay, lambda: step(i + 1))
        elif on_done:
            on_done()
    step(1)


def animate_progressbar(widget, bar, target, duration=420, steps=21):
    """Smoothly move a CTkProgressBar from its current value to ``target``."""
    start = bar.get()
    delta = target - start
    delay = max(1, int(duration / steps))

    def step(i):
        if not bar.winfo_exists():
            return
        if i >= steps:
            bar.set(target)
            return
        bar.set(start + delta * ease_out(i / steps))
        widget.after(delay, lambda: step(i + 1))
    step(1)


def animate_count(widget, label, start, end, duration=560, steps=20, fmt=None):
    """Count a label's number from ``start`` to ``end`` with an ease-out."""
    delay = max(1, int(duration / steps))
    fmt = fmt or (lambda v: str(int(round(v))))

    def step(i):
        if not label.winfo_exists():
            return
        if i >= steps:
            label.configure(text=fmt(end))
            return
        val = start + (end - start) * ease_out(i / steps)
        label.configure(text=fmt(val))
        widget.after(delay, lambda: step(i + 1))
    step(1)


def slide_in(view, duration=154, steps=11, distance=24):
    """Slide a frame in from a small rightward offset to its resting place.

    The frame is positioned with place(); the caller should have packed its
    parent container. Works for full-bleed views (relwidth/relheight = 1).
    """
    delay = max(1, int(duration / steps))

    def step(i):
        if not view.winfo_exists():
            return
        if i >= steps:
            view.place(x=0, y=0, relwidth=1, relheight=1)
            return
        offset = distance * (1 - ease_out(i / steps))
        view.place(x=offset, y=0, relwidth=1, relheight=1)
        view.after(delay, lambda: step(i + 1))
    view.place(x=distance, y=0, relwidth=1, relheight=1)
    step(1)
