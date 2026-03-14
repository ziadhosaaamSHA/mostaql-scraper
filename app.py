from flask import Flask
from scraper import check_jobs, load_config
import os
import threading

app = Flask(__name__)

# Basic route to show it's alive
@app.route('/')
def home():
    return "Mostaql Scraper Bot is Running! 🚀 Trigger scraping via /scrape"

# Endpoint for Cron-job.org or UptimeRobot to hit
@app.route('/scrape')
def run_scraper_route():
    # Run in a separate thread so the request returns quickly
    threading.Thread(target=check_jobs).start()
    return "Scraping triggered!", 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
