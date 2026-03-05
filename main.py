"""
main.py — JobAutomationBot Orchestrator
GitHub: https://github.com/alhamrizvi-cloud/JobAutomationBot

Runs all job application modules in sequence and handles scheduling.

Usage:
    python main.py              # Run once immediately
    python main.py --schedule   # Run daily at the time set in config.py
    python main.py --email      # Email campaign only
    python main.py --scrape     # Scrape only (no auto-apply)
    python main.py --stats      # Show application statistics
"""

import argparse
import sys
import time

import schedule

BANNER = r"""
      __      __    ___         __                        __  _             ____        __ 
     / /___  / /_  /   | __  __/ /_____  ____ ___  ____ _/ /_(_)___  ____  / __ )____  / /_
__  / / __ \/ __ \/ /| |/ / / / __/ __ \/ __ `__ \/ __ `/ __/ / __ \/ __ \/ __  / __ \/ __/
/ /_/ / /_/ / /_/ / ___ / /_/ / /_/ /_/ / / / / / / /_/ / /_/ / /_/ / / / / /_/ / /_/ / /_  
\____/\____/_.___/_/  |_\__,_/\__/\____/_/ /_/ /_/\__,_/\__/_/\____/_/ /_/_____/\____/\__/

  JobAutomationBot — github.com/alhamrizvi-cloud/JobAutomationBot
  Automated Cybersecurity Job Application System
"""

from config   import SCHEDULE_TIME, MAX_APPLICATIONS_PER_RUN
from tracker  import stats as get_stats
from notifier import notify
from logger   import get_logger

log = get_logger("main")


# ─── Individual Module Runners ────────────────────────────────────────────────

def run_scraper():
    from job_scraper import scrape_all_jobs
    log.info("=" * 50)
    log.info("MODULE: Web Job Scraper")
    log.info("=" * 50)
    jobs = scrape_all_jobs()
    log.info(f"Scraper found {len(jobs)} new jobs.")
    return jobs


def run_linkedin():
    from linkedin_bot import run_linkedin_bot
    log.info("=" * 50)
    log.info("MODULE: LinkedIn Bot")
    log.info("=" * 50)
    result = run_linkedin_bot()
    log.info(f"LinkedIn result: {result}")
    return result


def run_naukri():
    from naukri_bot import run_naukri_bot
    log.info("=" * 50)
    log.info("MODULE: Naukri Bot")
    log.info("=" * 50)
    result = run_naukri_bot()
    log.info(f"Naukri result: {result}")
    return result


def run_email_campaign():
    from email_sender import run_bulk_email_campaign
    log.info("=" * 50)
    log.info("MODULE: Email Campaign")
    log.info("=" * 50)
    result = run_bulk_email_campaign()
    log.info(f"Email campaign result: {result}")
    return result


# ─── Full Run ─────────────────────────────────────────────────────────────────

def run_all():
    """Execute all modules in sequence."""
    log.info("╔══════════════════════════════════════════════════╗")
    log.info("║     JobAutomationBot — STARTING FULL RUN         ║")
    log.info("║  github.com/alhamrizvi-cloud/JobAutomationBot    ║")
    log.info("╚══════════════════════════════════════════════════╝")

    total_applied = 0
    errors        = []

    # 1. Scrape public job boards (info only, no apply)
    try:
        scraped_jobs = run_scraper()
    except Exception as e:
        log.error(f"Scraper error: {e}")
        errors.append(f"Scraper: {e}")

    # 2. LinkedIn Easy Apply
    try:
        linkedin_result = run_linkedin()
        total_applied += linkedin_result.get("applied", 0)
    except Exception as e:
        log.error(f"LinkedIn bot error: {e}")
        errors.append(f"LinkedIn: {e}")

    # 3. Naukri Auto Apply
    try:
        naukri_result = run_naukri()
        total_applied += naukri_result.get("applied", 0)
    except Exception as e:
        log.error(f"Naukri bot error: {e}")
        errors.append(f"Naukri: {e}")

    # 4. Email Campaign
    try:
        email_result = run_email_campaign()
        total_applied += email_result.get("sent", 0)
    except Exception as e:
        log.error(f"Email campaign error: {e}")
        errors.append(f"Email: {e}")

    # ── Final Summary ──────────────────────────────────────────────────────────
    s = get_stats()
    summary = (
        f"Run Complete!\n"
        f"Applications this run: {total_applied}\n"
        f"Total ever applied: {s['total']}\n"
        f"By platform: {s['by_platform']}"
    )
    log.info(summary)

    if errors:
        error_msg = "Errors during run:\n" + "\n".join(errors)
        log.warning(error_msg)
        notify("error", error_msg)
    else:
        notify("applied", summary)

    log.info("╔══════════════════════════════════════════════════╗")
    log.info("║         JobAutomationBot — RUN COMPLETE          ║")
    log.info("╚══════════════════════════════════════════════════╝")


# ─── Statistics ───────────────────────────────────────────────────────────────

def print_stats():
    s = get_stats()
    print("\n" + "═" * 40)
    print("  JOB APPLICATION STATISTICS")
    print("═" * 40)
    print(f"  Total Applications : {s['total']}")
    print(f"  Successfully Applied: {s['applied']}")
    print(f"  Failed              : {s['failed']}")
    print(f"  By Platform:")
    for platform, count in s["by_platform"].items():
        print(f"    • {platform}: {count}")
    print("═" * 40 + "\n")


# ─── CLI Entry Point ──────────────────────────────────────────────────────────

def main():
    print(BANNER)
    parser = argparse.ArgumentParser(
        description="JobAutomationBot — Automated Cybersecurity Job Application System"
    )
    parser.add_argument(
        "--schedule", action="store_true",
        help=f"Run daily at {SCHEDULE_TIME} instead of once"
    )
    parser.add_argument(
        "--email", action="store_true",
        help="Run only the email campaign module"
    )
    parser.add_argument(
        "--scrape", action="store_true",
        help="Run only the web scraper (no applications sent)"
    )
    parser.add_argument(
        "--linkedin", action="store_true",
        help="Run only the LinkedIn bot"
    )
    parser.add_argument(
        "--naukri", action="store_true",
        help="Run only the Naukri bot"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show application statistics"
    )
    args = parser.parse_args()

    if args.stats:
        print_stats()
        return

    if args.email:
        run_email_campaign()
        return

    if args.scrape:
        jobs = run_scraper()
        for j in jobs:
            print(f"[{j['source']}] {j['title']} @ {j['company']} → {j['link']}")
        return

    if args.linkedin:
        run_linkedin()
        return

    if args.naukri:
        run_naukri()
        return

    if args.schedule:
        log.info(f"Scheduling daily run at {SCHEDULE_TIME}…")
        schedule.every().day.at(SCHEDULE_TIME).do(run_all)
        print(f"Job Bot scheduled — will run daily at {SCHEDULE_TIME}. Press Ctrl+C to stop.")
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_all()


if __name__ == "__main__":
    main()
