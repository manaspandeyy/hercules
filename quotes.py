"""Motivational quote notification system.

Daemon thread fires plyer desktop notifications at random 15–120 min intervals.
Tracks shown quotes in data/quotes_shown.json — cycles through all before repeat.
get_daily_quote() returns one consistent quote per calendar day (seeded by date).

The quotes below are generic — edit this list to make them your own.
"""

import json
import os
import random
import threading
import time
from datetime import date

import theme

# ---- the quotes ---------------------------------------------------------
# Generic discipline / focus / consistency quotes — edit freely.

QUOTES = [
    # --- discipline ---
    "Nobody is coming to save you. Build the life yourself.",
    "The world owes you nothing. Everything you get, you earn.",
    "Comfort is the enemy of growth. Choose discomfort every single day.",
    "Pain is temporary. Regret lasts forever.",
    "Stop waiting for motivation. Discipline doesn't need it.",
    "While you sleep, someone else is working. Choose your sacrifice.",
    "The version of you who gave up is the only version that failed.",
    "Hard things done daily become easy. Easy things done daily become your ceiling.",
    "You will not be remembered for what you planned. Only for what you did.",
    "Most people die with their potential still inside them. Don't.",
    "Mediocrity is loud and everywhere. Excellence is lonely and necessary.",
    "Stop being impressed by your own effort. Results are the only currency.",
    "The gap between who you are and who you want to be is called excuses.",
    "Every day you don't work is a gift to your competition.",
    "Fear of failure is just fear of a better version of yourself.",

    # --- focus & consistency ---
    "Someone with less talent than you is outworking you right now.",
    "Small steps every day beat giant leaps once in a while.",
    "Consistency compounds. Show up again tomorrow.",
    "You don't have to be extreme, just consistent.",
    "The market doesn't reward participation. It rewards preparation.",
    "Skills are rented. Demonstrated results are owned.",
    "Done is better than perfect. Finish the thing.",
    "Protect your focus like it's the most valuable thing you own — it is.",
    "Motivation gets you started. Habit keeps you going.",
    "The difference between a wish and a goal is a plan on the calendar.",
    "Progress, not perfection. Track it, then repeat it.",
    "One more rep. One more page. One more task. That's how it's built.",
    "Discipline is choosing what you want most over what you want now.",
    "Your future self is watching you right now through memories.",
    "Start where you are. Use what you have. Do what you can.",

    # --- goals & momentum ---
    "Every task done is one fewer thing standing between you and your goal.",
    "A strong body carries a strong mind. Don't skip the basics.",
    "A deadline isn't pressure. It's a contract with your future self.",
    "Rest is part of the system. Laziness is a bug in it.",
    "You are building a better version of yourself in real time. Show up.",
    "The grind feels pointless until the day it isn't. Keep going.",
    "Nobody who put in this work stayed stuck. You won't either.",
    "Streak broken is not spirit broken. Reset and continue.",
    "One great effort beats ten half-hearted ones.",
    "You didn't start this tracker to feel productive. You started it to be productive.",
    "The goal is not to look busy. The goal is to make progress.",
    "What you do today matters more than the day you started.",
]

# ---- file paths ---------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_SHOWN_PATH = os.path.join(_DATA_DIR, "quotes_shown.json")


# ---- persistence --------------------------------------------------------

def _load_shown():
    try:
        with open(_SHOWN_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_shown(shown):
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_SHOWN_PATH, "w", encoding="utf-8") as f:
        json.dump(shown, f)


# ---- public API ---------------------------------------------------------

def get_daily_quote():
    """Return the same quote for today (seeded by date ordinal)."""
    rng = random.Random(date.today().toordinal())
    return rng.choice(QUOTES)


def _next_quote():
    """Pick the next unseen quote; cycle after all have been shown."""
    shown = _load_shown()
    remaining = [q for q in QUOTES if q not in shown]
    if not remaining:
        shown = []
        remaining = list(QUOTES)
        _save_shown(shown)
    q = random.choice(remaining)
    shown.append(q)
    _save_shown(shown)
    return q


# ---- notification daemon ------------------------------------------------

class QuoteNotifier:
    """Start once in main(). Fires plyer desktop notifications indefinitely."""

    MIN_SECS = 15 * 60    # 15 minutes
    MAX_SECS = 120 * 60   # 2 hours

    def __init__(self):
        self._thread = threading.Thread(target=self._run, daemon=True, name="QuoteNotifier")

    def start(self):
        self._thread.start()

    def _run(self):
        # wait a bit before first notification so the app can finish loading
        time.sleep(90)
        while True:
            try:
                from plyer import notification
                q = _next_quote()
                notification.notify(
                    title=theme.APP_NAME,
                    message=q,
                    app_name=theme.APP_NAME,
                    timeout=8,
                )
            except Exception:
                pass   # plyer not installed or notification failed — silent
            delay = random.randint(self.MIN_SECS, self.MAX_SECS)
            time.sleep(delay)
