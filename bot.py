import os
import requests
import html
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RAPID_KEY = os.getenv("RAPIDAPI_KEY")

# TEST İÇİN: Sadece tek bir hesabı en basit yöntemle kontrol edelim
ACCOUNT = "FabrizioRomano"
STATE_FILE = "last_tweets.json"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload, timeout=15)

def check_tweets():
    # twitter241 API'sinin 'User Tweets' endpoint'ini deneyelim (Arama yerine daha garantidir)
    url = "https://twitter241.p.rapidapi.com/user-tweets"
    
    headers = {
        "x-rapidapi-key": RAPID_KEY,
        "x-rapidapi-host": "twitter241.p.rapidapi.com"
    }
    
    # Fabrizio'nun ID'si (Sabit)
    params = {"user": "FabrizioRomano", "count": "5"}

    try:
        print(f"🔄 {ACCOUNT} için son tweetler çekiliyor...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        data = response.json()
        
        # API'den gelen ham veriyi loglarda görmek için yazdıralım
        print(f"📡 API Yanıtı: {str(data)[:200]}...") 

        # Tweet yolunu bulalım
        instructions = data.get("result", {}).get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])
        
        for instr in instructions:
            if instr.get("type") == "TimelineAddEntries":
                entries = instr.get("entries", [])
                if entries:
                    tweet = entries[0] # En son tweet
                    content = tweet.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {}).get("legacy", {})
                    tweet_text = content.get("full_text", "Tweet içeriği alınamadı")
                    
                    msg = f"🧪 <b>BAĞLANTI BAŞARILI!</b>\n\n@{ACCOUNT}: {html.escape(tweet_text)}"
                    send_telegram(msg)
                    print("✅ Test mesajı Telegram'a gönderildi!")
                    return

        print("⚠️ API çalıştı ama tweet içeriği bulunamadı.")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    check_tweets()
