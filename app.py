import os
import time
import json
import urllib.request
import urllib.error
from flask import Flask
import threading
import database
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health_check():
    return "Bot is running!", 200

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

OPENER = urllib.request.build_opener()

MY_CHAT_ID = None

SYSTEM_PROMPT = """သင်သည် စနစ်ကျပြီး လေးစားမှုရှိသော ပရော်ဖက်ရှင်နယ် အမျိုးသမီး Executive Secretary ဖြစ်သည်။ 
သုံးစွဲသူ၏ ငွေကြေးနှင့် လုပ်ငန်းအချက်အလက်များကို တိကျစွာ မှတ်သားပြီး စနစ်တကျ စီမံခန့်ခွဲရမည်။
သုံးစွဲသူက ဘာမှမမေးဘဲ သို့မဟုတ် ဘာမှမတောင်းဆိုပါက သင်ကိုယ်တိုင် ဘာမှမပြောဘဲ နေရမည်။"""

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
    models = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-flash-latest"]
    last_error = ""
    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{
                    "parts": [{"text": f"{SYSTEM_PROMPT}\n\nUser: {prompt_text}"}]
                }]
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
            with OPENER.open(req, timeout=30) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if 'error' in res_data:
                    last_error = res_data['error'].get('message', 'Unknown error')
                    continue
                return res_data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            last_error = str(e)
            continue
    return f"System Error: {last_error}"

def check_and_send_reminders():
    global MY_CHAT_ID
    if MY_CHAT_ID is None:
        print("Chat ID not set yet.")
        return
    print("Checking reminders...")
    reminders = database.get_due_reminders()
    for reminder_id, message in reminders:
        send_telegram_message(MY_CHAT_ID, message)
        database.mark_reminder_sent(reminder_id)
        print(f"Reminder sent: {message}")

def add_schedule_from_text(text):
    import re
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    time_match = re.search(r'(\d{1,2}:\d{2})', text)
    reminder_match = re.search(r'(\d+)\s*နာရီ', text)
    
    if date_match and time_match:
        date = date_match.group(1)
        time = time_match.group(1)
        title = text
        title = title.replace(date, "").replace(time, "").strip()
        if not title:
            title = "အစည်းအဝေး"
        reminder_hours = 2
        if reminder_match:
            reminder_hours = int(reminder_match.group(1))
        return database.add_schedule_with_reminder(date, time, title, "", reminder_hours)
    return "ကျေးဇူးပြုပြီး ရက်စွဲ (2026-09-10) နဲ့ အချိန် (12:00) ကို ထည့်သွင်းပေးပါ။"

def process_user_request(chat_id, user_text):
    global MY_CHAT_ID
    if MY_CHAT_ID is None:
        MY_CHAT_ID = str(chat_id)
        print(f"Chat ID saved: {MY_CHAT_ID}")
    
    text_lower = user_text.lower()
    
    if "အစီအစဉ်" in text_lower or "သတ်မှတ်" in text_lower or "မှတ်ထား" in text_lower:
        return add_schedule_from_text(user_text)
    elif "စာရင်း" in text_lower or "အစီရင်ခံ" in text_lower or "အကျဉ်းချုပ်" in text_lower:
        return database.get_daily_report()
    elif "သုံးငွေ" in text_lower or "သုံးစွဲ" in text_lower:
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            amount = int(numbers[0])
            desc = text
            for n in numbers:
                desc = desc.replace(n, "")
            desc = desc.replace("သုံးငွေ", "").replace("သုံးစွဲ", "").strip()
            return database.add_transaction("သုံးငွေ", amount, desc)
        return "ကျေးဇူးပြုပြီး ငွေပမာဏကို ထည့်သွင်းပေးပါ။"
    elif "ယူငွေ" in text_lower or "ဝင်ငွေ" in text_lower:
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            amount = int(numbers[0])
            desc = text
            for n in numbers:
                desc = desc.replace(n, "")
            desc = desc.replace("ယူငွေ", "").replace("ဝင်ငွေ", "").strip()
            return database.add_transaction("ယူငွေ", amount, desc)
        return "ကျေးဇူးပြုပြီး ငွေပမာဏကို ထည့်သွင်းပေးပါ။"
    elif "ချေးငွေ" in text_lower:
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            amount = int(numbers[0])
            desc = text
            for n in numbers:
                desc = desc.replace(n, "")
            desc = desc.replace("ချေးငွေ", "").strip()
            return database.add_transaction("ချေးငွေ", amount, desc)
        return "ကျေးဇူးပြုပြီး ငွေပမာဏကို ထည့်သွင်းပေးပါ။"
    elif "ပြန်ဆပ်" in text_lower:
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            amount = int(numbers[0])
            desc = text
            for n in numbers:
                desc = desc.replace(n, "")
            desc = desc.replace("ပြန်ဆပ်", "").strip()
            return database.add_transaction("ပြန်ဆပ်ငွေ", amount, desc)
        return "ကျေးဇူးပြုပြီး ငွေပမာဏကို ထည့်သွင်းပေးပါ။"
    else:
        return call_gemini(user_text)

def run_bot_polling():
    offset = 0
    print("Bot Polling Thread Started!")
    database.init_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_send_reminders, 'interval', minutes=1)
    scheduler.start()
    print("Scheduler started!")
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
                            reply = process_user_request(chat_id, user_text)
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
