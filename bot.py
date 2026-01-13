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
    return {"init": True} # Dosya yoksa başlangıç değeri ver

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload, timeout=15)

def get_tweets_for_user(username):
    """Tek bir kullanıcı için son tweetleri çeker"""
    url = "https://twitter241.p.rapidapi.com/user-tweets"
    headers = {"x-rapidapi-key": RAPID_KEY, "x-rapidapi-host": "twitter241.p.rapidapi.com"}
    params = {"user": username, "count": "5"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=30)
        instructions = res.json().get("result", {}).get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])
        for instr in instructions:
            if instr.get("type") == "TimelineAddEntries":
                return instr.get("entries", [])
    except: return []
    return []

def check_tweets():
    last_tweets = load_state()
    new_state = last_tweets.copy()
    is_first_run = "init" in last_tweets

    print(f"🔄 Kontrol başlıyor... (İlk çalışma: {is_first_run})")
    
    # En az bir mesaj gelmesi için her hesaba tek tek bakalım (Daha garantidir)
    for account in ACCOUNTS:
        print(f"🔎 {account} kontrol ediliyor...")
        entries = get_tweets_for_user(account)
        
        if not entries:
            print(f"⚠️ {account} için veri alınamadı.")
            continue

        # En son tweeti al
        entry = entries[0]
        content = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
        if not content: continue
        
        # Tweet verisine ulaş (v2 yapısı)
        legacy = content.get("legacy") or content.get("tweet", {}).get("legacy", {})
        tweet_id = content.get("rest_id") or content.get("tweet", {}).get("rest_id")
        tweet_text = legacy.get("full_text", "")
        
        if tweet_id and (is_first_run or last_tweets.get(account) != tweet_id):
            link = f"https://twitter.com/{account}/status/{tweet_id}"
            prefix = "🧪 <b>KONTROL MESAJI:</b>\n" if is_first_run else "🔔 "
            msg = f"{prefix}@{account}\n\n{html.escape(tweet_text)}\n\n<a href='{link}'>Tweeti Görüntüle</a>"
            
            send_telegram(msg)
            new_state[account] = tweet_id
            print(f"✅ Mesaj gönderildi: {account}")
            
            # İlk çalışmada sadece 1 tane mesaj atıp hafızayı güncellemesi yeterli
            if is_first_run: 
                new_state.pop("init", None)
                break 

    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
