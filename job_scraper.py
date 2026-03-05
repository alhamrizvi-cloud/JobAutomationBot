"""
job_scraper.py — Scrape publicly available job listings
Sources: Indeed India, TimesJobs, Internshala, Freshersworld, Google Jobs RSS
"""

import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus

from config  import JOB_KEYWORDS, LOCATION_FILTERS
from tracker import already_applied
from notifier import notify
from logger  import get_logger

log = get_logger("job_scraper")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ─── Data Model ───────────────────────────────────────────────────────────────

def make_job(title: str, company: str, location: str, link: str, source: str) -> dict:
    return {
        "title":    title.strip(),
        "company":  company.strip(),
        "location": location.strip(),
        "link":     link.strip(),
        "source":   source,
    }


# ─── Keyword Match ────────────────────────────────────────────────────────────

def is_relevant(title: str) -> bool:
    """Return True if the job title matches any of our target keywords."""
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in JOB_KEYWORDS)


# ─── Indeed India ─────────────────────────────────────────────────────────────

def scrape_indeed(keyword: str = "cybersecurity", location: str = "India") -> list[dict]:
    """Scrape Indeed India job listings."""
    jobs = []
    params = {
        "q":   keyword,
        "l":   location,
        "sort":"date",
        "fromage": "7",     # Last 7 days
    }
    url = f"https://in.indeed.com/jobs?{urlencode(params)}"
    log.info(f"Scraping Indeed: {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.select("div.job_seen_beacon, div.jobsearch-SerpJobCard")
        for card in cards:
            title_el   = card.select_one("h2.jobTitle span, a.jobtitle")
            company_el = card.select_one("span.companyName, span.company")
            loc_el     = card.select_one("div.companyLocation, span.location")
            link_el    = card.select_one("a[id^='job_']") or card.select_one("a.jobtitle")

            if not title_el:
                continue
            title   = title_el.get_text(strip=True)
            company = company_el.get_text(strip=True) if company_el else "Unknown"
            loc     = loc_el.get_text(strip=True)    if loc_el    else location
            href    = link_el["href"] if link_el and link_el.get("href") else ""
            link    = f"https://in.indeed.com{href}" if href.startswith("/") else href

            if is_relevant(title) and link:
                jobs.append(make_job(title, company, loc, link, "Indeed"))

        log.info(f"Indeed → {len(jobs)} relevant jobs found")
    except Exception as e:
        log.error(f"Indeed scrape failed: {e}")

    time.sleep(random.uniform(2, 5))
    return jobs


# ─── TimesJobs ────────────────────────────────────────────────────────────────

def scrape_timesjobs(keyword: str = "cybersecurity") -> list[dict]:
    """Scrape TimesJobs for cybersecurity fresher roles."""
    jobs = []
    keyword_encoded = quote_plus(keyword)
    url = (
        f"https://www.timesjobs.com/candidate/job-search.html"
        f"?searchType=personalizedSearch&from=submit"
        f"&txtKeywords={keyword_encoded}"
        f"&txtLocation=India"
        f"&cboWorkExp1=0&cboWorkExp2=2"
    )
    log.info(f"Scraping TimesJobs: {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select("li.clearfix.job-bx"):
            title_el   = card.select_one("h2 a")
            company_el = card.select_one("h3.joblist-comp-name")
            loc_el     = card.select_one("ul.top-jd-dtl li span.srp-skills")

            if not title_el:
                continue
            title   = title_el.get_text(strip=True)
            company = company_el.get_text(strip=True) if company_el else "Unknown"
            loc     = loc_el.get_text(strip=True)     if loc_el    else "India"
            link    = title_el.get("href", "")

            if is_relevant(title) and link:
                jobs.append(make_job(title, company, loc, link, "TimesJobs"))

        log.info(f"TimesJobs → {len(jobs)} relevant jobs found")
    except Exception as e:
        log.error(f"TimesJobs scrape failed: {e}")

    time.sleep(random.uniform(2, 5))
    return jobs


# ─── Internshala ─────────────────────────────────────────────────────────────

def scrape_internshala(keyword: str = "cybersecurity") -> list[dict]:
    """Scrape Internshala for fresher/internship cybersecurity listings."""
    jobs = []
    keyword_slug = keyword.lower().replace(" ", "-")
    url = f"https://internshala.com/jobs/{keyword_slug}-jobs/"
    log.info(f"Scraping Internshala: {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select("div.individual_internship"):
            title_el   = card.select_one("div.profile")
            company_el = card.select_one("div.company_name a")
            loc_el     = card.select_one("div.location_link")
            link_el    = card.select_one("a.view_detail_button")

            if not title_el:
                continue
            title   = title_el.get_text(strip=True)
            company = company_el.get_text(strip=True) if company_el else "Unknown"
            loc     = loc_el.get_text(strip=True)     if loc_el    else "India"
            href    = link_el.get("href", "")          if link_el  else ""
            link    = f"https://internshala.com{href}" if href else ""

            if is_relevant(title) and link:
                jobs.append(make_job(title, company, loc, link, "Internshala"))

        log.info(f"Internshala → {len(jobs)} relevant jobs found")
    except Exception as e:
        log.error(f"Internshala scrape failed: {e}")

    time.sleep(random.uniform(2, 5))
    return jobs


# ─── Master Scraper ───────────────────────────────────────────────────────────

def scrape_all_jobs() -> list[dict]:
    """Run all scrapers and return a deduplicated list of new jobs."""
    all_jobs = []

    for keyword in JOB_KEYWORDS[:4]:   # Limit to top 4 to be polite
        all_jobs.extend(scrape_indeed(keyword))
        all_jobs.extend(scrape_timesjobs(keyword))

    all_jobs.extend(scrape_internshala("cybersecurity"))
    all_jobs.extend(scrape_internshala("penetration testing"))

    # Deduplicate by link
    seen  = set()
    unique = []
    for job in all_jobs:
        if job["link"] not in seen and not already_applied(job["link"]):
            seen.add(job["link"])
            unique.append(job)

    log.info(f"Total new unique jobs scraped: {len(unique)}")

    if unique:
        sample = "\n".join(f"• {j['title']} @ {j['company']}" for j in unique[:5])
        notify("new_jobs", f"Found {len(unique)} new jobs:\n{sample}")

    return unique


if __name__ == "__main__":
    jobs = scrape_all_jobs()
    for j in jobs:
        print(f"[{j['source']}] {j['title']} @ {j['company']} — {j['link']}")
