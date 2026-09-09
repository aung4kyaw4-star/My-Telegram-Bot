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
    
    # Gemini နဲ့ စာကိုခွဲထုတ်မယ်
    result = process_with_gemini(user_text)
    
    if not result:
        return "ဆရာရဲ့ စာကို အကျွန်နားမလည်လို့ပါဆရာ။ ကျေးဇူးပြုပြီး ပြန်ရှင်းပြပေးပါဆရာ။"
    
    action_type = result.get("type", "chat")
    
    # ---- ငွေစာရင်းထည့်ခြင်း ----
    if action_type == "transaction":
        trans_type = result.get("transaction_type", "")
        amount = result.get("amount", 0)
        description = result.get("description", "")
        person = result.get("person", "")
        category = result.get("category", "")
        
        if amount <= 0:
            return "ဆရာ ငွေပမာဏကို ထည့်ပေးပါဆရာ။"
        
        return database.add_transaction(trans_type, amount, description, person, category)
    
    # ---- မှတ်စုထည့်ခြင်း ----
    elif action_type == "note":
        category = result.get("category", "other")
        title = result.get("title", "")
        description = result.get("description", "")
        
        if not title:
            return "ဆရာ ခေါင်းစဉ်ကို ထည့်ပေးပါဆရာ။"
        
        return database.add_note(category, title, description)
    
    # ---- အကြွေးပြန်ဆပ်ခြင်း ----
    elif action_type == "repay":
        person = result.get("person", "")
        amount = result.get("amount", 0)
        
        if not person or amount <= 0:
            return "ဆရာ လူအမည်နဲ့ ငွေပမာဏကို ထည့်ပေးပါဆရာ။"
        
        return database.repay_debt(person, amount)
    
    # ---- စာရင်းတောင်းခြင်း ----
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
    
    # ---- အစီအစဉ်သိမ်းခြင်း ----
    elif action_type == "schedule":
        title = result.get("title", "အစည်းအဝေး")
        date = result.get("date", "")
        time_val = result.get("
