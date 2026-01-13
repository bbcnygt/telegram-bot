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
    is_first_run = len(last_tweets) == 0

    # Twitter v2 Search Endpoint
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    query = "(" + " OR ".join([f"from:{acc}" for acc in ACCOUNTS]) + ") -is:retweet"
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "User-Agent": "v2RecentSearchPython"
    }
    
    params = {
        "query": query,
        "max_results": 10,
        "tweet.fields": "author_id,text",
        "expansions": "author_id",
        "user.fields": "username"
    }

    try:
        response = requests.get(search_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Hata: {response.status_code} - {response.text}")
            return

        data = response.json()
        tweets = data.get("data", [])
        users = {u["id"]: u["username"] for u in data.get("includes", {}).get("users", [])}

        found_new = False
        # Tweetleri eskiden yeniye doğru işle
        for tweet in reversed(tweets):
            author_id = tweet.get("author_id")
            screen_name = users.get(author_id)
            tweet_id = tweet.get("id")
            tweet_text = tweet.get("text")

            # İlk çalışma ise veya yeni tweet ise gönder
            if screen_name in ACCOUNTS and (is_first_run or last_tweets.get(screen_name) != tweet_id):
                link = f"https://twitter.com/{screen_name}/status/{tweet_id}"
                prefix = "🧪 <b>İLK TEST MESAJI:</b>\n" if is_first_run else "🔔 "
                msg = f"{prefix}@{screen_name}\n\n{html.escape(tweet_text)}\n\n<a href='{link}'>Tweeti Görüntüle</a>"
                send_telegram(msg)
                new_state[screen_name] = tweet_id
                found_new = True
                if is_first_run: break # İlk çalışmada sadece 1 tane test mesajı at

        if not found_new:
            print("Yeni tweet bulunamadı.")

    except Exception as e:
        print(f"❌ Hata: {e}")
    
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
