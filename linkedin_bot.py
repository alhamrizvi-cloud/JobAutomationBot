"""
linkedin_bot.py — Automate LinkedIn Easy Apply for cybersecurity jobs
Uses Playwright (async) for reliable browser automation.

IMPORTANT LEGAL NOTE:
LinkedIn's Terms of Service prohibit automated scraping and applying.
Use this only for personal use and at your own risk. Rate-limit yourself
and avoid running this too aggressively to prevent account bans.
"""

import asyncio
import os
import random
import time

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from config  import (
    LINKEDIN_EMAIL, LINKEDIN_PASSWORD, RESUME_PATH,
    JOB_KEYWORDS, HEADLESS_BROWSER, SLOW_MO_MS,
    PAGE_TIMEOUT_MS, MAX_APPLICATIONS_PER_RUN, DELAY_BETWEEN_APPS_SEC,
    APPLICANT_NAME, APPLICANT_PHONE, APPLICANT_EMAIL,
)
from tracker  import already_applied, record_application
from notifier import notify
from logger   import get_logger

log = get_logger("linkedin_bot")

LINKEDIN_BASE = "https://www.linkedin.com"


class LinkedInBot:
    def __init__(self):
        self.browser  = None
        self.context  = None
        self.page     = None
        self.applied  = 0

    # ── Browser Setup ──────────────────────────────────────────────────────────

    async def start(self) -> None:
        self.pw      = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(
            headless=HEADLESS_BROWSER,
            slow_mo=SLOW_MO_MS,
            args=["--disable-blink-features=AutomationControlled"],
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
        log.info("Browser started.")

    async def stop(self) -> None:
        if self.browser:
            await self.browser.close()
        if hasattr(self, "pw"):
            await self.pw.stop()
        log.info("Browser stopped.")

    # ── Login ──────────────────────────────────────────────────────────────────

    async def login(self) -> bool:
        if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
            log.error("LinkedIn credentials not set in environment.")
            return False
        try:
            log.info("Logging into LinkedIn…")
            await self.page.goto(f"{LINKEDIN_BASE}/login", wait_until="domcontentloaded")
            await self.page.fill("#username", LINKEDIN_EMAIL)
            await self.page.fill("#password", LINKEDIN_PASSWORD)
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_url("**/feed**", timeout=15_000)
            log.info("LinkedIn login successful.")
            return True
        except PWTimeout:
            log.warning("Login may have triggered CAPTCHA or 2FA — check browser.")
            return False
        except Exception as e:
            log.error(f"LinkedIn login failed: {e}")
            return False

    # ── Search Jobs ────────────────────────────────────────────────────────────

    async def search_jobs(self, keyword: str, location: str = "India") -> list[dict]:
        """Navigate to LinkedIn job search and collect Easy Apply listings."""
        jobs = []
        try:
            search_url = (
                f"{LINKEDIN_BASE}/jobs/search/"
                f"?keywords={keyword.replace(' ', '%20')}"
                f"&location={location.replace(' ', '%20')}"
                f"&f_AL=true"      # Easy Apply filter
                f"&f_E=1,2"        # Entry level + Associate
                f"&sortBy=DD"      # Date posted
            )
            log.info(f"Searching LinkedIn: {keyword} in {location}")
            await self.page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(2, 4))

            # Scroll to load more results
            for _ in range(3):
                await self.page.keyboard.press("End")
                await asyncio.sleep(1)

            # Collect job cards
            cards = await self.page.query_selector_all(
                "li.jobs-search-results__list-item"
            )
            log.info(f"Found {len(cards)} job cards")

            for card in cards[:15]:   # Process top 15 per keyword
                try:
                    title_el   = await card.query_selector("a.job-card-list__title")
                    company_el = await card.query_selector("span.job-card-container__company-name")
                    link_el    = await card.query_selector("a.job-card-list__title")

                    title   = (await title_el.inner_text()).strip()   if title_el   else ""
                    company = (await company_el.inner_text()).strip() if company_el else "Unknown"
                    href    = await link_el.get_attribute("href")     if link_el    else ""
                    link    = f"{LINKEDIN_BASE}{href}" if href and href.startswith("/") else href

                    if title and link:
                        jobs.append({"title": title, "company": company, "link": link})
                except Exception:
                    continue

        except Exception as e:
            log.error(f"LinkedIn job search failed: {e}")

        return jobs

    # ── Easy Apply ─────────────────────────────────────────────────────────────

    async def easy_apply(self, job: dict) -> bool:
        """Click through LinkedIn Easy Apply for a single job. Returns True on success."""
        link    = job["link"]
        title   = job["title"]
        company = job["company"]

        if already_applied(link):
            log.info(f"Already applied: {title} @ {company}")
            return False

        if self.applied >= MAX_APPLICATIONS_PER_RUN:
            log.info("Reached max applications per run.")
            return False

        try:
            log.info(f"Opening job: {title} @ {company}")
            await self.page.goto(link, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(2, 4))

            # Click Easy Apply button
            apply_btn = await self.page.query_selector(
                "button.jobs-apply-button, button[aria-label*='Easy Apply']"
            )
            if not apply_btn:
                log.warning(f"No Easy Apply button found for: {title}")
                return False
            await apply_btn.click()
            await asyncio.sleep(2)

            # Step through multi-step application modal
            max_steps = 8
            for step in range(max_steps):
                await self._fill_easy_apply_fields()
                await asyncio.sleep(1)

                # Try to submit
                submit_btn = await self.page.query_selector(
                    "button[aria-label='Submit application']"
                )
                if submit_btn:
                    await submit_btn.click()
                    log.info(f"✅ Applied: {title} @ {company}")
                    record_application(title, company, "LinkedIn", "Applied", link)
                    notify("applied", f"LinkedIn Easy Apply\nRole: {title}\nCompany: {company}")
                    self.applied += 1
                    await asyncio.sleep(random.uniform(*DELAY_BETWEEN_APPS_SEC))
                    return True

                # Next step
                next_btn = await self.page.query_selector(
                    "button[aria-label='Continue to next step'], "
                    "button[aria-label='Review your application']"
                )
                if next_btn:
                    await next_btn.click()
                    await asyncio.sleep(1.5)
                else:
                    break   # No more steps, no submit — unexpected state

            log.warning(f"Could not complete Easy Apply for: {title}")
            record_application(title, company, "LinkedIn", "Incomplete", link)
            return False

        except PWTimeout:
            log.error(f"Timeout applying to: {title}")
            record_application(title, company, "LinkedIn", "Failed", link)
            return False
        except Exception as e:
            log.error(f"Error applying to {title}: {e}")
            record_application(title, company, "LinkedIn", "Failed", link)
            notify("error", f"LinkedIn apply failed\nRole: {title}\nError: {e}")
            return False

    async def _fill_easy_apply_fields(self) -> None:
        """Fill common Easy Apply form fields."""
        page = self.page

        # Phone number
        phone_field = await page.query_selector("input[id*='phoneNumber'], input[name*='phone']")
        if phone_field:
            val = await phone_field.input_value()
            if not val:
                await phone_field.fill(APPLICANT_PHONE)

        # Years of experience — select 0 or "Fresher"
        exp_selects = await page.query_selector_all("select[id*='experience'], select[name*='experience']")
        for sel in exp_selects:
            try:
                await sel.select_option(index=1)   # Usually "0" / "Fresher"
            except Exception:
                pass

        # Radio buttons — select first option (often "Yes" to simple questions)
        radios = await page.query_selector_all("input[type='radio']")
        if radios:
            try:
                await radios[0].click()
            except Exception:
                pass

        # Resume upload (if upload field is present)
        resume_input = await page.query_selector("input[type='file']")
        if resume_input and os.path.exists(RESUME_PATH):
            await resume_input.set_input_files(RESUME_PATH)
            await asyncio.sleep(1)

    # ── Main Run ───────────────────────────────────────────────────────────────

    async def run(self) -> dict:
        results = {"applied": 0, "failed": 0, "skipped": 0}
        await self.start()

        if not await self.login():
            await self.stop()
            return results

        for keyword in JOB_KEYWORDS:
            if self.applied >= MAX_APPLICATIONS_PER_RUN:
                break
            jobs = await self.search_jobs(keyword)
            for job in jobs:
                if self.applied >= MAX_APPLICATIONS_PER_RUN:
                    break
                success = await self.easy_apply(job)
                if success:
                    results["applied"] += 1
                else:
                    results["failed"] += 1

        await self.stop()
        log.info(f"LinkedIn run complete: {results}")
        return results


def run_linkedin_bot() -> dict:
    """Synchronous entry point called from main.py."""
    bot = LinkedInBot()
    return asyncio.run(bot.run())


if __name__ == "__main__":
    result = run_linkedin_bot()
    print(result)
