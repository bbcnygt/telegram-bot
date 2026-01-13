import os
import requests
import feedparser
import html
import json

# GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ACCOUNTS = ["yagosabuncuoglu", "FabrizioRomano", "MatteMoretto"]

# 2026 Güncel ve Aktif Nitter Örnekleri (GitHub dostu olanlar öncelikli)
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.perennialte.ch",
    "https://nitter.privacydev.net",
    "https://nitter.cz",
    "https://nitter.projectsegfau.lt",
    "https://nitter.no-logs.com",
    "https://nitter.dr460nf1r3.org"
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
        print(f"--- {account} kontrol ediliyor ---")
        success = False
        
        for instance in NITTER_INSTANCES:
            rss_url = f"{instance}/{account}/rss"
            try:
                # GitHub engelini aşmak için tarayıcı gibi davranıyoruz
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
                response = requests.get(rss_url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    print(f"⚠️ {instance} yanıt vermedi (Kod: {response.status_code})")
                    continue
                
                feed = feedparser.parse(response.content)
                if not feed.entries:
                    continue
                
                last_link = last_tweets.get(account)
                
                # Sadece yeni tweetleri bul
                new_items = []
                for entry in feed.entries:
                    if entry.link == last_link:
                        break
                    new_items.append(entry)
                
                # Tweetleri gönder
                for entry in reversed(new_items):
                    # Linki Twitter linkine dönüştür
                    link = entry.link
                    for n in NITTER_INSTANCES:
                        link = link.replace(n.split('//')[1], "twitter.com")
                    
                    msg = f"<b>🔔 @{account}</b>\n\n{html.escape(entry.title)}\n\n<a href='{link}'>Tweeti Görüntüle</a>"
                    send_telegram_message(msg)
                    new_state[account] = entry.link
                    print(f"✅ Yeni tweet gönderildi: {account}")
                
                if last_link is None and feed.entries:
                    new_state[account] = feed.entries[0].link

                success = True
                break # Başarılı olduysa diğer instance'lara bakma
            except Exception as e:
                print(f"❌ {instance} hatası: {str(e)[:50]}...")
                continue
        
        if not success:
            print(f"❗ HATA: {account} hiçbir kaynaktan çekilemedi.")
    
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
