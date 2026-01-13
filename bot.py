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

    print(f"🚀 Başlıyoruz... Mod: {'İlk' if is_first_run else 'Normal'}")

    for account in ACCOUNTS:
        print(f"🔎 {account} kontrol ediliyor...")
        try:
            # twitter241 için kullanıcı tweetleri sorgusu
            url = "https://twitter241.p.rapidapi.com/user-tweets"
            response = requests.get(url, headers=headers, params={"user": account, "count": "10"}, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ API Hatası ({account}): {response.status_code}")
                continue

            data = response.json()
            
            # --- TWEET BULMA MANTIĞI (FARKLI YAPILAR İÇİN) ---
            # 1. Yol: result -> data -> user -> timeline...
            # 2. Yol: result -> timeline...
            # 3. Yol: data -> user -> result...
            
            instructions = []
            try:
                # En yaygın yapı
                instructions = data.get("result", {}).get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])
                if not instructions:
                    # Alternatif yapı
                    instructions = data.get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])
            except:
                pass

            entries = []
            for instr in instructions:
                if instr.get("type") == "TimelineAddEntries":
                    entries = instr.get("entries", [])
                    break
            
            if not entries:
                print(f"⚠️ {account} için liste boş döndü. Ham veri özeti: {str(data)[:200]}")
                continue

            # En son tweeti alalım
            for entry in entries:
                if "tweet-" not in entry.get("entryId", ""): continue
                
                res = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
                legacy = res.get("legacy") or res.get("tweet", {}).get("legacy", {})
                t_id = res.get("rest_id") or res.get("tweet", {}).get("rest_id")
                text = legacy.get("full_text", "")

                if t_id and (is_first_run or state.get(account) != t_id):
                    link = f"https://twitter.com/{account}/status/{t_id}"
                    label = "🧪 <b>TEST MESAJI:</b>\n" if is_first_run else "🔔 "
                    msg = f"{label}@{account}\n\n{html.escape(text)}\n\n<a href='{link}'>Görüntüle</a>"
                    
                    send_telegram(msg)
                    new_state[account] = t_id
                    print(f"✅ Mesaj iletildi: {account}")
                    break # Bu hesap için işlemi tamamla

            if is_first_run and account in new_state:
                print("İlk test mesajı başarıyla gönderildi, durduruluyor...")
                break # Sadece 1 tane test mesajı gelsin

        except Exception as e:
            print(f"❌ {account} işlenirken hata: {e}")

    if "_first_run" in new_state:
        del new_state["_first_run"]
    save_state(new_state)

if __name__ == "__main__":
    check_tweets()
