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
    return {"_init": True}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload, timeout=15)

def check_tweets():
    state = load_state()
    new_state = state.copy()
    is_first_run = state.get("_init", False)
    
    headers = {
        "x-rapidapi-key": RAPID_KEY,
        "x-rapidapi-host": "twitter241.p.rapidapi.com"
    }

    print(f"🚀 Kontrol başlıyor... (İlk çalışma: {is_first_run})")

    for account in ACCOUNTS:
        print(f"🔎 {account} aranıyor...")
        try:
            # Daha stabil olan user-tweets endpointini kullanıyoruz
            url = "https://twitter241.p.rapidapi.com/user-tweets"
            response = requests.get(url, headers=headers, params={"user": account, "count": "5"}, timeout=30)
            data = response.json()

            # Tweet listesine ulaşmaya çalış (API yapısı bazen değişebilir)
            instructions = data.get("result", {}).get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])
            
            entries = []
            for instr in instructions:
                if instr.get("type") == "TimelineAddEntries":
                    entries = instr.get("entries", [])
                    break
            
            if not entries:
                print(f"⚠️ {account} için tweet bulunamadı.")
                continue

            # En güncel tweeti al
            entry = entries[0]
            result = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
            legacy = result.get("legacy") or result.get("tweet", {}).get("legacy", {})
            tweet_id = result.get("rest_id") or result.get("tweet", {}).get("rest_id")
            text = legacy.get("full_text", "")

            if tweet_id and (is_first_run or state.get(account) != tweet_id):
                link = f"https://twitter.com/{account}/status/{tweet_id}"
                label = "🧪 <b>TEST:</b>\n" if is_first_run else "🔔 "
                msg = f"{label}@{account}\n\n{html.escape(text)}\n\n<a href='{link}'>Görüntüle</a>"
                
                send_telegram(msg)
                new_state[account] = tweet_id
                print(f"✅ Mesaj gönderildi: {account}")
                
                # İlk çalışmada her hesaptan birer tane test mesajı alalım
                if is_first_run:
                    continue 

        except Exception as e:
            print(f"❌ {account} hatası: {e}")

    if "_init" in new_state:
        del new_state["_init"]
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
