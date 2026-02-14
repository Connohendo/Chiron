"""Settings view – email + AI configuration.

Auto-detects IMAP server for common providers (Gmail, Outlook, Yahoo …).
Scrollable so the form works on smaller windows.
"""

import imaplib
import threading
import customtkinter as ctk
from src.database.db import get_email_config, save_email_config, get_setting, save_setting

BG      = "#080808"
SURFACE = "#0e0e0e"
BORDER  = "#1a1a1a"
INPUT   = "#0b0b0b"
MUTED   = "#8a8a8a"
DIM     = "#606060"

IMAP_PRESETS: dict[str, tuple[str, int]] = {
    "gmail.com":       ("imap.gmail.com", 993),
    "googlemail.com":  ("imap.gmail.com", 993),
    "outlook.com":     ("outlook.office365.com", 993),
    "hotmail.com":     ("outlook.office365.com", 993),
    "live.com":        ("outlook.office365.com", 993),
    "yahoo.com":       ("imap.mail.yahoo.com", 993),
    "icloud.com":      ("imap.mail.me.com", 993),
    "me.com":          ("imap.mail.me.com", 993),
    "aol.com":         ("imap.aol.com", 993),
}


class SettingsView(ctk.CTkFrame):
    """Email + AI configuration panel (scrollable)."""

    def __init__(self, parent, email_monitor, on_save=None, **kwargs):
        super().__init__(parent, fg_color=BG, **kwargs)
        self.email_monitor = email_monitor
        self.on_save = on_save

        # Scrollable container so everything fits on small screens
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG,
            scrollbar_button_color="#1a1a1a",
            scrollbar_button_hover_color="#282828",
        )
        self.scroll.pack(fill="both", expand=True)

        inner = self.scroll  # shorthand

        # ── heading ──
        ctk.CTkLabel(
            inner, text="Settings",
            font=("Helvetica Neue", 18, "bold"), text_color="#d4d4d4",
        ).pack(anchor="w", pady=(12, 16))

        # ━━━━━━━━━━━━━━━━━━━━━━━━━ EMAIL CARD ━━━━━━━━━━━━━━━━━━━━━━━━━━━
        email_card = ctk.CTkFrame(
            inner, fg_color=SURFACE, corner_radius=8,
            border_width=1, border_color=BORDER,
        )
        email_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            email_card, text="Email Connection",
            font=("Helvetica Neue", 13, "bold"), text_color="#d4d4d4",
        ).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(
            email_card,
            text="IMAP credentials for inbox scanning",
            font=("Helvetica Neue", 10), text_color="#707070",
        ).pack(anchor="w", padx=20, pady=(0, 10))

        self.email_entry    = self._field(email_card, "Email Address", "you@example.com")
        self.email_entry.bind("<FocusOut>", self._auto_detect)
        self.server_entry   = self._field(email_card, "IMAP Server", "imap.gmail.com")
        self.port_entry     = self._field(email_card, "Port", "993")
        self.password_entry = self._field(email_card, "App Password",
                                          "Enter your app password", show="●")

        ctk.CTkLabel(
            email_card,
            text="Gmail users: create an App Password at  Google Account → Security → App Passwords",
            font=("Helvetica Neue", 9), text_color="#707070",
        ).pack(anchor="w", padx=20, pady=(2, 16))

        # ━━━━━━━━━━━━━━━━━━━━━━━━━ AI CARD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        ai_card = ctk.CTkFrame(
            inner, fg_color=SURFACE, corner_radius=8,
            border_width=1, border_color=BORDER,
        )
        ai_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            ai_card, text="AI Classification",
            font=("Helvetica Neue", 13, "bold"), text_color="#d4d4d4",
        ).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(
            ai_card,
            text="Optional — enables smarter email classification via OpenAI",
            font=("Helvetica Neue", 10), text_color="#707070",
        ).pack(anchor="w", padx=20, pady=(0, 10))

        self.api_key_entry = self._field(ai_card, "OpenAI API Key", "sk-...", show="●")

        # spacer at bottom of card
        ctk.CTkFrame(ai_card, fg_color="transparent", height=14).pack()

        # ━━━━━━━━━━━━━━━━━━━━━━━━━ ACTIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(
            actions, text="Test Connection",
            font=("Helvetica Neue", 11),
            fg_color="transparent", hover_color="#161616",
            text_color=MUTED, corner_radius=6,
            border_width=1, border_color="#1e1e1e",
            height=34,
            command=self._test_connection,
        ).pack(side="left")

        ctk.CTkButton(
            actions, text="Save",
            font=("Helvetica Neue", 11, "bold"),
            fg_color="#1a6dff", hover_color="#1558cc",
            text_color="#ffffff", corner_radius=6,
            height=34, width=100,
            command=self._save_config,
        ).pack(side="right")

        # ── status feedback ──
        self.status_label = ctk.CTkLabel(
            inner, text="", font=("Helvetica Neue", 11), text_color=DIM,
        )
        self.status_label.pack(anchor="w", pady=(0, 10))

        # Fix: propagate mouse-wheel events so scrolling works over any child
        self.scroll.after(100, lambda: self._bind_scroll(self.scroll))

    def _bind_scroll(self, parent):
        """Recursively bind mouse-wheel on every child to the scrollable frame."""
        canvas = self.scroll._parent_canvas  # internal canvas of CTkScrollableFrame

        def _on_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        for child in parent.winfo_children():
            child.bind("<MouseWheel>", _on_wheel, add="+")
            child.bind("<Button-4>", lambda e: canvas.yview_scroll(-3, "units"), add="+")
            child.bind("<Button-5>", lambda e: canvas.yview_scroll(3, "units"), add="+")
            self._bind_scroll(child)

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _field(parent, label: str, placeholder: str, show=None) -> ctk.CTkEntry:
        ctk.CTkLabel(
            parent, text=label,
            font=("Helvetica Neue", 10, "bold"), text_color=MUTED,
        ).pack(anchor="w", padx=20, pady=(8, 3))

        kw = dict(
            placeholder_text=placeholder,
            fg_color=INPUT, border_color=BORDER,
            text_color="#e0e0e0", height=34,
            font=("Helvetica Neue", 12), corner_radius=6,
        )
        if show:
            kw["show"] = show
        entry = ctk.CTkEntry(parent, **kw)
        entry.pack(fill="x", padx=20)
        return entry

    def _set(self, entry, value: str):
        entry.delete(0, "end")
        entry.insert(0, value)

    # ── auto-detect IMAP ──────────────────────────────────────────────────

    def _auto_detect(self, _event=None):
        addr = self.email_entry.get().strip()
        if "@" not in addr:
            return
        domain = addr.rsplit("@", 1)[1].lower()
        preset = IMAP_PRESETS.get(domain)
        if preset:
            self._set(self.server_entry, preset[0])
            self._set(self.port_entry, str(preset[1]))

    # ── test connection ───────────────────────────────────────────────────

    def _test_connection(self):
        self.status_label.configure(text="Testing connection…", text_color=MUTED)
        self.update()

        server   = self.server_entry.get().strip()
        port     = int(self.port_entry.get().strip() or "993")
        addr     = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        def _bg():
            try:
                m = imaplib.IMAP4_SSL(server, port)
                m.login(addr, password)
                m.logout()
                self.after(0, lambda: self.status_label.configure(
                    text="Connection successful", text_color="#4CAF50"))
            except Exception as exc:
                self.after(0, lambda: self.status_label.configure(
                    text=f"Connection failed — {exc}", text_color="#F44336"))

        threading.Thread(target=_bg, daemon=True).start()

    # ── save ──────────────────────────────────────────────────────────────

    def _save_config(self):
        addr     = self.email_entry.get().strip()
        server   = self.server_entry.get().strip()
        port     = int(self.port_entry.get().strip() or "993")
        password = self.password_entry.get().strip()

        if not all([addr, server, password]):
            self.status_label.configure(
                text="Please fill in all required fields.", text_color="#F44336")
            return

        save_email_config(addr, server, port, password)

        api_key = self.api_key_entry.get().strip()
        if api_key:
            save_setting("openai_api_key", api_key)

        self.status_label.configure(
            text="Saved", text_color="#4CAF50")

        if self.on_save:
            self.on_save()

    # ── load existing config into form ────────────────────────────────────

    def load_config(self):
        config = get_email_config()
        if config:
            self._set(self.email_entry, config.get("email_address", ""))
            self._set(self.server_entry, config.get("imap_server", ""))
            self._set(self.port_entry, str(config.get("imap_port", 993)))
            self._set(self.password_entry, config.get("app_password", ""))

        api_key = get_setting("openai_api_key") or ""
        self._set(self.api_key_entry, api_key)
