import os
import requests
import html
import json
import sys

# Logların anında görünmesi için ayar
def log(msg):
    print(f"LOG: {msg}", flush=True)

log("--- SCRIPT BAŞLADI ---")

# GitHub Secrets Kontrolü
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

if not BEARER_TOKEN:
    log("⚠️ HATA: TWITTER_BEARER_TOKEN bulunamadı! Secrets kısmını kontrol et.")
    sys.exit(1)

ACCOUNTS = ["yagosabuncuoglu", "FabrizioRomano", "MatteMoretto"]
STATE_FILE = "last_tweets.json"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        log(f"Telegram Gönderimi: {r.status_code}")
    except Exception as e:
        log(f"Telegram Hatası: {e}")

def check_tweets():
    log(f"Takip edilen hesaplar: {ACCOUNTS}")
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    for account in ACCOUNTS:
        log(f"🔎 {account} için ID aranıyor...")
        try:
            # 1. Kullanıcı ID'sini bulmaya çalış
            user_res = requests.get(
                f"https://api.twitter.com/2/users/by/username/{account}",
                headers=headers
            )
            
            if user_res.status_code != 200:
                log(f"❌ {account} ID bulunamadı! Durum: {user_res.status_code} Mesaj: {user_res.text}")
                continue

            user_id = user_res.json().get("data", {}).get("id")
            log(f"✅ ID bulundu: {user_id}")

            # 2. Tweetleri çekmeyi dene
            log(f"📡 {account} tweetleri isteniyor...")
            tweet_res = requests.get(
                f"https://api.twitter.com/2/users/{user_id}/tweets",
                headers=headers,
                params={"max_results": 5}
            )

            if tweet_res.status_code != 200:
                log(f"❌ Tweet çekilemedi! Durum: {tweet_res.status_code} Mesaj: {tweet_res.text}")
                continue

            log(f"🎉 {account} için veri başarıyla geldi!")
            # Buraya gelirse mesaj atma mantığı çalışır...
            
        except Exception as e:
            log(f"⚠️ Beklenmedik Hata: {e}")

if __name__ == "__main__":
    check_tweets()
    log("--- SCRIPT BİTTİ ---")
