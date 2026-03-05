"""
naukri_bot.py — Automate job applications on Naukri.com
Uses Playwright for browser automation.

NOTE: Naukri's ToS prohibit automated access. Use responsibly, for personal
      job searching only, and add human-like delays.
"""

import asyncio
import os
import random

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from config  import (
    NAUKRI_EMAIL, NAUKRI_PASSWORD, RESUME_PATH,
    JOB_KEYWORDS, HEADLESS_BROWSER, SLOW_MO_MS, PAGE_TIMEOUT_MS,
    MAX_APPLICATIONS_PER_RUN, DELAY_BETWEEN_APPS_SEC,
    APPLICANT_NAME, APPLICANT_PHONE,
)
from tracker  import already_applied, record_application
from notifier import notify
from logger   import get_logger

log = get_logger("naukri_bot")

NAUKRI_BASE = "https://www.naukri.com"


class NaukriBot:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page    = None
        self.applied = 0

    # ── Browser Setup ──────────────────────────────────────────────────────────

    async def start(self) -> None:
        self.pw      = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(
            headless=HEADLESS_BROWSER,
            slow_mo=SLOW_MO_MS,
        )
        self.context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
        )
        self.page = await self.context.new_page()
        self.page.set_default_timeout(PAGE_TIMEOUT_MS)
        log.info("Naukri browser started.")

    async def stop(self) -> None:
        if self.browser:
            await self.browser.close()
        if hasattr(self, "pw"):
            await self.pw.stop()
        log.info("Naukri browser stopped.")

    # ── Login ──────────────────────────────────────────────────────────────────

    async def login(self) -> bool:
        if not NAUKRI_EMAIL or not NAUKRI_PASSWORD:
            log.error("Naukri credentials not configured.")
            return False
        try:
            log.info("Logging into Naukri.com…")
            await self.page.goto(f"{NAUKRI_BASE}/nlogin/login", wait_until="domcontentloaded")
            await asyncio.sleep(2)

            await self.page.fill("input[placeholder='Enter your active Email ID / Username']", NAUKRI_EMAIL)
            await self.page.fill("input[placeholder='Enter your password']", NAUKRI_PASSWORD)
            await self.page.click("button[type='submit']")
            await asyncio.sleep(3)

            # Check login success by looking for user menu
            user_el = await self.page.query_selector("span.nI-gNb-menuTitle")
            if user_el:
                log.info("Naukri login successful.")
                return True

            log.warning("Naukri login may have failed — CAPTCHA or wrong credentials.")
            return False
        except Exception as e:
            log.error(f"Naukri login error: {e}")
            return False

    # ── Update Profile / Upload Resume ─────────────────────────────────────────

    async def upload_resume(self) -> None:
        """Navigate to profile and upload/update the resume PDF."""
        if not os.path.exists(RESUME_PATH):
            log.warning(f"Resume not found: {RESUME_PATH}")
            return
        try:
            await self.page.goto(f"{NAUKRI_BASE}/mnjuser/profile", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            upload_input = await self.page.query_selector("input[type='file']")
            if upload_input:
                await upload_input.set_input_files(RESUME_PATH)
                await asyncio.sleep(2)
                save_btn = await self.page.query_selector("button:has-text('Save')")
                if save_btn:
                    await save_btn.click()
                log.info("Resume uploaded to Naukri profile.")
        except Exception as e:
            log.warning(f"Resume upload skipped: {e}")

    # ── Search Jobs ────────────────────────────────────────────────────────────

    async def search_jobs(self, keyword: str) -> list[dict]:
        """Search Naukri for jobs and return a list of job dicts."""
        jobs = []
        try:
            keyword_slug = keyword.lower().replace(" ", "-")
            url = (
                f"{NAUKRI_BASE}/{keyword_slug}-jobs?"
                f"experience=0&jobAge=7"
            )
            log.info(f"Searching Naukri: {keyword}")
            await self.page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(2, 4))

            cards = await self.page.query_selector_all(
                "article.jobTuple, div.tuple-result-wrap"
            )
            log.info(f"Naukri: {len(cards)} cards found")

            for card in cards[:20]:
                try:
                    title_el   = await card.query_selector("a.title, a.subTitle")
                    company_el = await card.query_selector("a.subTitle, span.org-name")
                    link_el    = await card.query_selector("a.title")

                    title   = (await title_el.inner_text()).strip()   if title_el   else ""
                    company = (await company_el.inner_text()).strip() if company_el else "Unknown"
                    href    = await link_el.get_attribute("href")     if link_el    else ""

                    if title and href:
                        jobs.append({"title": title, "company": company, "link": href})
                except Exception:
                    continue
        except Exception as e:
            log.error(f"Naukri search error: {e}")

        return jobs

    # ── Apply to a Job ─────────────────────────────────────────────────────────

    async def apply_to_job(self, job: dict) -> bool:
        """Open a Naukri job listing and click Apply. Returns True on success."""
        link    = job["link"]
        title   = job["title"]
        company = job["company"]

        if already_applied(link):
            log.info(f"Already applied: {title} @ {company}")
            return False

        if self.applied >= MAX_APPLICATIONS_PER_RUN:
            return False

        try:
            log.info(f"Opening Naukri job: {title} @ {company}")
            await self.page.goto(link, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(2, 4))

            # Click Apply button
            apply_btn = await self.page.query_selector(
                "button#apply-button, button:has-text('Apply'), a:has-text('Apply Now')"
            )
            if not apply_btn:
                log.warning(f"No Apply button found: {title}")
                record_application(title, company, "Naukri", "No Apply Button", link)
                return False

            await apply_btn.click()
            await asyncio.sleep(2)

            # Handle any popup / confirmation
            confirm_btn = await self.page.query_selector(
                "button:has-text('Apply'), button:has-text('Confirm')"
            )
            if confirm_btn:
                await confirm_btn.click()
                await asyncio.sleep(2)

            # Fill extra fields if a modal appears
            await self._fill_naukri_fields()

            # Final submit
            submit_btn = await self.page.query_selector(
                "button:has-text('Submit'), button:has-text('Send Application')"
            )
            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(2)

            log.info(f"✅ Applied on Naukri: {title} @ {company}")
            record_application(title, company, "Naukri", "Applied", link)
            notify("applied", f"Naukri Application\nRole: {title}\nCompany: {company}")
            self.applied += 1
            await asyncio.sleep(random.uniform(*DELAY_BETWEEN_APPS_SEC))
            return True

        except PWTimeout:
            log.error(f"Timeout on Naukri job: {title}")
            record_application(title, company, "Naukri", "Failed", link)
            return False
        except Exception as e:
            log.error(f"Naukri apply error [{title}]: {e}")
            record_application(title, company, "Naukri", "Failed", link)
            notify("error", f"Naukri error\nRole: {title}\nError: {e}")
            return False

    async def _fill_naukri_fields(self) -> None:
        """Fill common Naukri application form fields if a popup appears."""
        page = self.page

        # Cover letter / message field
        msg_field = await page.query_selector("textarea[placeholder*='cover'], textarea[name*='message']")
        if msg_field:
            cover = (
                f"Dear Hiring Team,\n\n"
                f"I am {APPLICANT_NAME}, a cybersecurity enthusiast and aspiring penetration tester. "
                f"I am excited to apply for this role. Please find my resume for your review.\n\n"
                f"Thank you for your consideration.\n\nBest regards,\n{APPLICANT_NAME}"
            )
            await msg_field.fill(cover)

        # Expected salary
        salary_field = await page.query_selector("input[name*='salary'], input[placeholder*='salary']")
        if salary_field:
            await salary_field.fill("300000")  # 3 LPA

        # Phone number
        phone_field = await page.query_selector("input[name*='mobile'], input[placeholder*='phone']")
        if phone_field:
            val = await phone_field.input_value()
            if not val:
                await phone_field.fill(APPLICANT_PHONE)

    # ── Main Run ───────────────────────────────────────────────────────────────

    async def run(self) -> dict:
        results = {"applied": 0, "failed": 0, "skipped": 0}
        await self.start()

        if not await self.login():
            await self.stop()
            return results

        await self.upload_resume()

        for keyword in JOB_KEYWORDS:
            if self.applied >= MAX_APPLICATIONS_PER_RUN:
                break
            jobs = await self.search_jobs(keyword)
            for job in jobs:
                if self.applied >= MAX_APPLICATIONS_PER_RUN:
                    break
                success = await self.apply_to_job(job)
                if success:
                    results["applied"] += 1
                else:
                    results["skipped"] += 1

        await self.stop()
        log.info(f"Naukri run complete: {results}")
        return results


def run_naukri_bot() -> dict:
    """Synchronous entry point called from main.py."""
    bot = NaukriBot()
    return asyncio.run(bot.run())


if __name__ == "__main__":
    result = run_naukri_bot()
    print(result)
