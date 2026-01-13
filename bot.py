import os
import requests
import feedparser
import html
import json

# GitHub Secrets'dan gelen bilgiler
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ACCOUNTS = ["yagosabuncuoglu", "FabrizioRomano", "MatteMoretto"]

# Twitter RSS beslemeleri için Nitter adresleri
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.cz",
    "https://nitter.privacydev.net",
    "https://nitter.it"
]

STATE_FILE = "last_tweets.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Hatası: {e}")

def check_tweets():
    last_tweets = load_state()
    new_state = last_tweets.copy()
    
    for account in ACCOUNTS:
        print(f"Kontrol ediliyor: {account}")
        success = False
        for instance in NITTER_INSTANCES:
            rss_url = f"{instance}/{account}/rss"
            try:
                feed = feedparser.parse(rss_url)
                if not feed.entries:
                    continue
                
                latest_tweet = feed.entries[0]
                tweet_link = latest_tweet.link
                tweet_content = latest_tweet.title

                # Eğer bu tweet daha önce gönderilmediyse
                if last_tweets.get(account) != tweet_link:
                    msg = f"<b>🔔 @{account}</b>\n\n{html.escape(tweet_content)}\n\n<a href='{tweet_link}'>Tweeti Görüntüle</a>"
                    send_telegram_message(msg)
                    new_state[account] = tweet_link
                    print(f"Yeni tweet bulundu: {account}")
                
                success = True
                break 
            except:
                continue
        
        if not success:
            print(f"Hata: {account} verisi çekilemedi.")
    
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()