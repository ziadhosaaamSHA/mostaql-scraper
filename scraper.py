import requests
from bs4 import BeautifulSoup
import time
import json
import os
import schedule
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
CONFIG_FILE = 'config.json'
DATA_DIR = 'data'
SEEN_JOBS_FILE = os.path.join(DATA_DIR, 'seen_jobs.json')

def load_config():
    """Load configuration from JSON file or Environment Variables."""
    load_dotenv()
    config = {}
    
    # Try loading from file first
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
    # Override with Environment Variables (Best for GitHub Actions/Server)
    if os.environ.get('TELEGRAM_BOT_TOKEN'):
        config['telegram_bot_token'] = os.environ.get('TELEGRAM_BOT_TOKEN')
    if os.environ.get('TELEGRAM_CHAT_ID'):
        config['telegram_chat_id'] = os.environ.get('TELEGRAM_CHAT_ID')
        
    # Default URL if not in config
    if 'target_url' not in config:
        config['target_url'] = "https://mostaql.com/projects?category=development,ai-machine-learning&sort=latest"
        
    return config

def load_seen_jobs():
    """Load the list of seen job IDs."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(SEEN_JOBS_FILE):
        return []
        
    try:
        with open(SEEN_JOBS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_seen_jobs(seen_jobs):
    """Save the list of seen job IDs."""
    try:
        with open(SEEN_JOBS_FILE, 'w', encoding='utf-8') as f:
            json.dump(seen_jobs, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving seen jobs: {e}")

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def send_telegram_message(config, message):
    """Send a notification via Telegram with retry logic."""
    bot_token = config.get('telegram_bot_token')
    chat_id = config.get('telegram_chat_id')
    
    if not bot_token or not chat_id or "YOUR_" in bot_token:
        logging.warning("Telegram credentials not configured properly.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    
    try:
        response = session.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Telegram message: {e}")

def check_jobs():
    """Main function to scrape and check for new jobs."""
    config = load_config()
    if not config:
        return

    url = config.get('target_url')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    logging.info("Checking for new jobs...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching URL: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Depending on Mostaql structure, the container is usually a table row with class 'project-row'
    # or sometimes they use a div structure. Based on inspection, it's 'project-row'.
    project_rows = soup.select('tr.project-row')
    
    if not project_rows:
        project_rows = soup.select('.project-row') # Fallback to class only if table structure changes
    
    if not project_rows:
        logging.warning("No projects found on the page. Use debug mode to check HTML.")
        return

    seen_jobs = load_seen_jobs()
    # Convert seen_jobs to set for O(1) lookups, assuming it's a list of IDs/URLs
    seen_jobs_set = set(seen_jobs)
    
    new_jobs_found = []
    
    # Process from newest to oldest (top to bottom), but we want to notify for all new ones.
    # It's better to process list, then check which are new.
    
    for row in project_rows:
        # Extract Job Title and Link
        title_tag = row.select_one('h2 a')
        if not title_tag:
            continue
            
        job_title = title_tag.text.strip()
        job_link = title_tag['href']
        
        # Ensure full URL
        if not job_link.startswith('http'):
            job_link = f"https://mostaql.com{job_link}"
            
        # Use the link as the unique ID
        job_id = job_link
        
        if job_id not in seen_jobs_set:
            # Extract other details
            description_tag = row.select_one('.details-url')
            description = description_tag.text.strip() if description_tag else "No description"
            
            time_tag = row.select_one('time')
            time_posted = time_tag.text.strip() if time_tag else "Unknown time"
            
            msg = f"🚀 *New Job on Mostaql*\n\n" \
                  f"📌 *{job_title}*\n" \
                  f"🕒 {time_posted}\n\n" \
                  f"📝 {description}\n\n" \
                  f"🔗 [View Project]({job_link})"
            
            logging.info(f"New job found: {job_title}")
            send_telegram_message(config, msg)
            
            new_jobs_found.append(job_id)
            seen_jobs_set.add(job_id)
    
    if new_jobs_found:
        # Update seen jobs file
        # We might want to keep the list size manageable, e.g., keep last 1000
        updated_seen_list = sorted(seen_jobs_set)
        if len(updated_seen_list) > 1000:
             # Keep the ones we just found + random others? 
             # Simpler: just keep the last 1000 strings if we tracked order, 
             # but sets are unordered.
             # Logic: Just save them all for now.
             pass
             
        save_seen_jobs(updated_seen_list)
        logging.info(f"Sent notifications for {len(new_jobs_found)} new jobs.")
    else:
        logging.info("No new jobs found.")

def main():
    # If running in GitHub Actions (or any CI), we don't use 'schedule' loop. 
    # The CI platform triggers the script.
    # We check for an environment variable 'GITHUB_ACTIONS' to decide.
    
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        logging.info("Running in GitHub Actions mode (Single execution).")
        check_jobs()
        return

    config = load_config()
    if not config or not config.get('telegram_bot_token'):
        logging.error("Configuration failed. Make sure config.json exists or ENV variables are set.")
        return

    logging.info("Starting Mostaql Scraper...")
    logging.info(f"Target URL: {config.get('target_url')}")
    
    # Run once immediately
    check_jobs()
    
    interval = config.get('scrape_interval_minutes', 2)
    logging.info(f"Scheduling scraper to run every {interval} minutes.")
    
    schedule.every(interval).minutes.do(check_jobs)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
