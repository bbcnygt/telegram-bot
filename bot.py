import os
import requests
import html
import json

# GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RAPID_KEY = os.getenv("RAPIDAPI_KEY")

# Test için en garantili hesap
ACCOUNT = "yagosabuncuoglu"
STATE_FILE = "last_tweets.json"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload, timeout=15)

def check_tweets():
    # BOTUN ÇALIŞTIĞINI GÖRMEN İÇİN ANLIK MESAJ
    send_telegram("🚀 <b>Bot Tetiklendi!</b>\nAPI sorgusu gönderiliyor, lütfen bekleyin...")

    headers = {
        "x-rapidapi-key": RAPID_KEY,
        "x-rapidapi-host": "twitter241.p.rapidapi.com"
    }
    
    # 404 VERMEYEN GÜVENLİ ENDPOINT
    url = "https://twitter241.p.rapidapi.com/search"
    params = {"query": f"from:{ACCOUNT}", "type": "Latest", "count": "5"}

    try:
        print(f"🔎 Sorgulanıyor: {ACCOUNT}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            send_telegram(f"❌ API Hatası: {response.status_code}\nEndpoint: /search")
            return

        data = response.json()
        
        # twitter241 SEARCH JSON YOLU (En güncel hali)
        try:
            instructions = data.get("result", {}).get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {}).get("instructions", [])
            
            entries = []
            for instr in instructions:
                if instr.get("type") == "TimelineAddEntries":
                    entries = instr.get("entries", [])
                    break
            
            if not entries:
                send_telegram("⚠️ API bağlandı ama tweet bulunamadı. (Hesap son 24 saatte tweet atmamış olabilir)")
                return

            # En son tweeti çek ve gönder
            entry = entries[0]
            tweet_results = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
            legacy = tweet_results.get("legacy") or tweet_results.get("tweet", {}).get("legacy", {})
            t_id = tweet_results.get("rest_id") or tweet_results.get("tweet", {}).get("rest_id")
            text = legacy.get("full_text", "")

            link = f"https://twitter.com/{ACCOUNT}/status/{t_id}"
            msg = f"✅ <b>BAĞLANTI BAŞARILI!</b>\n\n@{ACCOUNT}: {html.escape(text)}\n\n<a href='{link}'>Görüntüle</a>"
            send_telegram(msg)
            
            # Hafızayı oluştur
            with open(STATE_FILE, "w") as f:
                json.dump({ACCOUNT: t_id}, f)

        except Exception as e:
            send_telegram(f"❌ Veri Okuma Hatası: {e}\n(API yanıtı geldi ama format değişmiş.)")

    except Exception as e:
        send_telegram(f"❌ Bağlantı Hatası: {e}")

if __name__ == "__main__":
    check_tweets()
