import os
import requests
import html
import json

# GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RAPID_KEY = os.getenv("RAPIDAPI_KEY")

ACCOUNTS = ["yagosabuncuoglu", "FabrizioRomano", "MatteMoretto"]
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

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=15)
        print(f"Telegram Yanıtı: {r.status_code}")
    except Exception as e:
        print(f"Telegram Hatası: {e}")

def check_tweets():
    last_tweets = load_state()
    new_state = last_tweets.copy()
    is_first_run = len(last_tweets) == 0 # Eğer dosya yoksa/boşsa True olur

    url = "https://twitter241.p.rapidapi.com/search"
    query = "(" + " OR ".join([f"from:{acc}" for acc in ACCOUNTS]) + ")"
    
    headers = {
        "x-rapidapi-key": RAPID_KEY,
        "x-rapidapi-host": "twitter241.p.rapidapi.com"
    }
    params = {"query": query, "type": "Latest", "count": "5"}

    try:
        print(f"🔎 Sorgulanıyor: {query}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        data = response.json()
        
        # API verisini ayıkla
        instructions = data.get("result", {}).get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {}).get("instructions", [])
        
        entries = []
        for instr in instructions:
            if instr.get("type") == "TimelineAddEntries":
                entries = instr.get("entries", [])
                break
        
        if not entries:
            print("⚠️ API'den hiç tweet dönmedi.")
            return

        # İlk çalışmada sadece en son 1 tanesini at, normalde tüm yenileri at
        tweets_to_process = [entries[0]] if is_first_run else reversed(entries)

        for entry in tweets_to_process:
            content = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
            if not content: continue
            
            # Bazı tweetler 'tweet' anahtarı altında olabiliyor
            if "legacy" not in content and "tweet" in content:
                content = content["tweet"]

            tweet_id = content.get("rest_id")
            legacy = content.get("legacy", {})
            tweet_text = legacy.get("full_text", "")
            screen_name = content.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {}).get("screen_name")
            
            if not screen_name: continue

            # Mesaj gönderme mantığı
            if is_first_run or (tweet_id and last_tweets.get(screen_name) != tweet_id):
                link = f"https://twitter.com/{screen_name}/status/{tweet_id}"
                label = "🧪 <b>İLK KONTROL MESAJI</b>\n" if is_first_run else "🔔 "
                msg = f"{label}@{screen_name}\n\n{html.escape(tweet_text)}\n\n<a href='{link}'>Tweeti Görüntüle</a>"
                
                send_telegram(msg)
                new_state[screen_name] = tweet_id
                print(f"✅ Mesaj iletildi: {screen_name}")
                
                if is_first_run: break # İlk seferde tek mesaj yeterli

    except Exception as e:
        print(f"❌ Hata: {e}")
    
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
