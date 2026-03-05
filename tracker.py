"""
tracker.py — CSV-based job application tracker
Stores every application and prevents duplicates.
"""

import csv
import os
from datetime import datetime
from config import DATA_FILE
from logger import get_logger

log = get_logger("tracker")

HEADERS = ["job_title", "company", "platform", "status", "date_applied", "job_link"]


def _ensure_file() -> None:
    """Create the CSV with headers if it doesn't exist yet."""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()
        log.info(f"Created tracker file: {DATA_FILE}")


def already_applied(job_link: str) -> bool:
    """Return True if this job URL is already in the tracker."""
    _ensure_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("job_link", "").strip() == job_link.strip():
                return True
    return False


def record_application(
    job_title: str,
    company: str,
    platform: str,
    status: str,
    job_link: str,
) -> None:
    """Append a new application record to the CSV."""
    _ensure_file()
    row = {
        "job_title":    job_title,
        "company":      company,
        "platform":     platform,
        "status":       status,
        "date_applied": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "job_link":     job_link,
    }
    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writerow(row)
    log.info(f"Recorded: [{status}] {job_title} @ {company} ({platform})")


def get_all_applications() -> list[dict]:
    """Return all recorded applications as a list of dicts."""
    _ensure_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stats() -> dict:
    """Return basic statistics about applications."""
    apps = get_all_applications()
    total     = len(apps)
    applied   = sum(1 for a in apps if a["status"] == "Applied")
    failed    = sum(1 for a in apps if a["status"] == "Failed")
    platforms = {}
    for a in apps:
        platforms[a["platform"]] = platforms.get(a["platform"], 0) + 1
    return {"total": total, "applied": applied, "failed": failed, "by_platform": platforms}
