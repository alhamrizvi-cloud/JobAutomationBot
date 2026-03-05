"""
config.py — Central configuration for JobAutomationBot
GitHub: https://github.com/alhamrizvi-cloud/JobAutomationBot
All secrets loaded from environment variables. Never hardcode credentials!
"""

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ─── LinkedIn ────────────────────────────────────────────────────────────────
LINKEDIN_EMAIL    = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")

# ─── Naukri ──────────────────────────────────────────────────────────────────
NAUKRI_EMAIL    = os.getenv("NAUKRI_EMAIL", "")
NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD", "")

# ─── Email (Gmail SMTP) ───────────────────────────────────────────────────────
EMAIL_SENDER   = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")   # Gmail App Password

# ─── Telegram Notifications ───────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ─── Resume ───────────────────────────────────────────────────────────────────
RESUME_PATH = os.getenv("RESUME_PATH", "resume.pdf")

# ─── Job Search Filters ───────────────────────────────────────────────────────
JOB_KEYWORDS = [
    "Penetration Tester",
    "Ethical Hacker",
    "Cybersecurity Analyst",
    "SOC Analyst",
    "Security Researcher",
    "Application Security",
    "Bug Bounty",
    "Vulnerability Analyst",
]

LOCATION_FILTERS = ["India", "Mumbai", "Remote", "Hybrid"]

EXPERIENCE_FILTERS = ["Fresher", "Entry Level", "0-2 Years", "0-1 Years"]

# ─── Applicant Details (used in email & form fill) ────────────────────────────
APPLICANT_NAME  = os.getenv("APPLICANT_NAME", "Your Name")
APPLICANT_PHONE = os.getenv("APPLICANT_PHONE", "+91-XXXXXXXXXX")
APPLICANT_EMAIL = os.getenv("APPLICANT_EMAIL", EMAIL_SENDER)

# ─── Paths ────────────────────────────────────────────────────────────────────
LOG_FILE  = "logs/job_bot.log"
DATA_FILE = "data/applied_jobs.csv"

# ─── Scheduling ───────────────────────────────────────────────────────────────
# Time to run daily (24h format)
SCHEDULE_TIME = "09:00"

# ─── Browser ──────────────────────────────────────────────────────────────────
HEADLESS_BROWSER = True      # Set False to watch the browser during debugging
SLOW_MO_MS       = 50        # Milliseconds between Playwright actions (be polite)
PAGE_TIMEOUT_MS  = 30_000    # 30 seconds max per page load

# ─── Safety ───────────────────────────────────────────────────────────────────
MAX_APPLICATIONS_PER_RUN = 20   # Cap per session to avoid rate-limiting / bans
DELAY_BETWEEN_APPS_SEC   = (5, 15)  # Random sleep range between applications
