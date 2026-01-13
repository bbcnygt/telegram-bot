import os
import requests
import feedparser
import html
import json
import time

# GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ACCOUNTS = ["yagosabuncuoglu", "FabrizioRomano", "MatteMoretto"]

# Nitter ve RSSHub karışık kaynak listesi (Hangisi çalışırsa)
SOURCES = [
    "https://rsshub.app/twitter/user/{account}",
    "https://rsshub.moeyy.cn/twitter/user/{account}",
    "https://nitter.poast.org/{account}/rss",
    "https://nitter.perennialte.ch/{account}/rss",
    "https://rsshub.rss.geek.edu.pl/twitter/user/{account}",
    "https://nitter.privacydev.net/{account}/rss"
]

STATE_FILE = "last_tweets.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        pass

def check_tweets():
    last_tweets = load_state()
    new_state = last_tweets.copy()
    
    for account in ACCOUNTS:
        print(f"🔎 {account} aranıyor...")
        success = False
        
        for source_template in SOURCES:
            url = source_template.format(account=account)
            try:
                # Bazı RSSHub'lar bot koruması için User-Agent ister
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
                response = requests.get(url, headers=headers, timeout=25)
                
                if response.status_code != 200:
                    continue
                
                feed = feedparser.parse(response.content)
                if not feed.entries:
                    continue
                
                last_link = last_tweets.get(account)
                new_entries = []
                
                for entry in feed.entries:
                    if entry.link == last_link:
                        break
                    new_entries.append(entry)
                
                # Yeni tweetleri gönder
                for entry in reversed(new_entries):
                    # Linki son kullanıcı için her zaman twitter.com yapalım
                    clean_link = entry.link
                    # Eğer link nitter veya rsshub içeriyorsa twitter.com ile değiştir
                    if "twitter.com" not in clean_link:
                        # Bu kısım basit bir temizlik yapar
                        clean_link = f"https://twitter.com/{account}/status/{entry.link.split('/')[-1]}"
                    
                    msg = f"<b>🔔 @{account}</b>\n\n{html.escape(entry.title)}\n\n<a href='{clean_link}'>Tweeti Görüntüle</a>"
                    send_telegram_message(msg)
                    new_state[account] = entry.link
                
                if last_link is None and feed.entries:
                    new_state[account] = feed.entries[0].link

                print(f"✅ {account} bilgisi alındı: {url}")
                success = True
                break 
            except:
                continue
        
        if not success:
            print(f"❌ {account} için hiçbir kaynak çalışmadı.")
    
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
