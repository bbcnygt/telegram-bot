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
    requests.post(url, json=payload, timeout=15)

def check_tweets():
    last_tweets = load_state()
    new_state = last_tweets.copy()

    # KREDİ TASARRUFU: 3 hesabı tek bir 'Search' isteği ile kontrol ediyoruz (1 istek = 1 kredi)
    url = "https://twitter241.p.rapidapi.com/search"
    query = "(" + " OR ".join([f"from:{acc}" for acc in ACCOUNTS]) + ")"
    
    headers = {
        "x-rapidapi-key": RAPID_KEY,
        "x-rapidapi-host": "twitter241.p.rapidapi.com"
    }
    
    params = {
        "query": query,
        "type": "Latest",
        "count": "20"
    }

    try:
        print(f"Sorgulanıyor: {query}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        data = response.json()
        
        # API'nin tweet listesini tuttuğu yeri bulalım (Twitter241 standart yapısı)
        # Not: API yapısına göre buradaki 'result' anahtarları değişebilir.
        instructions = data.get("result", {}).get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {}).get("instructions", [])
        
        entries = []
        for instr in instructions:
            if instr.get("type") == "TimelineAddEntries":
                entries = instr.get("entries", [])
                break
        
        for entry in reversed(entries):
            content = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
            if not content: continue
            
            tweet_id = content.get("rest_id")
            legacy = content.get("legacy", {})
            tweet_text = legacy.get("full_text", "")
            screen_name = content.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {}).get("screen_name")
            
            if tweet_id and screen_name in ACCOUNTS and last_tweets.get(screen_name) != tweet_id:
                link = f"https://twitter.com/{screen_name}/status/{tweet_id}"
                msg = f"<b>🔔 @{screen_name}</b>\n\n{html.escape(tweet_text)}\n\n<a href='{link}'>Tweeti Görüntüle</a>"
                send_telegram(msg)
                new_state[screen_name] = tweet_id
                print(f"✅ Yeni tweet gönderildi: {screen_name}")

    except Exception as e:
        print(f"❌ API Hatası: {e}")
    
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
