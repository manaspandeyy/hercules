"""Centralised colours and styling.

FIX 4: 8 preset color themes. apply_theme(name) updates the live DARK/LIGHT
dicts so every palette() call immediately returns the new colours.
The chosen theme name is saved to settings.json by the settings view.
"""

# ---- semantic colours (used throughout app, not palette-dependent) -------
SUCCESS = "#22C55E"
YELLOW  = "#EAB308"
ORANGE  = "#F97316"
DANGER  = "#EF4444"
INFO    = "#38BDF8"
TEAL    = "#2DD4BF"
WARNING = ORANGE

# ---- accent (overwritten by apply_theme) ---------------------------------
ACCENT       = "#6366F1"
ACCENT_HOVER = "#5457E5"
ACCENT_SOFT  = "#818CF8"

# ---- 8 preset themes -----------------------------------------------------
THEMES = {
    "MIDNIGHT": {
        "accent":      "#6366F1",
        "accent_hover":"#5457E5",
        "dark": {
            "name": "dark",
            "bg": "#0E1016", "surface": "#171A23", "surface_2": "#1F2330",
            "sidebar": "#11131B", "text": "#ECEEF4", "text_muted": "#8B90A3",
            "border": "#272B39", "chart_bg": "#171A23",
            "chart_grid": "#2B3040", "chart_text": "#C3C7D6",
        },
        "light": {
            "name": "light",
            "bg": "#F3F4FA", "surface": "#FFFFFF", "surface_2": "#EDEFF6",
            "sidebar": "#FFFFFF", "text": "#13151F", "text_muted": "#5C6175",
            "border": "#E2E5F0", "chart_bg": "#FFFFFF",
            "chart_grid": "#E2E5F0", "chart_text": "#4A4F63",
        },
    },
    "OCEAN": {
        "accent":      "#64ffda",
        "accent_hover":"#43e8c0",
        "dark": {
            "name": "dark",
            "bg": "#0a1628", "surface": "#112240", "surface_2": "#172c52",
            "sidebar": "#091220", "text": "#ccd6f6", "text_muted": "#8892b0",
            "border": "#1e3a5f", "chart_bg": "#112240",
            "chart_grid": "#1e3a5f", "chart_text": "#a8b2d8",
        },
        "light": {
            "name": "light",
            "bg": "#e8f4fd", "surface": "#ffffff", "surface_2": "#d0eaf8",
            "sidebar": "#ffffff", "text": "#0a1628", "text_muted": "#4a6080",
            "border": "#b0d4ee", "chart_bg": "#ffffff",
            "chart_grid": "#d0eaf8", "chart_text": "#2a4a6a",
        },
    },
    "CYBERPUNK": {
        "accent":      "#ff2d78",
        "accent_hover":"#e0205f",
        "dark": {
            "name": "dark",
            "bg": "#0d0221", "surface": "#1a0533", "surface_2": "#250744",
            "sidebar": "#0a0118", "text": "#f0e6ff", "text_muted": "#9b72cf",
            "border": "#3d1066", "chart_bg": "#1a0533",
            "chart_grid": "#3d1066", "chart_text": "#d4b3ff",
        },
        "light": {
            "name": "light",
            "bg": "#f5eaff", "surface": "#ffffff", "surface_2": "#ead6ff",
            "sidebar": "#ffffff", "text": "#1a0533", "text_muted": "#6a3a9a",
            "border": "#d4b3ff", "chart_bg": "#ffffff",
            "chart_grid": "#ead6ff", "chart_text": "#4a1a7a",
        },
    },
    "EMBER": {
        "accent":      "#ff6b35",
        "accent_hover":"#e55520",
        "dark": {
            "name": "dark",
            "bg": "#1a0a00", "surface": "#2d1500", "surface_2": "#3d1f00",
            "sidebar": "#120800", "text": "#ffe8d6", "text_muted": "#b07050",
            "border": "#5a2e00", "chart_bg": "#2d1500",
            "chart_grid": "#5a2e00", "chart_text": "#ffc4a0",
        },
        "light": {
            "name": "light",
            "bg": "#fff3ec", "surface": "#ffffff", "surface_2": "#ffe8d6",
            "sidebar": "#ffffff", "text": "#1a0a00", "text_muted": "#8a4020",
            "border": "#ffcaa0", "chart_bg": "#ffffff",
            "chart_grid": "#ffe8d6", "chart_text": "#5a2010",
        },
    },
    "ARCTIC": {
        "accent":      "#0066cc",
        "accent_hover":"#0052a3",
        "dark": {
            "name": "dark",
            "bg": "#0d1b2a", "surface": "#1a2e42", "surface_2": "#243d55",
            "sidebar": "#091520", "text": "#e8f4ff", "text_muted": "#7aa8cc",
            "border": "#2d4a66", "chart_bg": "#1a2e42",
            "chart_grid": "#2d4a66", "chart_text": "#a8ccee",
        },
        "light": {
            "name": "light",
            "bg": "#f0f4f8", "surface": "#ffffff", "surface_2": "#e2ecf6",
            "sidebar": "#ffffff", "text": "#0d1b2a", "text_muted": "#4a6a8a",
            "border": "#c2d8ee", "chart_bg": "#ffffff",
            "chart_grid": "#e2ecf6", "chart_text": "#2a4a6a",
        },
    },
    "FOREST": {
        "accent":      "#39ff14",
        "accent_hover":"#22dd00",
        "dark": {
            "name": "dark",
            "bg": "#0a1a0a", "surface": "#112211", "surface_2": "#172e17",
            "sidebar": "#071407", "text": "#d4ffd4", "text_muted": "#6a9a6a",
            "border": "#1e3e1e", "chart_bg": "#112211",
            "chart_grid": "#1e3e1e", "chart_text": "#a8d8a8",
        },
        "light": {
            "name": "light",
            "bg": "#edfaed", "surface": "#ffffff", "surface_2": "#d4f4d4",
            "sidebar": "#ffffff", "text": "#0a1a0a", "text_muted": "#3a6a3a",
            "border": "#a8d8a8", "chart_bg": "#ffffff",
            "chart_grid": "#d4f4d4", "chart_text": "#1a4a1a",
        },
    },
    "GOLD": {
        "accent":      "#ffd700",
        "accent_hover":"#e6c200",
        "dark": {
            "name": "dark",
            "bg": "#1a1500", "surface": "#2d2500", "surface_2": "#3d3200",
            "sidebar": "#120f00", "text": "#fff8d6", "text_muted": "#b09a40",
            "border": "#5a4a00", "chart_bg": "#2d2500",
            "chart_grid": "#5a4a00", "chart_text": "#ffeea0",
        },
        "light": {
            "name": "light",
            "bg": "#fffbea", "surface": "#ffffff", "surface_2": "#fff3c4",
            "sidebar": "#ffffff", "text": "#1a1500", "text_muted": "#7a6010",
            "border": "#ffe878", "chart_bg": "#ffffff",
            "chart_grid": "#fff3c4", "chart_text": "#4a3a00",
        },
    },
    "LAVENDER": {
        "accent":      "#b57bee",
        "accent_hover":"#9e5fe0",
        "dark": {
            "name": "dark",
            "bg": "#0f0a1a", "surface": "#1e1033", "surface_2": "#2a1844",
            "sidebar": "#0a0714", "text": "#ede6ff", "text_muted": "#8a72aa",
            "border": "#3a2255", "chart_bg": "#1e1033",
            "chart_grid": "#3a2255", "chart_text": "#c8b0ee",
        },
        "light": {
            "name": "light",
            "bg": "#f5f0ff", "surface": "#ffffff", "surface_2": "#ece4ff",
            "sidebar": "#ffffff", "text": "#0f0a1a", "text_muted": "#5a3a8a",
            "border": "#d4b8ff", "chart_bg": "#ffffff",
            "chart_grid": "#ece4ff", "chart_text": "#3a1a6a",
        },
    },
}

# ---- live palette dicts (mutated by apply_theme) -------------------------
DARK  = dict(THEMES["MIDNIGHT"]["dark"])
LIGHT = dict(THEMES["MIDNIGHT"]["light"])

_current_theme = "MIDNIGHT"


def palette(mode):
    return DARK if mode == "dark" else LIGHT


def current_theme_name():
    return _current_theme


def apply_theme(name, app=None):
    """Update live palette dicts + accent globals, then rebuild app UI if given."""
    global _current_theme, ACCENT, ACCENT_HOVER, ACCENT_SOFT
    t = THEMES.get(name, THEMES["MIDNIGHT"])
    _current_theme = name

    DARK.update(t["dark"])
    LIGHT.update(t["light"])
    ACCENT       = t["accent"]
    ACCENT_HOVER = t["accent_hover"]
    ACCENT_SOFT  = t["accent"]

    if app is not None:
        app.data.settings["color_theme"] = name
        app.data.save_settings()
        # rebuild UI same as toggle_theme
        app._views = {}
        for w in app.winfo_children():
            w.destroy()
        app.nav_buttons = {}
        app.view = None
        app._build_layout()
        app.show(app.current or "schedule", animate=False)


def progress_color(frac):
    pct = frac * 100
    if pct <= 0:
        return DANGER
    if pct <= 30:
        return ORANGE
    if pct <= 70:
        return YELLOW
    return SUCCESS


FONT = "Segoe UI"

# ---- app identity --------------------------------------------------------
# Change these to rebrand the whole app in one place.
APP_NAME = "Hercules"          # shown in the title bar, splash, notifications
APP_TAGLINE = "Daily Tracker"  # shown under the logo on the splash screen
SCORE_NAME = "Momentum Score"  # the daily 0-100 productivity score label
APP_ID = "hercules.daily.tracker"  # Windows taskbar app id
