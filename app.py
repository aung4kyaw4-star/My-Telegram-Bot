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

def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id, 
        "text": text,
        "reply_markup": reply_markup
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with OPENER.open(req, timeout=10) as response:
            pass
    except Exception as e:
        print(f"Telegram Send Error: {e}")

def answer_callback(callback_id):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
        payload = json.dumps({"callback_query_id": callback_id}).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        with OPENER.open(req, timeout=5) as response:
            pass
    except Exception as e:
        print(f"Answer callback error: {e}")

# ============ Keyboard Menus ============

def create_main_menu():
    return {
        "inline_keyboard": [
            [{"text": "📊 စာရင်းကြည့်မယ်", "callback_data": "report_menu"},
             {"text": "💰 ငွေထည့်မယ်", "callback_data": "money_menu"}],
            [{"text": "📝 မှတ်စုထည့်မယ်", "callback_data": "note_menu"},
             {"text": "🗑️ ဖျက်မယ်", "callback_data": "delete_menu"}],
            [{"text": "📋 အကြွေးစာရင်း", "callback_data": "report_debts"},
             {"text": "📅 အစီအစဉ်", "callback_data": "schedule_menu"}]
        ]
    }

def create_report_menu():
    return {
        "inline_keyboard": [
            [{"text": "📊 ဒီနေ့", "callback_data": "report_daily"},
             {"text": "📊 မနေ့က", "callback_data": "report_yesterday"}],
            [{"text": "📊 ဒီတစ်ပတ်", "callback_data": "report_week"},
             {"text": "📊 ဒီလ", "callback_data": "report_month"}],
            [{"text": "📊 အကုန်စာရင်း", "callback_data": "report_all"},
             {"text": "🔙 နောက်သို့", "callback_data": "back_main"}]
        ]
    }

def create_money_menu():
    return {
        "inline_keyboard": [
            [{"text": "💸 သုံးငွေ", "callback_data": "type_သုံးငွေ"},
             {"text": "💹 ယူငွေ", "callback_data": "type_ယူငွေ"}],
            [{"text": "💳 ချေးငွေ", "callback_data": "type_ချေးငွေ"},
             {"text": "🔄 ပြန်ဆပ်ငွေ", "callback_data": "type_ပြန်ဆပ်ငွေ"}],
            [{"text": "🔙 နောက်သို့", "callback_data": "back_main"}]
        ]
    }

def create_note_menu():
    return {
        "inline_keyboard": [
            [{"text": "💼 အလုပ်ကိစ္စ", "callback_data": "cat_work"},
             {"text": "👤 ကိုယ်ရေးကိစ္စ", "callback_data": "cat_personal"}],
            [{"text": "📌 အခြားကိစ္စ", "callback_data": "cat_other"},
             {"text": "🔙 နောက်သို့", "callback_data": "back_main"}]
        ]
    }

def create_delete_menu():
    return {
        "inline_keyboard": [
            [{"text": "🗑️ အကုန်ဖျက်မယ်", "callback_data": "delete_all"},
             {"text": "🗑️ ဒီနေ့ဖျက်မယ်", "callback_data": "delete_today"}],
            [{"text": "🗑️ အကြွေးဖျက်မယ်", "callback_data": "delete_debts"},
             {"text": "🗑️ အလုပ်စာရင်း", "callback_data": "delete_work"}],
            [{"text": "🗑️ ကိုယ်ရေးစာရင်း", "callback_data": "delete_personal"},
             {"text": "🗑️ အခြားစာရင်း", "callback_data": "delete_other"}],
            [{"text": "🔙 နောက်သို့", "callback_data": "back_main"}]
        ]
    }

# ============ Handle Callback ============

def handle_callback(chat_id, data):
    print(f"Handling callback: {data}")
    
    if data == "back_main":
        send_telegram_message(chat_id, "ဆရာ ဘာလုပ်ချင်ပါသလဲ။", create_main_menu())
    elif data == "report_menu":
        send_telegram_message(chat_id, "ဆရာ ဘယ်စာရင်းကို ကြည့်ချင်ပါသလဲ။", create_report_menu())
    elif data == "money_menu":
        send_telegram_message(chat_id, "ဆရာ ဘယ်ငွေအမျိုးအစား ထည့်ချင်ပါသလဲ။", create_money_menu())
    elif data == "note_menu":
        send_telegram_message(chat_id, "ဆရာ ဘယ်အမျိုးအစား မှတ်စုထည့်ချင်ပါသလဲ။", create_note_menu())
    elif data == "delete_menu":
        send_telegram_message(chat_id, "ဆရာ ဘာကိုဖျက်ချင်ပါသလဲ။", create_delete_menu())
    elif data == "schedule_menu":
        send_telegram_message(chat_id, "ဆရာ အစီအစဉ်သတ်မှတ်ဖို့ ရက်စွဲနဲ့ အချိန်ကို ရိုက်ထည့်ပေးပါဆရာ။", create_main_menu())
    
    # ---- စာရင်းတောင်းခြင်း ----
    elif data == "report_daily":
        reply = database.get_full_daily_report()
        send_telegram_message(chat_id, reply, create_main_menu())
    elif data == "report_yesterday":
        reply = database.get_detailed_report(days=1, months=0)
        send_telegram_message(chat_id, reply, create_report_menu())
    elif data == "report_week":
        reply = database.get_detailed_report(days=7, months=0)
        send_telegram_message(chat_id, reply, create_report_menu())
    elif data == "report_month":
        reply = database.get_detailed_report(days=0, months=1)
        send_telegram_message(chat_id, reply, create_report_menu())
    elif data == "report_all":
        reply = database.get_detailed_report(days=9999, months=0)
        send_telegram_message(chat_id, reply, create_report_menu())
    elif data == "report_debts":
        reply = database.get_debt_details()
        send_telegram_message(chat_id, reply, create_main_menu())
    
    # ---- ငွေအမျိုးအစား ----
    elif data.startswith("type_"):
        trans_type = data.replace("type_", "")
        send_telegram_message(chat_id, f"ဆရာ {trans_type} အတွက် ပမာဏနဲ့ အကြောင်းအရာကို ရိုက်ထည့်ပေးပါဆရာ။", create_money_menu())
    
    # ---- မှတ်စုအမျိုးအစား ----
    elif data.startswith("cat_"):
        cat = data.replace("cat_", "")
        cat_names = {"work": "အလုပ်ကိစ္စ", "personal": "ကိုယ်ရေးကိုယ်တာကိစ္စ", "other": "အခြားကိစ္စ"}
        send_telegram_message(chat_id, f"ဆရာ {cat_names.get(cat, cat)} အတွက် ခေါင်းစဉ်ကို ရိုက်ထည့်ပေးပါဆရာ။", create_note_menu())
    
    # ---- ဖျက်ခြင်း ----
    elif data == "delete_all":
        reply = database.delete_all_transactions()
        send_telegram_message(chat_id, reply, create_main_menu())
    elif data == "delete_today":
        reply = database.delete_today_transactions()
        send_telegram_message(chat_id, reply, create_main_menu())
    elif data == "delete_debts":
        reply = database.delete_category_transactions("ချေးငွေ")
        send_telegram_message(chat_id, reply, create_main_menu())
    elif data == "delete_work":
        reply = database.delete_category_notes("work")
        send_telegram_message(chat_id, reply, create_main_menu())
    elif data == "delete_personal":
        reply = database.delete_category_notes("personal")
        send_telegram_message(chat_id, reply, create_main_menu())
    elif data == "delete_other":
        reply = database.delete_category_notes("other")
        send_telegram_message(chat_id, reply, create_main_menu())
    
    else:
        send_telegram_message(chat_id, "ဆရာ ကျေးဇူးပြုပြီး ပြန်ရွေးချယ်ပါဆရာ။", create_main_menu())

# ============ Process User Request ============

def process_user_request(chat_id, user_text):
    global MY_CHAT_ID
    if MY_CHAT_ID is None:
        MY_CHAT_ID = str(chat_id)
        print(f"Chat ID saved: {MY_CHAT_ID}")
    
    text_lower = user_text.lower()
    import re
    
    # ---- ပင်မစာများ ----
    if text_lower in ["စာရင်း", "နေ့စာရင်း", "ဒီနေ့စာရင်း"]:
        reply = database.get_full_daily_report()
        send_telegram_message(chat_id, reply, create_main_menu())
        return
    
    if text_lower in ["မနေ့ကစာရင်း"]:
        reply = database.get_detailed_report(days=1, months=0)
        send_telegram_message(chat_id, reply, create_report_menu())
        return
    
    if text_lower in ["အကြွေးစာရင်း", "အကြွေး"]:
        reply = database.get_debt_details()
        send_telegram_message(chat_id, reply, create_main_menu())
        return
    
    # ---- သုံးငွေ ----
    if "သုံးငွေ" in text_lower or "သုံးစွဲ" in text_lower:
        numbers = re.findall(r'\d+', text_lower)
        if numbers:
            amount = int(numbers[0])
            desc = user_text
            for n in numbers:
                desc = desc.replace(n, "")
            desc = desc.replace("သုံးငွေ", "").replace("သုံးစွဲ", "").strip()
            reply = database.add_transaction("သုံးငွေ", amount, desc)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ ငွေပမာဏကို ထည့်ပေးပါဆရာ။", create_money_menu())
        return
    
    # ---- ယူငွေ ----
    if "ယူငွေ" in text_lower or "ဝင်ငွေ" in text_lower:
        numbers = re.findall(r'\d+', text_lower)
        if numbers:
            amount = int(numbers[0])
            desc = user_text
            for n in numbers:
                desc = desc.replace(n, "")
            desc = desc.replace("ယူငွေ", "").replace("ဝင်ငွေ", "").strip()
            reply = database.add_transaction("ယူငွေ", amount, desc)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ ငွေပမာဏကို ထည့်ပေးပါဆရာ။", create_money_menu())
        return
    
    # ---- ချေးငွေ ----
    if "ချေးငွေ" in text_lower or "ချေး" in text_lower:
        numbers = re.findall(r'\d+', text_lower)
        if numbers:
            amount = int(numbers[0])
            desc = user_text
            for n in numbers:
                desc = desc.replace(n, "")
            person = ""
            if "မောင်" in desc or "ဦး" in desc:
                parts = desc.split()
                for part in parts:
                    if "မောင်" in part or "ဦး" in part:
                        person = part
                        break
            desc = desc.replace("ချေးငွေ", "").replace("ချေး", "").strip()
            if person:
                reply = database.add_transaction("ချေးငွေ", amount, desc, person)
            else:
                reply = database.add_transaction("ချေးငွေ", amount, desc)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ ငွေပမာဏကို ထည့်ပေးပါဆရာ။", create_money_menu())
        return
    
    # ---- ပြန်ဆပ် ----
    if "ပြန်ဆပ်" in text_lower:
        numbers = re.findall(r'\d+', text_lower)
        if numbers:
            amount = int(numbers[0])
            desc = user_text
            for n in numbers:
                desc = desc.replace(n, "")
            person = ""
            if "မောင်" in desc or "ဦး" in desc:
                parts = desc.split()
                for part in parts:
                    if "မောင်" in part or "ဦး" in part:
                        person = part
                        break
            if person:
                reply = database.repay_debt(person, amount)
            else:
                desc = desc.replace("ပြန်ဆပ်", "").strip()
                reply = database.add_transaction("ပြန်ဆပ်ငွေ", amount, desc)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ ငွေပမာဏကို ထည့်ပေးပါဆရာ။", create_money_menu())
        return
    
    # ---- မှတ်စုထည့်ခြင်း ----
    if "အလုပ်" in text_lower:
        title = user_text.replace("အလုပ်", "").strip()
        if title:
            reply = database.add_note("work", title)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ အလုပ်ကိစ္စအကြောင်း ထည့်ပေးပါဆရာ။", create_note_menu())
        return
    
    if "ကိုယ်ရေး" in text_lower:
        title = user_text.replace("ကိုယ်ရေး", "").strip()
        if title:
            reply = database.add_note("personal", title)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ ကိုယ်ရေးကိုယ်တာကိစ္စအကြောင်း ထည့်ပေးပါဆရာ။", create_note_menu())
        return
    
    if "အခြား" in text_lower:
        title = user_text.replace("အခြား", "").strip()
        if title:
            reply = database.add_note("other", title)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ အခြားကိစ္စအကြောင်း ထည့်ပေးပါဆရာ။", create_note_menu())
        return
    
    # ---- နားမလည်ရင် ပင်မမီနူးပြမယ် ----
    send_telegram_message(chat_id, "ဆရာ ဘာလုပ်ချင်ပါသလဲ။", create_main_menu())

# ============ Reminder Checker ============

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

# ============ Polling Mode ============

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
                        
                        # Callback Query ကိုစစ်ဆေးမယ်
                        if "callback_query" in update:
                            callback = update["callback_query"]
                            chat_id = callback["message"]["chat"]["id"]
                            data = callback["data"]
                            callback_id = callback["id"]
                            
                            print(f"Callback received: {data}")
                            handle_callback(chat_id, data)
                            answer_callback(callback_id)
                            continue
                        
                        if "message" in update and "text" in update["message"]:
                            chat_id = update["message"]["chat"]["id"]
                            user_text = update["message"]["text"]
                            print(f"Received: {user_text}")
                            process_user_request(chat_id, user_text)
        except Exception as e:
            print(f"Polling loop error: {e}")
        time.sleep(1)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot_polling)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
