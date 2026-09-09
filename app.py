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
import re

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health_check():
    return "Bot is running!", 200

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

OPENER = urllib.request.build_opener()

MY_CHAT_ID = None

SYSTEM_PROMPT = """သင်သည် ယဉ်ကျေးပျူငှာပြီး စနစ်ကျတဲ့ အမျိုးသမီး Executive Secretary ဖြစ်ပါတယ်။
သုံးစွဲသူကို "ဆရာ" လို့ခေါ်ပြီး ကိုယ့်ကိုယ်ကို "အကျွန်" လို့သုံးပါ။

သုံးစွဲသူရဲ့ စာကို ခွဲခြမ်းစိတ်ဖြာပြီး အောက်ပါအတိုင်း JSON ပုံစံဖြင့် ပြန်ပေးပါ။

၁။ ငွေစာရင်းဆိုရင်:
{
    "type": "transaction",
    "transaction_type": "သုံးငွေ/ယူငွေ/ချေးငွေ/ပြန်ဆပ်ငွေ",
    "amount": 5000,
    "description": "ကော်ဖီဆိုင်",
    "person": "မောင်မောင်"
}

၂။ မှတ်စုဆိုရင် (အလုပ်၊ ကိုယ်ရေး၊ အခြား):
{
    "type": "note",
    "category": "work/personal/other",
    "title": "ခေါင်းစဉ်",
    "description": "အသေးစိတ်"
}

၃။ အကြွေးပြန်ဆပ်ရင်:
{
    "type": "repay",
    "person": "မောင်မောင်",
    "amount": 5000
}

၄။ စာရင်းတောင်းရင်:
{
    "type": "report",
    "report_type": "daily/yesterday/week/month/debts"
}

၅။ အစီအစဉ်ဆိုရင်:
{
    "type": "schedule",
    "title": "အစည်းအဝေး",
    "date": "2026-09-10",
    "time": "12:00",
    "reminder_hours": 2
}

၆။ စကားပြောဆိုရင်:
{
    "type": "chat",
    "message": "သင့်အဖြေ"
}

အရေးကြီး - "အလုပ်" ဆိုရင် category: "work", "ကိုယ်ရေး" ဆိုရင် "personal", "အခြား" ဆိုရင် "other" လို့သုံးပါ။
သုံးစွဲသူရဲ့ စာကို အပေါ်ပါပုံစံအတိုင်း JSON ပြန်ပေးပါ။"""

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
    try:
        models = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-flash-latest"]
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
                        continue
                    return res_data['candidates'][0]['content']['parts'][0]['text']
            except:
                continue
        return None
    except:
        return None

def process_with_gemini(user_text):
    try:
        gemini_response = call_gemini(user_text)
        if not gemini_response:
            return None
        
        json_match = re.search(r'\{.*\}', gemini_response, re.DOTALL)
        if not json_match:
            return None
        
        data = json.loads(json_match.group())
        return data
    except:
        return None

def process_user_request(chat_id, user_text):
    global MY_CHAT_ID
    if MY_CHAT_ID is None:
        MY_CHAT_ID = str(chat_id)
        print(f"Chat ID saved: {MY_CHAT_ID}")
    
    result = process_with_gemini(user_text)
    
    if not result:
        return "ဆရာရဲ့ စာကို အကျွန်နားမလည်လို့ပါဆရာ။ ကျေးဇူးပြုပြီး ပြန်ရှင်းပြပေးပါဆရာ။"
    
    action_type = result.get("type", "chat")
    
    if action_type == "transaction":
        trans_type = result.get("transaction_type", "")
        amount = result.get("amount", 0)
        description = result.get("description", "")
        person = result.get("person", "")
        category = result.get("category", "")
        
        if amount <= 0:
            return "ဆရာ ငွေပမာဏကို ထည့်ပေးပါဆရာ။"
        
        return database.add_transaction(trans_type, amount, description, person, category)
    
    elif action_type == "note":
        category = result.get("category", "other")
        title = result.get("title", "")
        description = result.get("description", "")
        
        if not title:
            return "ဆရာ ခေါင်းစဉ်ကို ထည့်ပေးပါဆရာ။"
        
        return database.add_note(category, title, description)
    
    elif action_type == "repay":
        person = result.get("person", "")
        amount = result.get("amount", 0)
        
        if not person or amount <= 0:
            return "ဆရာ လူအမည်နဲ့ ငွေပမာဏကို ထည့်ပေးပါဆရာ။"
        
        return database.repay_debt(person, amount)
    
    elif action_type == "report":
        report_type = result.get("report_type", "daily")
        
        if report_type == "debts":
            return database.get_debt_details()
        elif report_type == "yesterday":
            return database.get_detailed_report(days=1, months=0)
        elif report_type == "week":
            return database.get_detailed_report(days=7, months=0)
        elif report_type == "month":
            return database.get_detailed_report(days=0, months=1)
        elif report_type == "all":
            return database.get_detailed_report(days=9999, months=0)
        else:
            return database.get_full_daily_report()
    
    elif action_type == "schedule":
        title = result.get("title", "အစည်းအဝေး")
        date = result.get("date", "")
        time_val = result.get("time", "")
        reminder_hours = result.get("reminder_hours", 2)
        
        if not date or not time_val:
            return "ဆရာ ရက်စွဲနဲ့ အချိန်ကို ထည့်ပေးပါဆရာ။"
        
        return database.add_schedule_with_reminder(date, time_val, title, "", reminder_hours)
    
    else:
        return result.get("message", "ဆရာ ကျေးဇူးပြုပြီး ပြန်ရှင်းပြပေးပါဆရာ။")

def check_and_send_reminders():
    global MY_CHAT_ID
    if MY_CHAT_ID is None:
        return
    try:
        reminders = database.get_due_reminders()
        for reminder_id, message in reminders:
            send_telegram_message(MY_CHAT_ID, message)
            database.mark_reminder_sent(reminder_id)
            print(f"Reminder sent: {message}")
    except Exception as e:
        print(f"Reminder check error: {e}")

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
