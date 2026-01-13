import os
import requests
import html
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RAPID_KEY = os.getenv("RAPIDAPI_KEY")

ACCOUNT = "yagosabuncuoglu"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload, timeout=15)

def check_tweets():
    print("🚀 Sorgu gönderiliyor...")
    
    headers = {
        "x-rapidapi-key": RAPID_KEY,
        "x-rapidapi-host": "twitter241.p.rapidapi.com"
    }
    
    # Search yerine bazen daha stabil olan 'user-tweets' de denenebilir 
    # Ama 404 aldığına göre 'search' ile devam ediyoruz, sadece parametreleri sıkılaştırıyoruz.
    url = "https://twitter241.p.rapidapi.com/search"
    params = {"query": f"from:{ACCOUNT}", "type": "Latest", "count": "10"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        data = response.json()
        
        # Loglarda verinin yapısını görelim
        print(f"📡 API Yanıt Anahtarları: {list(data.keys())}")
        
        # Tweetleri bulmak için farklı yolları dene
        entries = []
        try:
            # Yol 1: Standart Search yolu
            instructions = data.get("result", {}).get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {}).get("instructions", [])
            for instr in instructions:
                if instr.get("type") == "TimelineAddEntries":
                    entries = instr.get("entries", [])
                    break
        except:
            pass

        if not entries:
            # Yol 2: Alternatif yapı (Bazı API güncellemeleri için)
            try:
                entries = data.get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {}).get("instructions", [{}])[0].get("entries", [])
            except:
                pass

        if not entries:
            print(f"⚠️ Veri ayıklanamadı. Ham veri (ilk 300 harf): {str(data)[:300]}")
            send_telegram("⚠️ API bağlandı ama tweetler ayıklanamadı. Logları kontrol et!")
            return

        found_any = False
        for entry in entries:
            if "tweet-" not in entry.get("entryId", ""): continue
            
            # Tweet içeriğine sızalım
            res = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
            legacy = res.get("legacy") or res.get("tweet", {}).get("legacy", {})
            t_id = res.get("rest_id") or res.get("tweet", {}).get("rest_id")
            text = legacy.get("full_text", "")

            if t_id and text:
                link = f"https://twitter.com/{ACCOUNT}/status/{t_id}"
                msg = f"🔔 <b>YENİ TWEET YAKALANDI!</b>\n\n@{ACCOUNT}: {html.escape(text)}\n\n<a href='{link}'>Görüntüle</a>"
                send_telegram(msg)
                print(f"✅ Tweet iletildi: {t_id}")
                found_any = True
                break # Şimdilik sadece en sonuncuyu atması yeterli

        if not found_any:
            print("⚠️ Entry bulundu ama tweet içeriği boş.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    check_tweets()
