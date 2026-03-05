"""
notifier.py — Send Telegram and/or email notifications
Called whenever a job is applied, an error occurs, or new jobs are found.
"""

import smtplib
import requests
from email.mime.text import MIMEText
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    EMAIL_SENDER, EMAIL_PASSWORD,
)
from logger import get_logger

log = get_logger("notifier")


# ─── Telegram ─────────────────────────────────────────────────────────────────

def send_telegram(message: str) -> bool:
    """Send a Telegram message via Bot API. Returns True on success."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram credentials not set — skipping Telegram notification.")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            log.info("Telegram notification sent.")
            return True
        log.warning(f"Telegram API error {resp.status_code}: {resp.text}")
    except Exception as e:
        log.error(f"Telegram notification failed: {e}")
    return False


# ─── Email Notification ───────────────────────────────────────────────────────

def send_email_notification(subject: str, body: str, to: str = None) -> bool:
    """Send a plain-text notification email to yourself."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        log.warning("Email credentials not set — skipping email notification.")
        return False
    recipient = to or EMAIL_SENDER
    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = recipient
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipient, msg.as_string())
        log.info(f"Email notification sent to {recipient}: {subject}")
        return True
    except Exception as e:
        log.error(f"Email notification failed: {e}")
    return False


# ─── Unified Notifier ─────────────────────────────────────────────────────────

def notify(event: str, details: str) -> None:
    """
    Send both Telegram and self-email for key events.
    event  : 'applied' | 'error' | 'new_jobs'
    details: human-readable description
    """
    icons = {"applied": "✅", "error": "❌", "new_jobs": "🔍"}
    icon  = icons.get(event, "ℹ️")
    msg   = f"{icon} <b>Job Bot [{event.upper()}]</b>\n{details}"
    plain = f"Job Bot [{event.upper()}]\n{details}"

    send_telegram(msg)
    send_email_notification(subject=f"Job Bot: {event}", body=plain)
