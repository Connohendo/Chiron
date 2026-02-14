"""Dashboard view – scrollable list of tracked job applications.

Each row has a coloured left accent bar and a status label on the right:
    green   OPEN
    orange  NEEDS ATTENTION
    red     CLOSED
"""

import customtkinter as ctk
from src.database.db import get_all_jobs

BG = "#080808"

STATUS_COLOURS = {
    "open":            "#4CAF50",
    "needs_attention": "#FF9800",
    "closed":          "#F44336",
}

STATUS_LABELS = {
    "open":            "OPEN",
    "needs_attention": "NEEDS ATTENTION",
    "closed":          "CLOSED",
}


class JobRow(ctk.CTkFrame):
    """A single row representing one tracked application."""

    CARD   = "#0e0e0e"
    HOVER  = "#141414"
    BORDER = "#1a1a1a"

    def __init__(self, parent, job: dict, **kwargs):
        super().__init__(
            parent, fg_color=self.CARD, corner_radius=6,
            border_width=1, border_color=self.BORDER, **kwargs,
        )

        status = job.get("status", "open")
        colour = STATUS_COLOURS.get(status, "#333333")

        # ── coloured accent bar on the left edge ──
        accent = ctk.CTkFrame(self, fg_color=colour, width=3, corner_radius=0)
        accent.pack(side="left", fill="y", padx=(0, 0), pady=6)

        # ── left: company + position + date ──
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=(12, 10), pady=10)

        ctk.CTkLabel(
            info, text=job["company"],
            font=("Helvetica Neue", 14, "bold"), text_color="#d4d4d4", anchor="w",
        ).pack(fill="x")

        if job.get("position"):
            ctk.CTkLabel(
                info, text=job["position"],
                font=("Helvetica Neue", 11), text_color="#686868", anchor="w",
            ).pack(fill="x", pady=(2, 0))

        ctk.CTkLabel(
            info,
            text=job.get("date_updated", ""),
            font=("Helvetica Neue", 9), text_color="#383838", anchor="w",
        ).pack(fill="x", pady=(4, 0))

        # ── right: status badge ──
        label_text = STATUS_LABELS.get(status, status.upper())

        badge = ctk.CTkFrame(self, fg_color="transparent", width=160)
        badge.pack(side="right", padx=(0, 16), pady=10)
        badge.pack_propagate(False)

        ctk.CTkLabel(
            badge,
            text=label_text,
            font=("Helvetica Neue", 11, "bold"),
            text_color=colour,
            anchor="e",
        ).pack(expand=True, anchor="e")

        # ── hover feedback ──
        self.bind("<Enter>", lambda _: self.configure(fg_color=self.HOVER))
        self.bind("<Leave>", lambda _: self.configure(fg_color=self.CARD))


class DashboardView(ctk.CTkFrame):
    """Main dashboard showing all tracked applications."""

    def __init__(self, parent, email_monitor, **kwargs):
        super().__init__(parent, fg_color=BG, **kwargs)
        self.email_monitor = email_monitor
        self._rows: list[ctk.CTkFrame] = []

        # ── header row ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(12, 8))

        ctk.CTkLabel(
            header, text="Applications",
            font=("Helvetica Neue", 18, "bold"), text_color="#d4d4d4",
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Scan",
            font=("Helvetica Neue", 11),
            fg_color="transparent", hover_color="#161616",
            text_color="#505050", corner_radius=6,
            border_width=1, border_color="#1e1e1e",
            width=80, height=28,
            command=self._on_check,
        ).pack(side="right")

        # ── scrollable list ──
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG,
            scrollbar_button_color="#1a1a1a",
            scrollbar_button_hover_color="#282828",
        )
        self.scroll.pack(fill="both", expand=True, pady=(4, 0))

        self._empty_label = ctk.CTkLabel(
            self.scroll,
            text=(
                "No applications tracked yet\n\n"
                "Connect your email in Settings and Chiron\n"
                "will begin scanning automatically."
            ),
            font=("Helvetica Neue", 13),
            text_color="#2a2a2a",
            justify="center",
        )

    # ── public ────────────────────────────────────────────────────────────

    def refresh(self):
        """Reload job data from the database and rebuild the list."""
        for row in self._rows:
            row.destroy()
        self._rows.clear()
        self._empty_label.pack_forget()

        jobs = get_all_jobs()

        if not jobs:
            self._empty_label.pack(expand=True, pady=120)
            return

        for job in jobs:
            row = JobRow(self.scroll, job)
            row.pack(fill="x", pady=(0, 4))
            self._rows.append(row)

    # ── private ───────────────────────────────────────────────────────────

    def _on_check(self):
        self.email_monitor.check_now()
