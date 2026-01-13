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
    return {"_first_run": True}

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
    is_first_run = state.get("_first_run", False)
    
    headers = {
        "x-rapidapi-key": RAPID_KEY,
        "x-rapidapi-host": "twitter241.p.rapidapi.com"
    }

    for account in ACCOUNTS:
        print(f"🔎 {account} kontrol ediliyor...")
        try:
            url = "https://twitter241.p.rapidapi.com/search"
            params = {"query": f"from:{account}", "type": "Latest", "count": "5"}
            response = requests.get(url, headers=headers, params=params, timeout=30)
            data = response.json()

            # LOGLARINA GÖRE DÜZELTİLEN YOL:
            instructions = data.get("result", {}).get("timeline", {}).get("instructions", [])
            
            entries = []
            for instr in instructions:
                if instr.get("type") == "TimelineAddEntries":
                    entries = instr.get("entries", [])
                    break
            
            if not entries: continue

            for entry in entries:
                if "tweet-" not in entry.get("entryId", ""): continue
                
                # Tweet detaylarını çek
                item = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
                legacy = item.get("legacy") or item.get("tweet", {}).get("legacy", {})
                t_id = item.get("rest_id") or item.get("tweet", {}).get("rest_id")
                text = legacy.get("full_text", "")

                if t_id and (is_first_run or state.get(account) != t_id):
                    link = f"https://twitter.com/{account}/status/{t_id}"
                    label = "🧪 <b>İLK KONTROL:</b>\n" if is_first_run else "🔔 "
                    msg = f"{label}@{account}\n\n{html.escape(text)}\n\n<a href='{link}'>Görüntüle</a>"
                    
                    send_telegram(msg)
                    new_state[account] = t_id
                    print(f"✅ Gönderildi: {account}")
                    if is_first_run: break # İlk çalışmada her hesaptan 1 tane al

        except Exception as e:
            print(f"❌ {account} hatası: {e}")

    if "_first_run" in new_state:
        del new_state["_first_run"]
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
