import os
import requests
import html
import json

# GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

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

def get_user_id(username):
    """Kullanıcı adından ID bulur"""
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    res = requests.get(url, headers=headers)
    return res.json().get("data", {}).get("id")

def check_tweets():
    state = load_state()
    new_state = state.copy()
    is_first_run = state.get("_init", False)
    
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    for account in ACCOUNTS:
        try:
            # 1. Önce kullanıcının sayısal ID'sini alalım
            user_id = get_user_id(account)
            if not user_id: continue

            # 2. O ID'ye ait son tweetleri çekelim
            tweet_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {"max_results": 5, "tweet.fields": "text"}
            res = requests.get(tweet_url, headers=headers, params=params)
            
            if res.status_code == 402:
                print(f"❌ X API Hatası: Krediniz bu işlem için yetersiz.")
                continue

            tweets = res.json().get("data", [])
            if not tweets: continue

            latest_tweet = tweets[0]
            tweet_id = latest_tweet.get("id")
            text = latest_tweet.get("text")

            if tweet_id and (is_first_run or state.get(account) != tweet_id):
                link = f"https://twitter.com/{account}/status/{tweet_id}"
                label = "🧪 <b>X API TEST:</b>\n" if is_first_run else "🔔 "
                msg = f"{label}@{account}\n\n{html.escape(text)}\n\n<a href='{link}'>Görüntüle</a>"
                
                send_telegram(msg)
                new_state[account] = tweet_id
                if is_first_run: break # İlk seferde 1 mesaj yeter

        except Exception as e:
            print(f"❌ {account} hatası: {e}")

    if "_init" in new_state: del new_state["_init"]
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
