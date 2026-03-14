# Mostaql Job Scraper

This tool automatically scrapes mostaql.com for new "Development" and "AI/ML" projects and sends notifications to your Telegram.

## 🚀 The Ultimate Solution: GitHub Actions + External Trigger
This method is **Free**, **Stable**, and can run every **2 minutes**.

### Required GitHub Secrets
In your GitHub repo, add:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### Step 1: Update GitHub Code
1.  Upload the updated `.github/workflows/scraper.yml` to your repository.

### Step 2: Get a GitHub Access Token (PAT)
We need a key to allow the external timer to "click" the Run button on your repo.

1.  Go to **GitHub Settings** -> **Developer settings** -> **Personal access tokens** -> **Tokens (classic)**.
2.  Click **Generate new token (classic)**.
3.  **Note**: "Scraper Trigger".
4.  **Scopes**: Check `repo` (Full control of private repositories).
5.  Click **Generate token**.
6.  **COPY THIS TOKEN**. You won't see it again.

### Step 3: Set up Cron-job.org
1.  Go to [cron-job.org](https://cron-job.org/) (Create free account).
2.  **Create Cronjob**.
3.  **URL**: `https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO_NAME/dispatches`
    *   Example: `https://api.github.com/repos/ziadhosaaam/mostaql-scraper/dispatches`
4.  **Execution Schedule**: Every 2 minutes.
5.  **Advanced / HTTP Headers** (Important!):
    *   Click "Add Header".
        *   Key: `Authorization`
        *   Value: `Bearer YOUR_GITHUB_TOKEN_HERE`
    *   Click "Add Header".
        *   Key: `Accept`
        *   Value: `application/vnd.github.v3+json`
    *   Click "Add Header".
        *   Key: `User-Agent`
        *   Value: `Mostaql-Scraper`
6.  **Request Body** (JSON):
    *   Paste this exactly: `{"event_type": "scrape_now"}`
7.  **HTTP Method**: Change from GET to **POST**.
8.  **Save**.

✅ **Done!** Cron-job.org will now send a signal to GitHub every 2 minutes to run your scraper.

## Local Run (Optional)
1. `pip install -r requirements.txt`
2. Create a `config.json` (see `config.example.json`) or set env vars `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
3. Run `python scraper.py`

## Web Trigger (Optional)
Run a small server and trigger scraping via HTTP:
1. `pip install -r requirements.txt`
2. `gunicorn app:app` (or `python app.py`)
3. Hit `/scrape` to trigger a scrape
