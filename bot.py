import os
import requests
import feedparser
import html
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ACCOUNTS = ["yagosabuncuoglu", "FabrizioRomano", "MatteMoretto"]

# Daha geniş ve stabil Nitter instance listesi
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.no-logs.com",
    "https://nitter.projectsegfau.lt",
    "https://nitter.perennialte.ch",
    "https://nitter.rawbit.ninja",
    "https://nitter.esmailelbob.xyz",
    "https://nitter.tinfoil-hat.net"
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
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def check_tweets():
    last_tweets = load_state()
    new_state = last_tweets.copy()
    
    for account in ACCOUNTS:
        print(f"Kontrol ediliyor: {account}")
        success = False
        
        for instance in NITTER_INSTANCES:
            rss_url = f"{instance}/{account}/rss"
            try:
                # User-agent ekleyerek bot olduğumuzu gizlemeye çalışıyoruz
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = requests.get(rss_url, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    continue
                    
                feed = feedparser.parse(response.content)
                if not feed.entries:
                    continue
                
                last_saved_link = last_tweets.get(account)
                new_entries = []
                
                for entry in feed.entries:
                    if entry.link == last_saved_link:
                        break
                    new_entries.append(entry)
                
                for entry in reversed(new_entries):
                    # Linki kullanıcı için Twitter'a çeviriyoruz
                    clean_link = entry.link
                    for inst in NITTER_INSTANCES:
                        clean_link = clean_link.replace(inst.split('//')[1], "twitter.com")
                    
                    msg = f"<b>🔔 @{account}</b>\n\n{html.escape(entry.title)}\n\n<a href='{clean_link}'>Tweeti Görüntüle</a>"
                    send_telegram_message(msg)
                    new_state[account] = entry.link
                
                if last_saved_link is None and feed.entries:
                    new_state[account] = feed.entries[0].link

                print(f"✅ {account} başarıyla güncellendi ({instance})")
                success = True
                break
            except Exception as e:
                print(f"⚠️ {instance} hatası: {e}")
                continue
        
        if not success:
            print(f"❌ HATA: {account} verisi hiçbir kaynaktan çekilemedi.")
    
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
