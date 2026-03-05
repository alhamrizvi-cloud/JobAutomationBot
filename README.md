# JobAutomationBot

```
      __      __    ___         __                        __  _             ____        __ 
     / /___  / /_  /   | __  __/ /_____  ____ ___  ____ _/ /_(_)___  ____  / __ )____  / /_
__  / / __ \/ __ \/ /| |/ / / / __/ __ \/ __ `__ \/ __ `/ __/ / __ \/ __ \/ __  / __ \/ __/
/ /_/ / /_/ / /_/ / ___ / /_/ / /_/ /_/ / / / / / / /_/ / /_/ / /_/ / / / / /_/ / /_/ / /_  
\____/\____/_.___/_/  |_\__,_/\__/\____/_/ /_/ /_/\__,_/\__/_/\____/_/ /_/_____/\____/\__/
```

> 🔗 **github.com/alhamrizvi-cloud/JobAutomationBot**

Automated Cybersecurity Job Application System — finds and applies to penetration testing,
ethical hacking, and security analyst jobs across LinkedIn, Naukri, web job boards, and via email.

---

## 📁 Project Structure

```
job_bot/
├── main.py           ← Orchestrator + CLI entry point
├── linkedin_bot.py   ← LinkedIn Easy Apply automation
├── naukri_bot.py     ← Naukri.com login + auto apply
├── email_sender.py   ← SMTP email applications with resume
├── job_scraper.py    ← Scrape Indeed, TimesJobs, Internshala
├── config.py         ← All settings (reads from .env)
├── tracker.py        ← CSV-based application tracker
├── notifier.py       ← Telegram + email notifications
├── logger.py         ← Shared logging setup
├── requirements.txt  ← Python dependencies
├── .env.example      ← Credentials template
├── .gitignore
├── resume.pdf        ← ⬅ Place YOUR resume here
├── logs/
│   └── job_bot.log
└── data/
    ├── applied_jobs.csv      ← Auto-created tracker
    └── email_targets.csv     ← Companies to email (edit this!)
```

---

## ⚡ Quick Setup

### Step 1 — Install Python 3.11+
```bash
python --version   # Should be 3.11 or higher
```

### Step 2 — Clone / Download the project
```bash
git clone github.com/alhamrizvi-cloud/JobAutomationBot
cd JobAutomationBot
```

### Step 3 — Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate.bat      # Windows
```

### Step 4 — Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 5 — Configure credentials
```bash
cp .env.example .env
```
Open `.env` in any text editor and fill in:
- Your name, phone, email
- LinkedIn login credentials
- Naukri login credentials
- Gmail + App Password (see Gmail Setup below)
- Telegram Bot token (optional)

### Step 6 — Add your resume
Place your resume as `resume.pdf` in the `job_bot/` folder.

### Step 7 — Run!
```bash
python main.py          # Full run (all modules)
python main.py --stats  # Check stats anytime
```

---

## 🔐 Gmail App Password Setup

Gmail requires an **App Password** (not your normal password) for SMTP.

1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification** if not already on
3. Go to https://myaccount.google.com/apppasswords
4. Select App: **Mail** | Device: **Windows Computer**
5. Click **Generate**
6. Copy the 16-character password into `.env` as `EMAIL_PASSWORD`

---

## 📬 Email Campaign Setup

Edit `data/email_targets.csv` (auto-created on first run):

```csv
company,contact_email,role,job_link
Infosys,hr@infosys.com,Security Analyst,https://infosys.com/careers/123
TCS,security.hiring@tcs.com,Penetration Tester,https://tcs.com/jobs/456
```

Then run:
```bash
python main.py --email
```

---

## 🤖 Telegram Bot Setup (Optional)

1. Open Telegram and message `@BotFather`
2. Send `/newbot` and follow prompts → copy the **Bot Token**
3. Message `@userinfobot` to get your **Chat ID**
4. Add both to `.env`

You'll receive instant notifications when jobs are applied or errors occur.

---

## 🕐 Scheduling Options

### Option A — Python scheduler (easiest)
```bash
python main.py --schedule
```
Runs every day at the time set in `config.py` (`SCHEDULE_TIME = "09:00"`).
Keep the terminal open or run in a `screen` / `tmux` session.

### Option B — Linux cron job
```bash
crontab -e
```
Add this line to run at 9 AM every day:
```
0 9 * * * cd /path/to/job_bot && /path/to/venv/bin/python main.py >> logs/cron.log 2>&1
```

### Option C — Windows Task Scheduler
1. Open Task Scheduler → Create Basic Task
2. Trigger: Daily at 9:00 AM
3. Action: Start Program
4. Program: `C:\path\to\venv\Scripts\python.exe`
5. Arguments: `C:\path\to\job_bot\main.py`

---

## 💻 All CLI Commands

```bash
python main.py              # Run all modules
python main.py --schedule   # Schedule daily runs
python main.py --linkedin   # LinkedIn only
python main.py --naukri     # Naukri only
python main.py --email      # Email campaign only
python main.py --scrape     # Scrape + display (no apply)
python main.py --stats      # Show application statistics
```

---

## 📊 Application Tracker

All applications are saved to `data/applied_jobs.csv`:

```
job_title, company, platform, status, date_applied, job_link
Penetration Tester, SecureTech, LinkedIn, Applied, 2024-07-01 09:15:00, https://...
SOC Analyst, Wipro, Naukri, Applied, 2024-07-01 09:18:33, https://...
```

The bot automatically skips jobs you've already applied to.

---

## ⚙️ Configuration (config.py)

| Setting | Default | Description |
|---|---|---|
| `JOB_KEYWORDS` | 8 keywords | Cybersecurity job title filters |
| `LOCATION_FILTERS` | India/Mumbai/Remote | Location targets |
| `MAX_APPLICATIONS_PER_RUN` | 20 | Safety cap per session |
| `DELAY_BETWEEN_APPS_SEC` | (5, 15) | Random delay range |
| `HEADLESS_BROWSER` | True | Set False to watch browser |
| `SCHEDULE_TIME` | "09:00" | Daily run time |

---

## ⚠️ Important Warnings

1. **Terms of Service**: LinkedIn and Naukri prohibit automated access.
   Use only for personal job searching and keep MAX_APPLICATIONS low.

2. **Rate Limiting**: The bot includes random delays. Don't remove them.

3. **Account Safety**: LinkedIn may temporarily restrict accounts if too
   many actions are detected. Start with `MAX_APPLICATIONS_PER_RUN = 5`
   and increase gradually.

4. **CAPTCHA**: Both platforms may show CAPTCHAs. Set `HEADLESS_BROWSER = False`
   to solve them manually when needed.

5. **Credentials**: Never share your `.env` file or commit it to GitHub.

---

## 🐛 Troubleshooting

**"No module named playwright"**
```bash
pip install playwright && playwright install chromium
```

**LinkedIn login fails / CAPTCHA**
```bash
# In config.py, set:
HEADLESS_BROWSER = False
# Then run and solve CAPTCHA manually
```

**Gmail SMTP authentication error**
- Make sure you're using an App Password, not your Gmail password
- Ensure 2-Step Verification is enabled on your Google account

**No jobs found**
- Check your internet connection
- The site's HTML structure may have changed — check logs for details

---

## 📈 Tips for Freshers

- Fill your LinkedIn profile completely before running the bot
- Upload your resume to Naukri profile manually once before using the bot
- Add a professional photo to all platforms
- Keep `resume.pdf` updated with certifications (CEH, CompTIA Security+, etc.)
- Add CTF wins (TryHackMe, HackTheBox) to your profiles

---

*Built with ❤️ for aspiring cybersecurity professionals*  
*🔗 github.com/alhamrizvi-cloud/JobAutomationBot*
