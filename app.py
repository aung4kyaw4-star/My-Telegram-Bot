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

# ============ User State (Duplicate အတည်ပြုချက်အတွက်) ============
user_states = {}


# ============ Telegram Send Functions ============

def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload_data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload_data["reply_markup"] = reply_markup
    payload = json.dumps(payload_data).encode('utf-8')
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
            [
                {"text": "📊 စာရင်းကြည့်မယ်", "callback_data": "report_menu"},
                {"text": "💰 ငွေထည့်မယ်", "callback_data": "money_menu"}
            ],
            [
                {"text": "📝 မှတ်စုထည့်မယ်", "callback_data": "note_menu"},
                {"text": "🗑️ ဖျက်မယ်", "callback_data": "delete_menu"}
            ],
            [
                {"text": "📋 အကြွေးစာရင်း", "callback_data": "report_debts"},
                {"text": "📅 အစီအစဉ်သတ်မှတ်", "callback_data": "schedule_help"}
            ]
        ]
    }


def create_report_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "📊 ဒီနေ့", "callback_data": "report_daily"},
                {"text": "📊 မနေ့က", "callback_data": "report_yesterday"}
            ],
            [
                {"text": "📊 ဒီတစ်ပတ်", "callback_data": "report_week"},
                {"text": "📊 ဒီလ", "callback_data": "report_month"}
            ],
            [
                {"text": "📊 အကုန်စာရင်း", "callback_data": "report_all"},
                {"text": "🔙 နောက်သို့", "callback_data": "back_main"}
            ]
        ]
    }


def create_money_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "💸 သုံးငွေ", "callback_data": "type_သုံးငွေ"},
                {"text": "💹 ယူငွေ", "callback_data": "type_ယူငွေ"}
            ],
            [
                {"text": "💳 ချေးငွေ", "callback_data": "type_ချေးငွေ"},
                {"text": "🔄 ပြန်ဆပ်ငွေ", "callback_data": "type_ပြန်ဆပ်ငွေ"}
            ],
            [
                {"text": "🔙 နောက်သို့", "callback_data": "back_main"}
            ]
        ]
    }


def create_note_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "💼 အလုပ်ကိစ္စ", "callback_data": "cat_work"},
                {"text": "👤 ကိုယ်ရေးကိစ္စ", "callback_data": "cat_personal"}
            ],
            [
                {"text": "📌 အခြားကိစ္စ", "callback_data": "cat_other"},
                {"text": "🔙 နောက်သို့", "callback_data": "back_main"}
            ]
        ]
    }


def create_delete_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "🗑️ အကုန်ဖျက်မယ်", "callback_data": "delete_all"},
                {"text": "🗑️ ဒီနေ့ဖျက်မယ်", "callback_data": "delete_today"}
            ],
            [
                {"text": "🗑️ အကြွေးဖျက်မယ်", "callback_data": "delete_debts"},
                {"text": "🗑️ အလုပ်စာရင်း", "callback_data": "delete_work"}
            ],
            [
                {"text": "🗑️ ကိုယ်ရေးစာရင်း", "callback_data": "delete_personal"},
                {"text": "🗑️ အခြားစာရင်း", "callback_data": "delete_other"}
            ],
            [
                {"text": "🔙 နောက်သို့", "callback_data": "back_main"}
            ]
        ]
    }


# ============ Handle Callback ============

def handle_callback(chat_id, data):
    print(f"Callback received: {data}")

    if data == "back_main":
        send_telegram_message(chat_id, "ဆရာ ဘာလုပ်ချင်ပါသလဲ။", create_main_menu())

    elif data == "report_menu":
        send_telegram_message(chat_id, "ဆရာ ဘယ်စာရင်းကို ကြည့်ချင်ပါသလဲ။", create_report_menu())

    elif data == "money_menu":
        send_telegram_message(chat_id, "ဆရာ ဘယ်ငွေအမျိုးအစား ထည့်ချင်ပါသလဲ။\nပမာဏကို စာရိုက်ထည့်ပါ။", create_money_menu())

    elif data == "note_menu":
        send_telegram_message(chat_id, "ဆရာ ဘယ်အမျိုးအစား မှတ်စုထည့်ချင်ပါသလဲ။\nခေါင်းစဉ်ကို စာရိုက်ထည့်ပါ။", create_note_menu())

    elif data == "delete_menu":
        send_telegram_message(chat_id, "ဆရာ ဘာကိုဖျက်ချင်ပါသလဲ။", create_delete_menu())

    elif data == "schedule_help":
        send_telegram_message(
            chat_id,
            "ဆရာ အစီအစဉ်သတ်မှတ်ဖို့ ဒီပုံစံအတိုင်း ရိုက်ထည့်ပါ -\n\n"
            "`2026-09-25 09:00 အစည်းအဝေး 2 နာရီအလိုသတိပေးပါ`",
            create_main_menu()
        )

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
        reply = database.get_detailed_report(days=99999, months=0)
        send_telegram_message(chat_id, reply, create_report_menu())

    elif data == "report_debts":
        reply = database.get_debt_details()
        send_telegram_message(chat_id, reply, create_main_menu())

    # ---- ငွေအမျိုးအစား ----
    elif data.startswith("type_"):
        trans_type = data.replace("type_", "")
        send_telegram_message(
            chat_id,
            f"ဆရာ {trans_type} အတွက် ပမာဏနဲ့ အကြောင်းအရာကို ရိုက်ထည့်ပါ။\n\n"
            f"ဥပမာ - `{trans_type} 5000 ကော်ဖီဆိုင်`",
            create_money_menu()
        )

    # ---- မှတ်စုအမျိုးအစား ----
    elif data.startswith("cat_"):
        cat = data.replace("cat_", "")
        cat_names = {"work": "အလုပ်ကိစ္စ", "personal": "ကိုယ်ရေးကိုယ်တာကိစ္စ", "other": "အခြားကိစ္စ"}
        send_telegram_message(
            chat_id,
            f"ဆရာ {cat_names.get(cat, cat)} အတွက် ခေါင်းစဉ်ကို ရိုက်ထည့်ပါ။\n\n"
            f"ဥပမာ - `{cat_names.get(cat, cat)} Report တင်ရမယ်`",
            create_note_menu()
        )

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

    text_lower = user_text.lower().strip()
    chat_id_str = str(chat_id)

    # ====== Duplicate အတည်ပြုချက် စစ်ဆေးခြင်း ======
    if chat_id_str in user_states:
        state = user_states[chat_id_str]
        if state.get("action") == "waiting_duplicate_confirm":
            if "ထပ်မှတ်" in text_lower or "yes" in text_lower or "ok" in text_lower:
                pending = state["pending_data"]
                if pending["type"] == "note":
                    reply = database.add_note(
                        pending["category"],
                        pending["title"],
                        pending.get("description", "")
                    )
                elif pending["type"] == "transaction":
                    reply = database.add_transaction(
                        pending["trans_type"],
                        pending["amount"],
                        pending.get("description", ""),
                        pending.get("person", "")
                    )
                elif pending["type"] == "schedule":
                    reply = database.add_schedule_with_reminder(
                        pending["date"],
                        pending["time_val"],
                        pending["title"],
                        "",
                        pending.get("reminder_hours", 2)
                    )
                else:
                    reply = "⚠️ မမှတ်နိုင်ပါ။"

                del user_states[chat_id_str]
                send_telegram_message(chat_id, reply, create_main_menu())
                return
            else:
                del user_states[chat_id_str]
                send_telegram_message(
                    chat_id,
                    "✅ ဆရာ ထပ်မမှတ်တော့ပါဘူး။",
                    create_main_menu()
                )
                return

    # ====== ၁။ အစီအစဉ် ======
    if "အစီအစဉ်" in text_lower or "အစည်းအဝေး" in text_lower:
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', user_text)
        time_match = re.search(r'(\d{1,2}:\d{2})', user_text)
        reminder_match = re.search(r'(\d+)\s*နာရီ', user_text)

        if date_match and time_match:
            date = date_match.group(1)
            time_val = time_match.group(1)
            reminder_hours = int(reminder_match.group(1)) if reminder_match else 2

            title = user_text
            title = title.replace(date, "").replace(time_val, "").strip()
            title = title.replace("အစီအစဉ်", "").replace("သတ်မှတ်", "").strip()
            title = title.replace("နာရီအလိုသတိပေးပါ", "").strip()
            title = re.sub(r'\d+', '', title).strip()
            if not title:
                title = "အစည်းအဝေး"

            if database.check_duplicate_schedule(date, time_val, title):
                user_states[chat_id_str] = {
                    "action": "waiting_duplicate_confirm",
                    "pending_data": {
                        "type": "schedule",
                        "date": date,
                        "time_val": time_val,
                        "title": title,
                        "reminder_hours": reminder_hours
                    }
                }
                send_telegram_message(
                    chat_id,
                    f"⚠️ ဆရာ ဒီအစီအစဉ် '{title}' ကို {date} {time_val} တွင် မှတ်ထားပြီးသားပါဆရာ။\n\nထပ်မှတ်ချင်လား?\n• 'ထပ်မှတ်' - ထပ်မှတ်မယ်\n• 'မမှတ်' - မမှတ်ဘူး",
                    create_main_menu()
                )
                return

            reply = database.add_schedule_with_reminder(date, time_val, title, "", reminder_hours)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        else:
            send_telegram_message(
                chat_id,
                "ဆရာ ရက်စွဲ (2026-09-25) နဲ့ အချိန် (09:00) ကို ထည့်ပေးပါဆရာ။",
                create_main_menu()
            )
            return

    # ====== ၂။ သုံးငွေ ======
    if "သုံးငွေ" in text_lower or "သုံးစွဲ" in text_lower:
        numbers = re.findall(r'\d+', text_lower)
        if numbers:
            amount = int(numbers[0])
            desc = user_text
            for n in numbers:
                desc = desc.replace(n, "")
            desc = desc.replace("သုံးငွေ", "").replace("သုံးစွဲ", "").strip()

            if database.check_duplicate_transaction("သုံးငွေ", amount, desc):
                user_states[chat_id_str] = {
                    "action": "waiting_duplicate_confirm",
                    "pending_data": {
                        "type": "transaction",
                        "trans_type": "သုံးငွေ",
                        "amount": amount,
                        "description": desc
                    }
                }
                send_telegram_message(
                    chat_id,
                    f"⚠️ ဆရာ ဒီငွေစာရင်း 'သုံးငွေ {amount} ကျပ် ({desc})' ကို ဒီနေ့ မှတ်ထားပြီးသားပါဆရာ။\n\nထပ်မှတ်ချင်လား?\n• 'ထပ်မှတ်' - ထပ်မှတ်မယ်\n• 'မမှတ်' - မမှတ်ဘူး",
                    create_main_menu()
                )
                return

            reply = database.add_transaction("သုံးငွေ", amount, desc)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ ငွေပမာဏကို ထည့်ပေးပါဆရာ။", create_money_menu())
        return

    # ====== ၃။ ယူငွေ ======
    if "ယူငွေ" in text_lower or "ဝင်ငွေ" in text_lower:
        numbers = re.findall(r'\d+', text_lower)
        if numbers:
            amount = int(numbers[0])
            desc = user_text
            for n in numbers:
                desc = desc.replace(n, "")
            desc = desc.replace("ယူငွေ", "").replace("ဝင်ငွေ", "").strip()

            if database.check_duplicate_transaction("ယူငွေ", amount, desc):
                user_states[chat_id_str] = {
                    "action": "waiting_duplicate_confirm",
                    "pending_data": {
                        "type": "transaction",
                        "trans_type": "ယူငွေ",
                        "amount": amount,
                        "description": desc
                    }
                }
                send_telegram_message(
                    chat_id,
                    f"⚠️ ဆရာ ဒီငွေစာရင်း 'ယူငွေ {amount} ကျပ် ({desc})' ကို ဒီနေ့ မှတ်ထားပြီးသားပါဆရာ။\n\nထပ်မှတ်ချင်လား?\n• 'ထပ်မှတ်' - ထပ်မှတ်မယ်\n• 'မမှတ်' - မမှတ်ဘူး",
                    create_main_menu()
                )
                return

            reply = database.add_transaction("ယူငွေ", amount, desc)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ ငွေပမာဏကို ထည့်ပေးပါဆရာ။", create_money_menu())
        return

    # ====== ၄။ ချေးငွေ ======
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

            if database.check_duplicate_transaction("ချေးငွေ", amount, desc, person):
                user_states[chat_id_str] = {
                    "action": "waiting_duplicate_confirm",
                    "pending_data": {
                        "type": "transaction",
                        "trans_type": "ချေးငွေ",
                        "amount": amount,
                        "description": desc,
                        "person": person
                    }
                }
                send_telegram_message(
                    chat_id,
                    f"⚠️ ဆရာ ဒီငွေစာရင်း 'ချေးငွေ {amount} ကျပ်' ကို ဒီနေ့ မှတ်ထားပြီးသားပါဆရာ။\n\nထပ်မှတ်ချင်လား?\n• 'ထပ်မှတ်' - ထပ်မှတ်မယ်\n• 'မမှတ်' - မမှတ်ဘူး",
                    create_main_menu()
                )
                return

            if person:
                reply = database.add_transaction("ချေးငွေ", amount, desc, person)
            else:
                reply = database.add_transaction("ချေးငွေ", amount, desc)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ ငွေပမာဏကို ထည့်ပေးပါဆရာ။", create_money_menu())
        return

    # ====== ၅။ ပြန်ဆပ် ======
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

    # ====== ၆။ စာရင်းတောင်းခြင်း ======
    if text_lower in ["စာရင်း", "နေ့စာရင်း", "ဒီနေ့စာရင်း"]:
        reply = database.get_full_daily_report()
        send_telegram_message(chat_id, reply, create_main_menu())
        return

    if text_lower in ["မနေ့ကစာရင်း"]:
        reply = database.get_detailed_report(days=1, months=0)
        send_telegram_message(chat_id, reply, create_report_menu())
        return

    if text_lower in ["ဒီတစ်ပတ်စာရင်း", "တစ်ပတ်စာရင်း"]:
        reply = database.get_detailed_report(days=7, months=0)
        send_telegram_message(chat_id, reply, create_report_menu())
        return

    if text_lower in ["ဒီလစာရင်း", "လစာရင်း"]:
        reply = database.get_detailed_report(days=0, months=1)
        send_telegram_message(chat_id, reply, create_report_menu())
        return

    if text_lower in ["အကုန်စာရင်း", "အကုန်လုံး"]:
        reply = database.get_detailed_report(days=99999, months=0)
        send_telegram_message(chat_id, reply, create_report_menu())
        return

    if text_lower in ["အကြွေးစာရင်း", "အကြွေး"]:
        reply = database.get_debt_details()
        send_telegram_message(chat_id, reply, create_main_menu())
        return

    if text_lower in ["အလုပ်စာရင်း", "အလုပ်"]:
        reply = database.get_category_report("work")
        send_telegram_message(chat_id, reply, create_main_menu())
        return

    if text_lower in ["ကိုယ်ရေးစာရင်း", "ကိုယ်ရေး"]:
        reply = database.get_category_report("personal")
        send_telegram_message(chat_id, reply, create_main_menu())
        return

    if text_lower in ["အခြားစာရင်း", "အခြား"]:
        reply = database.get_category_report("other")
        send_telegram_message(chat_id, reply, create_main_menu())
        return

    # ====== ၇။ မှတ်စုထည့်ခြင်း ======
    if "အလုပ်" in text_lower:
        title = user_text.replace("အလုပ်", "").strip()
        if title:
            if database.check_duplicate_note("work", title):
                user_states[chat_id_str] = {
                    "action": "waiting_duplicate_confirm",
                    "pending_data": {
                        "type": "note",
                        "category": "work",
                        "title": title
                    }
                }
                send_telegram_message(
                    chat_id,
                    f"⚠️ ဆရာ ဒီမှတ်စု 'အလုပ် {title}' ကို မှတ်ထားပြီးသားပါဆရာ။\n\nထပ်မှတ်ချင်လား?\n• 'ထပ်မှတ်' - ထပ်မှတ်မယ်\n• 'မမှတ်' - မမှတ်ဘူး",
                    create_main_menu()
                )
                return
            reply = database.add_note("work", title)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ အလုပ်ကိစ္စအကြောင်း ထည့်ပေးပါဆရာ။", create_note_menu())
        return

    if "ကိုယ်ရေး" in text_lower:
        title = user_text.replace("ကိုယ်ရေး", "").strip()
        if title:
            if database.check_duplicate_note("personal", title):
                user_states[chat_id_str] = {
                    "action": "waiting_duplicate_confirm",
                    "pending_data": {
                        "type": "note",
                        "category": "personal",
                        "title": title
                    }
                }
                send_telegram_message(
                    chat_id,
                    f"⚠️ ဆရာ ဒီမှတ်စု 'ကိုယ်ရေး {title}' ကို မှတ်ထားပြီးသားပါဆရာ။\n\nထပ်မှတ်ချင်လား?\n• 'ထပ်မှတ်' - ထပ်မှတ်မယ်\n• 'မမှတ်' - မမှတ်ဘူး",
                    create_main_menu()
                )
                return
            reply = database.add_note("personal", title)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ ကိုယ်ရေးကိုယ်တာကိစ္စအကြောင်း ထည့်ပေးပါဆရာ။", create_note_menu())
        return

    if "အခြား" in text_lower:
        title = user_text.replace("အခြား", "").strip()
        if title:
            if database.check_duplicate_note("other", title):
                user_states[chat_id_str] = {
                    "action": "waiting_duplicate_confirm",
                    "pending_data": {
                        "type": "note",
                        "category": "other",
                        "title": title
                    }
                }
                send_telegram_message(
                    chat_id,
                    f"⚠️ ဆရာ ဒီမှတ်စု 'အခြား {title}' ကို မှတ်ထားပြီးသားပါဆရာ။\n\nထပ်မှတ်ချင်လား?\n• 'ထပ်မှတ်' - ထပ်မှတ်မယ်\n• 'မမှတ်' - မမှတ်ဘူး",
                    create_main_menu()
                )
                return
            reply = database.add_note("other", title)
            send_telegram_message(chat_id, reply, create_main_menu())
            return
        send_telegram_message(chat_id, "ဆရာ အခြားကိစ္စအကြောင်း ထည့်ပေးပါဆရာ။", create_note_menu())
        return

    # ====== ၈။ နားမလည်ရင် ======
    send_telegram_message(
        chat_id,
        "ဆရာ ဘာလုပ်ချင်ပါသလဲ။ အောက်က ခလုတ်တွေကို နှိပ်ကြည့်ပါ။",
        create_main_menu()
    )


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
