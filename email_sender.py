"""
email_sender.py — Send job application emails with resume attached
Reads target company emails from data/email_targets.csv
"""

import smtplib
import csv
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email               import encoders

from config  import EMAIL_SENDER, EMAIL_PASSWORD, RESUME_PATH, APPLICANT_NAME
from tracker import already_applied, record_application
from notifier import notify
from logger  import get_logger

log = get_logger("email_sender")

EMAIL_TARGETS_FILE = "data/email_targets.csv"
EMAIL_TARGETS_HEADERS = ["company", "contact_email", "role", "job_link"]

# ─── Email Template ───────────────────────────────────────────────────────────

def build_email_body(company: str, role: str) -> str:
    return f"""\
Dear Hiring Team at {company},

I am writing to express my strong interest in the {role} position at {company}. \
As a cybersecurity enthusiast and aspiring penetration tester, I am eager to \
contribute my skills and grow within your organization.

I have foundational knowledge in:
- Network security and ethical hacking
- Vulnerability assessment and penetration testing
- OWASP Top 10, Burp Suite, Nmap, Metasploit
- Python scripting for security automation
- CTF competitions and hands-on lab environments (TryHackMe / HackTheBox)

I am a fresher with a passion for offensive security and a commitment to \
continuous learning. I would be grateful for the opportunity to discuss how \
I can contribute to your security team.

Please find my resume attached for your review.

Thank you for your time and consideration. I look forward to hearing from you.

Best regards,
{APPLICANT_NAME}
"""


def build_subject(role: str) -> str:
    return f"Application for {role} Position | Fresher | Cybersecurity Enthusiast"


# ─── Send One Email ───────────────────────────────────────────────────────────

def send_application_email(
    to_email: str,
    company: str,
    role: str,
    job_link: str = "email-application",
) -> bool:
    """Send an application email with resume attached. Returns True on success."""

    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        log.error("EMAIL_SENDER or EMAIL_PASSWORD not set in environment.")
        return False

    if not os.path.exists(RESUME_PATH):
        log.error(f"Resume not found at: {RESUME_PATH}")
        return False

    if already_applied(job_link):
        log.info(f"Already applied to {company} ({to_email}) — skipping.")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = to_email
        msg["Subject"] = build_subject(role)

        msg.attach(MIMEText(build_email_body(company, role), "plain"))

        # Attach resume PDF
        with open(RESUME_PATH, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(RESUME_PATH)}"',
        )
        msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())

        log.info(f"Email sent → {to_email} | {role} @ {company}")
        record_application(role, company, "Email", "Applied", job_link)
        notify("applied", f"Email application sent\nRole: {role}\nCompany: {company}\nTo: {to_email}")
        return True

    except Exception as e:
        log.error(f"Failed to send email to {to_email}: {e}")
        record_application(role, company, "Email", "Failed", job_link)
        notify("error", f"Email send failed\nCompany: {company}\nError: {e}")
        return False


# ─── Bulk Send from CSV ───────────────────────────────────────────────────────

def create_sample_targets_csv() -> None:
    """Create a sample email_targets.csv to get users started."""
    os.makedirs("data", exist_ok=True)
    if os.path.exists(EMAIL_TARGETS_FILE):
        return
    rows = [
        {"company": "Example Corp",   "contact_email": "hr@example.com",   "role": "Penetration Tester",   "job_link": "https://example.com/jobs/1"},
        {"company": "SecureTech Ltd", "contact_email": "jobs@securetech.io","role": "Cybersecurity Analyst", "job_link": "https://securetech.io/careers/2"},
    ]
    with open(EMAIL_TARGETS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EMAIL_TARGETS_HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    log.info(f"Sample email targets created: {EMAIL_TARGETS_FILE}")


def run_bulk_email_campaign() -> dict:
    """Read email_targets.csv and send applications to all companies."""
    create_sample_targets_csv()

    if not os.path.exists(EMAIL_TARGETS_FILE):
        log.warning(f"No email targets file found at {EMAIL_TARGETS_FILE}")
        return {"sent": 0, "skipped": 0, "failed": 0}

    results = {"sent": 0, "skipped": 0, "failed": 0}

    with open(EMAIL_TARGETS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        targets = list(reader)

    log.info(f"Starting bulk email campaign — {len(targets)} targets")

    for target in targets:
        company  = target.get("company", "Company")
        to_email = target.get("contact_email", "")
        role     = target.get("role", "Cybersecurity Role")
        link     = target.get("job_link", f"email-{company}")

        if not to_email:
            log.warning(f"No email for {company} — skipping.")
            results["skipped"] += 1
            continue

        if already_applied(link):
            log.info(f"Already applied to {company} — skipping.")
            results["skipped"] += 1
            continue

        success = send_application_email(to_email, company, role, link)
        if success:
            results["sent"] += 1
        else:
            results["failed"] += 1

    log.info(f"Email campaign complete: {results}")
    return results


if __name__ == "__main__":
    run_bulk_email_campaign()
