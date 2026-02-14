"""Navigation bar with animated hover glow effect.

Each tab is a custom Canvas widget.  On hover a *boxed outline* fades into
view from the bottom up while a gradient white light blooms upward from beneath
the button.
"""

import tkinter as tk
import customtkinter as ctk

BG = "#080808"


class NavButton(tk.Canvas):
    """Single navigation tab drawn entirely on a Canvas for full effect control."""

    def __init__(self, parent, text, command=None, **kwargs):
        super().__init__(parent, highlightthickness=0, bg=BG, bd=0, **kwargs)
        self.label = text
        self.command = command
        self.is_hovered = False
        self.is_active = False

        # Animation state – 0.0 (idle) → 1.0 (fully lit)
        self._intensity = 0.0
        self._anim_id: str | None = None

        # Will be set properly on first <Configure>
        self.w = 100
        self.h = 50

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    # ── drawing ───────────────────────────────────────────────────────────

    def _render(self):
        self.delete("all")
        w, h = self.w, self.h
        t = self._intensity  # 0 → 1

        if t > 0.0:
            # ── solid gradient glow from below (filled bands, no gaps) ──
            bands = h  # one band per pixel row for a perfectly smooth fill
            for i in range(bands):
                y_top = h - 1 - i
                fade = ((bands - i) / bands) ** 3 * t
                g = int(fade * 220)
                if g < 1:
                    continue
                c = f"#{g:02x}{g:02x}{g:02x}"
                self.create_rectangle(0, y_top, w, y_top + 1,
                                      fill=c, outline="")

            # ── seamless boxed border fading toward the top ──
            usable = h - 6
            for py in range(max(1, int(usable))):
                y = h - 3 - py
                frac = py / max(1, usable)
                fade = (1 - frac) ** 1.6 * t
                g = int(fade * 200)
                if g < 1:
                    continue
                c = f"#{g:02x}{g:02x}{g:02x}"
                self.create_rectangle(4, y, 5, y + 1, fill=c, outline="")
                self.create_rectangle(w - 5, y, w - 4, y + 1, fill=c, outline="")

            # bottom edge (brightest)
            bb = int(245 * t)
            bc = f"#{bb:02x}{bb:02x}{bb:02x}"
            self.create_rectangle(4, h - 3, w - 4, h - 1, fill=bc, outline="")

            # top edge (very faint)
            tb = int(18 * t)
            if tb > 0:
                tc = f"#{tb:02x}{tb:02x}{tb:02x}"
                self.create_rectangle(4, 3, w - 4, 4, fill=tc, outline="")

        # ── active indicator when idle ──
        if self.is_active and t <= 0.0:
            self.create_rectangle(16, h - 3, w - 16, h - 1,
                                  fill="#ffffff", outline="")

        # ── label ──
        active_boost = 1.0 if self.is_active else 0.0
        eff = max(t, active_boost)
        gray = min(255, int(136 + 119 * eff))
        self.create_text(
            w // 2, h // 2,
            text=self.label,
            fill=f"#{gray:02x}{gray:02x}{gray:02x}",
            font=("Helvetica", 11),
        )

    # ── events ────────────────────────────────────────────────────────────

    def _on_configure(self, event):
        self.w = event.width
        self.h = event.height
        self._render()

    def _on_enter(self, _):
        self.is_hovered = True
        self._animate_in()

    def _on_leave(self, _):
        self.is_hovered = False
        self._animate_out()

    def _on_click(self, _):
        if self.command:
            self.command()

    # ── animation helpers ─────────────────────────────────────────────────

    def _cancel(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None

    def _animate_in(self):
        self._cancel()
        if self._intensity < 1.0:
            self._intensity = min(1.0, self._intensity + 0.10)
            self._render()
            self._anim_id = self.after(18, self._animate_in)

    def _animate_out(self):
        self._cancel()
        if self._intensity > 0.0:
            self._intensity = max(0.0, self._intensity - 0.06)
            self._render()
            self._anim_id = self.after(18, self._animate_out)

    # ── public ────────────────────────────────────────────────────────────

    def set_active(self, active: bool):
        self.is_active = active
        self._render()


class NavBar(ctk.CTkFrame):
    """Horizontal bar of equally-spaced NavButtons."""

    def __init__(self, parent, tabs: list[str], command=None, **kwargs):
        kwargs.setdefault("fg_color", BG)
        super().__init__(parent, **kwargs)
        self.command = command
        self.buttons: dict[str, NavButton] = {}
        self.active_tab: str | None = tabs[0] if tabs else None

        for tab in tabs:
            btn = NavButton(self, text=tab, command=lambda t=tab: self._select(t))
            btn.configure(height=30)
            btn.pack(side="left", fill="x", expand=True, padx=1)
            self.buttons[tab] = btn

        if self.active_tab:
            self.buttons[self.active_tab].set_active(True)

    def _select(self, tab: str):
        if self.active_tab and self.active_tab in self.buttons:
            self.buttons[self.active_tab].set_active(False)
        self.active_tab = tab
        self.buttons[tab].set_active(True)
        if self.command:
            self.command(tab)
