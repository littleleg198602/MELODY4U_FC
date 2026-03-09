# Melody4U Facebook Autopost System

Production-ready GitHub-based autoposting for the Melody4U Facebook Page using the **official Meta Pages API** (no Selenium, no Playwright, no browser clicking).

This project reads post definitions from `data/posts.json`, checks due scheduled posts, publishes them with images from `images/`, and writes status updates back into `posts.json`.

## Features

- Python 3.11+ implementation using `requests` and standard libraries
- GitHub Actions scheduling (hourly by default) + manual trigger
- Post lifecycle states: `draft`, `scheduled`, `published`, `failed`
- Validation for:
  - missing caption
  - missing image file
  - invalid `scheduled_time`
  - unsupported platform
- Safe processing: invalid items are marked failed, while valid items continue
- Duplicate prevention by `id`
- Structured code so Instagram support can be added later

---

## Repository structure

```text
.
├── .github/workflows/autopost.yml
├── data/posts.json
├── images/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── facebook_publisher.py
│   ├── logger.py
│   ├── main.py
│   ├── post_loader.py
│   └── scheduler.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## 1) Create Meta credentials (official API)

You need a Facebook Page access token with permissions to publish to your page.

1. Go to [Meta for Developers](https://developers.facebook.com/).
2. Create an app (Business type recommended).
3. Add the Facebook Login / Graph API products as needed.
4. Generate a **long-lived Page Access Token** for your page.
5. Collect:
   - `META_PAGE_ID`
   - `META_ACCESS_TOKEN`

> Use only official Meta flows and permissions for your business/page setup.

---

## 2) Configure local environment

1. Copy `.env.example` to `.env`.
2. Fill in real values:

```env
META_PAGE_ID=your_real_page_id
META_ACCESS_TOKEN=your_real_page_access_token
DEFAULT_TIMEZONE=UTC
```

Install and run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main --dry-run
```

Use `--dry-run` for validation and due-check testing without publishing to Meta or changing post statuses.

---

## 3) Add GitHub Secrets

In GitHub repo settings:

**Settings → Secrets and variables → Actions → New repository secret**

Create these secrets:

- `META_PAGE_ID`
- `META_ACCESS_TOKEN`
- `DEFAULT_TIMEZONE` (optional, recommended)

The workflow reads these at runtime. No secrets are hardcoded in code.

---

## 4) Prepare `posts.json`

File: `data/posts.json`

Each post object requires:

- `id`
- `title`
- `caption`
- `image_path`
- `scheduled_time` (ISO 8601 format, e.g. `2026-03-10T12:00:00`)
- `timezone` (IANA timezone, e.g. `UTC`, `Asia/Bangkok`)
- `language` (defaults to `en` if omitted)
- `status` (`draft`, `scheduled`, `published`, `failed`)
- `platforms` (currently include `facebook`)

### Example entry

```json
{
  "id": "m4u-2026-03-10",
  "title": "Message to Music",
  "caption": "A simple voice note can become the most unforgettable gift.",
  "image_path": "spring-glow-03.jpg",
  "scheduled_time": "2026-03-10T12:00:00",
  "timezone": "UTC",
  "language": "en",
  "status": "scheduled",
  "platforms": ["facebook"]
}
```

---

## 5) Add images

Place image files inside `images/` and reference them from `image_path`.

Example:

- file on disk: `images/spring-glow-03.jpg`
- JSON value: `"image_path": "spring-glow-03.jpg"`

---

## 6) How scheduling works

Workflow file: `.github/workflows/autopost.yml`

- Runs automatically every hour (`0 * * * *`)
- Can be run manually with **Run workflow**

Run behavior:

1. Load `data/posts.json`
2. Validate each post
3. For posts with `status == "scheduled"`, check if `scheduled_time` is due
4. Publish to Facebook Page via Graph API if due
5. Update post state:
   - success → `published`
   - error/validation issue → `failed` with `failure_reason`
6. Commit and push `data/posts.json` changes from the workflow when statuses changed
7. Leave non-due or non-scheduled items unchanged/skipped

---

## 7) Local testing

### Dry-run (no API call)

```bash
python -m src.main --dry-run
```

### Real publish run

```bash
python -m src.main
```

Use dry-run first before enabling live publishing.

---

## Common troubleshooting

- **Missing env vars**
  - Error: required variables missing
  - Fix: set `META_PAGE_ID` and `META_ACCESS_TOKEN` in `.env` or GitHub Secrets

- **Invalid `scheduled_time`**
  - Use ISO 8601, e.g. `2026-03-18T15:45:00`

- **Invalid timezone**
  - Use a valid IANA value (`UTC`, `America/New_York`, `Asia/Bangkok`)

- **Unsupported platform**
  - For v1, only `facebook` is supported in `platforms`

- **Image not found**
  - Ensure file exists in `images/` and name exactly matches `image_path`

- **Meta API permission/token errors**
  - Re-check token validity, app mode, page permissions, and page-role access

- **Workflow cannot push `posts.json` updates**
  - Ensure Actions has write access (`permissions: contents: write`) and branch protection allows bot pushes

---

## NEXT IMPROVEMENTS

- **Instagram support**
  - Add `instagram_publisher.py` and route by platform in scheduler
- **AI caption generation**
  - Add optional generator module for drafts and A/B variants
- **Google Sheets integration**
  - Sync post planning from Sheets to `posts.json`
- **Approval workflow before publishing**
  - Require `approved: true` or PR-based editorial review before status can move to `scheduled`
