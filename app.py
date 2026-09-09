import os
import time
import json
import urllib.request
import urllib.error
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health_check():
    return "Bot is running!", 200

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

OPENER = urllib.request.build_opener()

SYSTEM_PROMPT = "သင်သည် စနစ်ကျပြီး လေးစားမှုရှိသော ပရော်ဖက်ရှင်နယ် အမျိုးသမီး Executive Secretary ဖြစ်သည်။ ရုံးသုံး မြန်မာစာ သတ်ပုံ မှန်ကန်စွာဖြင့် ယဉ်ကျေးပျူငှာစွာ၊ လိုရင်းတိုရှင်းနှင့် တိကျစွာ ပြန်လည် အကြောင်းပြန်ရမည်။"

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with OPENER.open(req, timeout=10) as response:
            pass
    except Exception as e:
        print(f"Telegram Send Error: {e}")

def call_gemini(prompt_text):
    # ဒီနေရာမှာ gemini-3.5-flash ကိုသုံးပါ
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": f"{SYSTEM_PROMPT}\n\nUser: {prompt_text}"}]
        }]
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with OPENER.open(req, timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if 'error' in res_data:
                return f"API Error: {res_data['error'].get('message', 'Unknown error')}"
            return res_data['candidates'][0]['content']['parts'][0]['text']
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return f"HTTP Error {e.code}: {error_body}"
    except Exception as e:
        return f"System Error: {str(e)}"

def run_bot_polling():
    offset = 0
    print("Bot Polling Thread Started!")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=15"
            req = urllib.request.Request(url)
            with OPENER.open(req, timeout=20) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("ok"):
                    for update in result.get("result", []):
                        offset = update["update_id"] + 1
                        if "message" in update and "text" in update["message"]:
                            chat_id = update["message"]["chat"]["id"]
                            user_text = update["message"]["text"]
                            print(f"Received: {user_text}")
                            reply = call_gemini(user_text)
                            print(f"Reply: {reply[:100]}...")
                            send_telegram_message(chat_id, reply)
        except Exception as e:
            print(f"Polling loop error: {e}")
        time.sleep(1)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot_polling)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
