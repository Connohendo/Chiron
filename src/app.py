"""Chiron application window.

Black window with a centred logo (hover to see the centaur archer),
an animated navigation bar, a status bar, and swappable content views.
"""

import logging
import tkinter as tk
import customtkinter as ctk

from src.database.db import init_db
from src.services.email_monitor import EmailMonitor
from src.ui.navbar import NavBar
from src.ui.dashboard import DashboardView
from src.ui.settings_view import SettingsView

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-24s  %(levelname)-8s  %(message)s",
)

BG = "#080808"
SURFACE = "#0f0f0f"


# ═══════════════════════════════════════════════════════════════════════════════
# Logo canvas – draws the title and a centaur‑archer animation on hover
# ═══════════════════════════════════════════════════════════════════════════════

class LogoCanvas(tk.Canvas):
    """Draws 'C  H  I  R  O  N' and reveals a line‑art centaur that shoots
    an arrow when the mouse enters the logo area."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, highlightthickness=0, bd=0, **kwargs)
        self.w = 400
        self.h = 64
        self._opacity = 0.0        # centaur fade 0→1
        self._arrow_t = 0.0        # arrow travel 0→1
        self._hovering = False
        self._anim_id: str | None = None

        self.bind("<Configure>", self._on_cfg)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    # ── events ────────────────────────────────────────────────────────────

    def _on_cfg(self, e):
        self.w, self.h = e.width, e.height
        self._draw()

    def _on_enter(self, _):
        self._hovering = True
        self._tick()

    def _on_leave(self, _):
        self._hovering = False
        self._tick()

    # ── animation loop ────────────────────────────────────────────────────

    def _tick(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None

        dirty = False

        if self._hovering:
            # Fade centaur in
            if self._opacity < 1.0:
                self._opacity = min(1.0, self._opacity + 0.06)
                dirty = True
            # Once centaur is mostly visible, shoot the arrow
            if self._opacity >= 0.4 and self._arrow_t < 1.0:
                self._arrow_t = min(1.0, self._arrow_t + 0.035)
                dirty = True
        else:
            # Fade everything out
            if self._opacity > 0:
                self._opacity = max(0.0, self._opacity - 0.045)
                dirty = True
            if self._arrow_t > 0:
                self._arrow_t = max(0.0, self._arrow_t - 0.07)
                dirty = True

        self._draw()
        if dirty:
            self._anim_id = self.after(18, self._tick)

    # ── colour helper ─────────────────────────────────────────────────────

    @staticmethod
    def _clr(opacity: float, brightness: int = 170) -> str | None:
        g = max(0, min(255, int(opacity * brightness)))
        return f"#{g:02x}{g:02x}{g:02x}" if g > 0 else None

    # ── drawing ───────────────────────────────────────────────────────────

    def _draw(self):
        self.delete("all")
        w, h = self.w, self.h
        mx, my = w // 2, h // 2

        # Title (always visible)
        self.create_text(
            mx, my,
            text="C  H  I  R  O  N",
            fill="#e8e8e8",
            font=("Helvetica Neue", 28, "bold"),
        )

        if self._opacity > 0.01:
            self._draw_centaur(mx - 210, my + 3)

    def _draw_centaur(self, cx, cy):
        op = self._opacity
        c = self._clr(op, 155)
        dim = self._clr(op, 80)
        if not c:
            return

        s = 0.65           # overall scale
        lw = 1.5           # line weight

        # ── Horse back (smooth curve) ──
        self.create_line(
            cx - 18*s, cy + 4*s,
            cx - 8*s,  cy + 0*s,
            cx + 2*s,  cy - 2*s,
            cx + 8*s,  cy - 1*s,
            fill=c, width=lw, smooth=True,
        )
        # Belly
        self.create_line(
            cx - 18*s, cy + 10*s,
            cx + 8*s,  cy + 9*s,
            fill=dim, width=lw,
        )
        # Rump + chest verticals
        self.create_line(cx - 18*s, cy + 4*s, cx - 18*s, cy + 10*s,
                         fill=dim, width=lw)
        self.create_line(cx + 8*s, cy - 1*s, cx + 8*s, cy + 9*s,
                         fill=dim, width=lw)

        # ── Legs ──
        for x1, y1, x2, y2 in [
            (-15*s, 10*s, -17*s, 19*s),
            (-9*s,  10*s, -7*s,  19*s),
            (1*s,   9*s,  -1*s,  19*s),
            (6*s,   9*s,  8*s,   19*s),
        ]:
            self.create_line(cx + x1, cy + y1, cx + x2, cy + y2,
                             fill=dim, width=lw)

        # ── Tail ──
        self.create_line(
            cx - 18*s, cy + 4*s,
            cx - 25*s, cy - 3*s,
            cx - 28*s, cy + 0*s,
            fill=dim, width=lw, smooth=True,
        )

        # ── Human torso ──
        self.create_line(cx + 8*s, cy - 1*s, cx + 7*s, cy - 16*s,
                         fill=c, width=lw)

        # ── Head ──
        r = 3 * s
        self.create_oval(
            cx + 7*s - r, cy - 19*s - r,
            cx + 7*s + r, cy - 19*s + r,
            outline=c, width=lw,
        )

        # ── Arm drawing the bow ──
        self.create_line(cx + 7*s, cy - 10*s, cx + 15*s, cy - 12*s,
                         fill=c, width=lw)

        # ── Bow (curved arc) ──
        self.create_line(
            cx + 15*s, cy - 18*s,
            cx + 19*s, cy - 12*s,
            cx + 15*s, cy - 6*s,
            fill=c, width=lw, smooth=True,
        )

        # ── Bowstring ──
        self.create_line(
            cx + 15*s, cy - 18*s,
            cx + 15*s, cy - 6*s,
            fill=dim, width=1,
        )

        # ── Arrow ──
        if self._arrow_t > 0.0:
            start_x = cx + 15 * s
            arrow_y = cy - 12 * s
            travel = self.w * 0.55
            offset = self._arrow_t * travel

            tip_x = start_x + offset
            tail_x = tip_x - 16 * s

            # Fade out as it travels
            arrow_op = op * max(0.12, 1.0 - self._arrow_t * 0.85)
            ac = self._clr(arrow_op, 200)
            if ac:
                # Shaft
                self.create_line(tail_x, arrow_y, tip_x, arrow_y,
                                 fill=ac, width=1.5)
                # Arrowhead
                self.create_line(tip_x, arrow_y,
                                 tip_x - 4*s, arrow_y - 2.5*s,
                                 fill=ac, width=1.5)
                self.create_line(tip_x, arrow_y,
                                 tip_x - 4*s, arrow_y + 2.5*s,
                                 fill=ac, width=1.5)

                # Faint trailing streak
                tc = self._clr(arrow_op * 0.25, 100)
                if tc:
                    streak = min(50 * s, offset * 0.6)
                    self.create_line(tail_x, arrow_y,
                                     tail_x - streak, arrow_y,
                                     fill=tc, width=1)


# ═══════════════════════════════════════════════════════════════════════════════
# Main application
# ═══════════════════════════════════════════════════════════════════════════════

class ChironApp(ctk.CTk):
    """Root application window."""

    def __init__(self):
        super().__init__()

        # ── window chrome ─────────────────────────────────────────────────
        self.title("Chiron")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(fg_color=BG)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # ── database ──────────────────────────────────────────────────────
        init_db()

        # ── email monitor ─────────────────────────────────────────────────
        self.monitor = EmailMonitor(on_update=self._on_email_update)

        # ── build UI ──────────────────────────────────────────────────────
        self._build_logo()
        self._build_navbar()
        self._build_content()
        self._build_status_bar()

        # Show dashboard first
        self._show("Dashboard")

        # Try to start monitoring after the window is up
        self.after(500, self._try_start)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI construction ───────────────────────────────────────────────────

    def _build_logo(self):
        self.logo = LogoCanvas(self, height=64)
        self.logo.pack(fill="x")

    def _build_navbar(self):
        self.navbar = NavBar(
            self,
            tabs=["Dashboard", "Settings"],
            command=self._on_nav,
            fg_color=BG,
        )
        self.navbar.pack(fill="x", padx=50, pady=(4, 0))

        # Thin separator
        ctk.CTkFrame(self, fg_color="#161616", height=1).pack(fill="x", padx=50)

    def _build_content(self):
        self.content = ctk.CTkFrame(self, fg_color=BG)
        self.content.pack(fill="both", expand=True, padx=50, pady=(8, 0))

        self.dashboard = DashboardView(self.content, self.monitor)
        self.settings = SettingsView(
            self.content, self.monitor, on_save=self._on_settings_saved,
        )

    def _build_status_bar(self):
        ctk.CTkFrame(self, fg_color="#121212", height=1).pack(
            fill="x", side="bottom",
        )
        bar = ctk.CTkFrame(self, fg_color=BG, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            bar, text="●  Email monitoring: Inactive",
            font=("Helvetica Neue", 10), text_color="#383838",
        )
        self.status_label.pack(side="left", padx=18, pady=5)

    # ── view switching ────────────────────────────────────────────────────

    def _on_nav(self, tab: str):
        self._show(tab)

    def _show(self, name: str):
        self.dashboard.pack_forget()
        self.settings.pack_forget()

        if name == "Dashboard":
            self.dashboard.pack(fill="both", expand=True)
            self.dashboard.refresh()
        elif name == "Settings":
            self.settings.pack(fill="both", expand=True)
            self.settings.load_config()

    # ── email monitoring ──────────────────────────────────────────────────

    def _try_start(self):
        ok = self.monitor.start()
        self._update_status(ok)

    def _on_email_update(self):
        self.after(0, self.dashboard.refresh)

    def _on_settings_saved(self):
        self.monitor.stop()
        ok = self.monitor.start()
        self._update_status(ok)

    def _update_status(self, active: bool):
        if active:
            self.status_label.configure(
                text="●  Email monitoring: Active", text_color="#4CAF50",
            )
        else:
            reason = self.monitor.last_error or "Not configured"
            self.status_label.configure(
                text=f"●  Email monitoring: Inactive — {reason}",
                text_color="#383838",
            )

    # ── cleanup ───────────────────────────────────────────────────────────

    def _on_close(self):
        self.monitor.stop()
        self.destroy()
