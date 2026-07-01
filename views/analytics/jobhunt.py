"""Job Hunt tab — portal applications, referrals, cold emails, funnel, insights."""

from datetime import date

import numpy as np
import customtkinter as ctk
import matplotlib.patches as mpatches
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import theme
from .charts import TabBase, ChartCard


class JobHuntTab(TabBase):
    def build(self):
        for w in self.winfo_children():
            w.destroy()
        s = self.scroll()
        self._insight_cards(s)
        self._funnel_editor(s)
        self._daily_stacked(s)
        self._response_rates(s)
        self._weekly_totals(s)
        self._cumulative(s)

    # ---- insight cards ---------------------------------------------------
    def _insight_cards(self, parent):
        totals = self.m.job_hunt_totals(30)
        insights = self.m.job_hunt_insights()

        card = self.card(parent)
        ctk.CTkLabel(card, text="30-Day Job Hunt Summary",
                     font=(theme.FONT, 15, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(12, 4))

        # big metric row
        metrics_row = ctk.CTkFrame(card, fg_color="transparent")
        metrics_row.pack(fill="x", padx=18, pady=(0, 8))
        big_stats = [
            ("Portal Apps", totals["portal"], theme.ACCENT),
            ("Referrals", totals["referrals"], theme.TEAL),
            ("Cold Emails", totals["cold"], theme.INFO),
            ("Total Outreach", totals["total_outreach"], theme.ORANGE),
        ]
        for label, val, color in big_stats:
            col = ctk.CTkFrame(metrics_row, fg_color=self.pal["surface_2"],
                               corner_radius=10)
            col.pack(side="left", fill="both", expand=True, padx=(0, 8))
            ctk.CTkLabel(col, text=str(val), font=(theme.FONT, 28, "bold"),
                         text_color=color).pack(pady=(10, 0))
            ctk.CTkLabel(col, text=label, font=(theme.FONT, 11),
                         text_color=self.pal["text_muted"]).pack(pady=(0, 10))

        # insight text rows
        for icon, text in insights:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=2)
            ctk.CTkLabel(row, text=icon, font=(theme.FONT, 14)).pack(side="left")
            ctk.CTkLabel(row, text=text, font=(theme.FONT, 12),
                         text_color=self.pal["text_muted"],
                         wraplength=580, justify="left").pack(side="left", padx=8)
        ctk.CTkFrame(card, height=10, fg_color="transparent").pack()

    # ---- funnel + interview/offer editor ---------------------------------
    def _funnel_editor(self, parent):
        card = self.card(parent)
        ctk.CTkLabel(card, text="Application Funnel  ·  last 90 days",
                     font=(theme.FONT, 15, "bold"),
                     text_color=self.pal["text"]).pack(anchor="w", padx=18, pady=(12, 2))
        ctk.CTkLabel(card, text="Interviews & offers — enter cumulative totals",
                     font=(theme.FONT, 11), text_color=self.pal["text_muted"]).pack(
            anchor="w", padx=18)

        funnel = self.m.job_hunt_funnel()

        # mini editor row for interviews / offers
        edit_row = ctk.CTkFrame(card, fg_color="transparent")
        edit_row.pack(fill="x", padx=18, pady=(8, 4))

        self._iv_ent = ctk.CTkEntry(edit_row, width=80, height=30, font=(theme.FONT, 13),
                                     fg_color=self.pal["surface_2"],
                                     border_color=self.pal["border"])
        self._iv_ent.insert(0, str(self.app.data.goals.get("interviews", 0)))
        ctk.CTkLabel(edit_row, text="Interviews:", font=(theme.FONT, 12),
                     text_color=self.pal["text_muted"]).pack(side="left")
        self._iv_ent.pack(side="left", padx=(4, 16))

        self._of_ent = ctk.CTkEntry(edit_row, width=80, height=30, font=(theme.FONT, 13),
                                     fg_color=self.pal["surface_2"],
                                     border_color=self.pal["border"])
        self._of_ent.insert(0, str(self.app.data.goals.get("offers", 0)))
        ctk.CTkLabel(edit_row, text="Offers:", font=(theme.FONT, 12),
                     text_color=self.pal["text_muted"]).pack(side="left")
        self._of_ent.pack(side="left", padx=(4, 12))
        ctk.CTkButton(edit_row, text="Save", width=64, height=30,
                      font=(theme.FONT, 12, "bold"), corner_radius=8,
                      fg_color=theme.SUCCESS, hover_color="#18A84E",
                      command=self._save_funnel).pack(side="left")

        # horizontal funnel bar chart
        fig = Figure(figsize=(6, 2.2), dpi=100)
        fig.patch.set_facecolor(self.pal["chart_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.pal["chart_bg"])
        ax.spines[:].set_visible(False)
        ax.tick_params(left=False, bottom=False, labelbottom=False)

        stages = [s for s, v in funnel]
        vals = [v for _, v in funnel]
        colors = [theme.ACCENT, theme.TEAL, theme.ORANGE, theme.SUCCESS]
        max_v = max(vals) if any(vals) else 1
        bar_height = 0.45
        for i, (label, val, color) in enumerate(zip(stages, vals, colors)):
            frac = val / max_v if max_v > 0 else 0
            ax.barh(i, frac, height=bar_height, color=color, alpha=0.85, zorder=3)
            ax.text(frac + 0.02, i, f"{label}: {val}",
                    va="center", color=self.pal["chart_text"], fontsize=9)
        ax.set_yticks(range(len(stages)))
        ax.set_yticklabels([""] * len(stages))
        ax.set_xlim(0, 1.6)
        ax.set_ylim(-0.5, len(stages) - 0.5)
        ax.invert_yaxis()
        ax.grid(False)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=(4, 10))

    def _save_funnel(self):
        try:
            iv = int(self._iv_ent.get())
            of = int(self._of_ent.get())
            self.app.data.update_interviews_offers(iv, of)
        except ValueError:
            pass

    # ---- daily stacked bar: portal + referrals + cold emails -------------
    def _daily_stacked(self, parent):
        labels, portals, refs, colds = self.m.job_hunt_series(30)

        cc = ChartCard(self, parent, "Daily Outreach — last 30 days",
                       subtitle="Portal applications  +  Referral requests  +  Cold emails",
                       height=3.0)
        x = np.arange(len(labels))
        p_arr = np.array(portals, dtype=float)
        r_arr = np.array(refs, dtype=float)
        c_arr = np.array(colds, dtype=float)

        bars_p = cc.ax.bar(x, p_arr, color=theme.ACCENT, label="Portal", zorder=3)
        bars_r = cc.ax.bar(x, r_arr, bottom=p_arr, color=theme.TEAL,
                           label="Referrals", zorder=3)
        cc.ax.bar(x, c_arr, bottom=p_arr + r_arr, color=theme.INFO,
                  label="Cold Emails", zorder=3)

        # show every 5th label to avoid crowding
        tick_labels = [l if i % 5 == 0 else "" for i, l in enumerate(labels)]
        cc.ax.set_xticks(x)
        cc.ax.set_xticklabels(tick_labels, fontsize=7)
        cc.ax.set_ylabel("count")
        cc.legend()
        total = p_arr + r_arr + c_arr
        cc.finish(hover=("bar", list(x), list(total), labels,
                          lambda v: f"{int(v)} total"))

    # ---- response rates --------------------------------------------------
    def _response_rates(self, parent):
        _, ref_sent, ref_resp = self.app.data.referrals_last_n(30)
        _, cold_sent, cold_rep = self.app.data.cold_emails_last_n(30)

        # compute weekly response rates
        weeks = self.m.last_weeks(8)
        wlabels = [w[0] for w in weeks]
        ref_rates, cold_rates = [], []
        from datetime import timedelta
        for _, start, end in weeks:
            rs = sum(self.m.referrals_sent(start + timedelta(days=i))
                     for i in range(7))
            rr = sum(self.app.data.log.get(
                (start + timedelta(days=i)).isoformat(), {}).get(
                "referrals", {}).get("responses", 0) for i in range(7))
            cs = sum(self.m.cold_emails_sent(start + timedelta(days=i))
                     for i in range(7))
            cr = sum(self.app.data.log.get(
                (start + timedelta(days=i)).isoformat(), {}).get(
                "cold_emails", {}).get("replies", 0) for i in range(7))
            ref_rates.append(round(rr / rs * 100) if rs > 0 else 0)
            cold_rates.append(round(cr / cs * 100) if cs > 0 else 0)

        cc = ChartCard(self, parent, "Weekly Response Rates",
                       subtitle="Referral response %  vs  Cold email reply %")
        xs = list(range(len(wlabels)))
        width = 0.35
        x = np.arange(len(wlabels))
        cc.ax.bar(x - width / 2, ref_rates, width, label="Referrals %",
                  color=theme.TEAL, zorder=3)
        cc.ax.bar(x + width / 2, cold_rates, width, label="Cold Emails %",
                  color=theme.INFO, zorder=3)
        cc.ax.axhline(10, color=theme.ORANGE, ls="--", lw=1.2, alpha=0.7)
        cc.ax.set_ylim(0, max(max(ref_rates + cold_rates, default=0) + 10, 25))
        cc.ax.set_xticks(x)
        cc.ax.set_xticklabels(wlabels, fontsize=8)
        cc.ax.set_ylabel("%")
        cc.legend()
        cc.finish()

    # ---- weekly totals grouped bar ---------------------------------------
    def _weekly_totals(self, parent):
        wlabels, portals, refs, colds = self.m.job_hunt_weekly(8)
        x = np.arange(len(wlabels))
        width = 0.25

        cc = ChartCard(self, parent, "Weekly Outreach Totals",
                       subtitle="Per-category totals — last 8 weeks", height=2.8)
        cc.ax.bar(x - width, portals, width, label="Portal", color=theme.ACCENT, zorder=3)
        cc.ax.bar(x, refs, width, label="Referrals", color=theme.TEAL, zorder=3)
        cc.ax.bar(x + width, colds, width, label="Cold Emails", color=theme.INFO, zorder=3)
        cc.ax.set_xticks(x)
        cc.ax.set_xticklabels(wlabels, fontsize=8)
        cc.ax.set_ylabel("count")
        cc.legend()
        cc.finish()

    # ---- cumulative portal apps sent ------------------------------------
    def _cumulative(self, parent):
        labels, vals, *_ = self.app.data.portal_apps_last_n(30)
        running = []
        total = 0
        for v in vals:
            total += v
            running.append(total)

        cc = ChartCard(self, parent, "Cumulative Portal Applications — last 30 days",
                       zoom=True)
        xs = list(range(len(labels)))
        (ln,) = cc.ax.plot([], [], color=theme.ACCENT, lw=2.2, zorder=3)
        cc.ax.fill_between(xs, [0] * len(xs), running, color=theme.ACCENT, alpha=0.12)
        cc.ax.set_xlim(0, max(1, len(xs) - 1))
        cc.ax.set_ylim(0, max(running + [1]) * 1.15)
        tick_labels = [l if i % 5 == 0 else "" for i, l in enumerate(labels)]
        cc.ax.set_xticks(xs)
        cc.ax.set_xticklabels(tick_labels, fontsize=7)
        cc.ax.set_ylabel("total applied")
        cc.finish(animate=("line", ln, xs, running),
                  hover=("line", xs, running, labels,
                          lambda v: f"{int(v)} total"))
