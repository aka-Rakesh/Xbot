# Twitter Bounty Bot — Step-by-step Instructions (for Cursor)

> Purpose: a practical, deployable plan and step-by-step instructions to build an automated bot that scrapes a bounty site for crypto posting bounties and posts threads to X/Twitter to claim bounties and grow an organic following. Save this file at your project root in Cursor (filename: `instructions.md`).

---

# 1. Quick summary

This document walks you from zero → working bot. It covers: project layout, environment & secrets, scraping strategy, thread generation, posting via X/Twitter API, scheduler & rate-limits, deployment (Docker / systemd), monitoring, safety/ToS checklist, testing, and next steps.

Use Cursor to edit files, run commands in an integrated terminal, and iterate quickly. Treat `instructions.md` as your project playbook.

---

# 2. Goals (explicit)

1. Monitor one or more bounty pages and detect new bounties.
2. Generate a clean, non-spammy Twitter/X thread for each new bounty.
3. Post the thread programmatically using a properly authorized developer/app token.
4. Avoid duplicates, respect platform rules, and operate within rate limits.

---

# 3. Architecture (logical)

* **Scraper service** — polls bounty site(s) and extracts bounty metadata (id, title, url, description, timestamp).
* **Database** — records seen bounty IDs, posting history, and rate-limit metadata. (SQLite for dev; Postgres for prod.)
* **Thread generator** — templates (or optional LLM) that convert raw bounty info into a 3–6 tweet thread.
* **Poster service** — posts the thread via X/Twitter API, records posted tweet IDs and timestamps.
* **Scheduler** — controls when scraper runs and posts happen (APScheduler or cron).
* **Operator UI / queue (optional)** — web UI or CLI to review candidate threads before posting.
* **Monitoring & alerts** — log aggregator, error alerts, rate-limit metrics.

---

# 4. Prerequisites

* Local dev: Python 3.11+, Node (optional for Playwright), Git.
* Accounts: X/Twitter developer account (approved app + write scopes).
* A hosting target for production: VPS (DigitalOcean, Linode), or PaaS (Render, Railway), or container hosting.
* Optional: OpenAI key (if you want LLM-written threads).

---

# 5. Project layout (suggested)

```
twitter-bounty-bot/
├─ instructions.md
├─ README.md
├─ .env.example
├─ requirements.txt
├─ src/
│  ├─ main.py            # scheduler entry
│  ├─ scraper.py         # bounty site-specific parsers
│  ├─ poster.py          # X/Twitter posting helper
│  ├─ generator.py       # thread generation templates/LLM wrapper
│  ├─ storage.py         # sqlite/postgres helpers
│  ├─ utils.py           # rate limit / backoff / helpers
│  └─ config.py          # loads environment, constant definitions
├─ migrations/           # optional DB migrations
├─ dockerfile
├─ docker-compose.yml
└─ tests/
   ├─ test_scraper.py
   └─ test_poster.py
```

---

# 6. Environment variables (`.env.example`)

```
# X/Twitter credentials (recommended to use OAuth user token for posting)
TW_API_KEY=
TW_API_SECRET=
TW_ACCESS_TOKEN=
TW_ACCESS_SECRET=
TW_BEARER_TOKEN=
OAUTH_CLIENT_ID=
OAUTH_CLIENT_SECRET=

# Bounty site & DB
BOUNTY_SITE_URL=
DATABASE_URL=sqlite:///./data.db

# Optional 3rd party
OPENAI_API_KEY=
SENTRY_DSN=

# Bot behavior
POST_INTERVAL_MINUTES=10
MAX_POSTS_PER_DAY=10
USER_DISPLAY_NAME=MyBountyBot
```

**Important**: keep credentials out of source control. Use a secrets manager when deploying.

---

# 7. Developer setup (local / Cursor)

1. Clone the repo.

```bash
git clone <repo-url>
cd twitter-bounty-bot
```

2. Create a virtual environment and install dependencies.

```bash
python -m venv .venv
source .venv/bin/activate   # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

3. Copy `.env.example` → `.env` and fill values.

4. Initialize the database (simple sqlite example):

```bash
python -c "from src.storage import init_db; init_db()"
```

5. Run the scheduler locally for testing:

```bash
python -m src.main
```

Cursor tip: open a terminal pane, run the commands above, and use the editor to update parsers and templates live.

---

# 8. Scraper: practical notes & code pattern

**Design principles**

* Prefer a public API from the bounty site if available.
* Check `robots.txt` and the site’s Terms of Service — stop if scraping is disallowed.
* Use polite request headers, rate-limiting, and caching.
* If the page is JavaScript-heavy, use Playwright (headless) rather than requests/bs4.

**Parsing pattern (Python)**

* Request page → parse list of bounties → for each item extract unique `bounty_id` → check DB for seen → if new, persist minimal metadata and hand to generator.

```py
# src/scraper.py  (skeleton)
import requests
from bs4 import BeautifulSoup

BOUNTY_SITE_URL = os.getenv('BOUNTY_SITE_URL')

def fetch_bounties():
    r = requests.get(BOUNTY_SITE_URL, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    out = []
    for node in soup.select('.bounty-row'):
        link = node.select_one('a')
        href = link['href']
        title = link.get_text(strip=True)
        bounty_id = href.split('/')[-1]
        out.append({'id': bounty_id, 'title': title, 'url': href})
    return out
```

**When to use Playwright**

* Use Playwright (or Selenium) when the content is rendered client-side. In that case create a small Playwright script that loads the page, waits for the selector, and extracts the HTML.

---

# 9. Storage / deduplication

**Schema (SQLite simple)**

```
CREATE TABLE IF NOT EXISTS seen_bounty (
  id TEXT PRIMARY KEY,
  title TEXT,
  url TEXT,
  seen_at INTEGER
);

CREATE TABLE IF NOT EXISTS posts (
  id SERIAL PRIMARY KEY,
  bounty_id TEXT,
  posted_at INTEGER,
  tweet_thread_root_id TEXT
);
```

**Key rules**

* Use the `bounty_id` supplied by the site when possible; otherwise hash the URL + title for a stable key.
* Use `INSERT OR IGNORE` pattern to avoid races in concurrent runs.
* For multi-instance deployments, use a centralized DB (Postgres) and a lightweight locking mechanism (advisory locks or Redis lock) to avoid double-posting.

---

# 10. Thread generation (templates & optional LLM)

Start with deterministic templates. Example 3-tweet thread:

1. `🔔 New bounty: {title}`
2. `Quick summary: {one-liner description or category}`
3. `Apply / details: {url} | Follow for more updates`

**Generator pattern (Python)**

```py
# src/generator.py
TEMPLATE = [
  '🔔 New bounty: {title}',
  'Why it matters: {why}',
  'Apply here: {url} — RT & follow for more.'
]

def build_thread(bounty):
    # fill fields and make sure none exceed limits
    why = (bounty.get('short_description') or '')[:200]
    return [t.format(title=bounty['title'], why=why, url=bounty['url']) for t in TEMPLATE]
```

**Optional LLM approach**

* Add an `OPENAI_API_KEY` and call OpenAI (or your preferred LLM) to paraphrase and enrich the thread. Use a strict prompt that keeps the model within length and style constraints and include a seed token to avoid repetition.

**Important**: always apply a deterministic post-processing step to ensure the content doesn’t accidentally leak personal data or break platform rules.

---

# 11. Posting to X/Twitter (pattern)

**General flow**

1. Post first tweet.
2. Save returned `tweet_id`.
3. Post subsequent tweets as replies to the previous tweet (use the `in_reply_to` or `reply` parameter depending on client/endpoint).
4. Record the root tweet id in the DB.

**Practical tips**

* Use official OAuth flow to obtain user-level write tokens (tweet.write).
* Implement exponential backoff on 429 responses.
* Keep tweets reasonably short; avoid repeating identical content across posts.

**Posting skeleton (requests)**

```py
# src/poster.py (very small skeleton)
import os, requests
TW_BEARER = os.getenv('TW_BEARER_TOKEN')
API_TWEET_URL = 'https://api.twitter.com/2/tweets'

headers = {'Authorization': f'Bearer {TW_BEARER}', 'Content-Type': 'application/json'}

def post_tweet(text, in_reply_to=None):
    payload = {'text': text}
    if in_reply_to:
        payload['reply'] = {'in_reply_to_tweet_id': in_reply_to}
    r = requests.post(API_TWEET_URL, headers=headers, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()
```

> NOTE: update your posting code to the modern client or SDK you choose (tweepy, an official SDK, or direct HTTP). If a platform changes endpoints or auth flows, update the wrapper accordingly.

---

# 12. Scheduler / Rate limiting

* Use APScheduler for fine-grained control in a single-process deploy.
* Enforce `MAX_POSTS_PER_DAY` and minimum gap between posts.
* On 429 responses: backoff, log, and delay further posts.

**Example**

```py
# src/main.py (skeleton)
from apscheduler.schedulers.blocking import BlockingScheduler
from scraper import fetch_bounties

sched = BlockingScheduler()
@sched.scheduled_job('interval', minutes=int(os.getenv('POST_INTERVAL_MINUTES', 10)))
def check_job():
    # fetch, filter, queue or post
    pass

sched.start()
```

---

# 13. Deploying (Docker + service)

**Dockerfile (minimal)**

```
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY .env ./
CMD ["python", "-m", "src.main"]
```

**docker-compose (dev)**

```yaml
version: '3.8'
services:
  bot:
    build: .
    env_file: .env
    volumes:
      - ./:/app
```

**systemd (example)**

```
[Unit]
Description=Twitter Bounty Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/twitter-bounty-bot
ExecStart=/home/ubuntu/.venv/bin/python -m src.main
Restart=always

[Install]
WantedBy=multi-user.target
```

---

# 14. Monitoring, logs & alerts

* Log every HTTP error and 429/403/401.
* Keep a daily summary of posted bounty IDs and posted threads.
* Add Sentry (or similar) for exceptions.
* If hosting on a VPS, set up `logrotate` for logs and health checks (or a small heartbeat endpoint and uptime monitor).

---

# 15. Testing checklist (before going live)

* [ ] Run scraper once and confirm it extracts IDs and titles.
* [ ] Run poster against a staging/test account to verify tweet posting flow.
* [ ] Simulate 429 to verify backoff logic.
* [ ] Confirm dedupe works (re-run scraper with same data).
* [ ] Manual review step enabled (queue) before enabling autopost in production.

---

# 16. Safety, legal & ToS (must-read before production)

1. **X/Twitter rules** — read and comply with their automation and spam policies. Do not create bot accounts that post repetitive unsolicited content.
2. **Bounty site TOS** — ensure the site allows scraping and automated posting for bounty claims. Some platforms prohibit automation or require human verification/KYC.
3. **Payments** — do not automate any flow that bypasses KYC, identity checks, or account verification. Automating a payout-without-authorization flow can be fraud.
4. **Labeling** — if X/Twitter requires that automated accounts disclose automation, apply the required labels.

If you are unsure about a rule, choose the conservative approach: manual approval for payout-related actions.

---

# 17. Scaling & reliability tips

* Move to Postgres + Redis for locks when running multiple workers.
* Use exponential backoff with jitter for network errors.
* Consider rate-limit token bucket for outgoing posts.
* Add a message queue (RabbitMQ / Redis Streams) if you want decoupling between scraper and poster.

---

# 18. Troubleshooting (common errors)

* **401 Unauthorized**: check tokens & scopes. Ensure tokens are user-authorized for tweet.write.
* **403 Forbidden**: API or account action blocked — check dev portal and account suspension / elevated access.
* **429 Too Many Requests**: backoff and respect Retry-After header.
* **Duplicate posts**: confirm DB dedupe and locking.

---

# 19. Checklist before flipping to autopost (go-live)

* [ ] Confirm bot complies with X/Twitter automation rules.
* [ ] Confirm bounty site's terms allow scraping or have you got permission.
* [ ] Limit `MAX_POSTS_PER_DAY` to a conservative number (start with 1–3).
* [ ] Put human-in-the-loop approval for high-value bounties.
* [ ] Set alerts for sudden error spikes or account warnings.

---

# 20. Next steps I can do for you (pick one)

* Generate a complete Git repo scaffold (code + Dockerfile + README + .env.example).
* Build a site-specific scraper if you paste the bounty page URL (I’ll write exact selectors + tests).
* Add LLM-powered thread generation and safe-post filters.
* Produce a `deploy.sh` + sample systemd unit for a typical VPS deployment.

Tell me which one and I’ll create it next.

---

# 21. Appendix: quick commands

* Run locally: `python -m src.main`
* Run tests: `pytest -q`
* Build docker: `docker build -t bounty-bot .`
* Run docker-compose dev: `docker compose up --build`

---

*This document is a working playbook — edit in Cursor as you implement. Keep a changelog in the repo when you change selectors, scheduling intervals, or posting rules.*
