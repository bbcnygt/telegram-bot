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

# Daha geniş ve güncel Nitter listesi
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.no-logs.com",
    "https://nitter.projectsegfau.lt",
    "https://nitter.rawbit.ninja",
    "https://nitter.perennialte.ch"
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
        response = requests.post(url, json=payload, timeout=10)
        if not response.ok:
            print(f"Telegram API Hatası: {response.text}")
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")

def check_tweets():
    last_tweets = load_state()
    new_state = last_tweets.copy()
    
    # İlk çalışma testi mesajı (Eğer daha önce hiç mesaj gelmediyse)
    if not last_tweets:
        send_telegram_message("✅ Bot bağlantısı kuruldu. Tweetler bekleniyor...")

    for account in ACCOUNTS:
        print(f"Kontrol ediliyor: {account}")
        success = False
        
        for instance in NITTER_INSTANCES:
            rss_url = f"{instance}/{account}/rss"
            try:
                # 15 saniye zaman aşımı ekledik ki takılı kalmasın
                feed = feedparser.parse(rss_url)
                
                if not feed.entries:
                    continue
                
                latest_tweet = feed.entries[0]
                tweet_link = latest_tweet.link.replace("nitter.net", "twitter.com") # Linkleri orijinal Twitter'a çevirir
                tweet_content = latest_tweet.title

                # Eğer yeni bir tweet ise gönder
                if last_tweets.get(account) != tweet_link:
                    msg = f"<b>🔔 @{account}</b>\n\n{html.escape(tweet_content)}\n\n<a href='{tweet_link}'>Tweeti Görüntüle</a>"
                    send_telegram_message(msg)
                    new_state[account] = tweet_link
                    print(f"Başarılı: {account} için yeni tweet gönderildi.")
                
                success = True
                break # Bu hesap için veri alındı, bir sonrakine geç
            except Exception as e:
                print(f"{instance} üzerinden {account} çekilemedi, bir sonraki deneniyor...")
                continue
        
        if not success:
            print(f"❌ HATA: {account} hiçbir kaynaktan çekilemedi.")
    
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
