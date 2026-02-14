"""Background IMAP monitor – checks the inbox for job-application emails."""

import imaplib
import email as email_lib
from email.header import decode_header
import threading
import time
import logging
from datetime import datetime, timedelta

from src.database.db import (
    get_email_config,
    get_setting,
    is_email_processed,
    mark_email_processed,
    add_job,
    find_job_by_company,
    update_job_status,
)
from src.services.classifier import (
    classify_email,
    classify_email_ai,
    extract_company_name,
    extract_position,
)

logger = logging.getLogger(__name__)

# Status-change priority (higher = further along)
_PRIORITY = {"open": 0, "needs_attention": 1, "closed": 2}


class EmailMonitor:
    """Periodically polls the user's IMAP inbox in a daemon thread."""

    def __init__(self, on_update=None):
        self._running = False
        self._thread: threading.Thread | None = None
        self.on_update = on_update          # UI callback (called from bg thread)
        self.check_interval = 60            # seconds between polls
        self.last_error: str | None = None

    # ── lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> bool:
        if self._running:
            return True
        config = get_email_config()
        if not config:
            self.last_error = "No email configured – open Settings to connect."
            return False
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    @property
    def is_running(self) -> bool:
        return self._running

    def check_now(self):
        """Trigger a one-off check in a separate thread."""
        threading.Thread(target=self._single_check, daemon=True).start()

    # ── internal ──────────────────────────────────────────────────────────

    def _loop(self):
        while self._running:
            self._single_check()
            for _ in range(self.check_interval):
                if not self._running:
                    return
                time.sleep(1)

    def _single_check(self):
        try:
            self._fetch_and_classify()
            self.last_error = None
        except Exception as exc:
            logger.error("Email check failed: %s", exc)
            self.last_error = str(exc)
        if self.on_update:
            self.on_update()

    def _fetch_and_classify(self):
        config = get_email_config()
        if not config:
            return

        mail = imaplib.IMAP4_SSL(config["imap_server"], config["imap_port"])
        try:
            mail.login(config["email_address"], config["app_password"])
            mail.select("INBOX")

            since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
            _, data = mail.search(None, f'(SINCE "{since}")')
            if not data or not data[0]:
                return

            for msg_id in data[0].split():
                if not self._running:
                    break
                self._process_message(mail, msg_id)
        finally:
            try:
                mail.logout()
            except Exception:
                pass

    def _process_message(self, mail, msg_id):
        _, msg_data = mail.fetch(msg_id, "(RFC822)")
        for part in msg_data:
            if not isinstance(part, tuple):
                continue

            msg = email_lib.message_from_bytes(part[1])

            # De-duplicate
            message_id = msg.get("Message-ID", "") or f"{msg_id}-{msg.get('Date', '')}"
            if is_email_processed(message_id):
                continue

            subject = self._decode(msg["Subject"])
            from_addr = self._decode(msg["From"])
            body = self._body(msg)

            # ── Try AI classification first, fall back to keywords ──
            api_key = get_setting("openai_api_key")
            ai_result = None
            if api_key:
                ai_result = classify_email_ai(subject, body, api_key)

            if ai_result is not None:
                status = ai_result["status"]
                company = ai_result["company"] or extract_company_name(from_addr, subject)
                position = ai_result["position"] or extract_position(subject, body)
            else:
                status = classify_email(subject, body)
                company = extract_company_name(from_addr, subject)
                position = extract_position(subject, body)

            if status is None:
                mark_email_processed(message_id)
                continue

            existing = find_job_by_company(company)
            if existing:
                if _PRIORITY.get(status, 0) > _PRIORITY.get(existing["status"], 0):
                    update_job_status(existing["id"], status)
            else:
                snippet = body[:200] if body else ""
                add_job(company, position, status, subject, from_addr, snippet)

            mark_email_processed(message_id)

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _decode(header: str | None) -> str:
        if not header:
            return ""
        parts = decode_header(header)
        out = []
        for fragment, charset in parts:
            if isinstance(fragment, bytes):
                out.append(fragment.decode(charset or "utf-8", errors="replace"))
            else:
                out.append(fragment)
        return "".join(out)

    @staticmethod
    def _body(msg) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        return part.get_payload(decode=True).decode("utf-8", errors="replace")
                    except Exception:
                        continue
        else:
            try:
                return msg.get_payload(decode=True).decode("utf-8", errors="replace")
            except Exception:
                pass
        return ""
